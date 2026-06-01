import type { DiscoverData } from "@/lib/discover/types";

import { HeroSparkline } from "./hero-sparkline";
import { MiniSparkline } from "./mini-sparkline";

// Hero metric + 3 minis — mirrors
// /tmp/cortex-handoff/cortex/project/cortex/dashboard.jsx lines 456–479.
export function KpiRow({
  hero,
  minis,
}: {
  hero: DiscoverData["hero"];
  minis: DiscoverData["minis"];
}) {
  return (
    <div className="hero">
      <div className="card h-main">
        <div className="lab">
          Brand visibility rate
          <span className="live">
            <span className="d" />
            {hero.live}
          </span>
        </div>
        <div className="v">
          {hero.v}
          <sup>{hero.suffix}</sup>
        </div>
        <div className="sub">
          <span className="up">{hero.delta}</span>
          <span>{hero.note}</span>
        </div>
        <HeroSparkline />
      </div>
      {minis.map((m, i) => (
        <div className="card mini" key={i}>
          <div className="lab">{m.lab}</div>
          <div className="v">{m.v}</div>
          <div className="row">
            <b>{m.note}</b>
          </div>
          <MiniSparkline trend={m.trend} />
        </div>
      ))}
    </div>
  );
}
