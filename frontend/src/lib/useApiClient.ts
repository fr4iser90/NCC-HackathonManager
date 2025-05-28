// src/lib/useApiClient.ts
import { useSession } from 'next-auth/react';
import { useCallback } from 'react';

export function useApiClient() {
  const { data: session } = useSession();

  const apiFetch = useCallback(
    async (input: RequestInfo, init: RequestInit = {}) => {
      const token = session?.user?.accessToken;

      if (!token) {
        throw new Error('No access token available');
      }

      // Start with a plain object for headers
      const modifiableHeaders: Record<string, string> = {
        Authorization: `Bearer ${token}`,
      };

      // Merge headers from init, ensuring they are also treated as Record<string, string>
      // This is a simplification; a more robust merge might be needed if init.headers can be Headers object or array
      if (init.headers) {
        for (const [key, value] of Object.entries(init.headers)) {
          if (typeof value === 'string') { // Ensure value is a string
            modifiableHeaders[key] = value;
          }
        }
      }
      
      // Do not set Content-Type if body is FormData, browser will set it with boundary
      if (!(init.body instanceof FormData)) {
        modifiableHeaders['Content-Type'] = 'application/json';
      }

      try {
        const response = await fetch(input, { ...init, headers: modifiableHeaders });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return response;
      } catch (error) {
        console.error('API request failed:', error);
        if (error instanceof Error) {
          throw error;
        }
        throw new Error('An unexpected error occurred');
      }
    },
    [session],
  );

  return apiFetch;
}
