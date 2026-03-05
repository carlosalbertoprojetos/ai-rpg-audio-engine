import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AIContextInfo,
  AudioTrackInfo,
  Availability,
  OrganizationInfo,
  Player,
  RegisteredUser,
  SessionInfo,
  addPlayer,
  buildAudioStreamUrl,
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
  uploadAudioTrackFile,
  updatePlayerAvailability,
  updateSubscriptionPlan,
  updateUser,
} from "../shared/api/client";
import { useTableSocket } from "../shared/ws/useTableSocket";
import { PlayerLed } from "../widgets/player-led/PlayerLed";
import { SoundDesk } from "../widgets/sound-desk/SoundDesk";
import "./DeskPage.css";

type SoundChannelTemplate = {
  id: string;
  title: string;
  category: string;
  description: string;
  defaultLevel: number;
  keywords: string[];
};

type SoundDeskChannel = {
  id: string;
  title: string;
  category: string;
  description: string;
  level: number;
  canPlay: boolean;
  isActive: boolean;
  sourceTrackId?: string;
};

type BlockedPlayback = {
  src: string;
  volume: number;
  channelId: string | null;
  title: string;
};

const SOUND_CHANNEL_TEMPLATES: SoundChannelTemplate[] = [
  {
    id: "amb-forest",
    title: "Floresta Viva",
    category: "Ambiente",
    description: "Camada de vento, folhas e vida selvagem.",
    defaultLevel: 46,
    keywords: ["forest", "floresta", "nature", "natureza", "wind", "vento"],
  },
  {
    id: "amb-cave",
    title: "Caverna Profunda",
    category: "Ambiente",
    description: "Textura subterranea com gotejamento e eco.",
    defaultLevel: 38,
    keywords: ["cave", "caverna", "dungeon", "echo", "subterraneo"],
  },
  {
    id: "amb-city",
    title: "Cidade Noturna",
    category: "Ambiente",
    description: "Movimento urbano e murmurio de fundo.",
    defaultLevel: 42,
    keywords: ["city", "cidade", "market", "vila", "street", "taverna"],
  },
  {
    id: "bg-battle",
    title: "Linha de Combate",
    category: "Trilha",
    description: "Base ritmica para cenas de acao.",
    defaultLevel: 64,
    keywords: ["battle", "combat", "fight", "boss", "war", "acao"],
  },
  {
    id: "fx-magic",
    title: "Efeito Magico",
    category: "Efeito",
    description: "Entrada para conjuracoes, portais e rituais.",
    defaultLevel: 58,
    keywords: ["magic", "spell", "arcane", "ritual", "mystic", "magia"],
  },
  {
    id: "fx-suspense",
    title: "Tensao",
    category: "Efeito",
    description: "Pulso grave para investigacao e suspense.",
    defaultLevel: 55,
    keywords: ["suspense", "mystery", "dark", "tense", "drone", "terror"],
  },
];

export function DeskPage() {
  const [tableId, setTableId] = useState<string | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");

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
  const [trackDuration, setTrackDuration] = useState(180);
  const [trackFile, setTrackFile] = useState<File | null>(null);
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
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blockedPlaybackRef = useRef<BlockedPlayback | null>(null);
  const [autoplayBlocked, setAutoplayBlocked] = useState(false);
  const [channelLevels, setChannelLevels] = useState<Record<string, number>>({});
  const [activeChannelId, setActiveChannelId] = useState<string | null>(null);

  const lastEventLabel = useMemo(() => {
    if (!socket.lastEvent) return "Sem eventos recentes";
    return `${socket.lastEvent.event_type} @ ${new Date(socket.lastEvent.occurred_at).toLocaleTimeString()}`;
  }, [socket.lastEvent]);

  const soundDeskTracks = useMemo(() => {
    const normalizedTracks = audioTracks.map((track) => ({
      ...track,
      normalizedTitle: track.title.toLowerCase(),
    }));
    const claimedTrackIds = new Set<string>();

    function claimByKeywords(keywords: string[]): AudioTrackInfo | undefined {
      const keywordSet = keywords.map((keyword) => keyword.toLowerCase());
      const exactMatch = normalizedTracks.find(
        (track) =>
          !claimedTrackIds.has(track.id) &&
          keywordSet.some((keyword) => track.normalizedTitle.includes(keyword))
      );
      if (exactMatch) {
        claimedTrackIds.add(exactMatch.id);
        return exactMatch;
      }
      const fallback = normalizedTracks.find((track) => !claimedTrackIds.has(track.id));
      if (fallback) {
        claimedTrackIds.add(fallback.id);
      }
      return fallback;
    }

    const channels: SoundDeskChannel[] = SOUND_CHANNEL_TEMPLATES.map((template) => {
      const linkedTrack = claimByKeywords(template.keywords);
      const baseDescription = linkedTrack
        ? `${template.description} Vinculada: ${linkedTrack.title}.`
        : `${template.description} Sem trilha vinculada no momento.`;
      return {
        id: template.id,
        title: template.title,
        category: template.category,
        description: baseDescription,
        level: channelLevels[template.id] ?? template.defaultLevel,
        canPlay: Boolean(linkedTrack),
        isActive: activeChannelId === template.id,
        sourceTrackId: linkedTrack?.id,
      };
    });

    const extraTracks = normalizedTracks
      .filter((track) => !claimedTrackIds.has(track.id))
      .map((track, index) => {
        const channelId = `custom-${track.id}`;
        return {
          id: channelId,
          title: track.title,
          category: "Biblioteca",
          description: "Faixa adicional da biblioteca registrada.",
          level: channelLevels[channelId] ?? (45 + (index % 5) * 8),
          canPlay: true,
          isActive: activeChannelId === channelId,
          sourceTrackId: track.id,
        };
      });

    return [...channels, ...extraTracks];
  }, [audioTracks, channelLevels, activeChannelId]);

  const channelMap = useMemo(
    () => new Map(soundDeskTracks.map((track) => [track.id, track])),
    [soundDeskTracks]
  );

  const sourceTrackToChannel = useMemo(() => {
    const map = new Map<string, string>();
    soundDeskTracks.forEach((track) => {
      if (track.sourceTrackId) {
        map.set(track.sourceTrackId, track.id);
      }
    });
    return map;
  }, [soundDeskTracks]);

  const stopCurrentAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (blockedPlaybackRef.current) {
      blockedPlaybackRef.current = null;
    }
    setAutoplayBlocked(false);
    setActiveChannelId(null);
  }, []);

  function describePlaybackError(error: unknown): string {
    if (error instanceof DOMException) {
      return `${error.name}: ${error.message}`.trim();
    }
    if (error instanceof Error) {
      return error.message;
    }
    return "erro desconhecido de reproducao";
  }

  async function probeAudioStream(src: string): Promise<{ ok: true } | { ok: false; detail: string }> {
    async function validateResponse(response: Response): Promise<{ ok: true } | { ok: false; detail: string }> {
      if (!response.ok) {
        return { ok: false, detail: `stream HTTP ${response.status}` };
      }
      const contentType = (response.headers.get("content-type") ?? "").toLowerCase();
      if (!contentType.startsWith("audio/")) {
        return {
          ok: false,
          detail: `stream sem tipo de audio (${contentType || "desconhecido"})`,
        };
      }
      return { ok: true };
    }

    try {
      const response = await fetch(src, { method: "HEAD" });
      if (response.status === 405) {
        const fallback = await fetch(src, {
          method: "GET",
          headers: { Range: "bytes=0-1" },
        });
        return validateResponse(fallback);
      }
      return validateResponse(response);
    } catch (error) {
      return { ok: false, detail: `erro de rede (${describePlaybackError(error)})` };
    }
  }

  async function unlockAudioContext(): Promise<void> {
    const contextCtor =
      window.AudioContext ??
      ((window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext ??
        null);
    if (!contextCtor) return;
    const ctx = new contextCtor();
    if (ctx.state === "suspended") {
      await ctx.resume();
    }
    const buffer = ctx.createBuffer(1, 1, 22050);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    source.start(0);
    source.stop(0);
    await ctx.close();
  }

  const retryBlockedPlayback = useCallback(async () => {
    const blocked = blockedPlaybackRef.current;
    if (!blocked) {
      return false;
    }
    try {
      const probe = await probeAudioStream(blocked.src);
      if (!probe.ok) {
        setMessage(`Falha ao retomar '${blocked.title}' (${probe.detail}).`);
        return false;
      }
      await unlockAudioContext();
      const player = new Audio(blocked.src);
      player.volume = blocked.volume;
      await player.play();
      audioRef.current = player;
      setActiveChannelId(blocked.channelId);
      setAutoplayBlocked(false);
      blockedPlaybackRef.current = null;
      setMessage(`Reproducao retomada: ${blocked.title}.`);
      return true;
    } catch (error) {
      setMessage(`Falha ao retomar audio (${describePlaybackError(error)}).`);
      return false;
    }
  }, []);

  useEffect(() => {
    if (!autoplayBlocked) {
      return;
    }
    const onUserInteraction = () => {
      void retryBlockedPlayback();
    };
    window.addEventListener("pointerdown", onUserInteraction);
    window.addEventListener("keydown", onUserInteraction);
    return () => {
      window.removeEventListener("pointerdown", onUserInteraction);
      window.removeEventListener("keydown", onUserInteraction);
    };
  }, [autoplayBlocked, retryBlockedPlayback]);

  useEffect(() => {
    const event = socket.lastEvent;
    if (!event || event.event_type !== "sound.event.executed") {
      return;
    }

    const action = event.payload.action;
    if (action === "stop_track") {
      stopCurrentAudio();
      setMessage("Reproducao interrompida.");
      return;
    }

    if (action !== "play_track" || !token) {
      return;
    }

    const sourceTrackId = event.payload.target_track_id;
    if (!sourceTrackId) {
      return;
    }

    const channelId = sourceTrackToChannel.get(sourceTrackId) ?? null;
    const channelTitle = channelMap.get(channelId ?? "")?.title ?? "trilha";
    const currentLevel = channelId ? (channelLevels[channelId] ?? 50) : 50;
    const src = buildAudioStreamUrl(sourceTrackId, token);
    stopCurrentAudio();
    void (async () => {
      const probe = await probeAudioStream(src);
      if (!probe.ok) {
        setMessage(`Falha ao reproduzir '${channelTitle}' (${probe.detail}).`);
        setAutoplayBlocked(false);
        setActiveChannelId(null);
        return;
      }

      const player = new Audio(src);
      player.volume = Math.min(1, Math.max(0, currentLevel / 100));

      void player.play()
        .then(() => {
          audioRef.current = player;
          setActiveChannelId(channelId);
        })
        .catch((error) => {
          if (error instanceof DOMException && error.name === "NotAllowedError") {
            blockedPlaybackRef.current = {
              src,
              volume: player.volume,
              channelId,
              title: channelTitle,
            };
            setAutoplayBlocked(true);
            setMessage(
              "Evento executado, mas navegador bloqueou autoplay. Clique na pagina para retomar automaticamente."
            );
            return;
          }
          setMessage(`Falha ao reproduzir '${channelTitle}' (${describePlaybackError(error)}).`);
          setAutoplayBlocked(false);
          setActiveChannelId(null);
        });
    })();
  }, [socket.lastEvent, token, channelLevels, sourceTrackToChannel, stopCurrentAudio, channelMap]);

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
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedOrganization = organizationId.trim();
    try {
      await registerUser({
        email: normalizedEmail,
        displayName: displayName.trim(),
        password,
        organizationId: normalizedOrganization,
        role: "admin",
      });
      const nextToken = await issueToken({
        email: normalizedEmail,
        password,
        organizationId: normalizedOrganization,
      });
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
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedOrganization = organizationId.trim();
    try {
      const nextToken = await issueToken({
        email: normalizedEmail,
        password,
        organizationId: normalizedOrganization,
      });
      setToken(nextToken);
      setMessage("Autenticado com sucesso.");
      await Promise.all([refreshUsers(nextToken), refreshEnterprise(nextToken)]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      if (String(detail).toLowerCase().includes("invalid credentials")) {
        setMessage(
          "Falha de autenticacao: credenciais invalidas. Registre o usuario primeiro ou confira email, senha e organizacao."
        );
      } else {
        setMessage(`Falha de autenticacao: ${detail}`);
      }
    } finally {
      setAuthBusy(null);
    }
  }

  function handleLogout() {
    stopCurrentAudio();
    setToken(null);
    setTableId(null);
    setPlayers([]);
    setUsers([]);
    setEditingUserId(null);
    setOrganization(null);
    setSession(null);
    setAudioTracks([]);
    setChannelLevels({});
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
    const selectedUser = users.find((user) => user.user_id === selectedUserId);
    if (!selectedUser) {
      setMessage("Selecione um jogador registrado antes de adicionar.");
      return;
    }
    try {
      const created = await addPlayer(tableId, selectedUser.display_name, token);
      setPlayers((current) => [...current, created]);
      setSelectedUserId("");
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

  async function handlePlay(channelId: string) {
    const channel = channelMap.get(channelId);
    if (!channel) {
      return;
    }
    if (!channel.sourceTrackId) {
      setMessage(`Canal '${channel.title}' sem trilha vinculada. Registre mais audios para habilitar.`);
      return;
    }
    if (!tableId || !token || !session) {
      return setMessage("Crie mesa e inicie sessao antes de tocar trilhas.");
    }
    const executeAt = new Date(Date.now() + 1000).toISOString();
    try {
      await scheduleSoundEvent({
        token,
        tableId,
        sessionId: session.id,
        action: "play_track",
        executeAt,
        targetTrackId: channel.sourceTrackId,
      });
      setActiveChannelId(channelId);
      setMessage(`Evento agendado para '${channel.title}'.`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao agendar evento sonoro: ${detail}`);
    }
  }

  async function handleStop(channelId: string) {
    const channel = channelMap.get(channelId);
    if (!channel) {
      return;
    }

    stopCurrentAudio();

    if (!tableId || !token || !session) {
      setMessage(`Reproducao local de '${channel.title}' interrompida.`);
      return;
    }

    const executeAt = new Date(Date.now() + 350).toISOString();
    try {
      await scheduleSoundEvent({
        token,
        tableId,
        sessionId: session.id,
        action: "stop_track",
        executeAt,
        targetTrackId: channel.sourceTrackId,
      });
      setMessage(`Parada agendada para '${channel.title}'.`);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "erro desconhecido";
      setMessage(`Falha ao enviar stop: ${detail}`);
    }
  }

  function handleChannelLevelChange(channelId: string, level: number) {
    setChannelLevels((current) => ({ ...current, [channelId]: level }));
    if (activeChannelId === channelId && audioRef.current) {
      audioRef.current.volume = Math.min(1, Math.max(0, level / 100));
    }
  }

  async function handleCreateTrack() {
    if (!token) return;
    if (!trackFile) {
      setMessage("Selecione um arquivo de audio para upload.");
      return;
    }
    try {
      const created = await uploadAudioTrackFile(
        { title: trackTitle, durationSeconds: trackDuration, file: trackFile },
        token
      );
      setAudioTracks((cur) => [created, ...cur]);
      setTrackFile(null);
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

      <form
        className="auth-grid"
        onSubmit={(event) => {
          event.preventDefault();
          if (token) {
            handleLogout();
          } else {
            void handleLogin();
          }
        }}
      >
        <input
          type="email"
          name="username"
          autoComplete="username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="E-mail"
        />
        <input
          name="display_name"
          autoComplete="name"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Nome de exibicao"
        />
        <input
          name="organization_id"
          autoComplete="organization"
          value={organizationId}
          onChange={(event) => setOrganizationId(event.target.value)}
          placeholder="Organizacao"
        />
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Senha"
        />
        <button type="button" onClick={handleRegister}>
          {authBusy === "register" ? "Registrando..." : "Registrar"}
        </button>
        <button
          type="submit"
          disabled={authBusy === "register" || authBusy === "login"}
        >
          {token ? "Logout" : authBusy === "login" ? "Entrando..." : "Login"}
        </button>
      </form>

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
            <input
              type="number"
              value={trackDuration}
              onChange={(e) => setTrackDuration(Number(e.target.value))}
              placeholder="duracao"
            />
            <input
              type="file"
              accept="audio/*"
              onChange={(e) => setTrackFile(e.target.files?.[0] ?? null)}
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
          <select
            value={selectedUserId}
            onChange={(event) => setSelectedUserId(event.target.value)}
            disabled={!users.length}
          >
            <option value="">Selecione um jogador</option>
            {users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.display_name}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => void handleAddPlayer()} disabled={!tableId || !selectedUserId}>
            Adicionar Jogador
          </button>
        </div>
      </section>

      <SoundDesk
        tracks={soundDeskTracks}
        onPlay={(trackId) => void handlePlay(trackId)}
        onStop={(trackId) => void handleStop(trackId)}
        onLevelChange={handleChannelLevelChange}
      />

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

      <footer className="message">
        <span>{message}</span>
        {autoplayBlocked ? (
          <button type="button" onClick={() => void retryBlockedPlayback()}>
            Retomar audio
          </button>
        ) : null}
      </footer>
    </main>
  );
}
