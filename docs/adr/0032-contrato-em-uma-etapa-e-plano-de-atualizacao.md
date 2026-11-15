# ADR 0032 — Contrato em uma etapa e plano de atualização dentro do app (v5.4.0)

- **Estado:** parte 1 aceita e implementada; parte 2 é proposta (nenhum código ainda).
- **Data:** 2026-11-11

## 1. Contrato conclui em uma etapa (implementado)

Antes, o modo Contrato tinha dois finais: "Confirmar e gerar" preenchia os formulários e, na tela
seguinte, "Finalizar processo" convertia e organizava. Agora há um só:

1. Na Conferência (Etapa 2) ficam os formulários, os documentos extras e o **formato de saída**.
2. "Confirmar e gerar documentos" pergunta sobre extras que faltam (antes de gerar) e dispara a geração.
3. Concluída a geração, a tela envia sozinha a organização (`POST /jobs/process`), sem outro clique.
4. A Etapa 3 mostra só o resultado final. O botão "Tentar concluir de novo" aparece apenas se a
   organização falhar depois de a geração dar certo (não gera de novo).

Decisões:

- **A API não mudou.** Seguem dois trabalhos (`generate` e `process`); a tela os encadeia. Um endpoint único
  duplicaria a publicação atômica e a idempotência que já existem em cada um.
- Os PDFs finais deixam de levar o prefixo `1-`, `2-` (vinha do nome da cópia de trabalho).
- Simples e Conversão não mudam.

## 2. Atualização dentro do app sem certificado de assinatura (proposta)

**Problema.** Atualizar hoje é baixar o instalador no navegador. Sem certificado de assinatura de código
(pago), o SmartScreen alerta a cada versão.

**Restrições.** O app promete funcionar sem rede e sem telemetria (`PRIVACIDADE.md`); a página tem
`connect-src` fechado; toda dependência nova passa por `DEPENDENCY_REVIEW.md`.

### Opções

| | A. Atualizador do Tauri | B. Verificação própria |
|---|---|---|
| Como | `tauri-plugin-updater` lê um `latest.json` da release, baixa o instalador NSIS e instala | o Rust consulta a API de releases do GitHub, baixa o instalador e confere o `.sha256.txt` |
| Garantia | assinatura **minisign** (chave gratuita, gerada por `tauri signer generate`); a chave pública vai no app | só integridade: o hash vem do mesmo lugar que o arquivo |
| Certificado pago | não precisa | não precisa |
| SmartScreen | não aparece: arquivo baixado pelo app não leva a marca de "veio da internet" | idem |
| Código novo | pouco: plugin + ~40 linhas em Rust + um botão | ~120 linhas em Rust, mais os casos de erro |
| Dependências | plugin do Tauri e TLS no `reqwest` | TLS no `reqwest` |

**Recomendação: A.** A assinatura minisign não é certificado de assinatura de código: é um par de chaves
criado na máquina de build, sem custo e sem autoridade certificadora. Ela é o que impede que alguém que
invada a conta do GitHub entregue um instalador falso; a opção B não tem essa proteção.

### Desenho proposto (opção A)

- **Só por pedido do usuário.** Botão "Verificar atualizações" em Configurações. Sem checagem ao abrir
  por padrão; uma caixa "Verificar ao abrir" pode vir depois, desligada de fábrica. Assim a promessa de
  não usar a rede sem pedido continua verdadeira; `PRIVACIDADE.md` passa a citar essa única conexão
  (GitHub, sem dado do usuário além do IP).
- **No Rust, não na página.** Novo comando nativo `check_update` → `{versao, notas}` ou `{atual: true}`;
  `install_update` baixa, valida a assinatura, fecha o sidecar e roda o instalador. A página continua
  sem acesso à rede.
- **Trabalho em andamento bloqueia a instalação** (mesma checagem do aviso ao fechar a janela).
- **Build:** `scripts/build_tauri.py` passa a gerar `latest.json` e o `.sig`; a chave privada fica fora
  do repositório (`TAURI_SIGNING_PRIVATE_KEY` no ambiente de build). Perder a chave obriga uma
  atualização manual de todos; guardar cópia.
- **Portátil (ZIP):** sem atualização automática; o botão só avisa e abre a página da release.

### Passos

1. Revisar dependências (`tauri-plugin-updater`, `reqwest` com `rustls-tls`) pelo `DEPENDENCY_REVIEW.md`.
2. Gerar o par de chaves; pôr a pública em `tauri.conf.json` (`plugins.updater`).
3. Comandos `check_update`/`install_update` em `main.rs`, contrato em `TAURI_CONTRATO.md`, funções em `api.js`.
4. Botão e modal em Configurações; texto em `PRIVACIDADE.md` e no README.
5. `build_tauri.py`: `latest.json` + assinatura; anexar ambos à release.
6. Teste real: instalar a versão N, publicar N+1 como pré-lançamento e atualizar por dentro do app.

**Fora do escopo:** atualização silenciosa, canal beta e reversão automática.
