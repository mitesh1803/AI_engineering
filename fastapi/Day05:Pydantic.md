# FastAPI — Day 04: Pydantic Crash Course


## 1. Why Pydantic?

Python is **dynamically typed** — nothing stops you from passing a string where an integer is expected. In production, that leads to silent bugs and unpredictable failures.

Pydantic enforces types and constraints **at the point of data entry**, with zero boilerplate:

| Without Pydantic | With Pydantic |
|---|---|
| Manual `if` checks for every field | Constraints declared once in the model |
| Type errors surface at runtime, deep in logic | Errors raised immediately on instantiation |
| Repetitive validation code across endpoints | Single model reused everywhere |

---

## 2. Core Workflow

Three steps, always in this order:

```
1. Define Model  ──▶  2. Instantiate (triggers validation)  ──▶  3. Use validated object
```

### Basic Example

```python
from pydantic import BaseModel

class Patient(BaseModel):
    name: str
    age: int
    weight: float  # kg
    height: float  # cm

# Instantiation triggers validation automatically
p = Patient(name="Mitesh", age=22, weight=70.5, height=175.0)
print(p.name)  # "Mitesh"
```

If a field fails validation, Pydantic raises a `ValidationError` immediately — before the object is created.

---

## 3. Validation Techniques

### `Field()` — Constraints & Metadata

Used to add numeric constraints and documentation hints directly on a field:

```python
from pydantic import BaseModel, Field

class Patient(BaseModel):
    name: str
    age: int   = Field(gt=0, lt=120, description="Patient age in years")
    weight: float = Field(gt=0, description="Weight in kg")
    height: float = Field(gt=0, description="Height in cm")
```

Common constraints: `gt` (greater than), `ge` (≥), `lt` (less than), `le` (≤), `min_length`, `max_length`.

---

### `@field_validator` — Single Field Custom Logic

For validation or transformation that goes beyond simple constraints — runs on a specific field.

Two modes:
- `mode='before'` — runs **before** Pydantic's type coercion (receives raw input)
- `mode='after'` — runs **after** coercion (receives the already-typed value)

```python
from pydantic import BaseModel, field_validator

class Patient(BaseModel):
    name: str
    email: str

    @field_validator("email", mode="after")
    @classmethod
    def validate_email_domain(cls, value):
        allowed_domains = ["gmail.com", "hospital.org"]
        domain = value.split("@")[-1]
        if domain not in allowed_domains:
            raise ValueError(f"Email domain '{domain}' is not allowed")
        return value
```

---

### `@model_validator` — Cross-Field Validation

Used when validation logic spans **multiple fields** — e.g., one field's valid range depends on another.

```python
from pydantic import BaseModel, model_validator

class Patient(BaseModel):
    age: int
    is_minor: bool

    @model_validator(mode="after")
    def check_minor_flag(self):
        if self.age < 18 and not self.is_minor:
            raise ValueError("Patient under 18 must be marked as a minor")
        return self
```

---

### `@computed_field` — Auto-Generated Fields

Derive a field from existing model data without requiring user input. The value is computed automatically on instantiation.

```python
from pydantic import BaseModel, computed_field

class Patient(BaseModel):
    weight: float  # kg
    height: float  # cm

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / ((self.height / 100) ** 2), 2)

p = Patient(weight=70.5, height=175.0)
print(p.bmi)  # 23.02 — computed, not provided by user
```

---

## 4. Structural Features

### Nested Models

Embed one Pydantic model inside another to represent hierarchical data:

```python
class Address(BaseModel):
    city: str
    state: str
    pincode: str

class Patient(BaseModel):
    name: str
    age: int
    address: Address  # nested model

p = Patient(
    name="Mitesh",
    age=22,
    address={"city": "Nashik", "state": "Maharashtra", "pincode": "422001"}
)
print(p.address.city)  # "Nashik"
```

Pydantic automatically validates the nested object — the `Address` model's rules apply recursively.

---

### Serialization — `.model_dump()`

Export a validated Pydantic object to a **Python dict** or **JSON string**:

```python
# To dict
patient_dict = p.model_dump()

# To JSON string
patient_json = p.model_dump_json()
```

Useful for:
- Saving to a JSON file (the `patients.json` data store)
- Returning structured API responses
- Logging and debugging

---

## 5. Full Validator Hierarchy

```
Input Data
    │
    ▼
Field-level type coercion  ◀── @field_validator(mode='before')
    │
    ▼
Type validation (BaseModel)
    │
    ▼
@field_validator(mode='after')  ◀── custom single-field logic
    │
    ▼
@model_validator(mode='after')  ◀── cross-field logic
    │
    ▼
@computed_field                 ◀── derived fields generated
    │
    ▼
Validated Object ✓
```

---

## Key Takeaways

- Pydantic replaces manual validation boilerplate with declarative, reusable models.
- `Field()` handles simple constraints; `@field_validator` handles custom per-field logic; `@model_validator` handles logic that spans fields.
- `@computed_field` is particularly useful in ML contexts — e.g., deriving BMI, risk scores, or normalized values from raw inputs before passing data downstream.
- `.model_dump()` is the bridge between a Pydantic model and JSON — critical for both API responses and writing to the `patients.json` data store.

---

*Next: Integrating Pydantic models into FastAPI POST and PUT endpoints →*