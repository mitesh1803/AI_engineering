# FastAPI — Day 06: PUT & DELETE — Completing the CRUD Cycle


## CRUD Status

| Endpoint | Method | Status |
|---|---|---|
| `/view` | `GET` | ✅ Done |
| `/patient/{patient_id}` | `GET` | ✅ Done |
| `/sort` | `GET` | ✅ Done |
| `/create` | `POST` | ✅ Done |
| `/update/{patient_id}` | `PUT` | 🔨 This video |
| `/delete/{patient_id}` | `DELETE` | 🔨 This video |

---

## 1. Update Endpoint (PUT)

### The Problem with Reusing `Patient`

The original `Patient` model requires **all fields** — that works for creation but not for updates. A client updating only a patient's weight shouldn't need to resend name, age, height, and everything else.

Reusing `Patient` for PUT would force the client to send a complete record every time, which is neither practical nor semantically correct.

### The Solution: `PatientUpdate` with Optional Fields

A dedicated model where every field is `Optional` — the client sends only what needs to change:

```python
from pydantic import BaseModel, Field
from typing import Optional, Annotated

class PatientUpdate(BaseModel):
    name: Optional[str]               = None
    age: Optional[Annotated[int, Field(gt=0, lt=120)]]     = None
    weight: Optional[Annotated[float, Field(gt=0)]]        = None
    height: Optional[Annotated[float, Field(gt=0)]]        = None
```

`id`, `bmi`, and `verdict` are excluded — the ID is a path parameter, and computed fields are always recalculated server-side.

---

### `exclude_unset=True` — Only Touch What Was Sent

When `.model_dump()` is called on a Pydantic model, it returns **all fields**, including those the client never sent (they'd just be `None`). That would overwrite existing values with `None` — which is wrong.

`exclude_unset=True` solves this by returning **only the fields explicitly provided** in the request:

```python
# Client sends: { "weight": 75.0 }
update.model_dump(exclude_unset=True)
# Returns: { "weight": 75.0 }  — not { "name": None, "age": None, ... }
```

---

### Recomputing BMI & Verdict After Update

After merging the client's changes into the existing record, computed fields (`bmi`, `verdict`) need to be recalculated. The cleanest way: pass the updated dict back through the original `Patient` model, which triggers all `@computed_field` logic automatically.

```python
# Patient model from Day 05 (with @computed_field for bmi and verdict)
from models import Patient, PatientUpdate

@app.put("/update/{patient_id}")
def update_patient(patient_id: str, update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    existing = data[patient_id]

    # Merge: only overwrite fields the client explicitly sent
    updated_fields = update.model_dump(exclude_unset=True)
    existing.update(updated_fields)

    # Revalidate through Patient model to recompute bmi and verdict
    updated_patient = Patient(id=patient_id, **existing)
    data[patient_id] = updated_patient.model_dump(exclude={"id"})

    save_data(data)
    return {"message": "Patient updated successfully", "patient_id": patient_id}
```

**The revalidation step is the key insight here:** feeding the merged dict back into `Patient` is not just about recomputing BMI — it also re-runs all field constraints and validators, ensuring the updated record is fully valid before it's saved.

---

## 2. Delete Endpoint (DELETE)

Simpler than update — no request body needed. The patient ID in the path is all the information required.

```python
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    del data[patient_id]
    save_data(data)

    return {"message": f"Patient '{patient_id}' deleted successfully"}
```

**Flow:**

```
DELETE /delete/P05
        │
        ▼
Load patients.json
        │
        ├── ID not found  ──▶  404 Not Found
        │
        └── ID found
                │
                ▼
           del data["P05"]
                │
                ▼
           save_data()
                │
                ▼
           200 OK + message ✓
```

---

## 3. The Complete CRUD System

With all six endpoints in place, here's the full API surface:

```
GET    /view                  ──▶  Return all patients
GET    /patient/{id}          ──▶  Return one patient by ID
GET    /sort?sort_by&order    ──▶  Return sorted patient list
POST   /create                ──▶  Add a new patient (body: full Patient)
PUT    /update/{id}           ──▶  Partially update a patient (body: PatientUpdate)
DELETE /delete/{id}           ──▶  Remove a patient by ID
```

---

## Key Takeaways

- Never reuse the creation model for updates. A dedicated `PatientUpdate` model with all-`Optional` fields is the correct pattern — it reflects the actual semantics of a partial update.
- `exclude_unset=True` is essential for partial updates. Without it, unset `Optional` fields default to `None` and silently overwrite existing data.
- After a partial update, always revalidate through the full model. This recomputes derived fields and re-runs all validators — the updated record is guaranteed to be in a consistent state before being persisted.
- DELETE endpoints rarely need a request body. The path parameter is the resource identifier; that's sufficient.

---

## Project Wrap-Up

The Patient Management System is complete. The full CRUD lifecycle now works end-to-end with a JSON file as the data store. The patterns covered — Pydantic models, `Optional` fields, `exclude_unset`, `@computed_field`, `HTTPException`, and JSON persistence — form the core toolkit for any FastAPI project before a real database is introduced.

---
