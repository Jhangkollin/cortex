/**
 * Nexus tab — placeholder for the Decisive Engine surface.
 *
 * Brand mode (counterfactual savings hero, quality delta, CDN donut) lands
 * in a follow-up slice. Advanced mode (zone scores, geo heatmap, live decision
 * stream) is even later. For now this is just a navigable stub so the
 * topbar's Nexus tab doesn't 404.
 */

export default function NexusTabPage() {
  return (
    <div className="bg-ink-25 px-8 py-12">
      <div className="text-[11px] font-bold uppercase tracking-[0.1em] text-brand-700">
        NEXUS · DECISIVE ENGINE
      </div>
      <h1
        className="mt-3.5 mb-3 text-ink-900"
        style={{
          font: "700 36px/1.15 var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        Multi-CDN routing,{" "}
        <span style={{ color: "var(--mly-teal-700)" }}>
          coming next slice.
        </span>
      </h1>
      <p className="max-w-[640px] text-base text-ink-500">
        Brand mode shows counterfactual savings vs single-CDN baselines.
        Advanced mode opens zone scores and the live decision stream.
        Both ship after the Discover skeleton lands.
      </p>
    </div>
  );
}
