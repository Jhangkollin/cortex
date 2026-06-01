"""Token-bounded corpus. The spike uses a char budget (≈ chars/4 tokens) to
stay pip-light — no tiktoken. The eval harness records real token usage.
"""

from __future__ import annotations

from pydantic import BaseModel


class SiteCorpus(BaseModel):
    text: str
    page_count: int
    truncated: bool


def build_corpus(pages: list[tuple[str, str]], *, max_chars: int = 60_000) -> SiteCorpus:
    chunks: list[str] = []
    total = 0
    truncated = False
    for url, body in pages:
        header = f"\n\n=== PAGE: {url} ===\n"
        remaining = max_chars - total
        if remaining <= 0:
            truncated = True
            break
        piece = (header + body)[:remaining]
        if len(header + body) > remaining:
            truncated = True
        chunks.append(piece)
        total += len(piece)
    return SiteCorpus(
        text="".join(chunks).strip(),
        page_count=len(pages),
        truncated=truncated,
    )
