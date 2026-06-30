# Day 11 — LangChain: Vector Stores (RAG Part 3)



## 🧠 Why Vector Stores Are Necessary

Traditional databases search by **exact keyword matching**. This breaks down for meaning-based queries.

```
Example: Movie Recommendation

Query: "A movie about a lone astronaut surviving alone in space"

Keyword search:
  Won't match "The Martian" unless it literally contains
  the words "lone astronaut surviving alone in space"

Semantic search:
  Embeds the query and movie descriptions into vectors
  Finds "The Martian" because its MEANING is close,
  even with zero shared keywords
```

**The fix:** convert text into embeddings (numerical vectors capturing semantic meaning), then search by **vector similarity** (cosine similarity) instead of keyword overlap.

---

## ⚠️ The Three Scaling Challenges

Once you have millions of embedded documents, naive similarity search breaks down:

| Challenge | What Happens at Scale |
|---|---|
| **Compute cost** | Comparing a query vector against every stored vector (brute-force) becomes too slow |
| **Storage inefficiency** | Traditional row/column databases aren't built for high-dimensional vector data |
| **Search degradation** | Linear scan time grows with dataset size — unusable beyond a certain point |

Vector Stores exist specifically to solve these three problems.

---

## 🧱 Core Features of a Vector Store

| Feature | What It Does |
|---|---|
| **Storage** | Persists vectors + associated metadata (IDs, source, tags) |
| **Similarity Search** | Built-in mechanism to find the nearest vectors to a query vector |
| **Indexing** | Uses ANN (Approximate Nearest Neighbor) algorithms — clustering, graph-based search — to avoid brute-force comparison |
| **CRUD Operations** | Create, Read, Update, Delete on stored vectors, same as a normal database |

**Indexing is the key performance unlock:**

```
Brute-force search (no index):
  Query vector vs. every single stored vector → O(n) comparisons

Indexed search (ANN):
  Query vector vs. a smart subset of candidates → much faster,
  approximate but highly accurate in practice
```

---

## ⚖️ Vector Store vs. Vector Database

These terms get used interchangeably but aren't the same thing.

| | Vector Store | Vector Database |
|---|---|---|
| Example | FAISS | Pinecone, Milvus |
| Scope | Lightweight library — storage + retrieval only | Full enterprise-grade system |
| Distributed architecture | ❌ | ✅ |
| Backups / persistence guarantees | Manual | ✅ Built-in |
| ACID transactions | ❌ | ✅ |
| Role-based access control | ❌ | ✅ |
| Best for | Prototypes, small-medium projects, local dev | Production systems with compliance/scale needs |

**ChromaDB sits in between** — lightweight and easy to set up like FAISS, but with database-like persistence and metadata filtering, making it the practical default for most LangChain RAG projects.

---

## 💻 Working with ChromaDB

### Setup

```bash
pip install langchain-chroma langchain-openai
```

### Step 1 — Import and Prepare Documents

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# Organize data into Document objects
documents = [
    Document(
        page_content="Virat Kohli is a top-order batsman known for his consistency and aggressive style.",
        metadata={"team": "RCB", "role": "Batsman"}
    ),
    Document(
        page_content="Jasprit Bumrah is a fast bowler famous for his unorthodox action and yorkers.",
        metadata={"team": "MI", "role": "Bowler"}
    ),
    Document(
        page_content="MS Dhoni is a former captain known for his calm finishing and wicketkeeping.",
        metadata={"team": "CSK", "role": "Wicketkeeper"}
    ),
]
```

### Step 2 — Initialize and Embed

```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name="cricket_players",
    persist_directory="./chroma_db"   # persists to disk
)
```

### Step 3 — Similarity Search

```python
results = vector_store.similarity_search(
    query="Who is a good fast bowler?",
    k=2   # return top 2 most relevant docs
)

for doc in results:
    print(doc.page_content)
    print(doc.metadata)
```

```
→ "Jasprit Bumrah is a fast bowler famous for..."   {"team": "MI", "role": "Bowler"}
→ "MS Dhoni is a former captain known for..."        {"team": "CSK", "role": "Wicketkeeper"}
```

### Step 4 — Add, Update, Delete

```python
# Add new documents to an existing store
new_doc = Document(
    page_content="Rohit Sharma is an opening batsman known for his elegant pull shots.",
    metadata={"team": "MI", "role": "Batsman"}
)
vector_store.add_documents([new_doc])

# Update an existing document (requires document ID)
vector_store.update_document(
    document_id="doc_id_here",
    document=Document(page_content="Updated content...", metadata={"team": "MI"})
)

# Delete by ID
vector_store.delete(ids=["doc_id_here"])
```

### Step 5 — Metadata Filtering

Combine semantic search with structured filters — narrow results to a specific subset before ranking by similarity.

```python
results = vector_store.similarity_search(
    query="Tell me about a player",
    k=3,
    filter={"team": "MI"}   # only search within Mumbai Indians players
)
```

This is powerful for multi-tenant or categorized data — e.g., filtering RAG search to only the current user's documents, or only documents from a specific date range.

---

## 🗺️ Vector Stores in the RAG Pipeline

```
Document Loaders     ← Day 09B
        ↓
  Text Splitters      ← Day 10
        ↓
  Embedding Model
  (vector per chunk)
        ↓
  Vector Store         ← TODAY
  (Chroma, FAISS, Pinecone)
  - Storage
  - Similarity Search
  - Indexing
  - CRUD + Metadata Filtering
        ↓
  Retriever            ← Day 12
  (query interface on top of the vector store)
        ↓
  LLM + Context
  (grounded response)
```

---

## 💡 Key Takeaways

**On semantic vs keyword search:** The movie recommendation example is the clearest illustration — two pieces of text can mean the same thing with zero overlapping words. Keyword search misses this entirely; vector similarity catches it.

**On Vector Store vs Vector Database distinction:** This matters when choosing infra for a real project. FAISS is great for local prototyping but has no persistence guarantees out of the box. For something like Intervio's candidate-matching or resume search at scale, Pinecone or Milvus would be the safer production choice — ChromaDB is the comfortable middle ground for getting started.

**On metadata filtering:** This is easy to overlook but critical in real applications. Pure semantic search without filters can pull in irrelevant results from unrelated documents. Combining filters (by user, by date, by category) with similarity search is standard practice in production RAG.

**On indexing:** ANN search trades a small amount of accuracy for a massive speed gain. At small scale this distinction doesn't matter — but it's the reason vector stores remain fast even at millions of records.

---

## 📚 Resources

- [LangChain Vector Stores Docs](https://python.langchain.com/docs/concepts/vectorstores/)
- [ChromaDB Integration](https://python.langchain.com/docs/integrations/vectorstores/chroma/)
- [FAISS Integration](https://python.langchain.com/docs/integrations/vectorstores/faiss/)
- [Pinecone Integration](https://python.langchain.com/docs/integrations/vectorstores/pinecone/)

---
