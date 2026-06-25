from fastapi import FastAPI  ,HTTPException,Query,Path
import json

app = FastAPI()
def load_data():
    with open('patients.json','r') as f:
        data=json.load(f)
    return data

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/view")
def view():
    return load_data();

@app.get("/patient/{patient_id}")
def get_patient(patient_id: str = Path(..., description="ID of the patient", example="P01")):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return data[patient_id]

@app.get("/sort")
def sort_patients(
    sort_by: str = Query("height", description="Field to sort by: height or weight"),
    order: str = Query("ascending", description="Sort order: ascending or descending")
):
    valid_fields = ["height", "weight"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field '{sort_by}'. Choose from {valid_fields}")

    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=(order == "descending"))
    return sorted_data