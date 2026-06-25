# Day 06 — LangChain: Structured Output

> **Topic:** Getting JSON from LLMs — TypedDict, Pydantic, and JSON Schema

---

## 🧠 What I Learned

By default, LLMs return plain text. That's fine for chat — but useless when you need to store data in a database, feed a response into another API, or run logic on the output. **Structured Output** solves this by forcing the model to respond in a defined schema (typically JSON).

---

## 📦 Unstructured vs Structured Output

### Unstructured (default)

```
Input:  "Extract the name and experience from this resume: ..."
Output: "The candidate's name is Mitesh Kokare and he has 2 years of experience."
```

You'd have to parse this string manually. Fragile, error-prone, doesn't scale.

### Structured

```
Input:  same resume text
Output: {
    "name": "Mitesh Kokare",
    "experience_years": 2
}
```

Now it's directly insertable into a database, passable to an API, or usable in application logic — zero parsing required.

---

## 🌍 Real-World Use Cases

| Use Case | What Structured Output Enables |
|---|---|
| **Resume Parsing** | Extract name, skills, experience as typed fields |
| **Sentiment Analysis API** | Return `{ "sentiment": "positive", "score": 0.91 }` instead of a paragraph |
| **Agent Tool Calls** | Pass structured inputs to calculators, search APIs, databases |
| **Data Extraction Pipelines** | Pull entities from documents directly into structured records |

The common thread: anywhere an LLM response needs to be **consumed by code rather than read by a human**, you want structured output.

---

## ⚙️ How It Works — `with_structured_output`

LangChain exposes a single method that wraps any compatible model:

```python
structured_llm = llm.with_structured_output(YourSchema)
result = structured_llm.invoke("your prompt")
# result is now a typed Python object, not a string
```

Under the hood, LangChain uses one of two execution methods (configurable via the `method` parameter):

| Method | How It Works | Best For |
|---|---|---|
| **Function Calling** | Model uses tool/function calling API to return structured data | Complex schemas, nested objects, most reliable |
| **JSON Mode** | Model is instructed to output raw JSON only | Simpler schemas, models without function calling support |

```python
structured_llm = llm.with_structured_output(Schema, method="function_calling")
structured_llm = llm.with_structured_output(Schema, method="json_mode")
```

> **Model compatibility note:** OpenAI, Anthropic, and Google models support structured output natively via `with_structured_output`. Other models (Ollama, older HuggingFace models) may not — for those, use **Output Parsers** instead (covered in Day 07).

---

## 🔨 Three Ways to Define a Schema

### Method 1 — TypedDict

Python's built-in type hinting system. Simple and lightweight.

```python
from typing import TypedDict, Annotated, Optional
from langchain_openai import ChatOpenAI

class Review(TypedDict):
    summary: Annotated[str, "A short summary of the review"]
    sentiment: Annotated[str, "Either 'positive', 'negative', or 'neutral'"]
    rating: Annotated[Optional[int], "Numeric rating out of 5, if mentioned"]

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Review)

result = structured_llm.invoke(
    "Review: 'This laptop is incredibly fast, great battery life. Worth every rupee.'"
)

print(result)
# → {'summary': 'Fast performance and great battery.', 'sentiment': 'positive', 'rating': None}
```

**What you get:** A plain Python `dict` with the defined keys.

---

### Method 2 — Pydantic ✅ Recommended

Pydantic models add **validation, default values, and type coercion** on top of TypedDict.

```python
from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI

class Review(BaseModel):
    summary: str = Field(description="A short summary of the review")
    sentiment: str = Field(description="Either 'positive', 'negative', or 'neutral'")
    rating: Optional[int] = Field(default=None, description="Numeric rating out of 5, if mentioned")

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Review)

result = structured_llm.invoke(
    "Review: 'The product broke after two days. Terrible quality. 1/5.'"
)

print(result)
# → Review(summary='Product broke after two days.', sentiment='negative', rating=1)

print(result.sentiment)   # → 'negative'
print(result.rating)      # → 1  (auto-coerced from "1/5" string to int)
```

**What you get:** A proper Pydantic object with attribute access, not just a dict.

**Extra Pydantic capabilities:**

```python
from pydantic import BaseModel, Field, field_validator

class Review(BaseModel):
    sentiment: str = Field(description="positive, negative, or neutral")
    rating: int = Field(ge=1, le=5, description="Rating between 1 and 5")

    @field_validator("sentiment")
    def validate_sentiment(cls, v):
        allowed = ["positive", "negative", "neutral"]
        if v not in allowed:
            raise ValueError(f"sentiment must be one of {allowed}")
        return v
```

Validation runs automatically — if the model returns something outside your rules, it errors immediately rather than silently passing bad data downstream.

---

### Method 3 — JSON Schema

Raw JSON Schema definition. No Python classes required.

```python
from langchain_openai import ChatOpenAI

schema = {
    "title": "Review",
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "Short summary of the review"},
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "rating": {"type": "integer", "minimum": 1, "maximum": 5}
    },
    "required": ["summary", "sentiment"]
}

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(schema)

result = structured_llm.invoke("Review: 'Excellent build quality, highly recommended!'")
print(result)
# → {'summary': 'Excellent build quality.', 'sentiment': 'positive', 'rating': None}
```

**What you get:** A plain Python dict matching the schema.

---

## 🧭 When to Use Which

| Scenario | Use |
|---|---|
| Quick prototype, simple schema, Python-only project | **TypedDict** |
| Production app, need validation, default values, type coercion | **Pydantic** ✅ |
| Cross-language team (Node.js, Go, etc. consuming the schema) | **JSON Schema** |
| Model doesn't support `with_structured_output` natively | **Output Parsers** (Day 07) |
| Nested objects, complex data relationships | **Pydantic** (handles nesting cleanly) |
| Schema needs to be stored/shared externally (e.g., config file) | **JSON Schema** |

**Default choice: Pydantic.** TypedDict is fine for throwaway scripts. JSON Schema is for polyglot teams. Pydantic covers everything in between — and is already a dependency in most FastAPI/LangChain projects anyway.

![alt text](assets/structuredOutput.png)
---

## 🗺️ Where Structured Output Sits in the Pipeline

```
User Input / Document
        ↓
  ChatPromptTemplate
  (structure the request)
        ↓
      LLM
        ↓
  with_structured_output(Schema)
  (force JSON response)
        ↓
  Typed Python Object
  (dict / Pydantic model)
        ↓
  Database / API / Next Chain Step
```

---

## 💡 Key Takeaways

**On why this matters for AI products:** The gap between a demo and a production app often comes down to whether LLM output is parseable by code. Structured output is what bridges that gap — it's what lets an LLM response go directly into a database row or an API response payload.

**On Pydantic's `type coercion`:** This is underrated. If the model returns `"1/5"` and your field is `int`, Pydantic tries to coerce it. If it returns `"POSITIVE"` and you expected `"positive"`, a validator catches it. This resilience matters in production where model output is never perfectly consistent.

**On function calling vs JSON mode:** Function calling is more reliable for complex schemas because the model is explicitly taught to fill a structured form. JSON mode just instructs the model to output JSON — which it can still malform. Use function calling by default unless you have a reason not to.

---

## 📚 Resources

- [LangChain Structured Output Docs](https://python.langchain.com/docs/concepts/structured_outputs/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [JSON Schema Reference](https://json-schema.org/understanding-json-schema/)

---

*Next up → Day 07: Output Parsers — for models that don't support native structured output*