from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from core.database import get_db

class Patient:
    def __init__(self):
        self.collection: Collection = get_db()["patients"]

    def create_patient(self, name: str, age: int, gender: str, 
                      hospital_id: str, admission_date: datetime = None) -> dict:
        patient_data = {
            "name": name,
            "age": age,
            "gender": gender,
            "hospital_id": hospital_id,
            "admission_date": admission_date or datetime.now()
        }
        result = self.collection.insert_one(patient_data)
        return {"id": str(result.inserted_id), **patient_data}

    def get_patient(self, patient_id: str) -> Optional[dict]:
        return self.collection.find_one({"_id": patient_id})

    def update_patient(self, patient_id: str, update_data: dict) -> bool:
        result = self.collection.update_one(
            {"_id": patient_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_patient(self, patient_id: str) -> bool:
        result = self.collection.delete_one({"_id": patient_id})
        return result.deleted_count > 0

    def list_patients(self, hospital_id: str = None) -> List[dict]:
        query = {}
        if hospital_id:
            query["hospital_id"] = hospital_id
        return list(self.collection.find(query))