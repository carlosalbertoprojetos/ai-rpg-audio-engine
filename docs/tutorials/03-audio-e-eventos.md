# Tutorial 03 - Audio e Eventos

Objetivo: tocar uma trilha (via agendamento) e confirmar execucao em tempo real.

## Passo a passo

1. Conclua o Tutorial 02 (precisa estar autenticado e com mesa criada)
2. Em `Mesa de Som`, clique `Play` em uma trilha
3. Aguarde alguns segundos

## Resultado esperado

- O backend agenda `sound.event.scheduled`
- O worker executa e publica `sound.event.executed`
- O frontend mostra `Ultimo Evento` mudando (executed)

Observacao:
- Nesta fase, "tocar" e um evento logico (nao ha engine de audio real no backend)

