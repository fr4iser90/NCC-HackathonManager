import { NextRequest, NextResponse } from 'next/server';
import formidable, { Fields, Files } from 'formidable';
import { Readable } from 'stream';

export const runtime = 'nodejs';

// === File validation config (edit as needed) ===
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED_MIME_TYPES = ['application/zip', 'application/pdf', 'image/png'];
const ALLOWED_EXTENSIONS = ['.zip', '.pdf', '.png'];
// ==============================================

// Custom type to satisfy formidable's IncomingMessage requirement
interface ReadableWithHeaders extends Readable {
  headers: Record<string, string>;
}

export async function POST(req: NextRequest) {
  const backendUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  // Parse the multipart form to extract project_id using formidable
  const contentType = req.headers.get('content-type') || '';
  if (!contentType.startsWith('multipart/form-data')) {
    return NextResponse.json(
      { error: 'Invalid content type' },
      { status: 400 },
    );
  }

  // Convert the request body to a stream for formidable
  const rawBody = Buffer.from(await req.arrayBuffer());
  const form = formidable();

  // formidable expects a Node.js IncomingMessage, so we create a mock
  const mockReq: ReadableWithHeaders = Object.assign(new Readable(), {
    headers: Object.fromEntries(req.headers.entries()),
  });
  mockReq.push(rawBody);
  mockReq.push(null);

  let projectId: string | undefined = undefined;
  let fields: Fields = {};
  let files: Files = {};

  try {
    [fields, files] = await new Promise<[Fields, Files]>((resolve, reject) => {
      // Type assertion to satisfy formidable's IncomingMessage requirement
      form.parse(
        mockReq as unknown as import('http').IncomingMessage,
        (err: Error | null, fields: Fields, files: Files) => {
          if (err) reject(err);
          else resolve([fields, files]);
        },
      );
    });
    const pid = fields.project_id;
    if (Array.isArray(pid)) {
      projectId = typeof pid[0] === 'string' ? pid[0] : undefined;
    } else if (typeof pid === 'string') {
      projectId = pid;
    }

    // === File validation logic ===
    const fileErrors: string[] = [];
    // formidable returns files as { [fieldName]: File | File[] }
    Object.entries(files).forEach(([, fileOrFiles]) => {
      const fileList = Array.isArray(fileOrFiles) ? fileOrFiles : [fileOrFiles];
      fileList.forEach((file) => {
        if (!file) return;
        // Check size
        if (file.size > MAX_FILE_SIZE) {
          fileErrors.push(
            `File "${file.originalFilename ?? 'unnamed'}" is too large (${file.size} bytes, max ${MAX_FILE_SIZE} bytes)`,
          );
        }
        // Check MIME type
        if (file.mimetype && !ALLOWED_MIME_TYPES.includes(file.mimetype)) {
          fileErrors.push(
            `File "${file.originalFilename ?? 'unnamed'}" has disallowed MIME type: ${file.mimetype}`,
          );
        }
        // Check extension
        if (
          file.originalFilename &&
          !ALLOWED_EXTENSIONS.some((ext) =>
            (file.originalFilename as string).toLowerCase().endsWith(ext),
          )
        ) {
          fileErrors.push(
            `File "${file.originalFilename}" has disallowed extension`,
          );
        }
      });
    });
    if (fileErrors.length > 0) {
      return NextResponse.json(
        { error: 'File validation failed', details: fileErrors },
        { status: 400 },
      );
    }
    // === End file validation ===
  } catch (err) {
    return NextResponse.json(
      { error: 'Failed to parse multipart form data', details: String(err) },
      { status: 400 },
    );
  }

  if (!projectId) {
    return NextResponse.json({ error: 'project_id missing' }, { status: 400 });
  }

  const apiUrl = `${backendUrl}/projects/${projectId}/submit_version`;
  // Remove trailing slash if present
  const cleanApiUrl = apiUrl.replace(/\/+$/, '');

  // Forward the request to the backend
  // Copy headers and explicitly forward Authorization if present
  const headers = new Headers();
  req.headers.forEach((value: string, key: string) => {
    if (key.toLowerCase() !== 'host') {
      headers.set(key, value);
    }
  });

  // Forward the original raw body to the backend
  const res = await fetch(cleanApiUrl, {
    method: 'POST',
    headers,
    body: rawBody,
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
