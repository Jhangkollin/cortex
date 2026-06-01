import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

/**
 * Flat ESLint config for cortex-web.
 *
 * Next 16 removed `next lint` and instead ships a flat config at
 * `eslint-config-next/core-web-vitals`. We import it directly and append
 * project-level ignores. See https://nextjs.org/docs/app/api-reference/config/eslint
 */
export default [
  ...nextCoreWebVitals,
  {
    ignores: [
      "node_modules",
      ".next",
      "out",
      "src/lib/api-client/generated",
    ],
  },
];
