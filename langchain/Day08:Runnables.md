# Day 09 — LangChain: Runnables & LCEL

## 🧠 What I Learned

Today covers the *why* behind the architecture we've been using since Day 08. Every `|` pipe, every `.invoke()` call — it all comes from the Runnable interface. Understanding this makes the entire LangChain codebase readable.

---

## 📜 The Evolution of LangChain

LangChain didn't start with Runnables. It evolved into them.

```
Phase 1 — Model Wrappers
  LangChain provided standardized interfaces for LLM providers
  (OpenAI, Anthropic, etc.)

Phase 2 — Component Expansion
  Added Document Loaders, Text Splitters, Vector Stores
  to support end-to-end RAG workflows

Phase 3 — Chains
  Introduced LLMChain, RetrievalQAChain, etc.
  to automate connecting components together

Problem: Too many specialized chain classes.
         Each component used different method names:
           - LLM used .predict()
           - Prompt used .format()
           - Retriever used .get_relevant_documents()
         No common interface → components couldn't be linked cleanly

Phase 4 — Runnables (current)
  Every component implements one standard method: .invoke()
  Now any component can connect to any other component
```

---

## 🧱 What Are Runnables?

A **Runnable** is any LangChain component that implements the standard `.invoke()` method.

Think of them as **LEGO blocks** — because every piece follows the same interface (same connector shape), you can snap any block to any other block without custom glue code.

```python
# Every one of these implements .invoke()
ChatOpenAI().invoke(...)
ChatPromptTemplate.invoke(...)
StrOutputParser().invoke(...)
HuggingFaceEmbeddings().invoke(...)
```

When `ChatOpenAI`, `PromptTemplate`, and `StrOutputParser` all share the same interface, you can compose them with `|` and call `.invoke()` on the result — the chain handles the rest.

---

## 🗂️ Two Categories of Runnables

```
Runnables
    │
    ├── Task-Specific Runnables
    │   Core components standardized to use .invoke()
    │   Examples: ChatOpenAI, ChatPromptTemplate, StrOutputParser
    │
    └── Runnable Primitives
        Orchestration tools that control HOW components connect
        Examples: RunnableSequence, RunnableParallel, RunnableBranch...
```

---

## 🔨 The Five Runnable Primitives

---

### 1. RunnableSequence

Connects runnables **one after another**. Output of step N → input of step N+1.

```python
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([("human", "Tell me about {topic}")])
llm    = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# Explicit class instantiation
chain = RunnableSequence(first=prompt, middle=[llm], last=parser)

# Equivalent LCEL syntax (preferred)
chain = prompt | llm | parser

result = chain.invoke({"topic": "black holes"})
```

**Data flow:**

```
{"topic": "black holes"}
        ↓ prompt
formatted messages
        ↓ llm
AIMessage(content="...")
        ↓ parser
"..." (plain string)
```

---

### 2. RunnableParallel

Runs multiple runnables **simultaneously** on the same input. Returns a dict of outputs.

```python
from langchain_core.runnables import RunnableParallel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm    = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

notes_chain = ChatPromptTemplate.from_messages([
    ("human", "Generate study notes from:\n\n{document}")
]) | llm | parser

quiz_chain = ChatPromptTemplate.from_messages([
    ("human", "Generate a 5-question quiz from:\n\n{document}")
]) | llm | parser

parallel = RunnableParallel(notes=notes_chain, quiz=quiz_chain)

result = parallel.invoke({"document": "...document text..."})
# → {"notes": "...", "quiz": "..."}
```

**Data flow:**

```
{"document": "..."}
        ↓
  ┌─────────────────────────┐
  │  notes_chain  (async)   │
  │  quiz_chain   (async)   │  ← both run concurrently
  └─────────────────────────┘
        ↓
  {"notes": "...", "quiz": "..."}
```

---

### 3. RunnablePassthrough

Passes input **through unchanged**. Used to preserve original data alongside transformed outputs in a pipeline.

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm    = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

summary_chain = ChatPromptTemplate.from_messages([
    ("human", "Summarize this in one sentence:\n\n{text}")
]) | llm | parser

# Keep original text AND add summary
chain = RunnableParallel(
    original=RunnablePassthrough(),   # passes {"text": "..."} unchanged
    summary=summary_chain
)

result = chain.invoke({"text": "LangChain is an orchestration framework..."})
# → {"original": {"text": "LangChain is..."}, "summary": "LangChain simplifies LLM app development."}
```

**When to use it:** RAG pipelines — you often want to pass the original question through alongside the retrieved context so the final step has access to both.

---

### 4. RunnableLambda

Wraps any **plain Python function** as a Runnable so it can be used inside a chain.

```python
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm    = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# Custom preprocessing logic
def word_count_check(input_dict):
    text = input_dict["text"]
    word_count = len(text.split())
    return {"text": text, "word_count": word_count}

def format_for_prompt(input_dict):
    return {"document": f"[{input_dict['word_count']} words]\n\n{input_dict['text']}"}

chain = (
    RunnableLambda(word_count_check)
    | RunnableLambda(format_for_prompt)
    | ChatPromptTemplate.from_messages([("human", "Summarize:\n\n{document}")])
    | llm
    | parser
)

result = chain.invoke({"text": "LangChain is a framework for building LLM apps..."})
```

**Use when:** You need data transformation, formatting, filtering, or any custom Python logic between chain steps.

---

### 5. RunnableBranch

Implements **if/else routing** — directs input to different chains based on a condition.

```python
from langchain_core.runnables import RunnableBranch, RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm    = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# Branch A: long report → summarize
summarize_chain = ChatPromptTemplate.from_messages([
    ("human", "Summarize this report in 3 bullet points:\n\n{text}")
]) | llm | parser

# Branch B: short report → expand
expand_chain = ChatPromptTemplate.from_messages([
    ("human", "Expand this into a full report:\n\n{text}")
]) | llm | parser

branch = RunnableBranch(
    (lambda x: len(x["text"].split()) > 300, summarize_chain),  # condition + chain
    expand_chain                                                  # default branch
)

result = branch.invoke({"text": "...your report text here..."})
```

**Data flow:**

```
{"text": "..."}
        ↓
  RunnableBranch
  ├── word count > 300  →  summarize_chain  →  bullet summary
  └── default           →  expand_chain     →  full report
        ↓
      result
```

---

## 🔤 LCEL — LangChain Expression Language

LCEL is the **declarative syntax** for composing Runnables using the `|` pipe operator.

```python
# LCEL (declarative) — preferred
chain = prompt | llm | parser

# Equivalent explicit instantiation
chain = RunnableSequence(first=prompt, middle=[llm], last=parser)
```

Currently, LCEL's `|` operator maps to `RunnableSequence`. For parallel and conditional patterns, you still instantiate `RunnableParallel` and `RunnableBranch` directly — though future LangChain versions may extend LCEL syntax to cover these.

**Why LCEL matters beyond syntax:**

Any chain built with LCEL automatically gets:

| Capability | What It Means |
|---|---|
| `.stream()` | Stream tokens as they're generated |
| `.batch()` | Process multiple inputs in parallel |
| `.ainvoke()` | Async execution |
| `.astream()` | Async streaming |

You write the chain once with `|` and get all four execution modes for free.

---

## 🗺️ Full Primitive Map

```
Runnable Primitives
│
├── RunnableSequence    A | B | C          (sequential pipeline)
├── RunnableParallel    {A, B} → {out_A, out_B}  (concurrent branches)
├── RunnablePassthrough input → input unchanged   (data preservation)
├── RunnableLambda      fn → Runnable      (custom Python logic)
└── RunnableBranch      condition → A or B (conditional routing)
```

---

## 💡 Key Takeaways

**On the Runnable standard:** The `.invoke()` unification is what makes LangChain composable. Before it, every component had its own method name and you needed custom adapter code between each pair. Now, any component can plug into any chain position — this is the architectural insight behind the whole framework.

**On RunnablePassthrough in RAG:** This primitive becomes essential in retrieval chains. The typical RAG pattern passes the original question through alongside retrieved documents so the final prompt has access to both — `RunnablePassthrough` is what enables that.

**On RunnableLambda as the escape hatch:** Whenever LangChain doesn't have a built-in for what you need, `RunnableLambda` bridges the gap. Any Python function becomes a first-class chain component — no subclassing required.

**On LCEL's hidden benefits:** The pipe syntax looks like a convenience feature, but the real value is the automatic `.stream()`, `.batch()`, and `.ainvoke()` support. Building an async streaming endpoint (like Intervio's real-time interview feedback) on top of a LangChain chain is essentially free if you used LCEL to compose it.

---

## 📚 Resources

- [LCEL Docs](https://python.langchain.com/docs/concepts/lcel/)
- [Runnable Interface](https://python.langchain.com/docs/concepts/runnables/)
- [RunnableParallel](https://python.langchain.com/docs/concepts/runnables/#runnableparallel)
- [RunnableBranch](https://python.langchain.com/docs/concepts/runnables/#runnablebranch)
- [RunnableLambda](https://python.langchain.com/docs/concepts/runnables/#runnablelambda)

---
