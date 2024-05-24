from pymongo import MongoClient
import os
from dotenv import load_dotenv
import gridfs

class DataBase:
    def __init__(self) -> None:
        try:
            load_dotenv()
            # self.uri = "mongodb://mongoadmin:mongoadmin@mongo_db:27017/?authMechanism=DEFAULT"
            self.uri = os.environ.get("MONGO_CONNECTION_STRING")
            self.client = MongoClient(self.uri, connect=False)
            print('🚀 Connected to MongoDB...')
            # Send a ping to confirm a successful connection
            self.motor_db = self.client["motor"]
            self.mt_data_coll = self.motor_db["motor_data"]
            self.mt_info_coll = self.motor_db["motor_info"]
            self.user_coll = self.motor_db["users"]
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
            
    def collection(self, coll_name: str):
        collection = self.motor_db[coll_name]
        return collection
    
    def get_db_fs(self):
        return self.client.gridfs_example

db = DataBase()