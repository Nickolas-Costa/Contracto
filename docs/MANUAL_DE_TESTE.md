# Manual de Teste — Contracto v4.5.9

Roteiro botão-por-botão + testes automatizados. Serve p/ QA manual e p/
conferir cobertura headless (prova p/ pywebview/Tauri).

## 1. Testes automatizados (rápido)

```powershell
# venv do projeto (obrigatório: customtkinter, reportlab)
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Só composição multi-perfis (feature v4.5.9)
.\.venv\Scripts\python.exe -m unittest tests.test_composicao_perfis -v

# Prova headless (backend sem UI — gate pywebview)
.\.venv\Scripts\python.exe -m unittest tests.test_headless_backend -v
```

> Testes usam pastas temporárias: **nunca tocam** `%APPDATA%/Contracto`.
> `ModuleNotFoundError: customtkinter/reportlab` → use `.venv`, não o
> Python do sistema.

## 2. Jornada manual — Modo Simples multi-seleção (novidade v4.5.9)

| # | Ação na UI | Esperado |
|---|---|---|
| 1 | Topbar → **Simples** | Stepper vira "Emissão de Formulário Único", dropdown some, aparece `✓ Selecionar formulários` |
| 2 | `✓ Selecionar formulários` | Modal com checkboxes de todos `formulario_simples`, contador `N documentos` |
| 3 | Marcar 2+ (ex: ITBI + Isenção) → Aplicar | Toast `N formulário(s) selecionado(s)`, botão vira `✓ Formulários selecionados: N` |
| 4 | Preencher Nome/CPF/Local uma vez | Campos combinados sem duplicar `id`; paginação ativa se >1 perfil |
| 5 | Gerar | 2+ PDFs com sufixo `(2)` se mesmo nome, sem sobrescrever |
| 6 | Marcar perfis incompatíveis (mesmo `id`, tipos dif) | `AlertModal Configurações Incompatíveis` lista `id`, nada aplica |
| 7 | `[x] Preservar dados` + gerar em sequência | Nome/CPF/Endereço/Local mantidos |
| 8 | Reabrir app | Seleção `formularios_basicos_selecionados` restaurada |

## 3. Jornada manual — Modo Avançado

| # | Ação | Esperado |
|---|---|---|
| 1 | Topbar → Avançado | Stepper 1/2, dropdown Perfil (MCMV/SBPE) |
| 2 | Etapa 1: 1–4 participantes, CPF inválido | Borda vermelha + bloqueio gerar |
| 3 | Gerar → Etapa 2: anexar extras → Finalizar | Conversão `-dSAFER` silenciosa, pastas `ASSINADOS/REGISTRADOS`, `Parar Processo` cancela e limpa |
| 4 | Perfis: Duplicar/Editar/Excluir | Cópia independente, nome único |
| 5 | Config: tema/claro/escuro, cor destaque | Gradiente senoidal acompanha cor; `get_icon` troca `_dark/_light` |

## 4. Massa de teste

- CPF válido: `52998224725`; CNPJ: tradicional + alfanumérico IN RFB 2.229/2024.
- `MANUAL_ZEBRA`-like: nome com acento, valor `1.234,56`, telefone `(88) 99999-0000`.
