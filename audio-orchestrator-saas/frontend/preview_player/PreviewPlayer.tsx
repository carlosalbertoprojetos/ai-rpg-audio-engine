type LayerPreview = {
  layer_id: string;
  label: string;
  provider: string;
  volume: number;
};

type Props = {
  audioUrl: string | null;
  apiBaseUrl: string;
  layers: LayerPreview[];
};

export function PreviewPlayer({ audioUrl, apiBaseUrl, layers }: Props) {
  if (!audioUrl) {
    return <p>No scene generated yet.</p>;
  }

  return (
    <section>
      <h2>Audio Preview</h2>
      <audio controls preload="metadata" src={`${apiBaseUrl.replace(/\/$/, "")}${audioUrl}`} />
      <ul>
        {layers.map((layer) => (
          <li key={layer.layer_id}>
            {layer.label} | provider={layer.provider} | volume={layer.volume.toFixed(2)}
          </li>
        ))}
      </ul>
    </section>
  );
}
