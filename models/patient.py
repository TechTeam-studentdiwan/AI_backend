from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
import asyncio

class Patient:
    def __init__(self):
        self.collection: AsyncIOMotorCollection = None

    async def init_collection(self):
        from core.database import get_db  # moved import here to avoid circular import
        async for db in get_db():
            self.collection = db["patients"]
            break

    async def create_patient(self, name: str, age: int, gender: str,
                            hospital_id: str, admission_date: datetime = None) -> dict:
        if self.collection is None:
            await self.init_collection()
        patient_data = {
            "name": name,
            "age": age,
            "gender": gender,
            "hospital_id": hospital_id,
            "admission_date": admission_date or datetime.now()
        }
        result = await self.collection.insert_one(patient_data)
        return {"id": str(result.inserted_id), **patient_data}

    async def get_patient(self, patient_id: str) -> Optional[dict]:
        if self.collection is None:
            await self.init_collection()
        return await self.collection.find_one({"_id": ObjectId(patient_id)})

    async def update_patient(self, patient_id: str, update_data: dict) -> bool:
        if self.collection is None:
            await self.init_collection()
        result = await self.collection.update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_patient(self, patient_id: str) -> bool:
        if self.collection is None:
            await self.init_collection()
        result = await self.collection.delete_one({"_id": ObjectId(patient_id)})
        return result.deleted_count > 0

    async def list_patients(self, hospital_id: str = None) -> List[dict]:
        if self.collection is None:
            await self.init_collection()
        query = {}
        if hospital_id:
            query["hospital_id"] = hospital_id
        cursor = self.collection.find(query)
        return [doc async for doc in cursor]
