/**
 * Bottom grid (spec §6.7): ranked media table + competitor head-to-head.
 *
 * Transcribed verbatim from /tmp/cortex-handoff/cortex/project/cortex/
 * dashboard.jsx lines 514–572. Structure only — the `.sp .grid`, `.media`,
 * `.comp`, `.h2h`, `.you`, `.lead`, `.track`, `.bar`, `.badge`, `.legend`
 * recipes (incl. YOU/LEADER `::before/::after` pseudo-elements) already live
 * in globals.css, so this emits classes and never tag text.
 */

import type { DiscoverData } from "@/lib/discover/types";

export function MediaCompetitorGrid({
  media,
  comp,
}: {
  media: DiscoverData["media"];
  comp: DiscoverData["comp"];
}) {
  return (
    <div className="grid">
      <div className="card media">
        <div className="ch">
          <div>
            <h3>Top media</h3>
            <div className="sub">{media.sub}</div>
          </div>
          <a href="#">View all 32 →</a>
        </div>
        <div className="row head">
          <div></div>
          <div>Media</div>
          <div>Visibility</div>
          <div style={{ textAlign: "right" }}>Share</div>
          <div style={{ textAlign: "right" }}>Clicks</div>
        </div>
        {media.rows.map((m, i) => (
          <div className="row" key={i}>
            <div className="rk">{m.rk}</div>
            <div className="nm">
              {m.nm}
              {m.badge ? <span className="badge">{m.badge}</span> : null}
            </div>
            <div className="bar">
              <i style={{ width: `${m.vis * 2.4}%` }} />
            </div>
            <div className="pct">{m.vis}%</div>
            <div className="clk">{m.clk}</div>
          </div>
        ))}
      </div>

      <div className="card comp">
        <div className="ch">
          <div>
            <h3>Competitor visibility</h3>
            <div className="sub">{comp.sub}</div>
          </div>
          <a href="#">Open benchmark →</a>
        </div>
        {comp.rows.map((c, i) => (
          <div className="h2h" key={i}>
            <div className="h2h-hd">
              <div className="nm">{c.nm}</div>
              <div className="lbl">{c.pct.toFixed(1)}%</div>
            </div>
            <div className="track">
              <i style={{ width: `${c.pct}%` }} />
            </div>
          </div>
        ))}
        <div className="legend">
          <span>
            <span className="material-icons-outlined">trending_down</span>
            Gap to leader
          </span>
          <span>
            <b>{comp.gap}</b>
          </span>
        </div>
      </div>
    </div>
  );
}
