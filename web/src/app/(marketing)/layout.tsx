import { MarketingNav } from "@/components/marketing/marketing-nav";

/**
 * Layout for the public marketing surfaces (/pricing today; /partnership and
 * /sales next). Wraps with the marketing nav chrome — the page itself owns
 * the body / hero / footer.
 */
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white text-ink-800">
      <MarketingNav />
      {children}
    </div>
  );
}
