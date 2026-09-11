import type { VercelRequest, VercelResponse } from '@vercel/node';

interface RouteRequest {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  vehicle: string;
  mode: string;
  waypoints?: { lat: number; lng: number }[];
}

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
) {
  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method not allowed' });
  }

  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';
  const body = request.body as RouteRequest;

  try {
    const res = await fetch(`${backendUrl}/api/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();
    return response.status(res.status).json(data);
  } catch (error) {
    return response.status(503).json({
      success: false,
      error: 'Backend unavailable',
      message: 'Routing service temporarily unavailable'
    });
  }
}