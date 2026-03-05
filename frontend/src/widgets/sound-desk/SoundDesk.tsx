import { useMemo } from "react";
import "./SoundDesk.css";

type Track = {
  id: string;
  title: string;
  level: number;
  category: string;
  description: string;
  canPlay: boolean;
  isActive: boolean;
};

type SoundDeskProps = {
  tracks: Track[];
  onPlay: (trackId: string) => void;
  onStop: (trackId: string) => void;
  onLevelChange: (trackId: string, level: number) => void;
};

export function SoundDesk({ tracks, onPlay, onStop, onLevelChange }: SoundDeskProps) {
  const meters = useMemo(
    () =>
      tracks.map((track) => ({
        id: track.id,
        level: Math.round(track.level * 10),
      })),
    [tracks]
  );

  return (
    <section className="sound-desk">
      <header>
        <h2>Mesa de Som</h2>
        <p>Ambiente ao vivo com trilhas e efeitos sincronizados.</p>
      </header>
      <div className="track-grid">
        {tracks.map((track, index) => (
          <article
            className={`track-strip ${track.isActive ? "active" : ""}`}
            key={track.id}
            style={{ animationDelay: `${index * 70}ms` }}
          >
            <p className="track-category">{track.category}</p>
            <div className="track-actions">
              <button
                type="button"
                className="play-btn"
                onClick={() => onPlay(track.id)}
                title={track.canPlay ? "Tocar faixa" : "Sem arquivo vinculado para esta opcao"}
              >
                Play
              </button>
              <button
                type="button"
                className="stop-btn"
                onClick={() => onStop(track.id)}
                disabled={!track.isActive}
                title={track.isActive ? "Parar reproducao" : "Nenhuma reproducao ativa"}
              >
                Stop
              </button>
            </div>
            <div className="fader-column">
              <div className="meter">
                <div className="meter-fill" style={{ height: `${meters[index]?.level ?? 0}%` }} />
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={track.level}
                onChange={(event) => onLevelChange(track.id, Number(event.target.value))}
                aria-label={`Volume da faixa ${track.title}`}
              />
            </div>
            <p className="track-title">{track.title}</p>
            <p className="track-desc">{track.description}</p>
            <p className="track-level">{track.level}%</p>
          </article>
        ))}
      </div>
    </section>
  );
}
