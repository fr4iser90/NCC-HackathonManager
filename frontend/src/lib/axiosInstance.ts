import axios from 'axios';
import { signOut } from 'next-auth/react';

const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL, // Your API base URL from .env.local
});

axiosInstance.interceptors.response.use(
  (response) => {
    // If the request was successful, just return the response
    return response;
  },
  async (error) => {
    // If the error is a 401 Unauthorized
    if (error.response && error.response.status === 401) {
      // Nur bei Auth-Check-Endpunkten automatisch ausloggen
      const url = error.config?.url || '';
      if (url.includes('/ping') || url.includes('/users/me')) {
        const publicAuthPaths = [
          '/auth/signin',
          '/auth/register',
          '/auth/error',
        ];
        if (
          typeof window !== 'undefined' &&
          !publicAuthPaths.includes(window.location.pathname)
        ) {
          console.log(
            '[axiosInstance] Received 401 from Auth-Check. Signing out and redirecting to signin.',
          );
          await signOut({ redirect: false });
          window.location.href =
            '/auth/signin?sessionExpired=true&reason=api_401';
        }
      }
      // Sonst: Kein Logout, sondern Fehler normal weitergeben
    }
    // If it's another error, just pass it through
    return Promise.reject(error);
  },
);

export default axiosInstance;
