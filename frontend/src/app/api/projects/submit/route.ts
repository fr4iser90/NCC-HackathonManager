import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Parse the multipart form to extract project_id and forward the rest
  const contentType = req.headers.get("content-type") || "";
  if (!contentType.startsWith("multipart/form-data")) {
    return NextResponse.json({ error: "Invalid content type" }, { status: 400 });
  }

  // Read the raw body as a buffer
  const rawBody = await req.arrayBuffer();
  const boundaryMatch = contentType.match(/boundary=([^\s;]+)/);
  if (!boundaryMatch) {
    return NextResponse.json({ error: "No boundary in content-type" }, { status: 400 });
  }
  const boundary = boundaryMatch[1];

  // Use a third-party library to parse multipart form (formidable, busboy, or custom)
  // For simplicity, use 'formdata-node' (works in edge/node envs)
  // If not available, fallback to a minimal parser
  let projectId = null;
  try {
    // @ts-ignore
    const { FormData, File } = await import("formdata-node");
    // @ts-ignore
    const { parseFormData } = await import("formdata-node/parser");
    const form = await parseFormData(new Request(req.url, {
      method: "POST",
      headers: req.headers,
      body: rawBody,
    }));
    projectId = form.get("project_id");
  } catch (e) {
    // Fallback: try to extract project_id from the raw body (not robust)
    const text = Buffer.from(rawBody).toString();
    const match = text.match(/name="project_id"\r\n\r\n([^\r\n]+)/);
    if (match) {
      projectId = match[1];
    }
  }

  if (!projectId) {
    return NextResponse.json({ error: "project_id missing" }, { status: 400 });
  }

  const apiUrl = `${backendUrl}/projects/${projectId}/submit_version`;
  // Remove trailing slash if present
  const cleanApiUrl = apiUrl.replace(/\/+$/, "");

  // Forward the request to the backend
  // Copy headers and explicitly forward Authorization if present
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") {
      headers.set(key, value);
    }
  });

  // Debug: log headers
  // console.log("Forwarding headers:", Array.from(headers.entries()));

  const res = await fetch(cleanApiUrl, {
    method: 'POST',
    headers,
    body: rawBody,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
