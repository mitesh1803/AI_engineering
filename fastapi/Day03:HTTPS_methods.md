# FastAPI — Day 02: HTTP Methods & First CRUD Endpoint

## 1. Project Overview

The goal of this project is to build a **Patient Management System API** that digitizes doctor-patient records. It exposes endpoints for full **CRUD** operations on patient data.

For now, a `patients.json` file serves as the temporary data store — no database yet, keeping the focus on FastAPI fundamentals before adding persistence complexity.

---

## 2. HTTP Methods & CRUD

Every API endpoint is defined by two things: a **path** and an **HTTP method**. The method tells the server what kind of operation the client wants to perform.

| HTTP Method | CRUD Operation | Example Use Case |
|---|---|---|
| `GET` | **Read** | Fetch a patient record or list all patients |
| `POST` | **Create** | Register a new patient |
| `PUT` | **Update** | Modify an existing patient's data |
| `DELETE` | **Delete** | Remove a patient record |

---

## 3. Environment Setup

**Dependencies:**

```bash
pip install fastapi pydantic uvicorn
```

- **FastAPI** — the web framework
- **Pydantic** — data validation and schema definition
- **Uvicorn** — ASGI server to run the application locally

**Run the server:**

```bash
uvicorn main:app --reload
```

---

## 4. Implementation

### Project Structure

```
patient-management/
├── main.py
└── patients.json
```

### Helper Function — `load_data`

Reads `patients.json` from disk and returns the parsed content, ready to be served by the API.

```python
import json

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
    return data
```

### First Endpoint — `GET /view`

Returns the complete list of patient records.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/view")
def view_patients():
    data = load_data()
    return data
```

**How it works:**

```
Client (Browser / curl)          FastAPI Server
        │                               │
        │  GET /view                    │
        │──────────────────────────────▶│
        │                               │ load_data()
        │                               │──▶ patients.json
        │                               │◀── parsed JSON
        │  200 OK + patient list        │
        │◀──────────────────────────────│
```

### Testing with `/docs`
Python Atutomatically Generated OPENAPI SPEC FILE

FastAPI auto-generates interactive API documentation at:

```
http://127.0.0.1:8000/docs
```

This Swagger UI lets you test every endpoint directly from the browser — no need for external tools like Postman at this stage.

---

## Key Takeaways

- HTTP methods map directly to CRUD — knowing which method to use on which endpoint is the foundation of RESTful API design.
- `patients.json` as a data store keeps the focus on FastAPI mechanics before introducing a real database.
- FastAPI's auto-generated `/docs` page (Swagger UI) is a built-in testing and documentation tool — use it aggressively during development.

---

*Next: Adding GET by ID, POST, PUT, and DELETE endpoints →*