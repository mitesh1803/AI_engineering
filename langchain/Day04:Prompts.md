# Day 05 — LangChain: Prompts (Deep Dive)

> **Topic:** Static vs Dynamic Prompts, PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

---

## 🧠 What Are Prompts?

A prompt is the message (or set of messages) sent to an LLM to elicit a response.

In practice, **99% of prompts are text-based**. Multi-modal prompts (images, audio) are emerging but not the mainstream case for most LangChain applications yet.

---

## ⚡ Static vs Dynamic Prompts

### Static Prompts — Raw User Input

The user types whatever they want, directly into the model.

```
User: "tell me abt cricket"
LLM:  [unpredictable response — may be too short, wrong tone, wrong format]
```

Problems with this:
- Inconsistent phrasing leads to inconsistent outputs
- No control over format, tone, or depth
- LLM quality is directly tied to how well the user phrases things

### Dynamic Prompts — Prompt Templates

The developer defines a structured template with fixed instructions and variable placeholders. The user only fills in the variables.

```
Template: "Summarize the following {topic} in {num_points} bullet points using a {tone} tone."

User provides: topic="cricket", num_points=5, tone="formal"

Final prompt: "Summarize the following cricket in 5 bullet points using a formal tone."
```

The structure is controlled. The output quality is consistent regardless of how the user phrased the input.

---

## 💻 PromptTemplate — Why Not Just Use f-strings?

A Python f-string technically does the same variable injection:

```python
topic = "cricket"
prompt = f"Tell me about {topic}"
```

But `PromptTemplate` from LangChain is superior for three reasons:

| | f-string | `PromptTemplate` |
|---|---|---|
| Validation | None — missing variables silently fail | Raises error if required variable is missing |
| Reusability | Lives in Python code only | Can be serialized to JSON and loaded back |
| Chain integration | Manual wiring required | Plugs directly into LCEL chains |

```python
from langchain_core.prompts import PromptTemplate

# Define template with named placeholders
template = PromptTemplate(
    input_variables=["topic", "num_points", "tone"],
    template="Summarize {topic} in {num_points} bullet points using a {tone} tone."
)

# Format at runtime
prompt = template.invoke({
    "topic": "cricket",
    "num_points": 5,
    "tone": "formal"
})

print(prompt.text)
# → "Summarize cricket in 5 bullet points using a formal tone."
```

**Saving and loading templates (reusability):**

```python
# Save to disk
template.save("summarizer_template.json")

# Load back
from langchain_core.prompts import load_prompt
loaded = load_prompt("summarizer_template.json")
```

This means prompt templates can be versioned, shared, and reused across projects — not buried in application code.

---

## 💬 Messages & ChatPromptTemplate

Modern LLMs don't just take raw text — they take **structured conversations** with explicit roles. Three message types:

| Message Type    | Role                                                           | Class              |
|-----------------|----------------------------------------------------------------|--------------------|
| `SystemMessage` | Defines the model's identity, behaviour, and constraints       | `SystemMessage`    |
| `HumanMessage`  | The user's input or query                                      | `HumanMessage`     |
| `AIMessage`     | A previous model response (used to reconstruct chat history)   | `AIMessage`        |

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

messages = [
    SystemMessage(content="You are a helpful cricket analyst. Answer concisely."),
    HumanMessage(content="Who is the best fast bowler in India right now?"),
    AIMessage(content="Jasprit Bumrah is widely considered the best."),
    HumanMessage(content="What makes his action so effective?")
]
```

When you pass this list to an LLM, it has full context of the conversation — the model knows it's a cricket analyst, sees the previous exchange, and responds accordingly.

### ChatPromptTemplate

`ChatPromptTemplate` manages lists of messages with dynamic variables — the conversational equivalent of `PromptTemplate`.

```python
from langchain_core.prompts import ChatPromptTemplate

chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}. Always respond in {language}."),
    ("human", "{user_input}")
])

prompt = chat_template.invoke({
    "role": "cricket analyst",
    "language": "English",
    "user_input": "Who won the 2011 World Cup?"
})
```

Variables work across all message types — system, human, and AI messages can all have placeholders.

---

## 🔄 MessagesPlaceholder — Injecting Chat History

**The problem:** Real conversational apps accumulate message history over time. You can't hardcode past messages into your template — they grow dynamically with each turn.

**The solution:** `MessagesPlaceholder` reserves a slot in the template where an entire list of messages gets injected at runtime.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are a customer support agent for {company}. Be professional and concise."),
    MessagesPlaceholder(variable_name="chat_history"),   # ← entire history injected here
    ("human", "{user_input}")
])
```

**At runtime, inject the accumulated history:**

```python
from langchain_core.messages import HumanMessage, AIMessage

history = [
    HumanMessage(content="I placed an order 3 days ago."),
    AIMessage(content="I can help with that. Could you share your order ID?"),
    HumanMessage(content="It's #ORD-4821."),
    AIMessage(content="Thank you. Let me look that up for you.")
]

prompt = chat_template.invoke({
    "company": "TechStore",
    "chat_history": history,
    "user_input": "Why hasn't it shipped yet?"
})
```

**What the LLM receives:**

```
System:  "You are a customer support agent for TechStore. Be professional and concise."
Human:   "I placed an order 3 days ago."
AI:      "I can help with that. Could you share your order ID?"
Human:   "It's #ORD-4821."
AI:      "Thank you. Let me look that up for you."
Human:   "Why hasn't it shipped yet?"   ← current question, with full context
```

The model can now answer with awareness of the full conversation — without the developer hardcoding any of it.

---

## 🗺️ How These Pieces Relate

```
           Raw User Input
                 ↓
        PromptTemplate / ChatPromptTemplate
     (structure + variable injection + validation)
                 ↓
      SystemMessage + HumanMessage + AIMessage
           (role-aware message list)
                 ↓
         MessagesPlaceholder (if needed)
           (dynamic history injection)
                 ↓
              LLM Call
                 ↓
            AI Response
```

---

## 💡 Key Takeaways

**On f-strings vs PromptTemplate:** The difference feels academic until you're debugging a production app where a missing variable causes a silent failure halfway through a chain. Validation at the boundary matters.

**On MessagesPlaceholder:** This is the primitive that makes stateful chatbots possible in LangChain. The memory modules from Day 02/03 — Buffer Memory, Summarizer Memory — all ultimately inject their output into a `MessagesPlaceholder` slot like this.

---

## 📚 Resources

- [LangChain Prompts Docs](https://python.langchain.com/docs/concepts/prompt_templates/)
- [ChatPromptTemplate Reference](https://python.langchain.com/docs/concepts/prompt_templates/#chatprompttemplate)
- [MessagesPlaceholder](https://python.langchain.com/docs/concepts/prompt_templates/#messagesplaceholder)

---

*Next up → Day 06: Output Parsers — StrOutputParser, PydanticOutputParser, and structured LLM responses*