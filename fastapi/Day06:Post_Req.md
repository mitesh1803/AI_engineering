# FastAPI — Day 05: POST Request & Creating Patient Records

## 1. Concept Overview

### Where We Are

| Endpoint | Method | Status |
|---|---|---|
| `/view` | `GET` | ✅ Done |
| `/patient/{patient_id}` | `GET` | ✅ Done |
| `/sort` | `GET` | ✅ Done |
| `/create` | `POST` | 🔨 This video |

### What is a Request Body?

GET requests pass data through the URL (path or query params). POST requests carry data in the **request body** — a structured payload sent alongside the HTTP request, invisible in the URL.

```
POST /create
Headers: { Content-Type: application/json }
Body:    { "id": "P05", "name": "Mitesh", "age": 22, ... }
```

FastAPI reads the request body, passes it through a Pydantic model for validation, and the endpoint receives a clean, type-safe object.

### Workflow

```
Client sends JSON body
        │
        ▼
Pydantic model validates + computes fields
        │
        ▼
Endpoint checks for duplicate ID
        │
        ├── Duplicate found  ──▶  400 Bad Request
        │
        └── New record       ──▶  Save to patients.json
                                        │
                                        ▼
                                 201 Created ✓
```

---

## 2. Pydantic Model

The `Patient` model handles both validation and computation — the client never needs to send BMI or Verdict.

```python
from pydantic import BaseModel, Field, computed_field
from typing import Annotated

class Patient(BaseModel):
    id: str = Field(..., description="Unique patient ID", example="P05")
    name: str = Field(..., description="Full name of the patient")
    age: Annotated[int, Field(gt=0, lt=120, description="Age in years")]
    weight: Annotated[float, Field(gt=0, description="Weight in kg")]
    height: Annotated[float, Field(gt=0, description="Height in cm")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / ((self.height / 100) ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"
```

**Key design decision:** `bmi` and `verdict` are `@computed_field`s — they are derived automatically from `weight` and `height`. The client does not send them; the server calculates and stores them. This prevents stale or inconsistent data.

---

## 3. Endpoint Implementation

```python
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

def load_data():
    with open("patients.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f, indent=4)

@app.post("/create", status_code=201)
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail=f"Patient with ID '{patient.id}' already exists")

    data[patient.id] = patient.model_dump(exclude={"id"})
    save_data(data)

    return JSONResponse(
        status_code=201,
        content={"message": "Patient created successfully", "patient_id": patient.id}
    )
```

**Notable details:**
- `status_code=201` on the decorator sets the default success response code to `201 Created` (more semantically correct than `200 OK` for resource creation).
- `patient.model_dump(exclude={"id"})` stores the record under `data[patient.id]` as the key, so the ID is not duplicated inside the value.
- `save_data()` writes back the entire updated dict — appropriate for a JSON file store at this stage.

---

## 4. Testing in Swagger UI (`/docs`)

FastAPI's `/docs` page is colour-coded by HTTP method — POST endpoints appear in **green**, making them easy to spot.

**Test flow:**

1. Open `http://127.0.0.1:8000/docs`
2. Click the `POST /create` endpoint → **Try it out**
3. Paste a JSON body with `id`, `name`, `age`, `weight`, `height`
4. Execute — observe `bmi` and `verdict` auto-populated in the stored record

**Error case:** Submitting the same `id` twice returns:

```json
{
  "detail": "Patient with ID 'P05' already exists"
}
```

with a `400 Bad Request` status — not a silent overwrite.

---

## Key Takeaways

- POST requests carry data in the **request body**, not the URL — Pydantic models are the natural counterpart for parsing and validating that body in FastAPI.
- `@computed_field` keeps derived data (BMI, verdict) consistent — the server owns the calculation, not the client.
- Always return `201 Created` for successful resource creation, not `200 OK`. The status code is part of the API contract.
- Duplicate ID checks before writing prevent silent data corruption — always validate against existing state before a write operation.

---
