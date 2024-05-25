import uuid
import hashlib
from fastapi import APIRouter, HTTPException, Response, Depends, UploadFile, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from database import db
from router.devices import motor_info_coll
from auth import Auth, ACCESS_TOKEN_EXPIRE_MINUTES
from model.devices import Motor_id
from model.users import Register, Login, Username
# from gridfs import GridFS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()
user_coll = db.collection("users")
# fs = GridFS(db.get_db_fs())

# Function to hash the password
def hash_password(password: str) -> str:
    algorithm = "sha256"
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(password.encode("utf-8"))
    hashed_password = hash_obj.hexdigest()
    return hashed_password

def get_user(email: str):
    user = user_coll.find_one({"email": email})
    return user

async def authenticate_user(user: Login):
    usr = get_user(user.email)
    hashed_passwd = hash_password(user.passwd)
    if not usr:
        return False
    if hashed_passwd != usr["passwd"]:
        return False
    return usr

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user_id = Auth.verify_authen(token)
    user = user_coll.find_one({"user_id": user_id})
    if not user:
        return False
    return user

@router.get("/")
async def hello_user():
    return {"msg": "Users Router!"}

@router.post("/register")
async def register(user: Register):
    try:
        user_exist = get_user(user.email)
        if user_exist:
            raise HTTPException(status_code=400, detail="Email already used.")
        #hash the password
        hashed_passwd = hash_password(user.passwd)
        user.passwd = hashed_passwd
        #assign user_id
        user_id = str(uuid.uuid4())
        user.user_id = user_id
        user_coll.insert_one(user.model_dump())
        return {"msg": "Registering successful."}
    except Exception as e:
        return {"msg": e}

@router.post("/login")
async def login(res: Response, user: Login):
    usr = await authenticate_user(user)
    if not usr:
        raise HTTPException(status_code=404, detail="User not found.")
    access_token = await Auth.create_access_token(data={"id": usr["user_id"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # res.set_cookie(key="token", value=access_token)
    res.set_cookie(key="token", value=access_token, httponly=True)
    return {"msg": "Logged in successfully.",
            "user":{
                "user_id": usr["user_id"],
                "username": usr["username"],
                "email": usr["email"],
                "role": usr["role"],
                "motor_owned": usr["motor_owned"]
            },
            "token": access_token
        }
@router.get("/is_authen")
async def is_authen(token: str = Depends(oauth2_scheme)):
    try:
        user_id = await Auth.verify_authen(token)
        user = user_coll.find_one({"user_id": user_id})
        if user:
            return {"isAuthen": True}
        return {"isAuthen": False}
    except Exception as e:
        raise HTTPException(status_code=500)

# Adding motor by customer
@router.post("/add/motor")
async def add_motor_owned(motor: Motor_id, token: str = Depends(oauth2_scheme)):
    try:
        user_id = await Auth.verify_authen(token)
        user = user_coll.find_one({"user_id": user_id})
        motor = motor_info_coll.find_one({"motor_id": motor.motor_id})
        if (not user) or (not motor): # If no user or motor
            raise HTTPException(status_code=404, detail="User or Motor not found")
        existing_motor = user_coll.aggregate([
            {"$match": {"user_id": user_id}},
            {"$project": {"_id": 0, "motor_owned": 1}},
            {"$unwind": "$motor_owned"},
            {"$match": {"motor_owned.motor_id": motor['motor_id']}},
        ])
        if list(existing_motor):
            return {"msg": "This motor_id has already added."}
        new_motor_own = {"motor_id": motor["motor_id"]}
        user_coll.update_one(
            {"user_id": user_id},
            {"$push": {"motor_owned": new_motor_own}}
        )
        return {"msg": "Motor added successfully",
                "motor_id": motor['motor_id'],
                "user": {
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "motor_owned": user["motor_owned"]
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# When user added motor then they need to update user data object
@router.post("/get/user_data")
async def get_user_data(token: str = Depends(oauth2_scheme)):
    try:
        user_id = await Auth.verify_authen(token)
        user = user_coll.find_one({"user_id": user_id})
        return {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "motor_owned": user["motor_owned"]
        }
    except Exception as e:
        return {"msg": e}
    
# User edit their username
@router.post("/edit/username")
async def edit_username(usr: Username, token: str = Depends(oauth2_scheme)):
    try:
        user_id = await Auth.verify_authen(token)
        user = user_coll.find_one({"user_id": user_id})
        if user :
            user_coll.update_one({"user_id": user_id}, {"$set":{"username": usr.username}})
            return {"msg": "Update username success!"}
    except Exception as e:
        return {"msg": e}