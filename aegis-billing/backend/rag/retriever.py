"""
Small local RAG retriever for demo policy documents.

This deliberately avoids external vector database dependencies. It chunks policy
text files and uses weighted lexical scoring to retrieve the most relevant
policy sections for a claim. The interface is shaped so it can later be replaced
with Chroma, Qdrant, pgvector, Vertex AI Search, or another vector store.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_DIR = _BACKEND_DIR.parent
_POLICY_DIR = _PROJECT_DIR / "data" / "policies"

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "if",
    "in", "into", "is", "it", "must", "of", "on", "or", "that", "the",
    "this", "to", "with", "within",
}


@dataclass(frozen=True)
class PolicyChunk:
    chunk_id: str
    source: str
    payer: str
    text: str
    tokens: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    chunk: PolicyChunk
    score: float
    matched_terms: tuple[str, ...]


def _tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if token.lower() not in _STOPWORDS and len(token) > 1
    ]


def _infer_payer(text: str, source: str) -> str:
    first_lines = "\n".join(text.splitlines()[:8]).lower()
    if "synthetic payer alpha" in first_lines or "synthetic_payer_alpha" in source:
        return "Synthetic Payer Alpha"
    return "Unknown Payer"


def _split_sections(text: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        starts_section = (
            stripped.startswith("ARTICLE ")
            or stripped.startswith("Covered service group:")
            or stripped.startswith("Medical necessity requirements:")
            or stripped.startswith("Required documents")
            or stripped.startswith("Additional required documents:")
            or stripped.startswith("Denial rules:")
            or stripped.startswith("Submission checklist")
        )
        if starts_section and current:
            sections.append("\n".join(current).strip())
            current = []
        current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if section]


@lru_cache(maxsize=1)
def load_policy_chunks() -> tuple[PolicyChunk, ...]:
    chunks: list[PolicyChunk] = []
    for path in sorted(_POLICY_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        payer = _infer_payer(text, path.name)
        for index, section in enumerate(_split_sections(text), start=1):
            chunk_id = f"{path.stem}:{index}"
            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    source=str(path.relative_to(_PROJECT_DIR)),
                    payer=payer,
                    text=section,
                    tokens=tuple(_tokenize(section)),
                )
            )
    return tuple(chunks)


def _expand_query_terms(terms: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for term in terms:
        normalized = term.lower().strip()
        if not normalized:
            continue
        expanded.append(normalized)
        expanded.extend(_tokenize(normalized.replace("-", " ")))

    aliases = {
        "proc-pt-therex": ["physical", "therapy", "therapeutic", "exercise", "rehabilitation"],
        "97110": ["physical", "therapy", "therapeutic", "exercise", "rehabilitation"],
        "proc-img-mri-brain": ["advanced", "brain", "imaging", "prior", "authorization"],
        "70551": ["advanced", "brain", "imaging", "prior", "authorization"],
        "proc-lab-cbc": ["laboratory", "blood", "count", "clinician", "order"],
        "85025": ["laboratory", "blood", "count", "clinician", "order"],
    }
    for term in list(expanded):
        expanded.extend(aliases.get(term, []))

    seen: set[str] = set()
    unique: list[str] = []
    for term in expanded:
        if term and term not in seen and term not in _STOPWORDS:
            seen.add(term)
            unique.append(term)
    return unique


def _score_chunk(chunk: PolicyChunk, query_terms: list[str], payer: str | None) -> tuple[float, tuple[str, ...]]:
    token_counts: dict[str, int] = {}
    for token in chunk.tokens:
        token_counts[token] = token_counts.get(token, 0) + 1

    matched: list[str] = []
    score = 0.0
    text_lower = chunk.text.lower()

    for term in query_terms:
        if term in token_counts:
            matched.append(term)
            score += 2.0 + math.log1p(token_counts[term])
        elif len(term) > 4 and term in text_lower:
            matched.append(term)
            score += 1.0

    if payer and payer.lower() == chunk.payer.lower():
        score *= 1.35
    elif payer and chunk.payer != "Unknown Payer":
        score *= 0.25

    return score, tuple(sorted(set(matched)))


def retrieve_policy_chunks(
    *,
    payer: str | None,
    procedure_codes: list[str],
    diagnosis_codes: list[str] | None = None,
    supporting_documents: list[str] | None = None,
    doctor_note: str = "",
    top_k: int = 5,
) -> list[RetrievalResult]:
    query_terms = _expand_query_terms(
        [
            *(procedure_codes or []),
            *(diagnosis_codes or []),
            *(supporting_documents or []),
            doctor_note,
            "required documents",
            "denial rules",
            "submission checklist",
        ]
    )
    scored: list[RetrievalResult] = []
    for chunk in load_policy_chunks():
        score, matched_terms = _score_chunk(chunk, query_terms, payer)
        if score > 0:
            scored.append(RetrievalResult(chunk=chunk, score=score, matched_terms=matched_terms))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def build_policy_context(results: list[RetrievalResult]) -> str:
    if not results:
        return ""

    blocks = []
    for result in results:
        blocks.append(
            "\n".join(
                [
                    f"Source: {result.chunk.source}",
                    f"Chunk ID: {result.chunk.chunk_id}",
                    f"Payer: {result.chunk.payer}",
                    f"Retrieval score: {result.score:.2f}",
                    "Text:",
                    result.chunk.text,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)

