import type { ReactElement } from "react";

export function Topbar(): ReactElement {
  return (
    <div className="top">
      <div className="left">
        <div className="page-title">
          <div className="title-row">
            <h1>Discover</h1>
            <span className="cortex-suggested">
              <span className="material-icons-outlined">auto_awesome</span>
              CORTEX SUGGESTED THIS VIEW
            </span>
          </div>
          <div className="subtitle">
            達摩本草 在 Mlytics 媒體網絡中的「相關需求池」與獲客機會 — 你尚未累積品牌數據，但 Mlytics 已有
            <span className="muted"> · updated 12 min ago</span>
          </div>
        </div>
      </div>
      <div className="right">
        <div className="chip">
          <span className="material-icons-outlined">filter_list</span>
          <span className="chip-label">All markets</span>
        </div>
        <div className="chip is-on">
          <span className="material-icons-outlined">calendar_today</span>
          <span className="chip-label">Last 30 days</span>
        </div>
        <span className="right-sep" aria-hidden />
        <button type="button" className="btn">
          <span className="material-icons-outlined">file_download</span>Export
        </button>
      </div>
    </div>
  );
}
