# Tutorial 02 - Primeira Mesa (UI)

Objetivo: registrar, autenticar, criar mesa, adicionar jogadores e alternar LEDs.

## Passo a passo

1. Abra o frontend: `http://localhost:5173`
2. Em `Email/Nome/Organizacao/Senha`:
   - Use uma organizacao simples, ex.: `org-demo`
   - Use uma senha com pelo menos 8 caracteres
3. Clique em `Registrar`
4. Clique em `Login`
5. Clique em `Criar Mesa`
6. Em `Nome do jogador`, digite um nome e clique em `Adicionar Jogador`
7. Clique no card do jogador para alternar LED:
   - verde (disponivel) <-> vermelho (indisponivel)
8. Inicie sessao no painel `Session` clicando em `Iniciar Sessao`
9. Opcional: ajuste plano da organizacao no painel `Organization`
10. Opcional: registre `AudioTrack`, crie `Trigger` e gere contexto de IA

## O que observar

- `Conexao WS` deve ficar `online` depois que mesa existe e token esta valido
- `Ultimo Evento` muda quando voce cria mesa/adiciona jogador/atualiza disponibilidade
- Sessao muda para `running` ao iniciar e `finished` ao encerrar
