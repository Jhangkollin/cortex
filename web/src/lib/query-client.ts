/**
 * TanStack Query — single QueryClient per Server Component request.
 *
 * Per the official Next.js App Router pattern, use `cache()` to dedupe within
 * a single request, and `new QueryClient()` per call so server prefetches
 * don't leak between requests.
 */
import { QueryClient, isServer } from "@tanstack/react-query";
import { cache } from "react";

function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 min — match Redis TTL on the server
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

export const getQueryClient = cache(() => {
  if (isServer) {
    // Server: always fresh per request
    return makeQueryClient();
  }
  // Browser: keep a singleton across navigations
  if (!browserQueryClient) browserQueryClient = makeQueryClient();
  return browserQueryClient;
});
