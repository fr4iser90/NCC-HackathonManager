// src/lib/useApiClient.ts
import { useSession } from "next-auth/react";

export function useApiClient() {
  const { data: session } = useSession();

  async function apiFetch(input: RequestInfo, init: RequestInit = {}) {
    const token = (session?.user as any)?.accessToken;
    const headers = {
      ...(init.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(input, { ...init, headers });
  }

  return apiFetch;
}