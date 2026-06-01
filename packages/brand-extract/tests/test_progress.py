from cortex_brand_extract.progress import ListSink, ProgressEvent


async def test_list_sink_collects_events() -> None:
    sink = ListSink()
    await sink.emit(ProgressEvent(stage="fetch", status="running", detail="acme.com"))
    await sink.emit(ProgressEvent(stage="fetch", status="ok", detail="200"))
    assert [e.status for e in sink.events] == ["running", "ok"]
    assert sink.events[0].stage == "fetch"


async def test_none_safe_emit_helper() -> None:
    from cortex_brand_extract.progress import emit

    await emit(None, ProgressEvent(stage="parse", status="ok"))  # no raise
