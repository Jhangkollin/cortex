# api/src/cortex_api/service/questions/config.py
"""Questions domain config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Weekly-questions service config."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_QUESTIONS_", extra="forbid")

    question_count: int = 6
    stale_job_seconds: int = 180
    dbx_catalog: str = "aigc_prod"
    # Minimum LLM relevance score (0-100) for a ranked pool question to be kept.
    # Below this the matcher drops the pick and lets D8 synth fill the slot, so a
    # brand whose category isn't in the pool gets brand-grounded questions rather
    # than globally-popular off-brand ones (the Hamilton-watch bug). Env-tunable
    # as CORTEX_QUESTIONS_MIN_RELEVANCE_SCORE so it can be recalibrated per env
    # without a code change.
    min_relevance_score: int = 40
