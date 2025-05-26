'use client';
import { useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useApiClient } from '@/lib/useApiClient';

export default function ProjectSubmitPage() {
  const params = useParams();
  const projectId =
    params && typeof params.id === 'string'
      ? params.id
      : params && Array.isArray(params.id)
        ? params.id[0]
        : '';
  useSession();
  const apiFetch = useApiClient();
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [loading, setLoading] = useState(false);
  // Removed unused progress state
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      // setProgress removed (progress state removed)
      setStatus(null);
      setLogs('');
      setError(null);
      setSuccess(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setStatus(null);
    setLogs('');
    // setProgress removed (progress state removed)
    setError(null);
    setSuccess(null);
    setLoading(false);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setStatus(null);
    setLogs('');
    setError(null);
    setSuccess(null);
    // setProgress removed (progress state removed)

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', description);

      const res = await apiFetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/projects/${projectId}/submit_version`,
        {
          method: 'POST',
          body: formData,
        },
      );

      if (!res.ok) {
        const errorData = await res
          .json()
          .catch(() => ({ detail: 'Submission failed' }));
        throw new Error(errorData.detail || 'Submission failed');
      }

      const data = await res.json();
      setStatus(data.status || 'success');
      setLogs(data.build_logs || data.logs || '');
      setSuccess('Submission successful!');
    } catch (err: unknown) {
      setStatus('error');
      if (
        err &&
        typeof err === 'object' &&
        'message' in err &&
        typeof (err as { message?: string }).message === 'string'
      ) {
        setError((err as { message: string }).message);
      } else {
        setError('Submission failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10">
      <h1 className="text-2xl font-bold mb-4">
        Projekt einreichen (ZIP-Upload)
      </h1>
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-xl flex flex-col items-center">
            <svg
              className="animate-spin h-8 w-8 text-blue-600 mb-2"
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
                d="M4 12a8 8 0 018-8v8z"
              ></path>
            </svg>
            <div className="text-blue-700 dark:text-blue-300 font-semibold">
              Build läuft, bitte warten...
            </div>
          </div>
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            required={!file}
            className="hidden"
            disabled={loading}
            id="zip-upload"
          />
          <label htmlFor="zip-upload">
            <button
              type="button"
              className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-4 py-2 rounded cursor-pointer transition-colors disabled:opacity-50"
              onClick={() => inputRef.current?.click()}
              disabled={loading}
            >
              {file ? 'Andere Datei wählen' : 'Datei auswählen'}
            </button>
          </label>
          {file && (
            <span className="ml-3 text-sm text-gray-700 dark:text-gray-200 font-medium">
              {file.name}
            </span>
          )}
        </div>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Beschreibung für diese Einreichung (optional)"
          className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
          rows={3}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!file || loading}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50 w-full"
        >
          {loading ? 'Einreichen...' : 'Projekt einreichen'}
        </button>
        {file && (
          <button
            type="button"
            onClick={handleReset}
            className="text-sm text-gray-500 underline"
            disabled={loading}
          >
            Reset
          </button>
        )}
      </form>
      {error && <div className="mt-4 text-red-600 font-semibold">{error}</div>}
      {success && (
        <div className="mt-4 text-green-600 font-semibold">{success}</div>
      )}
      {status && (
        <div className="mt-6">
          <div
            className={`font-semibold ${status === 'success' ? 'text-green-600' : 'text-red-600'}`}
          >
            Build-Status: {status}
          </div>
          <pre
            className="bg-gray-900 text-green-200 p-4 mt-2 rounded text-xs overflow-x-auto max-h-96 border border-gray-700 shadow-inner"
            style={{ background: '#18181b' }}
          >
            {logs}
          </pre>
        </div>
      )}
    </div>
  );
}
