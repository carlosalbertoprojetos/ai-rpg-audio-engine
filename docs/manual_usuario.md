# RPGSoundDesk - Manual de Instrucoes

## 1. Visao Geral

RPGSoundDesk e uma plataforma para narradores de RPG controlarem trilhas e efeitos sonoros em tempo real, com atualizacao de estado de jogadores e comunicacao via WebSocket.

Funcionalidades principais:
- Cadastro e login com JWT (seguranca por organizacao e perfil)
- Criacao de mesas de RPG
- Adicao de jogadores
- Indicadores LED de disponibilidade:
  - `verde`: disponivel
  - `vermelho`: indisponivel
- Agendamento de eventos sonoros (ex.: tocar trilha em horario definido)
- Auditoria de acoes

## 2. Requisitos

- Backend rodando (porta configurada, ex.: `8010`)
- Frontend rodando (normalmente `5173`)
- Navegador atualizado

## 3. Acesso ao Sistema

1. Abra o frontend no navegador: `http://localhost:5173`
2. Preencha:
   - Email
   - Nome de exibicao
   - Organizacao
   - Senha
3. Clique em `Registrar`
4. Clique em `Login`

Resultado esperado:
- O sistema gera token JWT e habilita operacoes protegidas.

## 3.1 Acesso por Outros Computadores (LAN/Internet)

Para usuarios em outros computadores acessarem a mesma mesa, o sistema precisa estar rodando em uma maquina "host" acessivel pela rede.

### Acesso na mesma rede (LAN)

1. Na maquina host, suba backend e frontend escutando em `0.0.0.0`.
2. Descubra o IP da maquina host (ex.: `192.168.0.50`).
3. Libere no firewall da maquina host as portas usadas (ex.: `8010` e `5173`).
4. Nos outros computadores, acesse:
   - Frontend: `http://<IP_DO_HOST>:5173`

Configuracao importante do frontend:
- `VITE_API_BASE_URL=http://<IP_DO_HOST>:8010/api/v1`
- `VITE_WS_BASE_URL=ws://<IP_DO_HOST>:8010`

### Acesso pela Internet

Recomendado apenas com HTTPS e proxy reverso (ex.: Nginx/Caddy), porque WebSocket e JWT trafegam dados sensiveis.

Boas praticas minimas:
- Usar dominio + TLS (HTTPS/WSS)
- Configurar proxy para WebSocket (upgrade headers)
- `JWT_SECRET` forte e privado
- Restringir CORS no backend (nao deixar `*` em producao)

### Como "ver a mesma mesa"

Conceito:
- Todos os usuarios devem estar na mesma `organization_id` (organizacao) e operar a mesma mesa pelo mesmo `table_id`.
- O backend envia eventos por WebSocket no endpoint `/api/v1/ws/tables/{table_id}?token=...`.

Limitacao atual da UI:
- A tela atual cria a mesa e guarda o `table_id` apenas em memoria do navegador.
- Usuarios em outros computadores ainda nao tem um campo "Entrar em mesa" para informar um `table_id` existente.

Workarounds (sem mudar codigo):
- Usar a mesma maquina/navegador para controlar a mesa.
- Usar chamadas diretas de API/WebSocket (via ferramentas como Postman/Insomnia) apontando para o `table_id`.

Se voce quiser, eu adiciono no frontend:
- Campo para colar `table_id` e "Entrar em mesa"
- Link compartilhavel (ex.: `http://<host>:5173/?table_id=...`) para abrir a mesa direto

## 4. Criando e Gerenciando Mesas

1. Clique em `Criar Mesa`
2. O sistema exibira o ID da mesa atual
3. Para adicionar jogadores:
   - Digite o nome do jogador
   - Clique em `Adicionar Jogador`

## 5. LEDs de Jogadores

Cada jogador possui um LED visual:
- Verde: jogador disponivel
- Vermelho: jogador indisponivel

Como alterar:
1. Clique no card do jogador
2. O estado alterna entre verde e vermelho
3. A mudanca e propagada em tempo real

## 6. Mesa de Som

A tela `Mesa de Som` permite controlar trilhas.

Como usar:
1. Com mesa criada, clique em `Play` na trilha desejada
2. O sistema agenda um evento sonoro
3. O worker executa o evento e publica notificacao em tempo real

## 7. Eventos em Tempo Real

O sistema usa WebSocket por mesa:
- Exibe conexao `online/offline`
- Mostra `Ultimo Evento` recebido

Eventos comuns:
- `table.created`
- `player.added`
- `player.availability.updated`
- `sound.event.scheduled`
- `sound.event.executed`

## 8. Perfis e Permissoes

Perfis suportados:
- `admin`
- `narrator`
- `observer`

Regras gerais:
- `admin` e `narrator`: operacoes de escrita (mesa, jogador, eventos)
- `observer`: leitura (ex.: auditoria, acompanhamento)
- Acoes sao isoladas por `organization_id`

## 9. Auditoria

Toda acao relevante gera registro de auditoria, como:
- Criacao de mesa
- Adicao de jogador
- Mudanca de disponibilidade
- Agendamento de evento sonoro

Consulta via API:
- `GET /api/v1/audit/{organization_id}`

## 10. Fluxo Recomendado de Uso

1. Registrar usuario
2. Fazer login
3. Criar mesa
4. Adicionar jogadores
5. Atualizar LEDs conforme status dos jogadores
6. Acionar trilhas/eventos durante a sessao
7. Consultar auditoria quando necessario

## 11. Solucao de Problemas

### 11.1 Frontend nao conecta no backend

Verifique variaveis do frontend:
- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`

Exemplo:
- `VITE_API_BASE_URL=http://localhost:8010/api/v1`
- `VITE_WS_BASE_URL=ws://localhost:8010`

### 11.2 Erro de autenticacao

- Refaça `Login`
- Confirme email/senha/organizacao corretos
- Verifique se o usuario foi registrado antes

### 11.3 Acoes bloqueadas por permissao

- Confirme o perfil (`admin`, `narrator`, `observer`)
- Confirme se a organizacao do token e a mesma da mesa

### 11.4 Comandos executados na pasta errada

- Backend: execute em `.../rpgsounddesk/backend`
- Frontend: execute em `.../rpgsounddesk/frontend`

## 12. Referencia Rapida de APIs

Autenticacao:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/token`

Mesa e jogadores:
- `POST /api/v1/tables`
- `POST /api/v1/tables/{table_id}/players`
- `PATCH /api/v1/tables/{table_id}/players/{player_id}`

Audio:
- `POST /api/v1/sound-events`

Auditoria:
- `GET /api/v1/audit/{organization_id}`

Healthcheck:
- `GET /api/v1/health`

## 13. Tutoriais e Demos

Tutoriais passo a passo:
- `docs/tutorials/README.md`

Scripts de demonstracao:
- `scripts/demo_api.ps1` (PowerShell)
- `scripts/demo_api.sh` (bash)

Colecao Postman:
- `docs/postman/RPGSoundDesk.postman_collection.json`
