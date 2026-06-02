import { Fragment } from "react";

import { Rich } from "@/lib/discover/rich-text";
import type { DiscoverData } from "@/lib/discover/types";

import { FunnelArrow } from "./funnel-arrow";

export function GeoFunnel({ funnel }: { funnel: DiscoverData["funnel"] }) {
  return (
    <div className="funnel">
      <div className="fh">
        <h3>
          {funnel.title}
          <small>{funnel.sub}</small>
        </h3>
        <span className="fnl-disc">
          <span className="material-icons-outlined">bolt</span>
          {funnel.disclaimer}
        </span>
      </div>
      <div className="flow">
        {funnel.blocks.map((b, i) => (
          <Fragment key={`nm-${i}`}>
            <div className={`fnl-nm fnl-nm-${i}${b.here ? " is-here" : ""}`}>
              <Rich value={b.nm} />
            </div>
            {i < funnel.arrows.length ? <div /> : null}
          </Fragment>
        ))}
        {funnel.blocks.map((b, i) => (
          <Fragment key={`v-${i}`}>
            <div className={`fnl-v${b.here ? " is-here" : ""}`}>{b.v}</div>
            {i < funnel.arrows.length ? (
              <FunnelArrow
                rate={funnel.arrows[i].rate}
                label={funnel.arrows[i].label}
                kind={funnel.arrows[i].kind}
              />
            ) : null}
          </Fragment>
        ))}
      </div>
    </div>
  );
}
