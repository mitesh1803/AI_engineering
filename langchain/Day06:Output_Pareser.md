# Day 07 — LangChain: Output Parsers

> **Topic:** StrOutputParser, JsonOutputParser, StructuredOutputParser, PydanticOutputParser

---

## 🧠 What Are Output Parsers?

Output Parsers sit **after the LLM** in a chain. They take the raw LLM response and convert it into a structured, usable Python object.

```
Prompt → LLM → [raw AIMessage response] → Output Parser → Usable Python object
```

### How They Differ from `with_structured_output` (Day 06)

| | `with_structured_output` | Output Parsers |
|---|---|---|
| Approach | Instructs the model at the API level | Post-processes the raw text response |
| Model requirement | Needs native structured output support | Works with **any** model |
| Reliability | Higher (model is explicitly constrained) | Depends on prompt quality |
| Use when | OpenAI, Anthropic, Google models | Older models, HuggingFace, Ollama |

Output Parsers are the fallback for models that don't support native structured output — and they're also cleaner for simple text extraction in chains.

---

## 🔨 The Four Key Output Parsers

---

### 1. StrOutputParser — Plain Text Extraction

The simplest parser. Strips everything except the text content from the LLM response.

**Why you need it:** An LLM returns an `AIMessage` object, not a string. It carries metadata — token usage, finish reason, model name. When chaining, you usually just want the text.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

# Chain: prompt → model → parser
chain = template | llm | parser

result = chain.invoke({"input": "What is the capital of India?"})
print(result)
# → "New Delhi"   (plain string, not AIMessage object)
print(type(result))
# → <class 'str'>
```

**Use when:** You need clean text output to feed into the next step in a chain, display to a user, or write to a file.

---

### 2. JsonOutputParser — Unstructured JSON

Forces the LLM to return valid JSON, but without enforcing any specific schema.

```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
parser = JsonOutputParser()

template = ChatPromptTemplate.from_messages([
    ("system", "Return your response as valid JSON only."),
    ("human", "Give me details about {topic}")
])

chain = template | llm | parser

result = chain.invoke({"topic": "Jasprit Bumrah"})
print(result)
# → {'name': 'Jasprit Bumrah', 'role': 'Fast Bowler', 'country': 'India', ...}
print(type(result))
# → <class 'dict'>
```

**Limitation:** No schema enforcement. The model decides what keys to return. If you ask about two different topics, you'll likely get different keys each time — unpredictable for downstream code.

**Use when:** You need JSON but don't care about the exact structure. Good for exploratory queries or when the model is deciding what to surface.

---

### 3. StructuredOutputParser — Defined Field Schema

Lets you specify exactly which fields you want returned, with descriptions. Injects format instructions directly into the prompt.

```python
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Define the schema
schemas = [
    ResponseSchema(name="name", description="Full name of the person"),
    ResponseSchema(name="role", description="Their professional role"),
    ResponseSchema(name="nationality", description="Their country of origin")
]

parser = StructuredOutputParser.from_response_schemas(schemas)

# Parser generates format instructions to inject into the prompt
format_instructions = parser.get_format_instructions()

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. {format_instructions}"),
    ("human", "Tell me about {topic}")
]).partial(format_instructions=format_instructions)

llm = ChatOpenAI(model="gpt-4o")
chain = template | llm | parser

result = chain.invoke({"topic": "Virat Kohli"})
print(result)
# → {'name': 'Virat Kohli', 'role': 'Cricketer', 'nationality': 'Indian'}
```

**Limitation:** Schema is enforced, but data types are not validated. If `age` was a field and the model returned `"twenty-eight"` instead of `28`, this parser won't catch it.

**Use when:** You need specific keys in the output but don't need strict type validation. Simpler than Pydantic for quick structured extraction.

---

### 4. PydanticOutputParser — Schema + Validation ✅ Recommended

Combines schema enforcement with full Pydantic validation. The most robust parser.

```python
from pydantic import BaseModel, Field, field_validator
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Define Pydantic model
class Person(BaseModel):
    name: str = Field(description="Full name of the person")
    age: int = Field(description="Age as an integer")
    role: str = Field(description="Professional role or occupation")

    @field_validator("age")
    def age_must_be_adult(cls, v):
        if v < 18:
            raise ValueError("Age must be 18 or above")
        return v

parser = PydanticOutputParser(pydantic_object=Person)
format_instructions = parser.get_format_instructions()

template = ChatPromptTemplate.from_messages([
    ("system", "Extract structured information. {format_instructions}"),
    ("human", "{input}")
]).partial(format_instructions=format_instructions)

llm = ChatOpenAI(model="gpt-4o")
chain = template | llm | parser

result = chain.invoke({"input": "MS Dhoni is a 42-year-old Indian cricket captain."})
print(result)
# → Person(name='MS Dhoni', age=42, role='Cricket Captain')

print(result.age)        # → 42  (int, not string)
print(type(result.age))  # → <class 'int'>
```

**What Pydantic adds over StructuredOutputParser:**
- `age` returned as `"42"` → automatically coerced to `42` (int)
- `age` returned as `15` → validator raises `ValueError` immediately
- Attribute access (`result.age`) instead of dict access (`result["age"]`)

**Use when:** Production apps, data pipelines, anywhere type correctness matters.

---

## 🧭 When to Use Which

| Parser | Schema Enforcement | Type Validation | Use Case |
|---|---|---|---|
| `StrOutputParser` | ❌ | ❌ | Clean text for chaining or display |
| `JsonOutputParser` | ❌ | ❌ | Flexible JSON, structure unknown upfront |
| `StructuredOutputParser` | ✅ | ❌ | Known fields, simple types, quick extraction |
| `PydanticOutputParser` | ✅ | ✅ | Production apps, type safety, complex validation |

**Default choice: PydanticOutputParser** for anything going into a database or API. **StrOutputParser** for everything else (text chains, summarization, generation).

---

## 🔗 The Chain Pattern (Standard Implementation)

All four parsers follow the same LCEL chain pattern:

```python
chain = prompt_template | llm | parser
result = chain.invoke({"key": "value"})
```

This is the canonical way to use parsers in LangChain. Avoid manually calling `.invoke()` on each step and passing results around — the pipe (`|`) operator handles it cleanly and enables streaming, async, and batch processing automatically.

---

## 🗺️ Output Parsers in the Full Pipeline

```
User Input
    ↓
ChatPromptTemplate
(+ format_instructions injected for Structured/Pydantic parsers)
    ↓
LLM
(returns raw AIMessage)
    ↓
Output Parser
    ↓
┌─────────────────────────────────────────────┐
│  StrOutputParser      → plain str           │
│  JsonOutputParser     → dict (any keys)     │
│  StructuredOutputParser → dict (fixed keys) │
│  PydanticOutputParser → Pydantic object     │
└─────────────────────────────────────────────┘
    ↓
Application / DB / API / Next Chain Step
```

---

## 📎 Beyond the Four — Other Parsers Worth Knowing

LangChain ships with additional specialized parsers in the docs:

| Parser | Output Type | Use Case |
|---|---|---|
| `CommaSeparatedListOutputParser` | `List[str]` | Extract lists from model responses |
| `DatetimeOutputParser` | `datetime` | Parse date/time strings into Python datetime |
| `EnumOutputParser` | `Enum` | Force output to one of a predefined set of values |
| `XMLOutputParser` | XML | When downstream systems expect XML |

---

## 💡 Key Takeaways

**On StrOutputParser:** It's easy to overlook but important — without it, chaining LLM calls means passing `AIMessage` objects around, not strings. Every text-in chain should end with `StrOutputParser` unless you need structure.

**On format instructions:** `StructuredOutputParser` and `PydanticOutputParser` both call `parser.get_format_instructions()` — this generates a text block telling the LLM exactly what format to return. It gets injected into the system prompt. Understanding this makes it clear why prompting and parsing are tightly coupled.

**On model agnosticism:** Unlike `with_structured_output` which requires native API support, all four parsers work with any text-generating model. This is critical for setups using Ollama, local HuggingFace models, or any model without function calling support.

**Relationship to Day 06:** `with_structured_output` (Day 06) and `PydanticOutputParser` (today) both use Pydantic — but via different mechanisms. `with_structured_output` constrains the model at the API level. `PydanticOutputParser` constrains via prompt instructions and post-processes the text. Former is more reliable; latter is more portable.

---

## 📚 Resources

- [LangChain Output Parsers Docs](https://python.langchain.com/docs/concepts/output_parsers/)
- [All Available Parsers](https://python.langchain.com/docs/integrations/output_parsers/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)

---
