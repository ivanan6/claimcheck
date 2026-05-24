"""CLI helper to inspect local policy retrieval."""
from __future__ import annotations

import argparse

from .retriever import build_policy_context, retrieve_policy_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect local RAG policy retrieval.")
    parser.add_argument("--payer", default="Synthetic Payer Alpha")
    parser.add_argument("--procedure", action="append", required=True)
    parser.add_argument("--diagnosis", action="append", default=[])
    parser.add_argument("--doc", action="append", default=[])
    parser.add_argument("--note", default="")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    results = retrieve_policy_chunks(
        payer=args.payer,
        procedure_codes=args.procedure,
        diagnosis_codes=args.diagnosis,
        supporting_documents=args.doc,
        doctor_note=args.note,
        top_k=args.top_k,
    )
    print(build_policy_context(results))


if __name__ == "__main__":
    main()

