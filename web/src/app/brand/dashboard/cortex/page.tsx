/**
 * Cortex tab — placeholder for slice L2 (intelligence / classifier console).
 *
 * Sits inside the brand layout so the sidebar + topbar render normally.
 * Topbar's "Cortex" tab routes here; renders an empty state explaining
 * what's coming.
 */

export default function CortexTabPage() {
  return (
    <div className="bg-ink-25 px-8 py-12">
      <div className="text-[11px] font-bold uppercase tracking-[0.1em] text-brand-700">
        CORTEX · INTELLIGENCE LAYER
      </div>
      <h1
        className="mt-3.5 mb-3 text-ink-900"
        style={{
          font: "700 36px/1.15 var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        Classifier introspection lands{" "}
        <span style={{ color: "var(--mly-teal-700)" }}>in slice L2.</span>
      </h1>
      <p className="max-w-[640px] text-base text-ink-500">
        This tab will host routing policy editing, classifier confidence
        thresholds, and the live decision visualization. For now, head back to
        Discover.
      </p>
    </div>
  );
}
