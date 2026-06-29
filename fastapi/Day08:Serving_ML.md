# FastAPI — Day 08: Serving ML Models with FastAPI


---

## The Big Picture

This is where the series shifts from framework fundamentals to the actual goal: **deploying ML models as APIs**. The pattern introduced here is the foundation for every ML serving use case — from simple classifiers to deep learning inference endpoints.

```
Jupyter Notebook          FastAPI Backend         Client
(Model Training)          (Model Serving)         (Frontend)
      │                         │                      │
      │  export model.pkl       │                      │
      │────────────────────────▶│                      │
      │                         │   POST /predict      │
      │                         │◀─────────────────────│
      │                         │  validate + infer    │
      │                         │  return prediction   │
      │                         │─────────────────────▶│
```

---

## 1. Model Building

**Problem:** Predict insurance premium category — `Low`, `Medium`, or `High` — based on user inputs.

**Pipeline:**
- Feature engineering for categorical and numerical columns
- `RandomForestClassifier` wrapped in a `sklearn` `Pipeline`
- Exported as `model.pkl` using `joblib` or `pickle`

```python
import joblib

# After training
joblib.dump(pipeline, "model.pkl")
```

The `Pipeline` object bundles preprocessing and the classifier together — the API loads it once and calls `.predict()` directly on raw input, no manual preprocessing needed at inference time.

---

## 2. FastAPI Endpoint

### Loading the Model

Load `model.pkl` once at startup — not on every request. This keeps inference fast.

```python
import joblib
from fastapi import FastAPI

app = FastAPI()
model = joblib.load("model.pkl")
```

### Pydantic Input Model with Computed Fields

The client sends raw, user-friendly inputs. The Pydantic model computes derived features internally before inference — keeping the API surface simple.

```python
from pydantic import BaseModel, computed_field

class UserInput(BaseModel):
    age: int
    weight: float
    height: float
    smoker: bool
    city: str
    income_bracket: str

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / ((self.height / 100) ** 2), 2)

    @computed_field
    @property
    def lifestyle_risk(self) -> int:
        # derived from age, smoker status, bmi
        risk = 0
        if self.smoker:
            risk += 2
        if self.bmi > 30:
            risk += 1
        if self.age > 50:
            risk += 1
        return risk

    @computed_field
    @property
    def city_tier(self) -> int:
        tier_1 = ["Mumbai", "Delhi", "Bangalore"]
        tier_2 = ["Pune", "Hyderabad", "Chennai"]
        if self.city in tier_1:
            return 1
        elif self.city in tier_2:
            return 2
        return 3
```

**Why computed fields here?** The ML model was trained on `bmi`, `lifestyle_risk`, and `city_tier` — not on raw `weight`, `height`, and `city`. The Pydantic model bridges this gap, keeping the feature engineering server-side and the client input minimal.

### The `/predict` Endpoint

```python
import pandas as pd
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.post("/predict")
def predict(data: UserInput):
    input_df = pd.DataFrame([{
        "age": data.age,
        "bmi": data.bmi,
        "lifestyle_risk": data.lifestyle_risk,
        "city_tier": data.city_tier,
        "income_bracket": data.income_bracket,
    }])

    prediction = model.predict(input_df)[0]
    return JSONResponse(content={"predicted_premium": prediction})
```

---

## 3. Frontend Integration with Streamlit

Streamlit acts as the user-facing layer — it collects inputs and calls the FastAPI endpoint using the `requests` library.

```python
import streamlit as st
import requests

st.title("Insurance Premium Predictor")

age = st.number_input("Age", min_value=1, max_value=120)
weight = st.number_input("Weight (kg)")
height = st.number_input("Height (cm)")
smoker = st.checkbox("Smoker?")
city = st.text_input("City")
income_bracket = st.selectbox("Income Bracket", ["Low", "Medium", "High"])

if st.button("Predict"):
    payload = {
        "age": age, "weight": weight, "height": height,
        "smoker": smoker, "city": city, "income_bracket": income_bracket
    }
    response = requests.post("http://127.0.0.1:8000/predict", json=payload)
    result = response.json()
    st.success(f"Predicted Premium: {result['predicted_premium']}")
```

**Streamlit here is a stand-in for any frontend** — the same FastAPI endpoint can be consumed by a React app, an Android client, or another backend service with zero changes.

---

## The Complete ML Serving Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Jupyter Notebook                      │
│  Train ──▶ Feature Engineering ──▶ Export model.pkl     │
└──────────────────────────┬──────────────────────────────┘
                           │
                    model.pkl loaded at startup
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                        │
│                                                         │
│  POST /predict                                          │
│  │                                                      │
│  ├── Pydantic validates raw input                       │
│  ├── @computed_field derives bmi, risk, city_tier       │
│  ├── model.predict(input_df)                            │
│  └── Return JSON { "predicted_premium": "Low" }         │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Streamlit         React App       Mobile App
```

---

## Key Takeaways

- Load the model **once at startup**, not per request — model loading is expensive; inference should be cheap.
- `@computed_field` is the right place for feature engineering at inference time — it keeps the client API clean and centralizes preprocessing logic on the server.
- Keep **Streamlit/frontend and FastAPI completely separate projects** — this makes it easy to swap the frontend later (React, mobile, etc.) without touching the API.
- This workflow scales directly to deep learning: swap `joblib.load("model.pkl")` for loading a PyTorch or TensorFlow model, and the rest of the pattern stays identical.

---

*Next: Day 09 — Making the API production-ready (project structure, health checks, error handling, response models) →*