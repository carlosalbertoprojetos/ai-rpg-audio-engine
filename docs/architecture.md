# RPGSoundDesk - Fase 1 (Planejamento Arquitetural)

## 1. Analise

RPGSoundDesk e uma plataforma SaaS para narradores de RPG que exige baixa latencia, auditabilidade e isolamento entre organizacoes. O sistema precisa suportar controle sonoro em tempo real, eventos programados e dinamicos por IA, multiplas mesas simultaneas e atualizacoes visuais de estado de jogadores.

Diretrizes obrigatorias:
- DDD + Clean Architecture
- Isolamento entre dominio e infraestrutura
- Tipagem forte e testes unitarios/integracao
- Observabilidade e logs estruturados

## 2. Arquitetura

### 2.1 Mapa de dominios e bounded contexts

- Identity & Access
  - User
  - Organization
  - Subscription
- Table Operations
  - Table
  - Session
  - Player
- Audio Orchestration
  - AudioTrack
  - SoundEvent
  - Trigger
  - AIContext
- Governance
  - AuditLog

### 2.2 Entidades e agregados

- UserAggregate
  - User (root): id, email, display_name, status, roles
- OrganizationAggregate
  - Organization (root): id, name, owner_user_id, plan, status
  - Subscription (entity): plan, billing_cycle, renew_at, status
- TableAggregate
  - Table (root): id, organization_id, name, mode, state
  - Player (entity): id, table_id, user_id/null, display_name, availability
- SessionAggregate
  - Session (root): id, table_id, started_at, ended_at, state
- AudioAggregate
  - AudioTrack (root): id, organization_id, s3_key, metadata
  - SoundEvent (entity): id, session_id, track_id/effect, execute_at, state
  - Trigger (entity): id, table_id, condition_type, payload
  - AIContext (value/object + entity): session snapshot and recommended ambience
- AuditAggregate
  - AuditLog (root): id, organization_id, actor_id, action, target, timestamp, data

### 2.3 Casos de uso por contexto

- Identity & Access
  - RegisterOrganization
  - InviteUserToOrganization
  - AssignRole
  - ChangeSubscriptionPlan
- Table Operations
  - CreateTable
  - AddPlayerToTable
  - UpdatePlayerAvailability (LED: green/red)
  - StartSession
  - EndSession
- Audio Orchestration
  - UploadAudioTrack
  - PlayTrackNow
  - StopTrack
  - ScheduleSoundEvent
  - ExecuteDueSoundEvents
  - ProcessTrigger
  - GenerateAdaptiveAmbience
- Governance
  - RecordAuditEvent
  - QueryAuditTrail

### 2.4 Boundaries e regras de dependencia

- Camadas
  - Domain: entidades, value objects, regras de negocio puras
  - Application: casos de uso, DTOs, interfaces (ports), transacoes
  - Infrastructure: banco, redis, s3, mensageria, provedores IA
  - Interface: HTTP/WebSocket controllers, schemas de I/O

Regra de ouro:
- Dependencias apontam para dentro (Interface -> Application -> Domain)
- Infrastructure implementa ports definidos na Application
- Dominio nunca importa infraestrutura

### 2.5 Estrategia de eventos assincronos

- Broker/cache: Redis Streams/PubSub para eventos internos em tempo real
- Tipos de evento:
  - session.started
  - session.ended
  - player.availability.updated
  - sound.event.scheduled
  - sound.event.executed
  - ai.ambience.generated
  - audit.logged
- Entrega para clientes: WebSocket gateway publica eventos da mesa/sessao
- Garantia:
  - idempotencia por event_id
  - retry com backoff em handlers
  - dead-letter strategy futura (fila separada)

### 2.6 Estrutura de pastas backend

```text
backend/
  app/
    domain/
      identity/
      tableops/
      audio/
      governance/
      shared/
    application/
      identity/
      tableops/
      audio/
      governance/
      ports/
    infrastructure/
      db/
      repositories/
      messaging/
      storage/
      ai/
      logging/
    interfaces/
      api/
      ws/
      schemas/
    main.py
```

### 2.7 Estrutura de pastas frontend

```text
frontend/
  src/
    app/
    pages/
    widgets/
      sound-desk/
      player-led/
    entities/
    shared/
      api/
      ws/
      ui/
      styles/
```

### 2.8 Estrategia de testes

- Unitarios (dominio e casos de uso):
  - regras de agregados
  - validacoes de entrada
  - comportamento dos casos de uso com mocks de ports
- Integracao:
  - API FastAPI + banco de teste
  - WebSocket handshake e broadcast de eventos
  - fluxo de agendamento/execucao de sound events
- Contrato:
  - schemas HTTP e eventos WS
- Coverage inicial alvo: 80% nas camadas Domain/Application

### 2.9 Estrategia de logs e auditoria

- Logs JSON estruturados com correlation_id e tenant_id
- Niveis:
  - INFO: fluxos de negocio
  - WARN: retries e degradacoes
  - ERROR: falhas de integracao/excecoes
- Auditoria imutavel:
  - cada acao critica gera AuditLog + evento audit.logged
  - trilha consultavel por organizacao, ator e periodo

### 2.10 Estrategia de escalabilidade

- Stateless API pods com escalonamento horizontal
- WebSocket gateway com Redis para fan-out
- Particionamento logico por organization_id
- Filas/eventos para tarefas de IA e execucao programada
- S3 para objetos de audio e CDN opcional para streaming
- Caches Redis para metadados de mesa/sessao

## 3. Validacao

Checklist de conformidade:
- Arquitetura DDD + Clean definida
- Dominios obrigatorios modelados
- Casos de uso e boundaries explicitados
- Estrategia de eventos, testes, logs e escalabilidade definida

## 4. Proximo passo

Implementar Fase 2 com geracao controlada:
- scaffolding backend por modulos independentes
- frontend com sound desk e LEDs
- infraestrutura docker + qualidade + testes base
