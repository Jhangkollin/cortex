import type { ReactElement } from "react";
import { Rich } from "@/lib/discover/rich-text";
import type { DiscoverData } from "@/lib/discover/types";

export function PriorityAlerts({
  alerts,
}: {
  alerts: DiscoverData["alerts"];
}): ReactElement {
  return (
    <div className="alerts">
      {alerts.map((a, i) => (
        <article key={i} className={`alert is-${a.kind}`}>
          <div className="alert-bot-row">
            <div className="alert-avatar-wrap">
              <div className="alert-avatar">
                <span className="material-icons-outlined">auto_awesome</span>
              </div>
              <span className="alert-bot-name">Cortex</span>
            </div>
            <div className="alert-content">
              <span className="alert-cat">{a.cat}</span>
              <div className="alert-body">
                <Rich value={a.headline} />
              </div>
              <div className="alert-sub">{a.sub}</div>
            </div>
          </div>
          <button type="button" className="alert-cta">
            {a.cta}
          </button>
        </article>
      ))}
    </div>
  );
}
