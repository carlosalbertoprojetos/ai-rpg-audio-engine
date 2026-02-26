# Tutorial 04 - Acesso na LAN (Multiplos PCs)

Objetivo: permitir que outros computadores na mesma rede abram o frontend e acompanhem eventos da mesa.

## Preparacao (na maquina host)

1. Suba backend e frontend escutando em `0.0.0.0`.
2. Descubra o IP do host:
   - Windows: `ipconfig` e procure o IPv4, ex.: `192.168.0.50`
3. Libere firewall para:
   - porta do backend (ex.: `8010` ou `8000` no Docker)
   - porta do frontend (`5173`)

## Acesso (nos outros PCs)

1. Acesse no navegador:
   - `http://<IP_DO_HOST>:5173`
2. Configure as variaveis do frontend (se voce roda `npm run dev` no host):
   - `VITE_API_BASE_URL=http://<IP_DO_HOST>:8010/api/v1`
   - `VITE_WS_BASE_URL=ws://<IP_DO_HOST>:8010`

## Importante: entrar na mesma mesa

Para ser a "mesma mesa", os usuarios precisam:
- Estar na mesma `organization_id`
- Usar o mesmo `table_id`

Limitacao atual da UI:
- Ainda nao existe um campo "Entrar em mesa" por `table_id`.
- O host cria a mesa e mantem o `table_id` apenas na sessao do navegador.

Alternativas:
- Operar a mesa pelo host e os outros PCs acompanharem via API/WS (ver Tutorial 05)
- Implementar "entrar na mesa" e link compartilhavel (futuro)

