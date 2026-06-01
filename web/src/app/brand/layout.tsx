import { OnboardingGate } from "@/components/auth/onboarding-gate";
import { BrandShell } from "@/components/shell/brand-shell";

export default function BrandLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <OnboardingGate>
      <BrandShell>{children}</BrandShell>
    </OnboardingGate>
  );
}
