# This module contains function call handlers for OpenAIService
from fastapi import HTTPException
from models import Patient

async def get_patient_details(patient_id: str, hospital_id: str):
    patient_model = Patient()
    patient = await patient_model.get_patient(patient_id)
    if not patient or patient.get("hospital_id") != hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found in this hospital.")
    patient.pop("_id", None)
    return patient

async def get_patient_details_by_name(name: str, hospital_id: str):
    patient_model = Patient()
    if patient_model.collection is None:
        await patient_model.init_collection()
    patient = await patient_model.collection.find_one({"name": name, "hospital_id": hospital_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in this hospital.")
    patient.pop("_id", None)
    return patient

GET_PATIENT_DETAILS_FUNCTION = {
    "name": "get_patient_details",
    "description": "Get patient details by patient ID and hospital ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string", "description": "The ID of the patient."},
            "hospital_id": {"type": "string", "description": "The ID of the hospital."}
        },
        "required": ["patient_id", "hospital_id"]
    }
}

GET_PATIENT_DETAILS_BY_NAME_FUNCTION = {
    "name": "get_patient_details_by_name",
    "description": "Get patient details by name and hospital ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The name of the patient."},
            "hospital_id": {"type": "string", "description": "The ID of the hospital."}
        },
        "required": ["name", "hospital_id"]
    }
}
