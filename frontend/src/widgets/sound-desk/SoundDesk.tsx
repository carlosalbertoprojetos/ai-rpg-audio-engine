import { useMemo } from "react";
import "./SoundDesk.css";

type Track = {
  id: string;
  title: string;
  level: number;
};

type SoundDeskProps = {
  tracks: Track[];
  onPlay: (trackId: string) => void;
};

export function SoundDesk({ tracks, onPlay }: SoundDeskProps) {
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
          <article className="track-strip" key={track.id} style={{ animationDelay: `${index * 70}ms` }}>
            <button type="button" className="play-btn" onClick={() => onPlay(track.id)}>
              Play
            </button>
            <div className="fader-column">
              <div className="meter">
                <div className="meter-fill" style={{ height: `${meters[index]?.level ?? 0}%` }} />
              </div>
              <input type="range" min={0} max={100} value={track.level} readOnly />
            </div>
            <p className="track-title">{track.title}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

