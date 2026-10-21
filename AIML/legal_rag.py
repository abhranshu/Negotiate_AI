"""
Module 6 (optional) — Legal RAG for the Negotiation Moderator
==============================================================
Retrieves relevant Indian legal provisions (MSMED Act 2006, Indian Contract
Act 1872, MSEFC conciliation orders) so the LLM mediator can cite real law
instead of hallucinating it.

Pipeline:
  1. Build:  chunk plain-text legal files in data/legal/ → embed → store in ChromaDB
  2. Query:  embed the case context / last message → retrieve top-k relevant chunks
  3. Format: return a prompt-ready "RELEVANT LAW" block for NegotiationModerator

Graceful fallback:
  - If `chromadb` / `sentence-transformers` are not installed, falls back to a
    lightweight TF-IDF keyword retriever (pure stdlib) so the module still works.
    The vector path is strictly better — install the extras for production:
        pip install chromadb sentence-transformers

Usage:
  # Build the index from data/legal/*.txt
  python -m AIML.legal_rag --build

  # Query the index
  python -m AIML.legal_rag --query "compound interest under section 16 overdue payment"

  # Wire into the moderator
  from AIML.legal_rag import LegalRetriever
  rag = LegalRetriever()
  law_block = rag.format_context(rag.retrieve_law_for_case(dispute_type="non_payment",
                                                           overdue_days=120))
"""

import math
import re
from collections import Counter
from pathlib import Path
from typing import Optional

# ─── Paths (mirrors AIML/outcome_prediction.py convention) ────────────────────
BASE_DIR      = Path(__file__).parent.parent
CORPUS_DIR    = BASE_DIR / "data" / "legal"
PERSIST_DIR   = BASE_DIR / "data" / "chroma"
COLLECTION    = "msmed_law"
KEYWORD_CACHE = PERSIST_DIR / "keyword_corpus.json"   # persistence for the keyword backend
EMBED_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"   # 22 Indian languages, ~120MB

CHUNK_SIZE    = 600      # characters per chunk
CHUNK_OVERLAP = 100      # overlap between consecutive chunks


# ─── Text cleaning & chunking ─────────────────────────────────────────────────

# Matches section headers at the start of a paragraph, including markdown
# bold (`**15. ...**`) and plain (`15. ...`, `Section 16. ...`) forms.
# No trailing \b: "15. Liability" has a non-word char after the dot.
_SECTION_RE = re.compile(
    r"(?im)^\s*(?:\*\*)?(section\s+\d+[a-z]?|sec\.?\s*\d+[a-z]?|\d+[a-z]?\.)"
)

# Markdown chapter/heading lines ("## CHAPTER V", "### DELAYED PAYMENTS ...").
# Left unmerged these become the highest-scoring chunks in TF-IDF, because a
# heading has a very high term-frequency/length ratio — which is how a bare
# "DELAYED PAYMENTS TO MICRO AND SMALL ENTERPRISES" line ended up at rank 1
# with no provision text behind it.
_MD_HEADING_RE = re.compile(r"^\s*#{1,6}\s+\S")

# A heading is short enough to be buffered and attached to its body.
_HEADING_MAX_LEN = 160

# Leading section title only (used to check whether a chunk has real body text).
_LEADING_SECTION_RE = re.compile(
    r"^\s*(?:\*\*)?(?:section\s+\d+[a-z]?|sec\.?\s*\d+[a-z]?|\d+[a-z]?\.)\s*"
    r"[A-Za-z][^.]{0,100}?\.?(?:\*\*)?\s*",
    re.IGNORECASE,
)


def clean_text(raw: str) -> str:
    """Normalise whitespace/newlines but keep paragraph breaks."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def _split_paragraphs(text: str):
    """Yield paragraphs, attaching each short section heading to the body that
    follows it.

    Without this, a heading such as ``**15. Liability of buyer to make
    payment.**`` (41 chars) clears the 40-char noise filter on its own and gets
    indexed as a standalone chunk. Retrieval then hands the mediator a bare
    section title with no provision text behind it — exactly the "Section 15."
    fragment observed in the prompt — which invites the model to fill the gap
    with invented or unrelated text.
    """
    pending_heading = ""
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para:
            continue
        if len(para) <= _HEADING_MAX_LEN and (
            _SECTION_RE.match(para) or _MD_HEADING_RE.match(para)
        ):
            # Hold it; the body comes next. Consecutive headings are merged so
            # "## CHAPTER V" + "### DELAYED PAYMENTS..." reach the body together.
            pending_heading = f"{pending_heading} {para}".strip()
            continue
        if len(para) >= 40:                # skip headings / noise
            if pending_heading:
                para = f"{pending_heading} {para}"
                pending_heading = ""
            yield para
    # Trailing heading with no body — keep it so the section still exists,
    # but only if it carries enough text to be worth retrieving.
    if pending_heading and len(pending_heading) >= 40:
        yield pending_heading


def _window_chunks(text: str, size: int, overlap: int):
    """Split long paragraphs into overlapping character windows."""
    if len(text) <= size:
        yield text.strip()
        return
    step = size - overlap
    for i in range(0, len(text) - overlap, step):
        yield text[i:i + size].strip()


def chunk_document(text: str, source: str) -> list[dict]:
    """
    Chunk one document into overlapping windows, tracking the section each
    chunk belongs to (e.g. 'Section 16') for citation metadata.
    Returns: [{text, source, section}, ...]
    """
    text = clean_text(text)
    chunks: list[dict] = []
    current_section = "General"

    for para in _split_paragraphs(text):
        m = _SECTION_RE.search(para)
        if m:
            raw = re.sub(r"\s+", " ", m.group(1).strip().rstrip("."))
            # Normalise bare numbers to "Section N" so citations read nicely
            current_section = raw if raw.lower().startswith("sec") else f"Section {raw}"
        for window in _window_chunks(para, CHUNK_SIZE, CHUNK_OVERLAP):
            # Safety net: never index a chunk that is only a section title.
            # A heading repeated without its body is worse than nothing,
            # because the model will cite the section and then invent the text.
            body = _LEADING_SECTION_RE.sub("", window).strip()
            if len(body) < 40:
                continue
            chunks.append({
                "text":    window,
                "source":  source,
                "section": current_section,
            })
    return chunks


# ─── Vector retriever (primary) ───────────────────────────────────────────────

class VectorRetriever:
    """ChromaDB with its BUILT-IN ONNX embeddings (all-MiniLM-L6-v2).

    Deliberately NOT sentence-transformers/torch: the ONNX model is ~80MB and
    runs on onnxruntime alone, so the deploy image stays light (~300MB vs
    ~2GB) and queries stay fast (~20ms on CPU). The ONNX model is downloaded
    once to ~/.cache/chroma/onnx_models/ (baked into the Docker image by the
    `python -m AIML.legal_rag --build` build step).
    """

    def __init__(self, persist_dir: Path = PERSIST_DIR, collection: str = COLLECTION):
        import chromadb

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        # The default embedding function is registered automatically on
        # collection creation and used for both upsert(query texts) and
        # query_texts — no explicit embedding calls needed anywhere.
        self._col = self._client.get_or_create_collection(
            collection, metadata={"hnsw:space": "cosine"}
        )

    def build(self, documents: list[dict]):
        ids         = [f"{d['source']}::{i}" for i, d in enumerate(documents)]
        texts       = [d["text"] for d in documents]
        metadatas   = [{"source": d["source"], "section": d["section"]} for d in documents]
        # ChromaDB embeds via the collection's default ONNX function.
        # Caps upsert batch size (~5461); chunk to stay under it.
        batch = 1000
        for i in range(0, len(documents), batch):
            self._col.upsert(
                ids=ids[i:i + batch],
                documents=texts[i:i + batch],
                metadatas=metadatas[i:i + batch],
            )
        print(f"[RAG] Vector store: {len(documents)} chunks upserted to '{self._col.name}'.")

    def query(self, query: str, k: int = 3) -> list[dict]:
        hits = self._col.query(query_texts=[query], n_results=k)
        out  = []
        for i, doc in enumerate(hits["documents"][0]):
            out.append({
                "text":    doc,
                "score":   round(float(hits["distances"][0][i]), 4) if hits.get("distances") else None,
                **hits["metadatas"][0][i],
            })
        return out


# ─── Keyword retriever (fallback, pure stdlib) ────────────────────────────────

class KeywordRetriever:
    """Lightweight TF-IDF retriever. No external deps — used when the vector
    packages aren't installed, or as a sanity cross-check."""

    def __init__(self):
        self._docs: list[dict] = []

    def build(self, documents: list[dict]):
        self._docs = documents

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [t for t in re.findall(r"[a-z0-9]{3,}", text.lower())
                if t not in _STOPWORDS]

    def query(self, query: str, k: int = 3) -> list[dict]:
        if not self._docs:
            return []
        q_tokens = self._tokens(query)
        if not q_tokens:
            return []

        # Document frequency
        df = Counter()
        for d in self._docs:
            df.update(set(self._tokens(d["text"])))

        n_docs = len(self._docs)
        scored = []
        for d in self._docs:
            tokens = self._tokens(d["text"])
            tf     = Counter(tokens)
            score  = 0.0
            for t in set(q_tokens):
                if t in tf:
                    idf = math.log((n_docs + 1) / (df.get(t, 0) + 1)) + 1.0
                    score += (tf[t] / len(tokens)) * idf
            if score > 0:
                scored.append((score * _source_boost(d) * _length_prior(d), d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**d, "score": round(s, 4), "retriever": "keyword"}
            for s, d in scored[:k]
        ]


_STOPWORDS = set("""a an and are as at be but by for from has have if in into is it
its no not of on or such than that the their there these they this to was were
will with you your shall may""".split())


# The corpus pairs two very differently-sized statutes: MSMED_Act_2006.md
# (37 KB, the domain law this project is about) and A2013-18.md (1.3 MB, the
# Companies Act). Pure TF-IDF lets the large generic file win on incidental
# word overlap — it was returning Sections 378Y and 127 (dividends) for a
# delayed-payment dispute. Weight the domain statute up instead.
_SOURCE_BOOST = {
    "MSMED_Act_2006.md": 1.6,
}


def _source_boost(doc: dict) -> float:
    return _SOURCE_BOOST.get(doc.get("source", ""), 1.0)


def _length_prior(doc: dict) -> float:
    """Mild penalty for heading-sized fragments.

    A 60-char chunk matching two query terms outscores a 500-char provision
    that matches four, purely because score is normalised by token count.
    """
    text = doc.get("text", "")
    if len(text) < 120:
        return 0.5
    if len(text) < 250:
        return 0.8
    return 1.0


# ─── Facade ───────────────────────────────────────────────────────────────────

class LegalRetriever:
    """
    Main entry point. Uses the vector retriever when available, otherwise the
    keyword fallback. Both expose the same build()/query() interface.

    Set keyword_only=True to skip the sentence-transformers / chromadb imports
    entirely — saves ~0.5-2s on first query and avoids downloading the
    embedding model. The TF-IDF keyword backend is fast and sufficient for
    retrieving MSMED Act provisions by keyword overlap.
    """

    def __init__(self, corpus_dir: Path = CORPUS_DIR, persist_dir: Path = PERSIST_DIR,
                 keyword_only: bool = False):
        self.corpus_dir = corpus_dir
        self.persist_dir = persist_dir
        self._backend: Optional[object] = None

        if keyword_only:
            # Skip vector retriever entirely — no torch/sentence-transformers import
            self._backend = KeywordRetriever()
            self._mode = "keyword"
            if KEYWORD_CACHE.exists():
                import json
                try:
                    self._backend.build(json.loads(KEYWORD_CACHE.read_text(encoding="utf-8")))
                except Exception:
                    pass
            print("[RAG] keyword-only mode (skipped sentence-transformers/chromadb)")
        else:
            try:
                self._backend = VectorRetriever(persist_dir=persist_dir)
                self._mode = "vector"
            except ImportError:
                self._backend = KeywordRetriever()
                self._mode = "keyword"
                if KEYWORD_CACHE.exists():
                    import json
                    try:
                        self._backend.build(json.loads(KEYWORD_CACHE.read_text(encoding="utf-8")))
                    except Exception:
                        pass
                print("[RAG] chromadb not installed - using keyword "
                      "fallback. Install with: pip install chromadb")

    @property
    def mode(self) -> str:
        return self._mode

    def _load_corpus(self) -> list[dict]:
        """Read all .txt/.md files in the corpus dir and chunk them."""
        if not self.corpus_dir.exists():
            print(f"[RAG] Corpus dir not found: {self.corpus_dir}. "
                  f"Create it and add MSMED Act / Contract Act text files, then run --build.")
            return []
        docs = []
        for path in sorted(self.corpus_dir.glob("*.txt")) + sorted(self.corpus_dir.glob("*.md")):
            raw = path.read_text(encoding="utf-8", errors="ignore")
            docs.extend(chunk_document(raw, source=path.name))
        return docs

    def build(self) -> int:
        """(Re)build the index from all files in the corpus dir."""
        docs = self._load_corpus()
        if not docs:
            return 0
        self._backend.build(docs)
        # Persist the corpus so the keyword fallback survives across processes
        # (the vector backend persists itself inside ChromaDB).
        import json
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        KEYWORD_CACHE.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
        return len(docs)

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        if self._backend is None:
            self._backend = KeywordRetriever()   # nothing built yet → empty result
        return self._backend.query(query, k=k)

    # ── Case-aware query builder ─────────────────────────────────────────────

    def retrieve_law_for_case(self,
                              dispute_type: Optional[str] = None,
                              overdue_days: Optional[int] = None,
                              industry: Optional[str] = None,
                              description: Optional[str] = None,
                              k: int = 3) -> list[dict]:
        """Build a domain query from case fields and retrieve relevant law."""
        parts = ["MSME payment dispute"]
        if dispute_type:
            parts.append(dispute_type.replace("_", " "))
        if overdue_days:
            parts.append(f"overdue {overdue_days} days")
        if industry:
            parts.append(industry.replace("_", " "))
        if description:
            parts.append(description[:300])
        query = " ".join(parts)
        return self.retrieve(query, k=k)

    # ── Prompt formatting ────────────────────────────────────────────────────

    def format_context(self, results: list[dict]) -> str:
        """Turn retrieval results into a prompt-ready legal block for the moderator."""
        if not results:
            return "No relevant legal provisions retrieved."
        lines = ["=== RELEVANT LAW (retrieved from legal corpus) ==="]
        for r in results:
            src    = r.get("source", "unknown")
            sect   = r.get("section", "")
            lines.append(f"[{src}" + (f" | {sect}" if sect else "") + "]")
            lines.append(r["text"])
            lines.append("")
        lines.append(
            "Instruction: You may cite ONLY the provisions above. If none of them "
            "apply to this dispute, say so plainly instead of inventing law."
        )
        return "\n".join(lines).strip()


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NegotiateAI legal RAG index")
    parser.add_argument("--build", action="store_true",
                        help="(Re)build the index from data/legal/*.txt")
    parser.add_argument("--query", type=str, help="Retrieve top-k chunks for a query")
    parser.add_argument("--k", type=int, default=3, help="Number of results (default 3)")
    args = parser.parse_args()

    rag = LegalRetriever()

    if args.build:
        n = rag.build()
        print(f"[RAG] Index built ({rag.mode} backend): {n} chunks from {rag.corpus_dir}")

    if args.query:
        results = rag.retrieve(args.query, k=args.k)
        print(f"[RAG] Top {len(results)} results for: {args.query!r}\n")
        print(rag.format_context(results))
