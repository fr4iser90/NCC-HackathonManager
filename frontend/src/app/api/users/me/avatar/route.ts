import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const apiUrl = `${backendUrl}/users/me/avatar`;

  const body = req.body;
  const headers = new Headers(req.headers);
  headers.delete('host');

  // @ts-expect-error Node.js fetch needs duplex for streaming uploads
  const res = await fetch(apiUrl, {
    method: 'POST',
    headers,
    body,
    duplex: 'half',
  });

  const data = await res.text();
  return new NextResponse(data, {
    status: res.status,
    headers: { 'content-type': res.headers.get('content-type') || 'application/json' },
  });
} 