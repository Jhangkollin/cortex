import cortex_brand_extract


def test_package_exposes_version() -> None:
    assert isinstance(cortex_brand_extract.__version__, str)
    assert cortex_brand_extract.__version__
