import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const res = await fetch(`${backendUrl}/api/random-blockages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.body)
    });
    const data = await res.json();
    return response.status(res.status).json(data);
  } catch (error) {
    return response.status(503).json({ success: false, error: 'Blockages service unavailable' });
  }
}