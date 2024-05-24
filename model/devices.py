import pytz
from pydantic import BaseModel
from datetime import datetime, timezone

bkk_tz = pytz.timezone('Asia/Bangkok')


class IoT_Recv(BaseModel): # Data that sent by MQTT.
    motor_id: str
    temperature: float
    vibration: float
    voltage: float
    current: float
    timestamp: datetime = datetime.now(bkk_tz)

class Sensors(BaseModel): # Model for only sensors that will be call from web-app.
    temperature: float
    vibration: float
    voltage: float
    current: float
    timestamp: datetime = datetime.now(bkk_tz)

class Motor_info(BaseModel):
    motor_id: str
    motor_name: str
    location: str
    series: str
    department: str
    create_on: datetime = datetime.now()

class Motor_info(BaseModel):
    motor_id: str
    motor_name: str
    location: str
    series: str
    department: str
    create_on: datetime = datetime.now(bkk_tz)
    records: list = []

class Motor_id(BaseModel):
    motor_id: str