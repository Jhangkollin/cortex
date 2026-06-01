"use client";

import type { BrandListItem } from "@/lib/cortex-api";

export type PortfolioBandProps = {
  brands: BrandListItem[];
  justOnboardedBrandId: string;
  onAddBrand: () => void;
  addBusy?: boolean;
};

// Stable monogram + color derived from the brand display_name. No need to
// persist a color on the brand — same name → same visual.
function fav(name: string): { color: string; mono: string } {
  const palette = ["#1C726B", "#225D59", "#144948", "#8A5A00", "#33597a", "#5A2D6E", "#3E6B2C", "#A04420"];
  const sum = [...name].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return { color: palette[sum % palette.length], mono: name.slice(0, 1).toUpperCase() };
}

export function PortfolioBand({ brands, justOnboardedBrandId, onAddBrand, addBusy }: PortfolioBandProps) {
  // Render order: OTHER brands first (server's updated_at DESC), then the
  // just-onboarded one with NEW pip, then the add-another tile.
  const others = brands.filter((b) => b.id !== justOnboardedBrandId);
  const justOnboarded = brands.find((b) => b.id === justOnboardedBrandId);

  return (
    <div className="my-6 rounded-md border border-ink-200 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="m-0 text-sm font-bold text-ink-700">
          Your portfolio
          <span className="ml-2 inline-flex items-center rounded-full bg-ink-100 px-2 py-0.5 text-xs font-medium text-ink-600">
            {brands.length} brands
          </span>
        </h3>
        <span className="text-xs text-ink-500">View all brands →</span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {others.map((b) => {
          const f = fav(b.display_name);
          return (
            <div key={b.id} className="flex items-center gap-3 rounded-md border border-ink-150 bg-ink-25 p-3">
              <div
                className="grid h-9 w-9 shrink-0 place-items-center rounded font-bold text-white"
                style={{ background: f.color }}
              >
                {f.mono}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-ink-900">{b.display_name}</div>
                <div className="truncate text-xs text-ink-500">
                  {b.onboarded_at ? "live · ready" : "indexing"}
                </div>
              </div>
            </div>
          );
        })}
        {justOnboarded ? (() => {
          const f = fav(justOnboarded.display_name);
          return (
            <div className="relative flex items-center gap-3 rounded-md border-2 border-brand-700 bg-brand-50 p-3">
              <span className="absolute -right-2 -top-2 rounded-full bg-brand-700 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                NEW
              </span>
              <div
                className="grid h-9 w-9 shrink-0 place-items-center rounded font-bold text-white"
                style={{ background: f.color }}
              >
                {f.mono}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-ink-900">{justOnboarded.display_name}</div>
                <div className="truncate text-xs text-ink-500">indexing · first agents starting</div>
              </div>
            </div>
          );
        })() : null}
        <button
          type="button"
          onClick={onAddBrand}
          disabled={addBusy}
          className="flex items-center justify-center gap-2 rounded-md border border-dashed border-ink-300 bg-white p-3 text-sm text-ink-600 hover:border-brand-700 hover:text-brand-700 disabled:opacity-60"
        >
          <span className="material-icons-outlined">add</span>
          {addBusy ? "Preparing…" : "Add another brand"}
        </button>
      </div>
    </div>
  );
}
