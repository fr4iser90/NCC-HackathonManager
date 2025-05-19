"use client";
import { useState, useRef } from "react";

export default function ProjectSubmitPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setProgress(0);
      setStatus(null);
      setLogs("");
      setError(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setStatus(null);
    setLogs("");
    setProgress(0);
    setError(null);
    setLoading(false);
    if (inputRef.current) inputRef.current.value = "";
  };

  // Drag&Drop Events
  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setProgress(0);
      setStatus(null);
      setLogs("");
      setError(null);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const handleClickDrop = () => {
    if (inputRef.current) inputRef.current.click();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setStatus(null);
    setLogs("");
    setError(null);
    setProgress(0);
    // Upload mit XHR für Fortschrittsbalken
    const formData = new FormData();
    formData.append("file", file);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/projects/submit", true);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      setLoading(false);
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText);
          setStatus(data.status);
          setLogs(data.logs);
        } catch (err) {
          setStatus("error");
          setError("Fehler beim Parsen der Serverantwort.");
        }
      } else {
        setStatus("error");
        setError(`Upload fehlgeschlagen (Status ${xhr.status})`);
      }
    };
    xhr.onerror = () => {
      setLoading(false);
      setStatus("error");
      setError("Netzwerkfehler beim Upload.");
    };
    xhr.send(formData);
  };

  return (
    <div className="max-w-xl mx-auto py-10">
      <h1 className="text-2xl font-bold mb-4">Projekt einreichen (ZIP-Upload)</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleClickDrop}
          className={`border-2 border-dashed rounded p-6 text-center cursor-pointer transition-colors ${dragActive ? "border-blue-600 bg-blue-50" : "border-gray-300 bg-white"} ${loading ? "opacity-50 pointer-events-none" : ""}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            required={!file}
            className="hidden"
            disabled={loading}
          />
          {file ? (
            <div className="flex flex-col items-center gap-2">
              <span className="truncate font-medium">{file.name}</span>
              <button type="button" onClick={handleReset} className="text-sm text-gray-500 underline">Reset</button>
            </div>
          ) : (
            <span className="text-gray-500">Datei hierher ziehen oder klicken, um auszuwählen (.zip)</span>
          )}
        </div>
        {loading && (
          <div className="w-full bg-gray-200 rounded h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-3 transition-all"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        )}
        <button
          type="submit"
          disabled={!file || loading}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50 w-full"
        >
          {loading ? (progress < 100 ? `Upload läuft... (${progress}%)` : "Build läuft...") : "Projekt einreichen"}
        </button>
      </form>
      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
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