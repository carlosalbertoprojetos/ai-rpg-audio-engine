export type Availability = "green" | "red";

export type Player = {
  id: string;
  display_name: string;
  availability: Availability;
};

export type RegisteredUser = {
  user_id: string;
  email: string;
  display_name: string;
  organization_id: string;
  role: string;
};

export type OrganizationInfo = {
  id: string;
  name: string;
  owner_user_id: string;
  subscription_plan: string;
  subscription_status: string;
  billing_cycle: string;
};

export type SessionInfo = {
  id: string;
  table_id: string;
  state: string;
  started_at: string;
  ended_at: string | null;
};

export type AudioTrackInfo = {
  id: string;
  organization_id: string;
  title: string;
  s3_key: string;
  duration_seconds: number;
};

export type TriggerInfo = {
  id: string;
  table_id: string;
  condition_type: string;
  payload: Record<string, string>;
};

export type AIContextInfo = {
  id: string;
  session_id: string;
  mood: string;
  recommended_track_tags: string[];
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

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const json = (await response.json()) as { detail?: unknown };
      if (typeof json.detail === "string") return json.detail;
      return `HTTP ${response.status}`;
    }
    const text = await response.text();
    return text ? text.slice(0, 200) : `HTTP ${response.status}`;
  } catch {
    return `HTTP ${response.status}`;
  }
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
    throw new Error(await readErrorMessage(response));
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
    throw new Error(await readErrorMessage(response));
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
    throw new Error(await readErrorMessage(response));
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
    throw new Error(await readErrorMessage(response));
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
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<Player>;
}

export async function scheduleSoundEvent(input: {
  token: string;
  tableId: string;
  sessionId: string;
  action: string;
  executeAt: string;
  targetTrackId?: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/sound-events`, {
    method: "POST",
    headers: authHeaders({ token: input.token }),
    body: JSON.stringify({
      table_id: input.tableId,
      session_id: input.sessionId,
      action: input.action,
      execute_at: input.executeAt,
      target_track_id: input.targetTrackId,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}

export async function uploadAudioTrackFile(
  input: { title: string; durationSeconds: number; file: File },
  token: string
): Promise<AudioTrackInfo> {
  const body = new FormData();
  body.append("title", input.title);
  body.append("duration_seconds", String(input.durationSeconds));
  body.append("file", input.file);

  const response = await fetch(`${API_BASE}/audio-tracks/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<AudioTrackInfo>;
}

export function buildAudioStreamUrl(trackId: string, token: string): string {
  return `${API_BASE}/audio-tracks/${trackId}/stream?token=${encodeURIComponent(token)}`;
}

export async function listUsers(token: string): Promise<RegisteredUser[]> {
  const response = await fetch(`${API_BASE}/users`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<RegisteredUser[]>;
}

export async function updateUser(
  userId: string,
  token: string,
  input: { displayName?: string; role?: string }
): Promise<RegisteredUser> {
  const response = await fetch(`${API_BASE}/users/${userId}`, {
    method: "PATCH",
    headers: authHeaders({ token }),
    body: JSON.stringify({
      display_name: input.displayName,
      role: input.role,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<RegisteredUser>;
}

export async function getOrganization(
  organizationId: string,
  token: string
): Promise<OrganizationInfo> {
  const response = await fetch(`${API_BASE}/organizations/${organizationId}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<OrganizationInfo>;
}

export async function updateSubscriptionPlan(
  organizationId: string,
  token: string,
  plan: string
): Promise<OrganizationInfo> {
  const response = await fetch(`${API_BASE}/organizations/${organizationId}/subscription`, {
    method: "PATCH",
    headers: authHeaders({ token }),
    body: JSON.stringify({ plan }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<OrganizationInfo>;
}

export async function startSession(tableId: string, token: string): Promise<SessionInfo> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({ table_id: tableId }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<SessionInfo>;
}

export async function endSession(sessionId: string, token: string): Promise<SessionInfo> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/end`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<SessionInfo>;
}

export async function createAudioTrack(
  input: { title: string; s3Key: string; durationSeconds: number },
  token: string
): Promise<AudioTrackInfo> {
  const response = await fetch(`${API_BASE}/audio-tracks`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({
      title: input.title,
      s3_key: input.s3Key,
      duration_seconds: input.durationSeconds,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<AudioTrackInfo>;
}

export async function listAudioTracks(token: string): Promise<AudioTrackInfo[]> {
  const response = await fetch(`${API_BASE}/audio-tracks`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<AudioTrackInfo[]>;
}

export async function createTrigger(
  input: { tableId: string; conditionType: string; payload: Record<string, string> },
  token: string
): Promise<TriggerInfo> {
  const response = await fetch(`${API_BASE}/triggers`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({
      table_id: input.tableId,
      condition_type: input.conditionType,
      payload: input.payload,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<TriggerInfo>;
}

export async function generateAIContext(
  input: { sessionId: string; mood: string },
  token: string
): Promise<AIContextInfo> {
  const response = await fetch(`${API_BASE}/ai-contexts`, {
    method: "POST",
    headers: authHeaders({ token }),
    body: JSON.stringify({ session_id: input.sessionId, mood: input.mood }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json() as Promise<AIContextInfo>;
}
