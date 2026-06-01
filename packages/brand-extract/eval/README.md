# Eval harness & rubric

Run `run_eval.py` for `lite` and `deep`, then score each profile by hand.

## Rubric (1–5 per facet, per URL)

- **category** — is the inferred category correct and specific?
- **about** — is the summary accurate and grounded (no hallucination)?
- **products** — are the listed products real and correctly named?
- **voice** — do voice samples sound like the brand's actual copy?

## Done-criteria (from the spec)

- Median ≥ 4 for category, about, products.
- Median ≥ 3 for voice.
- `deep` ≥ `lite` on the URLs marked `"js": true`.
- Cost ≤ ~$0.10 (lite) / ~$0.30 (deep) per extraction with prompt caching.
- Library imports cleanly; MCP server callable from Claude / the `mcp` CLI.

## Resolved open question — competitor / media candidate source

The spec flagged "deterministic competitor/media candidate generation needs a
source" as open. **Resolved for the spike:** the library does NOT invent
candidates. `extract_brand_profile` accepts `competitor_candidates` and
`seed_media_catalog` from the caller; the LLM only *ranks* supplied candidates
(enforced by an allowed-set filter — hallucinated entries are dropped). When a
caller supplies none, that match is skipped and a warning is recorded in
`extraction_meta.warnings`. A real candidate source (search / curated set /
Library context) is an **SP-3 / Library** concern, not SP-2.
