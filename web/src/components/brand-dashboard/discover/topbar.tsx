import type { ReactElement } from "react";

export function Topbar(): ReactElement {
  return (
    <div className="top">
      <div className="left">
        <div className="page-title">
          <h1>Discover</h1>
          <div className="subtitle">
            What AI is saying about your brand.{" "}
            <span className="muted">Updated 12 min ago · cortex-geo</span>
          </div>
        </div>
      </div>
      <div className="right">
        <div className="chip">
          <span className="material-icons-outlined">filter_list</span><span className="chip-label">All markets</span>
        </div>
        <div className="chip is-on">
          <span className="material-icons-outlined">calendar_today</span><span className="chip-label">Last 30 days</span>
        </div>
        <span className="right-sep" aria-hidden />
        <button type="button" className="btn">
          <span className="material-icons-outlined">file_download</span>Export
        </button>
      </div>
    </div>
  );
}
