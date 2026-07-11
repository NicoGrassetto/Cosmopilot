const BASE = import.meta.env.VITE_API_BASE ?? '';

async function toJsonOrThrow(res) {
  let body = null;
  try {
    body = await res.json();
  } catch {
    // fall through to generic error below
  }
  if (!res.ok) {
    const detail = body?.detail || `${res.status} ${res.statusText}`;
    throw new Error(detail);
  }
  return body;
}

export async function fetchAgents() {
  const res = await fetch(`${BASE}/api/agents`);
  const data = await toJsonOrThrow(res);
  return data.agents ?? [];
}

export async function sendChat({ agent, message, responseId }) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent, message, response_id: responseId ?? null }),
  });
  return toJsonOrThrow(res); // { reply, response_id }
}
