import { Availability } from "../../shared/api/client";
import "./PlayerLed.css";

type PlayerLedProps = {
  name: string;
  availability: Availability;
  onToggle: () => void;
};

export function PlayerLed({ name, availability, onToggle }: PlayerLedProps) {
  const isAvailable = availability === "green";
  return (
    <button className="player-led" onClick={onToggle} type="button">
      <span className={`led ${isAvailable ? "ok" : "danger"}`} />
      <span className="player-name">{name}</span>
      <span className="player-state">{isAvailable ? "Disponivel" : "Indisponivel"}</span>
    </button>
  );
}

