import type { DiscoverData } from "@/lib/discover/types";

import { MiniSparkline } from "./mini-sparkline";

export function KpiRow({ kpis }: { kpis: DiscoverData["kpis"] }) {
  return (
    <div className="hero hero-4kpi">
      {kpis.map((k, i) => (
        <div className="card mini" key={i}>
          <div className="lab">{k.lab}</div>
          <div className={`v${k.v.length > 8 ? " is-long" : ""}`}>{k.v}</div>
          <div className="row">
            <b>{k.note}</b>
          </div>
          <MiniSparkline trend={k.trend} />
        </div>
      ))}
    </div>
  );
}
