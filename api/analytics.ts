import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

  try {
    const res = await fetch(`${backendUrl}/api/analytics`);
    const data = await res.json();
    return response.status(res.status).json(data);
  } catch (error) {
    return response.status(503).json({ success: false, error: 'Analytics service unavailable' });
  }
}