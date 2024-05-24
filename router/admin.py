import pymongo
from fastapi import APIRouter, HTTPException
from router.users import user_coll
from router.devices import motor_info_coll
from model.devices import Motor_info
from pydantic import BaseModel

router = APIRouter()

class Credential(BaseModel):
    user_id: str
    motor_id: str

class User_Id(BaseModel):
    user_id: str

@router.get("/get_users")
async def get_all_users():
    try:
        users = user_coll.find()
        if users:
            all_users = [user for user in user_coll.find({}, {"_id": 0})]
            return {"users": all_users}
    except Exception:
        raise HTTPException(status_code=404, detail="No any user.")
    
@router.post("/get/user_info")
async def get_user_by_id(usr: User_Id):
    try:
        user = user_coll.find_one({"user_id": usr.user_id})
        if user :
            return {"user":{
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "motor_owned": user["motor_owned"]
            }}
    except Exception as e :
        return e
    
@router.get("/get_motors")
async def get_all_motors():
    try:
        motors = motor_info_coll.find()
        if motors:
            all_motors = [motor for motor in motor_info_coll.find({}, {"_id":0})]
            return {"data": all_motors}
    except Exception:
        raise HTTPException(status_code=404, detail="No any motor in system.")

@router.post("/add_motor")
async def add_motor_to_customer(cred: Credential):
    try:
        user = user_coll.find_one({"user_id": cred.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found.")
        existing_motor = user_coll.aggregate([
            {"$match": {"user_id": cred.user_id}},
            {"$project": {"_id": 0, "motor_owned": 1}},
            {"$unwind": "$motor_owned"},
            {"$match": {"motor_owned.motor_id": cred.motor_id}},
        ])
        if list(existing_motor):
            return {"msg": "This motor_id has already added."}
        new_motor_own = {"motor_id": cred.motor_id}
        user_coll.update_one(
            {"user_id": cred.user_id},
            {"$push": {"motor_owned": new_motor_own}}
        )
        return {"msg": "Motor added successfully", "motor_id": cred.motor_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete_motor")
async def remove_motor_from_customer(cred: Credential):
    try:
        user = user_coll.find_one({"user_id": cred.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found.")

        # Use $pull operator to remove the motor_id
        result = user_coll.update_one(
            {"user_id": cred.user_id},
            {"$pull": {"motor_owned": {"motor_id": cred.motor_id}}},
        )

        if result.matched_count == 0:
            return {"msg": "Motor_id not found for this user."}

        # Motor removed successfully
        return {"msg": "Motor removed successfully", "motor_id": cred.motor_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/add_new_motor")
async def add_new_motor(motor: Motor_info):
    try:
        motor_existed = motor_info_coll.find_one({"motor_id": motor.motor_id})
        if motor_existed:
            return {"msg": "This motor is existed."}
        motor_info_coll.insert_one(motor.model_dump())
        return {"msg": "Added new motor successfully"}
    except Exception:
        raise HTTPException(status_code=500)

