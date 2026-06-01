-- Bootstrap the first brand and owner for a fresh environment.
--
-- Usage (against RDS, after `alembic upgrade head`):
--   psql "$DATABASE_URL" \
--     -v brand_id="'<uuid7>'" \
--     -v display_name="'Acme Brands Co.'" \
--     -v industry="'retail'" \
--     -v domain="'acme.example'" \
--     -v owner_oauth_subject="'google-oauth2|...'" \
--     -v owner_email="'founder@example.com'" \
--     -v owner_display_name="'Founder Name'" \
--     -f scripts/seed_demo_brand.sql
--
-- All 7 variables are required; psql aborts on unbound references.
-- Pass empty single-quoted strings for nullable fields you want to skip
-- (industry, domain, owner_display_name) — the script's COALESCE-on-empty
-- clauses below convert '' → NULL.
--
-- Generate brand_id (UUID v7) ahead of time, NOT via the DB — the same
-- value is later embedded in JWT claims at login and used as `brand_uuid`
-- in Databricks WHERE clauses, so ops must know it before any login happens.
--
-- Idempotent: ON CONFLICT clauses make re-running safe.

BEGIN;

INSERT INTO brand (id, display_name, industry, domain)
VALUES (
    :brand_id::uuid,
    :'display_name',
    NULLIF(:'industry', ''),
    NULLIF(:'domain', '')
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO app_user (id, oauth_subject, email, display_name)
VALUES (
    gen_random_uuid(),
    :'owner_oauth_subject',
    :'owner_email',
    NULLIF(:'owner_display_name', '')
)
ON CONFLICT (oauth_subject) DO NOTHING;

INSERT INTO brand_membership (id, user_id, brand_id, role)
SELECT gen_random_uuid(), u.id, :brand_id::uuid, 'admin'
FROM app_user u
WHERE u.oauth_subject = :'owner_oauth_subject'
ON CONFLICT (user_id, brand_id) DO NOTHING;

INSERT INTO brand_profile (brand_id, name, industry_vertical)
VALUES (
    :brand_id::uuid,
    :'display_name',
    NULLIF(:'industry', '')
)
ON CONFLICT (brand_id) DO NOTHING;

COMMIT;
