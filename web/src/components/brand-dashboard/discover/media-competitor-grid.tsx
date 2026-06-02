import type { DiscoverData } from "@/lib/discover/types";

export function MediaCompetitorGrid({
  media,
  intent,
}: {
  media: DiscoverData["media"];
  intent: DiscoverData["intent"];
}) {
  const maxViews = Math.max(...intent.rows.map((r) => r.views));

  return (
    <div className="grid">
      <div className="card media">
        <div className="ch">
          <div>
            <h3>{media.title}</h3>
            <div className="sub">{media.sub}</div>
          </div>
        </div>
        {media.rows.map((m, i) => (
          <div className="row media-simple" key={i}>
            <div className="nm">
              {m.nm}
              {m.badge ? <span className="badge">{m.badge}</span> : null}
            </div>
            <div className="bar">
              <i style={{ width: `${m.vis}%` }} />
            </div>
            <div className="pct">{m.vis}%</div>
          </div>
        ))}
      </div>

      <div className="card intent">
        <div className="ch">
          <div>
            <h3>意圖類別 × 你的產品線</h3>
            <div className="sub">依月相關曝光排序</div>
          </div>
        </div>
        {intent.rows.map((r, i) => (
          <div className="int-row" key={i}>
            <div className="int-hd">
              <div className="int-nm">
                {r.top && <span className="int-top">TOP</span>}
                {r.nm} ({r.count}題)
              </div>
              <div className="int-views">{r.views.toLocaleString()} views</div>
            </div>
            <div className="int-track">
              <i
                className={r.top ? "is-top" : ""}
                style={{ width: `${(r.views / maxViews) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
