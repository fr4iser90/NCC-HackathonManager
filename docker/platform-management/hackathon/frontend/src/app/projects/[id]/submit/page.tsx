"use client";
import { useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { useApiClient } from "@/lib/useApiClient";

export default function ProjectSubmitPage({ params }: { params: { id: string } }) {
  const { data: session } = useSession();
  const apiFetch = useApiClient();
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const projectId = params.id;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setProgress(0);
      setStatus(null);
      setLogs("");
      setError(null);
      setSuccess(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setStatus(null);
    setLogs("");
    setProgress(0);
    setError(null);
    setSuccess(null);
    setLoading(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setStatus(null);
    setLogs("");
    setError(null);
    setSuccess(null);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("description", description);

      const res = await apiFetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/projects/${projectId}/submit_version`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Submission failed" }));
        throw new Error(errorData.detail || "Submission failed");
      }

      const data = await res.json();
      setStatus(data.status || "success");
      setLogs(data.logs || "");
      setSuccess("Submission successful!");
    } catch (err: any) {
      setStatus("error");
      setError(err.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10">
      <h1 className="text-2xl font-bold mb-4">Projekt einreichen (ZIP-Upload)</h1>
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
              {file ? "Andere Datei wählen" : "Datei auswählen"}
            </button>
          </label>
          {file && (
            <span className="ml-3 text-sm text-gray-700 dark:text-gray-200 font-medium">{file.name}</span>
          )}
        </div>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
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
          {loading ? "Einreichen..." : "Projekt einreichen"}
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
      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
      )}
      {success && (
        <div className="mt-4 text-green-600 font-semibold">{success}</div>
      )}
      {status && (
        <div className="mt-6">
          <div className={`font-semibold ${status === "success" ? "text-green-600" : "text-red-600"}`}>
            Build-Status: {status}
          </div>
          <pre className="bg-gray-100 p-4 mt-2 rounded text-xs overflow-x-auto max-h-96">
            {logs}
          </pre>
        </div>
      )}
    </div>
  );
}
