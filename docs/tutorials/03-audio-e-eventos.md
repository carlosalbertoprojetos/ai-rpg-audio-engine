# Tutorial 03 - Audio e Eventos

Objetivo: tocar uma trilha real (via agendamento) e confirmar execucao em tempo real.

## Passo a passo

1. Conclua o Tutorial 02 (autenticado, mesa criada e sessao iniciada)
2. Na secao `Audio Tracks`, envie um arquivo de audio (`audio/*`) e clique `Registrar`
3. Na `Mesa de Som`, clique `Play` na trilha enviada
4. Aguarde alguns segundos

## Resultado esperado

- O backend agenda `sound.event.scheduled`
- O worker executa e publica `sound.event.executed`
- O frontend mostra `Ultimo Evento` mudando (executed)
- O frontend reproduz o audio do `target_track_id` via endpoint de stream autenticado
