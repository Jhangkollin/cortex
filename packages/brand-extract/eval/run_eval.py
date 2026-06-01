"""Manual eval harness. NOT a unit test — it makes real network + LLM calls.

Usage:
  CORTEX_EXTRACT_API_KEY=sk-... \
  uv run python eval/run_eval.py --tier lite --provider claude --model claude-sonnet-4-6

Default model is Sonnet 4.6 (cost mitigation, see mcp/server.py).
To re-baseline against Opus, pass `--model claude-opus-4-7`.

Writes eval/results-<tier>.json with one BrandProfile per URL plus cost.
Score each facet by hand 1-5 using eval/README.md, then check the
done-criteria thresholds in the spec.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig

HERE = Path(__file__).parent


async def _run(tier: str, kind: str, model: str, base_url: str | None) -> None:
    cfg = ProviderConfig(
        kind=kind,  # type: ignore[arg-type]
        api_key=os.environ["CORTEX_EXTRACT_API_KEY"],
        model=model,
        base_url=base_url,
    )
    provider = ClaudeProvider(cfg) if kind == "claude" else OpenAICompatProvider(cfg)
    targets = json.loads((HERE / "urls.json").read_text())
    out = []
    for t in targets:
        try:
            profile = await extract_brand_profile(t["url"], tier=tier, provider=provider)
            out.append({"target": t, "profile": profile.model_dump(mode="json")})
            print(f"OK  {t['url']}  ${profile.extraction_meta.cost_usd:.4f}")
        except Exception as exc:  # noqa: BLE001 - eval keeps going
            out.append({"target": t, "error": repr(exc)})
            print(f"ERR {t['url']}  {exc!r}")
    (HERE / f"results-{tier}.json").write_text(json.dumps(out, indent=2))
    total = sum(r["profile"]["extraction_meta"]["cost_usd"] for r in out if "profile" in r)
    print(f"\nTotal cost: ${total:.4f}  ({tier})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="lite", choices=["lite", "deep"])
    ap.add_argument("--provider", default="claude", choices=["claude", "openai_compat"])
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--base-url", default=None)
    args = ap.parse_args()
    asyncio.run(_run(args.tier, args.provider, args.model, args.base_url))


if __name__ == "__main__":
    main()
