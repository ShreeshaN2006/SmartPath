import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  request: VercelRequest,
  response: VercelResponse
) {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';
  
  try {
    const res = await fetch(`${backendUrl}/api/health`);
    const data = await res.json();
    return response.status(200).json(data);
  } catch (error) {
    return response.status(503).json({ 
      status: 'degraded', 
      message: 'Backend unavailable',
      timestamp: new Date().toISOString()
    });
  }
}