-- Bootstrap the real Mlytics publisher catalog so non-Databricks envs and
-- first boot work off real data without the live Databricks sync. Idempotent:
-- safe to run repeatedly; the periodic Databricks sync overwrites these later.
--
-- Usage (against RDS, after `alembic upgrade head`):
--   psql "$DATABASE_URL" -f scripts/seed_media_network.sql
--
-- No variables required — all values are hardcoded from the verified
-- Mlytics-network member catalog. Re-running is safe: ON CONFLICT updates
-- member_name, wau, and synced_at in place (no duplicate rows).

BEGIN;

INSERT INTO media_network_member (hostname, member_name, customer_uuid, wau, category_hint, synced_at) VALUES
  ('ai-news.udn.com',        '聯合新聞網',       null, 2007695, null, now()),
  ('aigc.nownews.com',       'NOWnews今日新聞',  null, 2311155, null, now()),
  ('ai.bnext.com.tw',        '數位時代',         null, 112239,  null, now()),
  ('ai.managertoday.com.tw', '經理人',           null, 75317,   null, now()),
  ('ai.edh.tw',              '早安健康',         null, 11567,   null, now()),
  ('ai.bella.tw',            'Bella.tw儂儂',     null, 718436,  null, now()),
  ('aigc.cmoney.tw',         'CMoney',           null, 117260,  null, now()),
  ('ai.u-car.com.tw',        'U-CAR',            null, 270877,  null, now()),
  ('ai-meet.bnext.com.tw',   '創業小聚',         null, 16162,   null, now()),
  ('ai-fc.bnext.com.tw',     '未來商務',         null, null,    null, now()),
  ('ai-star.ebc.net.tw',     '東森娛樂',         null, 915166,  null, now()),
  ('school.gugu.fund/ai',    '股股知識庫',       null, 45612,   null, now())
ON CONFLICT (hostname) DO UPDATE SET
  member_name = EXCLUDED.member_name,
  wau         = EXCLUDED.wau,
  synced_at   = now();

COMMIT;
