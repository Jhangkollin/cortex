import type { DiscoverData } from "@/lib/discover/types";

export function GeoOpportunity({ geo }: { geo: DiscoverData["geo"] }) {
  return (
    <div className="card geo-opp">
      <div className="geo-hd">
        <div>
          <h3>
            Google AIO / GEO 機會{" "}
            <small>(Search API 接通中)</small>
          </h3>
          <div className="geo-sub">{geo.sub}</div>
        </div>
        <span className="geo-status">{geo.status}</span>
      </div>
      <div className="geo-tags">
        {geo.tags.map((tag, i) => (
          <span className="geo-tag" key={i}>{tag}</span>
        ))}
      </div>
      <div className="geo-note">
        <span className="material-icons-outlined">arrow_forward</span>
        {geo.note}
      </div>
    </div>
  );
}
