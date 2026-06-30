# Day 12 — LangChain: Retrievers (RAG Part 4)

## 🧠 What Are Retrievers?

A **Retriever** is the query interface sitting on top of a data source (most often a Vector Store). It takes a user's query and returns a list of relevant `Document` objects.

```python
retriever.invoke("What is RAG?")
# → [Document(...), Document(...), Document(...)]
```

**Important:** Every retriever in LangChain is a **Runnable** (Day 09 callback) — meaning it implements `.invoke()` and can be dropped directly into any LCEL chain.

```python
chain = retriever | format_docs | prompt | llm | parser
```

---

## 🗂️ Two Ways to Categorize Retrievers

```
Retrievers
    │
    ├── By Data Source
    │   What the retriever queries against
    │   (Wikipedia, Vector Store, etc.)
    │
    └── By Search Strategy
        HOW it decides what's relevant
        (similarity, diversity, multi-query, compression)
```

---

## 📚 Data-Source-Based Retrievers

---

### 1. WikipediaRetriever

Queries the live Wikipedia API directly — no vector store required. Uses keyword-based matching internally.

```python
from langchain_community.retrievers import WikipediaRetriever

retriever = WikipediaRetriever(top_k_results=3, lang="en")

docs = retriever.invoke("Quantum computing")

for doc in docs:
    print(doc.metadata["title"])
    print(doc.page_content[:200])
```

**Use when:** You need general knowledge grounding and don't want to maintain your own knowledge base.

---

### 2. VectorStoreRetriever — The Most Common Type

Performs semantic similarity search within a vector store (Chroma, FAISS, Pinecone). This is what you get by converting a vector store into a retriever.

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vector_store = Chroma(
    collection_name="my_docs",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    persist_directory="./chroma_db"
)

# Convert vector store into a retriever
retriever = vector_store.as_retriever(search_kwargs={"k": 4})

docs = retriever.invoke("How does RAG work?")
```

This is the connective tissue between Day 11 (Vector Stores) and the rest of a RAG pipeline — `.as_retriever()` is the standard way to expose a vector store as a queryable Runnable.

---

## 🎯 Search-Strategy-Based Retrievers

These wrap a base retriever (usually a Vector Store Retriever) and change *how* relevance is determined.

---

### 3. Maximum Marginal Relevance (MMR) — Reducing Redundancy

**The problem:** Pure similarity search often returns near-duplicate chunks. If 5 chunks all say roughly the same thing, you've wasted your retrieval budget.

**MMR's fix:** Balances relevance *and* diversity. It iteratively picks the next most relevant document **that is also least similar to already-selected documents**.

```python
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,              # final number of docs to return
        "fetch_k": 20,       # initial candidate pool size
        "lambda_mult": 0.5   # 0 = max diversity, 1 = max relevance
    }
)

docs = retriever.invoke("Explain transformer architecture")
```

```
Pure similarity search:
  [chunk_A] [chunk_A'] [chunk_A''] [chunk_B]   ← 3 near-duplicates, 1 unique

MMR:
  [chunk_A] [chunk_B] [chunk_C] [chunk_D]      ← 4 distinct perspectives
```

**Use when:** Your document set has overlapping content and you want broader coverage, not repetition.

---

### 4. Multi-Query Retriever — Solving Query Ambiguity

**The problem:** A single user query might be phrased ambiguously or narrowly, missing relevant documents that use different terminology.

**The fix:** Uses an LLM to generate **multiple reformulations** of the original query, retrieves documents for each, then merges and deduplicates the results.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

base_retriever = vector_store.as_retriever(search_kwargs={"k": 3})

multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

docs = multi_query_retriever.invoke("How do I improve model accuracy?")
```

**What happens internally:**

```
Original query: "How do I improve model accuracy?"

LLM generates variations:
  1. "What techniques increase machine learning model performance?"
  2. "Ways to reduce prediction error in ML models"
  3. "Best practices for boosting classifier accuracy"

Each variation → retrieves its own set of docs
        ↓
   Merge + deduplicate
        ↓
   Final combined result set
```

**Use when:** Queries are often vague, short, or use different vocabulary than your source documents.

---

### 5. Contextual Compression Retriever — Improving Precision

**The problem:** Retrieved chunks often contain a mix of relevant and irrelevant text. Passing the full chunk to the LLM wastes context window and can dilute the answer.

**The fix:** After retrieval, an LLM **compresses** each document — stripping out everything except the parts that actually answer the query.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

base_retriever = vector_store.as_retriever(search_kwargs={"k": 5})
compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

docs = compression_retriever.invoke("What is the chunk_overlap parameter used for?")
```

```
Raw retrieved chunk (300 words):
  "Text splitting is important for RAG... [200 words of general context]
   ...chunk_overlap ensures boundary information isn't lost between
   adjacent chunks... [80 more words of unrelated detail]"

Compressed output (after LLM extraction):
  "chunk_overlap ensures boundary information isn't lost
   between adjacent chunks."
```

**Trade-off:** Adds an extra LLM call per retrieved document — increases latency and cost, but improves precision and reduces noise in the final prompt.

**Use when:** Context window space is tight, or retrieved chunks tend to be long and only partially relevant.

---

## 🧭 Choosing the Right Retriever

| Retriever | Solves | Cost | Use When |
|---|---|---|---|
| WikipediaRetriever | No need for your own knowledge base | Low | General knowledge questions |
| VectorStoreRetriever | Baseline semantic search | Low | Default starting point |
| MMR | Redundant/duplicate results | Low | Document set has overlapping content |
| Multi-Query | Query ambiguity / vocabulary mismatch | Medium (extra LLM call) | Users phrase queries inconsistently |
| Contextual Compression | Noisy, partially-relevant chunks | Higher (LLM call per doc) | Context window is tight, precision matters |

> These aren't mutually exclusive — Multi-Query and Contextual Compression can both wrap an MMR-based base retriever for a layered pipeline.

---

## 🗺️ Retrievers in the Full RAG Pipeline

```
Document Loaders     ← Day 09B
        ↓
  Text Splitters      ← Day 10
        ↓
  Vector Store         ← Day 11
        ↓
  Retriever             ← TODAY
  (the tunable layer — this is where RAG quality is won or lost)
        ↓
  LLM + Context
  (grounded response)
```

---

## 💡 Key Takeaways

**On why retrievers matter most:** Standard RAG implementations often plateau in quality not because of the LLM, but because of weak retrieval. Swapping `similarity_search` for `MMR` or `Multi-Query` is frequently the highest-leverage change you can make to improve answer quality — more impactful than switching the LLM itself.

**On layering retrievers:** Production RAG systems often combine multiple strategies — e.g., Multi-Query to handle phrasing variance, feeding into MMR to ensure diversity, feeding into Contextual Compression to trim noise before the final LLM call. Each adds latency, so layer only what your accuracy requirements justify.

**On Runnables again:** The fact that retrievers are Runnables means they slot directly into `RunnableParallel`, `RunnablePassthrough`, and the rest of the primitives from Day 09. A typical RAG chain looks like: `RunnableParallel(context=retriever, question=RunnablePassthrough()) | prompt | llm | parser`.

**Connection to Intervio:** For the GitHub repo scraping use case, Multi-Query could help — a candidate's repo description might use different terminology than the interview question generator expects. Reformulating the query before retrieval would likely improve which repo sections get surfaced.

---

## 📚 Resources

- [LangChain Retrievers Docs](https://python.langchain.com/docs/concepts/retrievers/)
- [MultiQueryRetriever](https://python.langchain.com/docs/how_to/MultiQueryRetriever/)
- [ContextualCompressionRetriever](https://python.langchain.com/docs/how_to/contextual_compression/)
- [MMR Search](https://python.langchain.com/docs/how_to/vectorstore_retriever/#maximum-marginal-relevance-mmr-retrieval)

---
