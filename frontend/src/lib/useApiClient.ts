// src/lib/useApiClient.ts
import { useSession } from "next-auth/react";
import { useCallback } from "react"; // Import useCallback

export function useApiClient() {
  const { data: session } = useSession();

  const apiFetch = useCallback(async (input: RequestInfo, init: RequestInit = {}) => {
    // Ensure session and user are checked before accessing accessToken
    const token = session?.user && (session.user as any).accessToken 
                  ? (session.user as any).accessToken 
                  : null;
                  
    const headers = {
      ...(init.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(input, { ...init, headers });
  }, [session]); // Dependency array for useCallback includes session

  return apiFetch;
}
