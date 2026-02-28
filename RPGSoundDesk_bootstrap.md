# RPGSoundDesk - Bootstrap Enterprise

------------------------------------------------------------------------

# 1. FORMULÁRIO PREENCHIDO

## Nome do Projeto

RPGSoundDesk

## Tipo de Sistema

SaaS

## Objetivo Principal

Criar uma plataforma SaaS inteligente de controle e ambientação sonora
para mesas de RPG online, permitindo que narradores gerenciem trilhas,
efeitos, estados dos jogadores (com indicadores visuais verde/vermelho),
ambientações dinâmicas, programação de eventos e suporte de IA
adaptativa para aumentar imersão e controle narrativo.

## Stack Backend

FastAPI

## Stack Frontend

React

## Banco de Dados

PostgreSQL

## Padrão Arquitetural

DDD + Clean Architecture

## Nível de Engenharia

Enterprise

## Papéis de Agentes

-   Arquiteto de Software
-   Backend Engineer
-   Frontend Engineer
-   AI Engineer
-   DevOps Engineer
-   QA Engineer

## Regras de Qualidade

-   SOLID rigoroso
-   100% tipado
-   Testes unitários obrigatórios
-   Testes de integração obrigatórios
-   Linter obrigatório

## Pipeline de Validação

Rigoroso

## Logs e Auditoria

Logs JSON + Auditoria completa

------------------------------------------------------------------------

# 2. VERSÃO ENTERPRISE FORMAL ESTRUTURADA

## Visão Estratégica

RPGSoundDesk é uma plataforma SaaS de engenharia sonora imersiva para
RPGs online com foco em controle narrativo avançado, automação
inteligente e governança operacional.

## Pilares Arquiteturais

1.  Separação estrita de camadas (DDD + Clean)
2.  Observabilidade completa
3.  Modularização por contexto de domínio
4.  Escalabilidade horizontal
5.  Eventos assíncronos para sincronização sonora

## Domínios Principais

-   Usuário & Organização
-   Mesa
-   Sessão
-   Jogador
-   Motor de Áudio
-   Motor de Eventos
-   IA Narrativa
-   Assinaturas & Planos
-   Auditoria

------------------------------------------------------------------------

# 3. BLUEPRINT ARQUITETURAL COMPLETO

## Camadas

### 1. Camada de Apresentação

-   React
-   WebSocket para tempo real
-   Indicadores LED verde/vermelho por jogador
-   Painel de mesa sonora

### 2. Camada de Aplicação (Use Cases)

-   Criar Sessão
-   Ativar Ambientação
-   Programar Evento Sonoro
-   Alterar Estado do Jogador
-   Executar Trigger Inteligente

### 3. Camada de Domínio

Entidades: - User - Table - Session - Player - AudioTrack - SoundEvent -
Trigger - AIContext

### 4. Camada de Infraestrutura

-   PostgreSQL
-   Redis (eventos e cache)
-   Storage S3-compatible
-   Logs estruturados JSON
-   Observabilidade (OpenTelemetry)

------------------------------------------------------------------------

# 4. MATRIZ DE AGENTES E RESPONSABILIDADES

  Agente                  Responsabilidades
  ----------------------- ----------------------------------------------
  Arquiteto de Software   Definir boundaries, domínios, regras DDD
  Backend Engineer        Implementar APIs, regras de negócio, eventos
  Frontend Engineer       Interface mesa sonora, estados visuais
  AI Engineer             Motor adaptativo de ambientação
  DevOps Engineer         CI/CD, containers, observabilidade
  QA Engineer             Testes unitários, integração e regressão

------------------------------------------------------------------------

# 5. PROMPT FINAL DE BOOTSTRAP ENTERPRISE

Você agora atuará como um Sistema de Engenharia Avançada orientado por
Arquitetura.

## CONTEXTO

Projeto: RPGSoundDesk Tipo: SaaS Arquitetura: DDD + Clean Nível:
Enterprise

## OBJETIVO

Planejar arquitetura completa, definir módulos, dependências, modelo de
domínio, estratégia de escalabilidade e pipeline rigoroso.

## REGRAS OBRIGATÓRIAS

-   SOLID rigoroso
-   100% tipado
-   Testes unitários e integração obrigatórios
-   Linter obrigatório
-   Logs estruturados JSON
-   Auditoria completa

## ETAPAS

1.  Modelagem de Domínio
2.  Definição de Casos de Uso
3.  Estruturação de Pastas
4.  Estratégia de Eventos Assíncronos
5.  Estratégia de Escalabilidade
6.  Plano de Testes
7.  Plano de Observabilidade

Nunca gerar código antes do planejamento completo.
