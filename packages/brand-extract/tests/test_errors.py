import pytest

from cortex_brand_extract.errors import (
    ExtractError,
    UpstreamError,
    UpstreamTimeoutError,
)


def test_hierarchy() -> None:
    assert issubclass(UpstreamError, ExtractError)
    assert issubclass(UpstreamTimeoutError, UpstreamError)


def test_carries_message_and_chains() -> None:
    cause = ValueError("boom")
    err = UpstreamError("llm failed", stage="synthesize")
    err.__cause__ = cause
    assert err.stage == "synthesize"
    assert "llm failed" in str(err)


def test_stage_defaults_to_none() -> None:
    assert ExtractError("bare").stage is None


def test_chaining_via_raise_from() -> None:
    cause = ValueError("boom")
    with pytest.raises(UpstreamError) as exc_info:
        try:
            raise cause
        except ValueError as e:
            raise UpstreamError("llm failed", stage="synthesize") from e
    assert exc_info.value.__cause__ is cause
    assert exc_info.value.__suppress_context__ is True
    assert exc_info.value.stage == "synthesize"
