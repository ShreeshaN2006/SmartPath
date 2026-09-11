import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

  try {
    if (request.method === 'POST') {
      const res = await fetch(`${backendUrl}/api/incidents/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request.body)
      });
      const data = await res.json();
      return response.status(res.status).json(data);
    }

    const res = await fetch(`${backendUrl}/api/incidents?${new URLSearchParams(request.query as Record<string, string>).toString()}`);
    const data = await res.json();
    return response.status(res.status).json(data);
  } catch (error) {
    return response.status(503).json({ success: false, error: 'Incidents service unavailable' });
  }
}