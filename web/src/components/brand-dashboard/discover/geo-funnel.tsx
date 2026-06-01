import { Fragment } from "react";

import { Rich } from "@/lib/discover/rich-text";
import type { DiscoverData } from "@/lib/discover/types";

import { FunnelArrow } from "./funnel-arrow";

/**
 * GEO funnel (§09 / spec §6.6).
 *
 * Markup mirrors `dashboard.jsx` 482–511 verbatim: `.funnel` → `.fh` header,
 * `.flow` grid interleaving 5 `.blk` blocks with 4 `<FunnelArrow>` connectors
 * (`React.Fragment` per block+arrow pair), then the v2 `.fnl-takeaway` row.
 *
 * Data flows in via props — the section does not import mock data so the
 * parent page can swap fixtures (BASE_DATA / QUERY_PRESETS) without touching
 * the visual layer.
 */
export function GeoFunnel({ funnel }: { funnel: DiscoverData["funnel"] }) {
  return (
    <div className="funnel">
      <div className="fh">
        <h3>
          GEO funnel
          <small>Article → click — last 30 days</small>
        </h3>
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
            <div className="fnl-v">{b.v}</div>
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

      {/* v2: plain-English takeaway turns analysis into action */}
      <div className="fnl-takeaway">
        <span className="material-icons-outlined">lightbulb</span>
        <span>
          <Rich value={funnel.takeaway} />
        </span>
        <a href="#">{funnel.takeawayCta}</a>
      </div>
    </div>
  );
}
