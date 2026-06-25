# Day 02 — LangChain: The Six Core Components

> **Topic:** Architectural building blocks of the LangChain framework

---

## 🧠 What I Learned

LangChain is built around **six core components**. Before writing any code, it's worth understanding what each one does architecturally — because every LangChain project you build will be some combination of these six pieces.

---

## ⚙️ The Six Components
![alt text](<assets/Screenshot from 2026-06-18 13-58-59.png>)
### 1. 🤖 Models — Solving API Fragmentation
 
**The problem before LangChain:**
 
LLMs are typically >100GB in size, so companies host them remotely and expose them via web APIs. But every provider designed their API differently:
 
- OpenAI uses `openai.ChatCompletion.create(...)`
- Anthropic uses `anthropic.messages.create(...)`
- Google uses `genai.GenerativeModel(...).generate_content(...)`
Switching providers meant rewriting your entire integration layer. Combining providers in one app was even messier.
 
**LangChain's fix:** A unified calling interface. Regardless of the backend model, the orchestration code looks identical.
 
```python
# Same interface, different providers
llm = ChatOpenAI(model="gpt-4o")
llm = ChatAnthropic(model="claude-3-5-sonnet")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
 
response = llm.invoke("Explain RAG in one paragraph")
# ↑ identical call regardless of provider
```
 
**Two model types:**
 
| Type             | Input → Output     | Primary Use                        |
|------------------|--------------------|------------------------------------|
| Language Models  | Text → Text        | Chat, Q&A, summarization, code gen |
| Embedding Models | Text → Vector      | Semantic search, RAG, clustering   |
 
---
 
### 2. 📝 Prompts — Managing Inputs Programmatically
 
Model outputs are **extremely sensitive to phrasing**. A tiny wording change can shift the output completely. Hardcoding prompts as strings doesn't scale.
 
**Three prompt patterns LangChain provides:**
 
**a) Dynamic Templates** — parameterized prompts with runtime variables
 
```
"Summarize this {topic} in a {tone} tone."
                ↑              ↑
        filled at runtime from user input
```
 
**b) Role-Based Prompting** — explicit separation of instruction layers
 
```
System:  "You are an expert cardiologist. Answer only medical questions."
Human:   "What are the early symptoms of a myocardial infarction?"
```
 
The system prompt defines the model's *identity and constraints*. The user prompt carries the *actual task*.
 
**c) Few-Shot Prompt Templates** — inject worked examples before the real query
 
Useful when you need structured, predictable output formats. For example, classifying support tickets:
 
```
Example 1 → Input: "I was charged twice" → Output: Billing
Example 2 → Input: "App keeps crashing" → Output: Technical
Example 3 → Input: "How do I reset password?" → Output: General
 
Real Input: "My invoice shows the wrong amount"
Expected:   Billing   ← model follows the pattern
```
 
---
 
### 3. 🔗 Chains — Three Pipeline Patterns
 
Chains automate the passing of outputs between components. No manual catching and re-feeding.
 
**a) Sequential Chains** — linear multi-step pipelines
 
```
English Brief (1000 words)
        ↓
    LLM 1  →  translate to Hindi
        ↓
    LLM 2  →  summarize to 100 words
        ↓
    Final Hindi Summary
```
 
**b) Parallel Chains** — fan-out and consolidate
 
```
                User Query
               ↙     ↓     ↘
           LLM 1   LLM 2   LLM 3
         (Report A) (Report B) (Report C)
               ↘     ↓     ↙
           Final Consolidating LLM
                ↓
           Master Document
```
 
Good for: research synthesis, multi-perspective analysis, ensemble outputs.
 
**c) Conditional Chains** — branching logic based on LLM evaluation
 
```
Customer Feedback
        ↓
  Sentiment LLM
   ↙           ↘
Positive      Negative
   ↓              ↓
"Thank You"   Alert email
  screen    → Support team
```
 
The LLM acts as the condition evaluator, routing the flow dynamically.
 
---
 
### 4. 🗂️ Indexes — The RAG Architecture
 
Indexes let you ground an LLM in **your private data** without retraining or fine-tuning the base model.
 
**Full RAG pipeline:**
 
```
[Document Source]
        ↓
  Document Loaders       ← connect to Drive, S3, local FS, web
        ↓
    Raw Text
        ↓
   Text Splitters        ← chunk by paragraph, sentence, or page
        ↓
   Text Chunks
        ↓
  Embedding Model        ← convert each chunk to a vector
        ↓
   Vector Store          ← store + index all vectors (FAISS, Pinecone, ChromaDB)
 
 
        [User Query]
              ↓
   Embedding Model       ← convert query to vector
              ↓
   Semantic Search       ← compare query vector against stored vectors
              ↓
    Retriever            ← pull top-K most relevant chunks
              ↓
    LLM + Context        ← answer using retrieved chunks as grounding
              ↓
    Final Response
```
 
**The four sub-components:**
 
| Sub-component     | Role                                                                 |
|-------------------|----------------------------------------------------------------------|
| Document Loaders  | Adapters for PDF, CSV, markdown, Google Drive, AWS S3, databases     |
| Text Splitters    | Break large docs into overlapping chunks for effective embedding     |
| Vector Stores     | Specialized DBs that index and query embedding vectors               |
| Retrievers        | Turn user queries into vectors and fetch the most relevant chunks    |
 
---
 
### 5. 🧠 Memory — Four Strategies
 
Every LLM API call is **stateless by default** — the model has zero memory of the previous message. LangChain injects state tracking on top of the API.
 
**Four memory strategies:**
 
| Strategy                      | How It Works                                                   | Best For                        | Trade-off                          |
|-------------------------------|----------------------------------------------------------------|---------------------------------|------------------------------------|
| Conversation Buffer           | Appends full chat history to every request                     | Short sessions, high accuracy   | Token cost grows unboundedly       |
| Conversation Buffer Window    | Keeps only the last N messages, drops older ones               | Medium-length sessions          | Older context lost                 |
| Conversation Summarizer       | Background LLM compresses history into a running summary       | Long sessions, token efficiency | Slight information loss            |
| Custom Memory                 | Logs specific facts (user profile, preferences) only           | Personalization use cases       | Requires explicit schema design    |
 
**Visualized:**
 
```
Buffer Memory:       [msg1][msg2][msg3][msg4][msg5] → LLM
Window Memory (N=3):              [msg3][msg4][msg5] → LLM
Summarizer Memory:  [Summary of msg1-4][msg5] → LLM
```
 
---
 
### 6. 🤖 Agents — Reasoning + Tool Use
 
Agents are the step-change from *passive chatbot* to *active autonomous assistant*.
 
**What makes an Agent different from a Chain:**
 
| | Chain | Agent |
|---|---|---|
| Flow | Pre-defined, fixed | Dynamic, decided at runtime |
| Decision-making | None | LLM reasons about next step |
| Tool use | Static | Chooses tools autonomously |
 
**Two core capabilities:**
 
1. **Reasoning (Chain-of-Thought)** — breaks a complex task into logical sub-steps before acting
2. **Tool Access** — a curated toolkit (calculator, weather API, web scraper, DB connector) the LLM can invoke
**Agent execution loop:**
 
```
User Query
    ↓
Thought: What do I need to answer this?
    ↓
Action: Pick a tool + pass inputs
    ↓
Observation: Receive tool output
    ↓
Thought: Do I have enough to answer? If not → loop
    ↓
Final Answer
```
 
**Worked example — "Multiply today's Delhi temperature by 3":**
 
```
Thought:   I need the current Delhi temperature. Use weather tool.
Action:    weather_api("Delhi")  →  returns 25°C
 
Thought:   Now multiply 25 × 3. Use calculator.
Action:    calculator(25 * 3)    →  returns 75
 
Final:     "The result is 75."
```
 
The LLM never hardcodes the temperature or does the math itself — it **decides which tools to call and sequences them correctly**.
 
---
 
## 🗺️ Full Component Interaction Map
 
```
              [User Input]
                   ↓
           [2] Prompt Templates
        (structure + role injection)
                   ↓
             [1] Models
         (LLM / Embedding Model)
            ↙           ↘
     [4] Indexes       [5] Memory
  (external knowledge)  (chat history)
            ↘           ↙
           [3] Chains
      (orchestrate the pipeline)
                   ↓
             [6] Agents
    (if autonomous action is needed)
                   ↓
           [Final Output]
```

In most apps, you won't use all six at once — but knowing all of them lets you pick the right tool for the job.

---

## 💡 Key Takeaway

These six components map cleanly onto the six hard problems of building an LLM app:

| Problem                              | Component  |
|--------------------------------------|------------|
| Which model do I use?                | Models     |
| How do I structure my prompt?        | Prompts    |
| How do I chain multiple steps?       | Chains     |
| How do I query my own data?          | Indexes    |
| How does it remember past messages?  | Memory     |
| How does it take real-world actions? | Agents     |

LangChain doesn't invent new AI capabilities — it gives you **clean abstractions** over the messy engineering that every LLM app eventually needs.

---

## 📚 Resources

- [LangChain Docs — Components](https://python.langchain.com/docs/concepts/)
- [CampusX LangChain Playlist](https://www.youtube.com/@campusx-official)

---

*Next up → Day 03: Hands-on — Setting up LangChain, connecting to a model, and building a first chain*