'use client';

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const errorMessages: Record<string, string> = {
  CredentialsSignin: 'Invalid email or password. Please try again.',
  Default: 'An unexpected authentication error occurred. Please try again.',
  OAuthSignin: 'Error trying to sign in with the OAuth provider.',
  OAuthCallback: 'Error processing the OAuth callback.',
  OAuthCreateAccount: 'Error creating user account with OAuth.',
  EmailCreateAccount: 'Error creating user account with email.',
  Callback: 'Error in the OAuth callback process.',
  OAuthAccountNotLinked: 
    'This OAuth account is not linked to a user. If you have signed in with this provider before, try signing in with the original method.',
  EmailSignin: 'Could not send sign-in email. Please try again.',
  SessionRequired: 'You must be signed in to access this page.',
  // Add any custom error keys you might throw from your authorize function
};

export default function AuthErrorPage() {
  const searchParams = useSearchParams();
  if (!searchParams) return null;
  const errorKey = searchParams.get('error');
  const [errorMessage, setErrorMessage] = useState('Loading error details...');

  useEffect(() => {
    let message = errorMessages.Default;
    if (errorKey) {
      // Attempt to decode if it's a NextAuth internal error key
      message = errorMessages[errorKey] || errorKey; 
      // If errorKey is not in errorMessages, it might be a custom message thrown from authorize(), 
      // which might already be decoded or needs decoding.
      // We try to decode it, assuming it might be URL-encoded custom message.
      try {
        const decodedKey = decodeURIComponent(errorKey);
        message = errorMessages[decodedKey] || decodedKey;
      } catch (e) {
        // If decoding fails, use the errorKey as is (it might not have been encoded)
        console.warn("Failed to decode errorKey or it was not encoded:", errorKey);
      }
    }
    setErrorMessage(message);
  }, [errorKey]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2 bg-slate-100">
      <div className="w-full max-w-lg p-10 text-center bg-white shadow-xl rounded-xl">
        <h1 className="text-3xl font-bold text-red-600 mb-6">Authentication Error</h1>
        <div className="p-6 mb-6 text-red-800 bg-red-100 border border-red-300 rounded-lg">
          <p className="font-semibold">Details:</p>
          <p>{errorMessage}</p>
        </div>
        <Link
          href="/auth/signin"
          className="px-6 py-3 font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
        >
          Try Sign In Again
        </Link>
        <Link
          href="/"
          className="ml-4 px-6 py-3 font-medium text-slate-700 bg-slate-200 rounded-lg hover:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 transition-colors"
        >
          Go to Homepage
        </Link>
      </div>
    </div>
  );
} 