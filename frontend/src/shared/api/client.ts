export type Availability = "green" | "red";

export type Player = {
  id: string;
  display_name: string;
  availability: Availability;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

type AuthHeadersInput = {
  token: string;
};

function authHeaders(input: AuthHeadersInput): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${input.token}`,
  };
}

export async function registerUser(input: {
  email: string;
  displayName: string;
  password: string;
  organizationId: string;
  role: "admin" | "narrator" | "observer";
}): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: input.email,
      display_name: input.displayName,
      password: input.password,
      organization_id: input.organizationId,
      role: input.role,
    }),
  });
  if (!response.ok) {
    throw new Error("failed to register");
  }
}

export async function issueToken(input: {
  email: string;
  password: string;
  organizationId: string;
}): Promise<string> {
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      organization_id: input.organizationId,
    }),
  });
  if (!response.ok) {
    throw new Error("failed to authenticate");
  }
  const payload = (await response.json()) as { access_token: string };
  return payload.access_token;
}

export async function createTable(name: string, token: string): Promise<{ id: string }> {
  const response = await fetch(`${API_BASE}/tables`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    throw new Error("failed to create table");
  }
  return response.json() as Promise<{ id: string }>;
}

export async function addPlayer(
  tableId: string,
  displayName: string,
  token: string
): Promise<Player> {
  const response = await fetch(`${API_BASE}/tables/${tableId}/players`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({ display_name: displayName }),
  });
  if (!response.ok) {
    throw new Error("failed to add player");
  }
  return response.json() as Promise<Player>;
}

export async function updatePlayerAvailability(
  tableId: string,
  playerId: string,
  availability: Availability,
  token: string
): Promise<Player> {
  const response = await fetch(`${API_BASE}/tables/${tableId}/players/${playerId}`, {
    method: "PATCH",
    headers: authHeaders({ token }),
    body: JSON.stringify({ availability }),
  });
  if (!response.ok) {
    throw new Error("failed to update availability");
  }
  return response.json() as Promise<Player>;
}

export async function scheduleSoundEvent(input: {
  token: string;
  tableId: string;
  sessionId: string;
  action: string;
  executeAt: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/sound-events`, {
    method: "POST",
    headers: authHeaders({ token: input.token }),
    body: JSON.stringify({
      table_id: input.tableId,
      session_id: input.sessionId,
      action: input.action,
      execute_at: input.executeAt,
    }),
  });
  if (!response.ok) {
    throw new Error("failed to schedule event");
  }
}

