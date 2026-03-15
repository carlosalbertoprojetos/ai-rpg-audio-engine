import { useMemo, useState } from "react";

export type LayerPreview = {
  layer_id: string;
  label: string;
  provider: string;
  volume: number;
};

export type SceneResponse = {
  scene_id: string;
  audio_url: string;
  output_format: string;
  layers: LayerPreview[];
};

type Props = {
  apiBaseUrl: string;
  onGenerated: (scene: SceneResponse) => void;
};

export function SceneBuilder({ apiBaseUrl, onGenerated }: Props) {
  const [prompt, setPrompt] = useState("Medieval forest ambience with distant battle");
  const [outputFormat, setOutputFormat] = useState("wav");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Ready");

  const canSubmit = useMemo(() => prompt.trim().length >= 3 && !busy, [prompt, busy]);

  async function handleGenerate() {
    if (!canSubmit) return;
    setBusy(true);
    setMessage("Generating scene...");
    try {
      const response = await fetch(`${apiBaseUrl}/generate-audio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, output_format: outputFormat }),
      });
      const payload = (await response.json()) as SceneResponse | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : `HTTP ${response.status}`);
      }
      onGenerated(payload as SceneResponse);
      setMessage("Scene generated");
    } catch (error) {
      const text = error instanceof Error ? error.message : "unknown error";
      setMessage(`Generation failed: ${text}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Scene Builder</h2>
      <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={4} />
      <div>
        <label htmlFor="format">Output format</label>
        <select id="format" value={outputFormat} onChange={(event) => setOutputFormat(event.target.value)}>
          <option value="wav">wav</option>
          <option value="mp3">mp3</option>
          <option value="ogg">ogg</option>
        </select>
      </div>
      <button type="button" disabled={!canSubmit} onClick={() => void handleGenerate()}>
        {busy ? "Generating..." : "Generate Audio"}
      </button>
      <p>{message}</p>
    </section>
  );
}
