import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: NextRequest) {
  const backendUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const apiUrl = `${backendUrl}/users/me/avatar`;

  const body = req.body;
  const headers = new Headers(req.headers);
  headers.delete('host');

  const res = await fetch(apiUrl, {
    method: 'POST',
    headers,
    body,
  });

  const data = await res.text();
  return new NextResponse(data, {
    status: res.status,
    headers: {
      'content-type': res.headers.get('content-type') || 'application/json',
    },
  });
}
