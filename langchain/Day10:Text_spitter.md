# Day 10 — LangChain: Text Splitters (RAG Part 2)
---

## 🧠 Why Text Splitting Matters

After Document Loaders fetch raw content, the next step is chunking — breaking large documents into smaller pieces before embedding.

**Why not just embed the full document?**

- LLMs have **context window limits** — a 500-page PDF won't fit in a single prompt
- Large chunks produce **noisy embeddings** — the vector tries to represent too many ideas at once, weakening semantic search precision
- Smaller, focused chunks → **better retrieval accuracy** → better final answers

```
Full PDF (500 pages)
        ↓
  Text Splitter
        ↓
[chunk_1][chunk_2][chunk_3]...[chunk_N]
        ↓
  Embed each chunk individually
        ↓
  Vector Store
        ↓
  Query → retrieve only the 3-5 most relevant chunks
```

---

## ⚙️ Key Parameters (Universal Across Splitters)

| Parameter | What It Controls | Typical Value |
|---|---|---|
| `chunk_size` | Maximum characters/tokens per chunk | 500–1000 |
| `chunk_overlap` | Characters shared between adjacent chunks | 10–20% of chunk_size |

**Why overlap?** Without overlap, meaningful information at chunk boundaries gets cut in half — the end of chunk N and the start of chunk N+1 each become incomplete. Overlap ensures boundary context is preserved in at least one chunk.

```
chunk_size=100, chunk_overlap=20:

Chunk 1: [-------- 100 chars --------]
Chunk 2:               [-------- 100 chars --------]
                ↑ 20-char overlap
```

---

## 🔨 Four Splitting Strategies

---

### 1. Length-Based — `CharacterTextSplitter`

Simplest and fastest. Splits purely by character count.

```python
from langchain_text_splitters import CharacterTextSplitter

text = "..." # your raw document text

splitter = CharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
    separator="\n"   # try to split at newlines before hard-cutting
)

chunks = splitter.split_text(text)

# Or split Document objects directly
from langchain_community.document_loaders import PyPDFLoader
docs = PyPDFLoader("report.pdf").load()
chunks = splitter.split_documents(docs)

print(len(chunks))
print(chunks[0].page_content)
```

**Limitation:** If a sentence spans a chunk boundary and there's no separator, it gets cut mid-sentence. The splitter tries the given `separator` first, but falls back to hard character cuts if needed.

**Use when:** Simple text, logs, transcripts where hard splits are acceptable.

---

### 2. Structure-Based — `RecursiveCharacterTextSplitter`

The **recommended default** for most RAG applications. Tries a hierarchy of separators before resorting to character splits.

**Separator hierarchy (tried in order):**

```
1. "\n\n"   (paragraph breaks)
2. "\n"     (line breaks)
3. " "      (word boundaries)
4. ""       (character-level — last resort)
```

It starts with the largest structural unit (paragraphs) and works down only when needed — keeping semantically related sentences together as long as they fit within `chunk_size`.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_documents(docs)

print(f"Total chunks: {len(chunks)}")
print(chunks[0].page_content)
```

**Why this is the default:** Natural text is structured — paragraphs are semantic units. Splitting at paragraph boundaries preserves meaning far better than arbitrary character cuts.

---

### 3. Document-Structure Based — Language-Aware Splitting

Extends `RecursiveCharacterTextSplitter` with **language-specific separators** for code and structured formats.

**For Python code:**

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=500,
    chunk_overlap=50
)

python_code = """
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [item.strip() for item in self.data]

def load_data(path):
    with open(path) as f:
        return f.readlines()
"""

chunks = python_splitter.split_text(python_code)
# Splits at class/function boundaries, not mid-function
```

**Supported languages:** Python, JavaScript, TypeScript, Markdown, HTML, Rust, Go, and more.

**For Markdown:**

```python
md_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=500,
    chunk_overlap=50
)
# Splits at ## headers, not mid-paragraph
```

**Use when:** Building RAG over codebases, documentation repos, or structured markdown files. Splitting mid-function destroys the semantic unit — this preserves it.

---

### 4. Semantic Meaning-Based — `SemanticChunker`

The most intelligent approach. Uses **embedding similarity** to decide where to split — rather than structure or length.

**How it works:**

```
Sentence 1 → embed → vector_1
Sentence 2 → embed → vector_2
Sentence 3 → embed → vector_3

cosine_similarity(vector_1, vector_2) = 0.91  → same chunk (high similarity)
cosine_similarity(vector_2, vector_3) = 0.43  → new chunk (similarity drops below threshold)
```

When the semantic similarity between consecutive sentences drops significantly (measured by standard deviation from the mean), the splitter creates a new chunk boundary.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="standard_deviation"   # or "percentile", "interquartile"
)

chunks = splitter.split_documents(docs)
```

**Limitation:** Computationally expensive — every sentence gets embedded during the split phase, not just at query time. Still experimental; chunk quality depends heavily on the embedding model.

**Use when:** High-quality retrieval is critical and compute cost is not a concern. Good for dense technical documents where topic shifts aren't obvious from structure alone.

---

## 🧭 When to Use Which

| Strategy | Splitter | Use When |
|---|---|---|
| Length-based | `CharacterTextSplitter` | Simple text, logs, speed matters, quick prototype |
| Structure-based | `RecursiveCharacterTextSplitter` | **General default** — most plain text RAG applications |
| Document-structure | `RecursiveCharacterTextSplitter.from_language()` | Code, Markdown, HTML, structured formats |
| Semantic | `SemanticChunker` | High-stakes retrieval, dense technical docs, compute not a concern |

> **Default recommendation: `RecursiveCharacterTextSplitter`** with `chunk_size=500`, `chunk_overlap=50`. Start here for any new RAG project.

---

## 🗺️ Text Splitters in the RAG Pipeline

```
Document Loaders      ← Day 09B
(raw Document objects)
        ↓
  Text Splitters      ← TODAY
  (chunked Document objects)
        ↓
  Embedding Model     ← next
  (vectors per chunk)
        ↓
  Vector Store
  (indexed vector DB)
        ↓
  Retriever
  (top-K relevant chunks at query time)
        ↓
  LLM + Context
  (grounded response)
```

---

## 💡 Key Takeaways

**On chunk size:** Larger chunks → more context per chunk but noisier embeddings. Smaller chunks → crisper embeddings but risk splitting related ideas. 500 chars with 10–20% overlap is a well-tested starting point — tune from there based on retrieval quality.

**On overlap:** It's easy to skip overlap when prototyping and then wonder why retrieval misses obvious answers. Boundary information is always at risk — overlap is cheap insurance.

**On RecursiveCharacterTextSplitter as the default:** It's not the most sophisticated method, but it respects natural text structure without the compute cost of semantic splitting. For 90% of RAG projects, it's the right choice.

**On SemanticChunker's cost:** Every sentence in every document gets embedded at index time — not just at query time. For a 10,000-page corpus, this is a significant upfront compute investment. Worth it for high-stakes retrieval; overkill for most applications.

**Connection to Intervio:** When scraping GitHub READMEs and feeding them into the question-generation pipeline, chunking strategy directly affects what context the LLM sees. `RecursiveCharacterTextSplitter` with code-aware separators would preserve function-level context better than character splitting.

---

## 📚 Resources

- [LangChain Text Splitters Docs](https://python.langchain.com/docs/concepts/text_splitters/)
- [RecursiveCharacterTextSplitter](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [SemanticChunker](https://python.langchain.com/docs/how_to/semantic-chunker/)
- [Language Enum (all supported languages)](https://api.python.langchain.com/en/latest/text_splitter/langchain_text_splitters.base.Language.html)

---