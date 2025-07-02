from typing import List, Optional
from pymongo.collection import Collection


class Hospital:
    def __init__(self):
        from core.database import get_db  # moved import here to avoid circular import
        self.collection: Collection = get_db()["hospitals"]

    def create_hospital(self, name: str, address: str, phone: str, departments: List[str]) -> dict:
        hospital_data = {
            "name": name,
            "address": address,
            "phone": phone,
            "departments": departments
        }
        result = self.collection.insert_one(hospital_data)
        return {"id": str(result.inserted_id), **hospital_data}

    def get_hospital(self, hospital_id: str) -> Optional[dict]:
        return self.collection.find_one({"_id": hospital_id})

    def update_hospital(self, hospital_id: str, update_data: dict) -> bool:
        result = self.collection.update_one(
            {"_id": hospital_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_hospital(self, hospital_id: str) -> bool:
        result = self.collection.delete_one({"_id": hospital_id})
        return result.deleted_count > 0

    def list_hospitals(self) -> List[dict]:
        return list(self.collection.find({}))