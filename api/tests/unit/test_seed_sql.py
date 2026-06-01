from pathlib import Path

_SEED = (Path(__file__).resolve().parents[2] / "scripts" / "seed_demo_brand.sql").read_text()


def test_seed_inserts_brand_profile_idempotently() -> None:
    assert "INSERT INTO brand_profile" in _SEED
    assert "ON CONFLICT (brand_id) DO NOTHING" in _SEED


def test_seed_brand_profile_runs_before_commit() -> None:
    assert _SEED.rstrip().endswith("COMMIT;")
    assert _SEED.index("INSERT INTO brand_profile") < _SEED.rindex("COMMIT;")
