# Day 08 — LangChain: Chains

## 🧠 What Are Chains?

Building an LLM app without chains means manually calling each component, catching its output, reformatting it, and passing it to the next step. That's fragile and doesn't scale.

**Chains automate this.** Each component's output becomes the next component's input — automatically — triggered by a single `.invoke()` call.

```
Without chains:
  prompt = template.format(topic=topic)
  response = llm.invoke(prompt)
  text = response.content
  parsed = parser.parse(text)        ← manual at every step

With chains (LCEL):
  result = chain.invoke({"topic": topic})   ← one call, everything runs
```

LangChain Expression Language (LCEL) uses the **pipe operator `|`** to compose chains:

```python
chain = prompt | llm | parser
```

---

## 🔗 Chain Type 1 — Simple Chain

The baseline pattern: `PromptTemplate → LLM → OutputParser`.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "Tell me about {topic}")
])

chain = template | llm | parser

result = chain.invoke({"topic": "black holes"})
print(result)   # → clean text string
```

**Data flow:**

```
{"topic": "black holes"}
        ↓
  ChatPromptTemplate   →  formats into messages
        ↓
     ChatOpenAI        →  returns AIMessage
        ↓
  StrOutputParser      →  extracts .content as plain string
        ↓
      result (str)
```

---

## 🔗 Chain Type 2 — Sequential Chain

Multiple LLM calls chained end-to-end. The output of call 1 becomes the input to call 2.

**Example:** Generate a detailed report on a topic → summarize it into 5 bullet points.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# Step 1: Generate detailed report
report_template = ChatPromptTemplate.from_messages([
    ("system", "You are a research assistant."),
    ("human", "Write a detailed report on {topic}.")
])

# Step 2: Summarize the report
summary_template = ChatPromptTemplate.from_messages([
    ("system", "You are a concise summarizer."),
    ("human", "Summarize the following report in exactly 5 bullet points:\n\n{report}")
])

# Chain them: topic → report → summary
report_chain  = report_template | llm | parser
summary_chain = summary_template | llm | parser

# Compose: output of report_chain feeds into {report} in summary_template
full_chain = report_chain | (lambda report: {"report": report}) | summary_chain

result = full_chain.invoke({"topic": "quantum computing"})
print(result)
```

**Data flow:**

```
{"topic": "quantum computing"}
        ↓
  report_template + LLM + parser   →  detailed report (str)
        ↓
  {"report": <report text>}
        ↓
  summary_template + LLM + parser  →  5 bullet summary (str)
        ↓
      result
```

---

## 🔗 Chain Type 3 — Parallel Chain

Uses `RunnableParallel` to run multiple chains **simultaneously** on the same input, then merges their outputs downstream.

**Example:** Given a document, generate notes AND a quiz in parallel, then merge both into a single study guide.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

llm = ChatOpenAI(model="gpt-4o")
parser = StrOutputParser()

# Branch 1: Generate notes
notes_template = ChatPromptTemplate.from_messages([
    ("system", "You are a study assistant."),
    ("human", "Generate concise notes from the following document:\n\n{document}")
])

# Branch 2: Generate a quiz
quiz_template = ChatPromptTemplate.from_messages([
    ("system", "You are a quiz creator."),
    ("human", "Create a 5-question quiz from the following document:\n\n{document}")
])

# Merge step: combine notes + quiz into a study guide
merge_template = ChatPromptTemplate.from_messages([
    ("system", "You are a document editor."),
    ("human", "Combine the following notes and quiz into a clean study guide.\n\nNotes:\n{notes}\n\nQuiz:\n{quiz}")
])


# Run notes and quiz in parallel, then merge
parallel_chain = RunnableParallel(notes=notes_template | llm | parser, quiz=quiz_template  | llm | parser)

merge_chain = merge_template | llm | parser

full_chain = parallel_chain | merge_chain

result = full_chain.invoke({"document": "...your document text here..."})
print(result)
```
For imagination of flow chains use :
```python
chain.get_graph().print_ascii()
```
**Data flow:**

```
{"document": "..."}
        ↓
  RunnableParallel
  ┌───────────────────────────────┐
  │  notes_chain  →  notes (str) │   ← runs simultaneously
  │  quiz_chain   →  quiz  (str) │
  └───────────────────────────────┘
        ↓
  {"notes": "...", "quiz": "..."}
        ↓
  merge_chain   →  final study guide (str)
        ↓
      result
```

**Key benefit:** Both branches run concurrently — faster than sequential execution when steps are independent.

---

## 🔗 Chain Type 4 — Conditional Chain

Uses `RunnableBranch` and `RunnableLambda` to implement **if/else routing** inside a chain.

**Example:** Classify customer feedback as positive or negative, then route to a different response chain based on the result.

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnableParallel, RunnableBranch, RunnableLambda
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

model = ChatOpenAI()

parser = StrOutputParser()

class Feedback(BaseModel):

    sentiment: Literal['positive', 'negative'] = Field(description='Give the sentiment of the feedback')

parser2 = PydanticOutputParser(pydantic_object=Feedback)

prompt1 = PromptTemplate(
    template='Classify the sentiment of the following feedback text into postive or negative \n {feedback} \n {format_instruction}',
    input_variables=['feedback'],
    partial_variables={'format_instruction':parser2.get_format_instructions()}
)

classifier_chain = prompt1 | model | parser2

prompt2 = PromptTemplate(
    template='Write an appropriate response to this positive feedback \n {feedback}',
    input_variables=['feedback']
)

prompt3 = PromptTemplate(
    template='Write an appropriate response to this negative feedback \n {feedback}',
    input_variables=['feedback']
)

branch_chain = RunnableBranch(
    (lambda x:x.sentiment == 'positive', prompt2 | model | parser),
    (lambda x:x.sentiment == 'negative', prompt3 | model | parser),
    RunnableLambda(lambda x: "could not find sentiment")
)

chain = classifier_chain | branch_chain

print(chain.invoke({'feedback': 'This is a beautiful phone'}))

chain.get_graph().print_ascii()
```
* We have used pydantic as we can't trust llm output whether it will give positive or negative

**Data flow:**

```
{"feedback": "..."}
        ↓
  classifier_chain   →  Sentiment(label="negative")
        ↓
  RunnableBranch
  ├── label == "positive"  →  positive_chain  →  thank-you response
  └── default              →  negative_chain  →  empathy + solution
        ↓
      result (routed response)
```

---

## 🔑 Key LCEL Primitives

| Primitive | Purpose |
|---|---|
| `|` (pipe) | Compose components sequentially |
| `RunnableParallel` | Execute multiple branches simultaneously |
| `RunnableBranch` | Route to different chains based on a condition |
| `RunnableLambda` | Wrap a plain Python function as a chain component |

---

## 🗺️ All Four Chain Types — Side by Side

```
Simple:
  A | B | C

Sequential:
  A | B | C | D | E

Parallel:
  ┌── B ──┐
  A       ├── D
  └── C ──┘

Conditional:
  A → classifier
          ├── condition true  → B
          └── condition false → C
```

---

## 💡 Key Takeaways

**On LCEL and the pipe operator:** The `|` syntax is not just syntactic sugar — it returns a `Runnable` object that supports `.invoke()`, `.stream()`, `.batch()`, and `.ainvoke()` (async) automatically. You get streaming and async for free just by using LCEL composition.

**On `RunnableLambda`:** This is the escape hatch. Whenever you need custom Python logic inside a chain — data transformation, conditional prep, format conversion — wrap it in `RunnableLambda` and it plugs in cleanly.

**On Parallel vs Sequential:** Use `RunnableParallel` whenever two steps don't depend on each other's output. Running notes and quiz generation in parallel halves the latency versus running them sequentially.

**On Conditional Chains + Pydantic:** The classifier uses `with_structured_output(Sentiment)` to guarantee the label is always exactly `"positive"` or `"negative"` — not `"Positive"`, `"POSITIVE"`, or `"mostly positive"`. Without this, the branch condition becomes unreliable. Structured output is what makes conditional routing production-safe.

---

## 📚 Resources

- [LangChain LCEL Docs](https://python.langchain.com/docs/concepts/lcel/)
- [RunnableParallel](https://python.langchain.com/docs/concepts/runnables/#runnableparallel)
- [RunnableBranch](https://python.langchain.com/docs/concepts/runnables/#runnablebranch)
- [RunnableLambda](https://python.langchain.com/docs/concepts/runnables/#runnablelambda)

---

*Next up → Day 09: Indexes & RAG — Document Loaders, Text Splitters, Vector Stores, and Retrievers*