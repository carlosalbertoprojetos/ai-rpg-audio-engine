# RPGSoundDesk - Manual de Uso

## 1. Visao Geral

RPGSoundDesk e uma plataforma SaaS para mesas de RPG online com controle sonoro em tempo real, estados de jogadores por LED e automacao por eventos.

Recursos principais:
- Cadastro e login com JWT
- Gestao de mesa e jogadores
- Indicador LED por jogador (`green`/`red`)
- Sessao de jogo (`start`/`end`)
- Eventos sonoros agendados
- Registro de `AudioTrack`
- Criacao de `Trigger`
- Geracao de `AIContext`
- Gestao de `Organization` e plano de `Subscription`
- Auditoria de eventos

## 2. Requisitos

- Backend ativo (exemplo: `http://localhost:8010`)
- Frontend ativo (exemplo: `http://localhost:5173`)
- Navegador atualizado

## 3. Primeiro Acesso

1. Abra `http://localhost:5173`.
2. Preencha `E-mail`, `Nome de exibicao`, `Organizacao` e `Senha`.
3. Clique `Registrar`.
4. Clique `Login` (ou use o login automatico apos registrar).

Resultado esperado:
- LED de autenticacao fica verde.
- Operacoes protegidas ficam disponiveis.

## 4. Fluxo Operacional Recomendado

1. Criar mesa (`Criar Mesa`).
2. Iniciar sessao (`Iniciar Sessao`).
3. Adicionar jogadores.
4. Ajustar LEDs dos jogadores.
5. Registrar tracks de audio.
6. Criar triggers da mesa.
7. Gerar contexto de IA para a sessao.
8. Agendar eventos sonoros.
9. Encerrar sessao.
10. Consultar auditoria.

## 5. Modulos da Interface

### 5.1 Autenticacao
- Botao luminoso no topo:
  - verde: logado
  - vermelho: deslogado
- Tooltip do botao mostra status atual.

### 5.2 Organization e Subscription
- Exibe plano atual.
- Permite atualizar o plano da organizacao.
- Requer perfil `admin`.

### 5.3 Session
- `Iniciar Sessao` cria sessao para a mesa atual.
- `Encerrar Sessao` finaliza a sessao ativa.

### 5.4 Audio, Trigger e IA
- `AudioTrack`: registra metadados (`title`, `s3_key`, `duration`).
- `Trigger`: cria gatilhos por mesa.
- `AIContext`: gera sugestao de tags por `mood`.

### 5.5 Jogadores (Tabela)
- Lista usuarios registrados da organizacao.
- Botao `Editar` por linha para nome/role.
- Requer perfil `admin`.

### 5.6 LED de Jogadores
- Clique no card do jogador para alternar disponibilidade.
- Mudanca e publicada em tempo real por WebSocket.

### 5.7 Mesa de Som
- Botao `Play` agenda evento sonoro para a sessao ativa.
- Eventos executados sao exibidos no status de eventos.

## 6. Perfis e Permissoes

Perfis:
- `admin`
- `narrator`
- `observer`

Regras gerais:
- `admin`: acesso total (inclui usuarios e subscription).
- `narrator`: operacao de mesa/sessao/audio.
- `observer`: leitura.
- Escopo sempre limitado por `organization_id`.

## 7. Acesso por Outros Computadores

### 7.1 Mesma rede (LAN)

1. Rode backend/frontend no host com `0.0.0.0`.
2. Descubra o IP do host (exemplo: `192.168.0.50`).
3. Libere portas no firewall (`8010` e `5173`, conforme setup).
4. Nos outros computadores, abra `http://<IP_DO_HOST>:5173`.

Variaveis do frontend:
- `VITE_API_BASE_URL=http://<IP_DO_HOST>:8010/api/v1`
- `VITE_WS_BASE_URL=ws://<IP_DO_HOST>:8010`

### 7.2 Internet

Recomendacoes minimas:
- HTTPS/WSS com proxy reverso
- `JWT_SECRET` forte e privado
- CORS restritivo em producao

Observacao atual da UI:
- Ainda nao ha campo para "entrar em mesa existente por table_id" via link compartilhavel.

## 8. Troubleshooting

### 8.1 Registrar/Login nao acontece
- Verifique backend em `GET /api/v1/health`.
- Confirme `VITE_API_BASE_URL` e `VITE_WS_BASE_URL`.
- Veja a mensagem no rodape da tela (mostra detalhe da falha).

### 8.2 Tabela Jogadores vazia
- Endpoint exige token `admin`.
- Confirme login ativo (LED verde).
- Clique `Recarregar` na secao Jogadores.

### 8.3 Erro de permissao (403)
- Confira role do usuario.
- Confira se token e recurso pertencem a mesma organizacao.

### 8.4 Erro por pasta errada no terminal
- Backend: executar em `.../rpgsounddesk/backend`
- Frontend: executar em `.../rpgsounddesk/frontend`

## 9. Referencia Rapida de API

Autenticacao:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/token`

Usuarios:
- `GET /api/v1/users`
- `PATCH /api/v1/users/{user_id}`

Organizacao:
- `GET /api/v1/organizations/{organization_id}`
- `PATCH /api/v1/organizations/{organization_id}/subscription`

Mesa e Jogadores:
- `POST /api/v1/tables`
- `POST /api/v1/tables/{table_id}/players`
- `PATCH /api/v1/tables/{table_id}/players/{player_id}`

Sessao:
- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{session_id}/end`

Audio e IA:
- `POST /api/v1/sound-events`
- `POST /api/v1/audio-tracks`
- `GET /api/v1/audio-tracks`
- `POST /api/v1/triggers`
- `POST /api/v1/ai-contexts`

Auditoria:
- `GET /api/v1/audit/{organization_id}`

Health:
- `GET /api/v1/health`

## 10. Materiais de Apoio

- Tutoriais: `docs/tutorials/README.md`
- Script PowerShell: `scripts/demo_api.ps1`
- Script bash: `scripts/demo_api.sh`
- Postman: `docs/postman/RPGSoundDesk.postman_collection.json`

