'use client';

import { useState, FormEvent, useEffect } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams?.get('callbackUrl') || '/';
  const error = searchParams?.get('error') || null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(error);

  useEffect(() => {
    if (error) {
      setPageError(decodeURIComponent(error));
    }
  }, [error]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setPageError(null);

    const result = await signIn('credentials', {
      redirect: false,
      email: email,
      password: password,
    });

    setIsLoading(false);

    if (result?.error) {
      setPageError(
        result.error === 'CredentialsSignin'
          ? 'Invalid email or password.'
          : result.error,
      );
    } else if (result?.ok) {
      router.push(callbackUrl);
    } else {
      setPageError('An unexpected error occurred during sign in.');
    }
  };

  if (!searchParams) return null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2 bg-slate-50">
      <div className="w-full max-w-md p-8 space-y-8 bg-white shadow-xl rounded-xl">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-slate-800">Sign In</h1>
          <p className="mt-2 text-slate-600">
            Access your Hackathon Platform account.
          </p>
        </div>

        {pageError && (
          <div
            className="p-4 text-sm text-red-700 bg-red-100 border border-red-400 rounded-md"
            role="alert"
          >
            <p className="font-semibold">Authentication Error:</p>
            <p>{pageError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
            >
              {isLoading ? (
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              ) : (
                'Sign In'
              )}
            </button>
          </div>
        </form>
        <p className="mt-6 text-center text-sm text-slate-600">
          No account yet?{' '}
          <Link
            href="/auth/signup"
            className="font-medium text-indigo-600 hover:text-indigo-500"
          >
            Sign Up
          </Link>{' '}
          (Not implemented)
        </p>
      </div>
    </div>
  );
}
