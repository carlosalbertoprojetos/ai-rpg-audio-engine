import { useMemo, useState } from "react";
import {
  Availability,
  Player,
  addPlayer,
  createTable,
  issueToken,
  registerUser,
  scheduleSoundEvent,
  updatePlayerAvailability,
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

  const socket = useTableSocket(tableId, token);

  const lastEventLabel = useMemo(() => {
    if (!socket.lastEvent) {
      return "Sem eventos recentes";
    }
    return `${socket.lastEvent.event_type} @ ${new Date(socket.lastEvent.occurred_at).toLocaleTimeString()}`;
  }, [socket.lastEvent]);

  async function handleRegister() {
    try {
      await registerUser({
        email,
        displayName,
        password,
        organizationId,
        role: "admin",
      });
      setMessage("Usuario registrado com sucesso.");
    } catch {
      setMessage("Falha ao registrar usuario.");
    }
  }

  async function handleLogin() {
    try {
      const nextToken = await issueToken({ email, password, organizationId });
      setToken(nextToken);
      setMessage("Autenticado com sucesso.");
    } catch {
      setMessage("Falha de autenticacao.");
    }
  }

  function handleLogout() {
    setToken(null);
    setTableId(null);
    setPlayers([]);
    setMessage("Deslogado.");
  }

  async function handleCreateTable() {
    if (!token) {
      setMessage("Autentique antes de criar mesa.");
      return;
    }
    try {
      const table = await createTable("Mesa Principal", token);
      setTableId(table.id);
      setMessage(`Mesa criada: ${table.id}`);
    } catch {
      setMessage("Falha ao criar mesa.");
    }
  }

  async function handleAddPlayer() {
    if (!tableId || !token) {
      return;
    }
    try {
      const created = await addPlayer(tableId, newPlayerName, token);
      setPlayers((current) => [...current, created]);
      setNewPlayerName("");
    } catch {
      setMessage("Falha ao adicionar jogador.");
    }
  }

  async function handleTogglePlayer(player: Player) {
    if (!tableId || !token) {
      return;
    }
    const nextAvailability: Availability = player.availability === "green" ? "red" : "green";
    try {
      const updated = await updatePlayerAvailability(tableId, player.id, nextAvailability, token);
      setPlayers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch {
      setMessage("Falha ao atualizar estado do jogador.");
    }
  }

  async function handlePlay(trackId: string) {
    if (!tableId || !token) {
      setMessage("Crie uma mesa e autentique antes de tocar trilhas.");
      return;
    }
    const executeAt = new Date(Date.now() + 1000).toISOString();
    try {
      await scheduleSoundEvent({
        token,
        tableId,
        sessionId: "session-demo",
        action: `play:${trackId}`,
        executeAt,
      });
      setMessage(`Evento agendado para trilha ${trackId}.`);
    } catch {
      setMessage("Falha ao agendar evento sonoro.");
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
            onClick={() => {
              if (token) {
                handleLogout();
              } else {
                setMessage("Deslogado. Registre e faca login.");
              }
            }}
            title={token ? `Logado como ${email} (${organizationId})` : "Deslogado"}
            aria-label={token ? "Usuario logado" : "Usuario deslogado"}
          >
            <span className="auth-led" aria-hidden="true" />
            <span className="auth-text">{token ? "Logado" : "Deslogado"}</span>
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
          Registrar
        </button>
        <button
          type="button"
          onClick={() => {
            if (token) {
              handleLogout();
            } else {
              void handleLogin();
            }
          }}
        >
          {token ? "Logout" : "Login"}
        </button>
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
        <button type="button" onClick={handleCreateTable}>
          Criar Mesa
        </button>
        <div className="player-form">
          <input
            value={newPlayerName}
            onChange={(event) => setNewPlayerName(event.target.value)}
            placeholder="Nome do jogador"
          />
          <button type="button" onClick={handleAddPlayer} disabled={!tableId || !newPlayerName.trim()}>
            Adicionar Jogador
          </button>
        </div>
      </section>

      <SoundDesk tracks={TRACKS} onPlay={handlePlay} />

      <section className="players">
        <h2>LED de Jogadores</h2>
        <div className="player-list">
          {players.map((player) => (
            <PlayerLed
              key={player.id}
              name={player.display_name}
              availability={player.availability}
              onToggle={() => {
                void handleTogglePlayer(player);
              }}
            />
          ))}
        </div>
      </section>

      <footer className="message">{message}</footer>
    </main>
  );
}
