export default function AuthErrorPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-4 p-8 text-center">
        <h1 className="text-xl font-semibold">Sign-in failed</h1>
        <p className="text-sm text-ink-500">
          {searchParams.error ?? "Unknown error"}
        </p>
        <p className="text-xs text-ink-500">
          You may not have access yet. Contact ops to be added to{" "}
          <code>cortex-internal-users@mlytics.com</code>.
        </p>
      </div>
    </div>
  );
}
