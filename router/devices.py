from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta
from database import db
from model.devices import Motor_id, Motor_info, Sensors, IoT_Recv

router = APIRouter()
motor_data_coll = db.collection("motor_data")
motor_info_coll = db.collection("motor_info")

tz = timezone(timedelta(hours=7))

@router.get("/")
async def hello_devices():
    return {"msg": "Device Router!"}

def getMotorFromData(motor_id: str):
    motor = motor_data_coll.find_one({"motor_id": motor_id})
    return motor
###___ Motor Info ___###
@router.post("/motor/add")
async def add_motor(motor_info: Motor_info):
    motor = motor_info_coll.find_one(motor_info.model_dump())
    if motor:
        return { "msg": "This motor is already added." }
    motor_info_coll.insert_one(motor_info.model_dump())
    return { "msg": "Motor added." }

@router.post("/motor/find")
async def find_motor(motor: Motor_id):
    motor = motor_info_coll.find_one(motor.model_dump())
    if motor :
        return {"motor_id": motor["motor_id"],
                "motor_name": motor["motor_name"],
                "department": motor["department"],
                "location": motor["location"]
            }
    else:
        raise HTTPException(status_code=404)

@router.delete("/motor/delete")
async def delete_motor(motor_id: Motor_id):
    try:
        motor = motor_info_coll.find_one(motor_id.model_dump())
        if motor :
            motor_info_coll.delete_one(motor_id.model_dump())
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# @router.post('/data/migration')
async def migrate_data(ft):
    motor_info = motor_info_coll.find_one(ft)
    motor_data = motor_data_coll.find_one(ft)
    if motor_info:
        record = {
            "temperature": [data['temperature'] for data in motor_data['sensors']],
            "vibration": [data['vibration'] for data in motor_data['sensors']],
            "voltage": [data['voltage'] for data in motor_data['sensors']],
            "current": [data['current'] for data in motor_data['sensors']],
            "timestamp": f"{motor_data['sensors'][0]['timestamp']} - {motor_data['sensors'][-1]['timestamp']}"
        }
        update = {"$push":{"records": record}}
        motor_info_coll.update_one(filter=ft, update=update, upsert=True)
        clean = {"$set": {"sensors": []}}
        motor_data_coll.update_one(filter=ft, update=clean)
        return {"msg": "Data migrated completed."}
    raise HTTPException(status_code=404)

###___ Motor Data / Sensor ___###

# Adding sensors data from esp
@router.post("/sensor/store")
async def store_data(mt_data: IoT_Recv):
    sensor = {
        "temperature": mt_data.temperature,
        "vibration": mt_data.vibration,
        "voltage": mt_data.voltage,
        "current": mt_data.current,
        "timestamp": datetime.now(tz=tz)
    }
    motor = motor_data_coll.find_one({"motor_id":mt_data.motor_id})
    if motor:
        ft = {"motor_id": mt_data.motor_id}
        update = {"$push": {"sensors": sensor}}
        if len(motor['sensors']) == 100: # every 1 hr or 1800 records // 100 doc compress -> 1 doc
            migrate = await migrate_data(ft)
            return migrate
        else:
            motor_data_coll.update_one(ft, update=update, upsert=True) #push new data to sensors array
            return {"msg": "Added new data."}
    else:
        motor = {
            "motor_id": mt_data.motor_id,
            "sensors": [sensor] #create array with first sensors data
        }
        motor_data_coll.insert_one(motor)
        return { "msg": "Stored data to database." }

# Getting sensors data from web-app
@router.post("/get/motor_data")
async def get_motor_data(motor: Motor_id):
    motor = getMotorFromData(motor.motor_id)
    if motor:
        sensors = [Sensors(**sensor) for sensor in motor["sensors"]]
        return { "motor_id": motor["motor_id"],
                "data": sensors}
    else:
        return { "msg": "Motor not found." }

@router.post("/get/last_data")
async def get_last_data(motor_id: Motor_id):
    motor = motor_data_coll.find_one(motor_id.model_dump())
    if not motor:
        return HTTPException(status_code=404, detail="motor not found")
    if motor and len(motor["sensors"]) >= 1:
        return {
            "motor_id": motor["motor_id"],
            "data": motor["sensors"][-1]
        }
    else:
        pass

@router.post("/get/motor_temp")
async def get_motor_temp(motor_id: Motor_id):
    motor = motor_data_coll.find_one(motor_id.model_dump())
    if motor:
        return {"temperature": motor["sensors"][-1]["temperature"]}

@router.post("/records")
async def get_records(motor: Motor_id):
    try:
        motor = motor_info_coll.find_one(motor.model_dump())
        if motor:
            return {"data": motor["records"]}
        # motors = [data for data in motor_info_coll.find({}, {"_id": 0})]
        # return {"msg": motors}
    except Exception as e:
        return {"error": e}