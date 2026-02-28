import { useMemo, useState } from "react";
import {
  AIContextInfo,
  AudioTrackInfo,
  Availability,
  OrganizationInfo,
  Player,
  RegisteredUser,
  SessionInfo,
  addPlayer,
  createAudioTrack,
  createTable,
  createTrigger,
  endSession,
  generateAIContext,
  getOrganization,
  issueToken,
  listAudioTracks,
  listUsers,
  registerUser,
  scheduleSoundEvent,
  startSession,
  updatePlayerAvailability,
  updateSubscriptionPlan,
  updateUser,
} from "../shared/api/client";
import { useTableSocket } from "../shared/ws/useTableSocket";
import { PlayerLed } from "../widgets/player-led/PlayerLed";
import { SoundDesk } from "../widgets/sound-desk/SoundDesk";
import "./DeskPage.css";

const TRACKS = [
  { id: "forest", title: "Floresta Nebulosa", level: 82 },
  { id: "tavern", title: "Taberna da Fronteira", level: 64 },
  { id: "battle", title: "Emboscada Orc", level: 91 },
  { id: "void", title: "Abismo Arcano", level: 48 },
];

export function DeskPage() {
  const [tableId, setTableId] = useState<string | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [newPlayerName, setNewPlayerName] = useState("Luna");

  const [email, setEmail] = useState("gm@rpgsounddesk.com");
  const [displayName, setDisplayName] = useState("Game Master");
  const [password, setPassword] = useState("StrongPass123");
  const [organizationId, setOrganizationId] = useState("org-demo");
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState("Registre e autentique para iniciar.");
  const [authBusy, setAuthBusy] = useState<"register" | "login" | null>(null);

  const [organization, setOrganization] = useState<OrganizationInfo | null>(null);
  const [plan, setPlan] = useState("pro");
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [audioTracks, setAudioTracks] = useState<AudioTrackInfo[]>([]);
  const [trackTitle, setTrackTitle] = useState("Battle Theme");
  const [trackKey, setTrackKey] = useState("org-demo/battle-theme.mp3");
  const [trackDuration, setTrackDuration] = useState(180);
  const [triggerType, setTriggerType] = useState("scene_change");
  const [triggerScene, setTriggerScene] = useState("battle");
  const [aiMood, setAiMood] = useState("battle");
  const [latestAI, setLatestAI] = useState<AIContextInfo | null>(null);

  const socket = useTableSocket(tableId, token);

  const [usersOpen, setUsersOpen] = useState(true);
  const [users, setUsers] = useState<RegisteredUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [editingRole, setEditingRole] = useState("");

  const lastEventLabel = useMemo(() => {
    if (!socket.lastEvent) return "Sem eventos recentes";
    return `${socket.lastEvent.event_type} @ ${new Date(socket.lastEvent.occurred_at).toLocaleTimeString()}`;
  }, [socket.lastEvent]);

  async function refreshEnterprise(activeToken: string) {
    try {
      const [org, tracks] = await Promise.all([
        getOrganization(organizationId, activeToken),
        listAudioTracks(activeToken),
      ]);
      setOrganization(org);
      setAudioTracks(tracks);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao carregar modulos enterprise: ${detail}`);
    }
  }

  async function refreshUsers(activeToken: string) {
    setUsersLoading(true);
    try {
      const fetched = await listUsers(activeToken);
      setUsers(fetched);
    } catch {
      setMessage("Falha ao carregar usuarios (precisa ser admin).");
    } finally {
      setUsersLoading(false);
    }
  }

  async function handleRegister() {
    if (authBusy) return;
    setAuthBusy("register");
    setMessage("Registrando...");
    try {
      await registerUser({ email, displayName, password, organizationId, role: "admin" });
      const nextToken = await issueToken({ email, password, organizationId });
      setToken(nextToken);
      setMessage("Usuario registrado e logado com sucesso.");
      await Promise.all([refreshUsers(nextToken), refreshEnterprise(nextToken)]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao registrar: ${detail}`);
    } finally {
      setAuthBusy(null);
    }
  }

  async function handleLogin() {
    if (authBusy) return;
    setAuthBusy("login");
    setMessage("Autenticando...");
    try {
      const nextToken = await issueToken({ email, password, organizationId });
      setToken(nextToken);
      setMessage("Autenticado com sucesso.");
      await Promise.all([refreshUsers(nextToken), refreshEnterprise(nextToken)]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha de autenticacao: ${detail}`);
    } finally {
      setAuthBusy(null);
    }
  }

  function handleLogout() {
    setToken(null);
    setTableId(null);
    setPlayers([]);
    setUsers([]);
    setEditingUserId(null);
    setOrganization(null);
    setSession(null);
    setAudioTracks([]);
    setLatestAI(null);
    setMessage("Deslogado.");
  }

  async function handleCreateTable() {
    if (!token) return setMessage("Autentique antes de criar mesa.");
    try {
      const table = await createTable("Mesa Principal", token);
      setTableId(table.id);
      setMessage(`Mesa criada: ${table.id}`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao criar mesa: ${detail}`);
    }
  }

  async function handleStartSession() {
    if (!token || !tableId) return setMessage("Crie uma mesa antes de iniciar sessao.");
    try {
      const started = await startSession(tableId, token);
      setSession(started);
      setMessage(`Sessao iniciada: ${started.id}`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao iniciar sessao: ${detail}`);
    }
  }

  async function handleEndSession() {
    if (!token || !session) return;
    try {
      const ended = await endSession(session.id, token);
      setSession(ended);
      setMessage(`Sessao encerrada: ${ended.id}`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao encerrar sessao: ${detail}`);
    }
  }

  async function handleAddPlayer() {
    if (!tableId || !token) return;
    try {
      const created = await addPlayer(tableId, newPlayerName, token);
      setPlayers((current) => [...current, created]);
      setNewPlayerName("");
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao adicionar jogador: ${detail}`);
    }
  }

  async function handleTogglePlayer(player: Player) {
    if (!tableId || !token) return;
    const nextAvailability: Availability = player.availability === "green" ? "red" : "green";
    try {
      const updated = await updatePlayerAvailability(tableId, player.id, nextAvailability, token);
      setPlayers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao atualizar jogador: ${detail}`);
    }
  }

  async function handlePlay(trackId: string) {
    if (!tableId || !token || !session) {
      return setMessage("Crie mesa e inicie sessao antes de tocar trilhas.");
    }
    const executeAt = new Date(Date.now() + 1000).toISOString();
    try {
      await scheduleSoundEvent({
        token,
        tableId,
        sessionId: session.id,
        action: `play:${trackId}`,
        executeAt,
      });
      setMessage(`Evento agendado para trilha ${trackId}.`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao agendar evento sonoro: ${detail}`);
    }
  }

  async function handleCreateTrack() {
    if (!token) return;
    try {
      const created = await createAudioTrack(
        { title: trackTitle, s3Key: trackKey, durationSeconds: trackDuration },
        token
      );
      setAudioTracks((cur) => [created, ...cur]);
      setMessage(`Track registrada: ${created.title}`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao registrar track: ${detail}`);
    }
  }

  async function handleCreateTrigger() {
    if (!token || !tableId) return;
    try {
      await createTrigger(
        { tableId, conditionType: triggerType, payload: { scene: triggerScene } },
        token
      );
      setMessage("Trigger criada com sucesso.");
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao criar trigger: ${detail}`);
    }
  }

  async function handleGenerateAI() {
    if (!token || !session) return;
    try {
      const context = await generateAIContext({ sessionId: session.id, mood: aiMood }, token);
      setLatestAI(context);
      setMessage(`IA gerou contexto para mood '${context.mood}'.`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao gerar contexto IA: ${detail}`);
    }
  }

  async function handleUpdatePlan() {
    if (!token) return;
    try {
      const updated = await updateSubscriptionPlan(organizationId, token, plan);
      setOrganization(updated);
      setMessage(`Plano atualizado para ${updated.subscription_plan}.`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao atualizar plano: ${detail}`);
    }
  }

  return (
    <main className="desk-page">
      <header className="topbar">
        <div className="topbar-row">
          <div>
            <h1>RPGSoundDesk</h1>
            <p>Orquestracao sonora adaptativa para mesas online.</p>
          </div>
          <button
            type="button"
            className={`auth-indicator ${token ? "on" : "off"}`}
            onClick={() => (token ? handleLogout() : setMessage("Deslogado. Faca login abaixo."))}
            title={
              token
                ? `Logado como ${email} (${organizationId}). Clique para sair.`
                : "Deslogado. Faça login abaixo."
            }
            aria-label={token ? "Usuario logado" : "Usuario deslogado"}
          >
            <span className="auth-led" aria-hidden="true" />
          </button>
        </div>
      </header>

      <section className="auth-grid">
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="E-mail" />
        <input
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Nome de exibicao"
        />
        <input
          value={organizationId}
          onChange={(event) => setOrganizationId(event.target.value)}
          placeholder="Organizacao"
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Senha"
        />
        <button type="button" onClick={handleRegister}>
          {authBusy === "register" ? "Registrando..." : "Registrar"}
        </button>
        <button
          type="button"
          onClick={() => (token ? handleLogout() : void handleLogin())}
          disabled={authBusy === "register" || authBusy === "login"}
        >
          {token ? "Logout" : authBusy === "login" ? "Entrando..." : "Login"}
        </button>
      </section>

      <section className="enterprise-grid">
        <article className="enterprise-card">
          <h3>Organization</h3>
          <p>Plano: {organization?.subscription_plan ?? "-"}</p>
          <div className="inline-form">
            <input value={plan} onChange={(e) => setPlan(e.target.value)} placeholder="plano" />
            <button type="button" onClick={() => void handleUpdatePlan()} disabled={!token}>
              Atualizar Plano
            </button>
          </div>
        </article>
        <article className="enterprise-card">
          <h3>Session</h3>
          <p>Sessao: {session?.id ?? "-"}</p>
          <p>Estado: {session?.state ?? "nao iniciada"}</p>
          <div className="inline-form">
            <button type="button" onClick={() => void handleStartSession()} disabled={!tableId || !token}>
              Iniciar Sessao
            </button>
            <button
              type="button"
              onClick={() => void handleEndSession()}
              disabled={!session || !token || session.state === "finished"}
            >
              Encerrar Sessao
            </button>
          </div>
        </article>
        <article className="enterprise-card">
          <h3>AI Context</h3>
          <div className="inline-form">
            <input value={aiMood} onChange={(e) => setAiMood(e.target.value)} placeholder="mood" />
            <button type="button" onClick={() => void handleGenerateAI()} disabled={!session || !token}>
              Gerar IA
            </button>
          </div>
          <p>{latestAI ? `Tags: ${latestAI.recommended_track_tags.join(", ")}` : "Sem contexto gerado"}</p>
        </article>
      </section>

      <section className="enterprise-grid">
        <article className="enterprise-card">
          <h3>Audio Tracks</h3>
          <div className="inline-form">
            <input value={trackTitle} onChange={(e) => setTrackTitle(e.target.value)} placeholder="titulo" />
            <input value={trackKey} onChange={(e) => setTrackKey(e.target.value)} placeholder="s3 key" />
            <input
              type="number"
              value={trackDuration}
              onChange={(e) => setTrackDuration(Number(e.target.value))}
              placeholder="duracao"
            />
            <button type="button" onClick={() => void handleCreateTrack()} disabled={!token}>
              Registrar
            </button>
          </div>
          <p>Tracks registradas: {audioTracks.length}</p>
        </article>
        <article className="enterprise-card">
          <h3>Trigger</h3>
          <div className="inline-form">
            <input value={triggerType} onChange={(e) => setTriggerType(e.target.value)} placeholder="tipo" />
            <input value={triggerScene} onChange={(e) => setTriggerScene(e.target.value)} placeholder="scene" />
            <button type="button" onClick={() => void handleCreateTrigger()} disabled={!token || !tableId}>
              Criar Trigger
            </button>
          </div>
        </article>
      </section>

      <section className="users-panel">
        <header className="users-header">
          <div>
            <h2>Jogadores</h2>
            <p>Usuarios registrados na organizacao atual.</p>
          </div>
          <div className="users-actions">
            <button type="button" className="users-btn" onClick={() => setUsersOpen((v) => !v)}>
              {usersOpen ? "Colapsar" : "Expandir"}
            </button>
            <button
              type="button"
              className="users-btn"
              onClick={() => {
                if (token) void refreshUsers(token);
              }}
              disabled={!token || usersLoading}
              title={!token ? "Faça login como admin" : "Recarregar lista"}
            >
              {usersLoading ? "Carregando..." : "Recarregar"}
            </button>
          </div>
        </header>

        {usersOpen ? (
          <div className="users-table-wrap">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Nome</th>
                  <th>Role</th>
                  <th>Acoes</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="users-empty">
                      {token ? "Nenhum usuario listado." : "Faça login para listar usuarios."}
                    </td>
                  </tr>
                ) : (
                  users.map((user) => {
                    const isEditing = editingUserId === user.user_id;
                    return (
                      <tr key={user.user_id}>
                        <td className="mono">{user.email}</td>
                        <td>
                          {isEditing ? (
                            <input
                              value={editingName}
                              onChange={(e) => setEditingName(e.target.value)}
                            />
                          ) : (
                            user.display_name
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <select
                              value={editingRole}
                              onChange={(e) => setEditingRole(e.target.value)}
                            >
                              <option value="admin">admin</option>
                              <option value="narrator">narrator</option>
                              <option value="observer">observer</option>
                            </select>
                          ) : (
                            user.role
                          )}
                        </td>
                        <td className="users-row-actions">
                          {isEditing ? (
                            <>
                              <button
                                type="button"
                                className="row-btn"
                                onClick={() => setEditingUserId(null)}
                              >
                                Cancelar
                              </button>
                              <button
                                type="button"
                                className="row-btn primary"
                                onClick={() => {
                                  if (!token) return;
                                  void (async () => {
                                    try {
                                      const updated = await updateUser(user.user_id, token, {
                                        displayName: editingName,
                                        role: editingRole,
                                      });
                                      setUsers((cur) =>
                                        cur.map((u) => (u.user_id === updated.user_id ? updated : u))
                                      );
                                      setEditingUserId(null);
                                      setMessage("Usuario atualizado.");
                                    } catch {
                                      setMessage("Falha ao atualizar usuario.");
                                    }
                                  })();
                                }}
                              >
                                Salvar
                              </button>
                            </>
                          ) : (
                            <button
                              type="button"
                              className="row-btn"
                              onClick={() => {
                                setEditingUserId(user.user_id);
                                setEditingName(user.display_name);
                                setEditingRole(user.role);
                              }}
                              disabled={!token}
                            >
                              Editar
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="status-cards">
        <article>
          <h3>Conexao WS</h3>
          <p className={socket.connected ? "ok" : "warn"}>{socket.connected ? "online" : "offline"}</p>
        </article>
        <article>
          <h3>Mesa Atual</h3>
          <p>{tableId ?? "nao criada"}</p>
        </article>
        <article>
          <h3>Ultimo Evento</h3>
          <p>{lastEventLabel}</p>
        </article>
      </section>

      <section className="actions">
        <button type="button" onClick={() => void handleCreateTable()}>
          Criar Mesa
        </button>
        <div className="player-form">
          <input
            value={newPlayerName}
            onChange={(event) => setNewPlayerName(event.target.value)}
            placeholder="Nome do jogador"
          />
          <button type="button" onClick={() => void handleAddPlayer()} disabled={!tableId || !newPlayerName.trim()}>
            Adicionar Jogador
          </button>
        </div>
      </section>

      <SoundDesk tracks={TRACKS} onPlay={(trackId) => void handlePlay(trackId)} />

      <section className="players">
        <h2>LED de Jogadores</h2>
        <div className="player-list">
          {players.map((player) => (
            <PlayerLed
              key={player.id}
              name={player.display_name}
              availability={player.availability}
              onToggle={() => void handleTogglePlayer(player)}
            />
          ))}
        </div>
      </section>

      <footer className="message">{message}</footer>
    </main>
  );
}

