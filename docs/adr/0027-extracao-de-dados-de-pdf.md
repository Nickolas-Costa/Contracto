# ADR 0027 — Extração de dados de PDF para preencher o formulário

- **Estado:** aceita como plano; **nada implementado**. A Fase 1 pode ser iniciada sem
  nova dependência. As Fases 2 e 3 dependem do gate de `DEPENDENCY_REVIEW.md` e de
  aceite explícito (ver *Pendências de aceite*).
- **Data:** 2026-10-28
- **Substitui:** a linha "Extração de dados de PDF geral" do índice de ADRs.
- **Contexto:** o usuário já tem PDFs com os dados do cliente (documento de identificação,
  cartão CNPJ, comprovante de residência, ficha cadastral, formulário anterior preenchido,
  contrato) e hoje redigita tudo na Etapa 1. A promessa é *anexar o PDF e o sistema busca
  os dados*, mantendo o princípio do produto: o sistema **sugere**, o usuário **confirma**;
  a responsabilidade legal dos dados continua sendo do usuário (`DECISIONS.md §1`).
  Tudo roda local, sem nuvem (`DECISIONS.md §4`).

## Decisão

Um pipeline local em três estágios — **ler → propor → revisar** — que nunca grava no
rascunho sem confirmação por campo.

### 1. Fases

| Fase | Entrada | Técnica | Dependência nova |
|---|---|---|---|
| **1** | PDF com camada de texto e/ou campos AcroForm | (a) valores de AcroForm via mapeamento inverso do perfil (alta confiança, ex.: formulário que o próprio Contracto gerou); (b) texto pesquisável com padrões validados pelos validadores existentes (CPF, CNPJ, PIS/PASEP, data, CEP, e-mail, telefone, moeda); (c) âncoras de rótulo ("Nome:", "CPF:", "Razão Social") para layouts conhecidos | **Nenhuma** (`pypdf` e `pypdfium2` já são distribuídos) |
| **2** | PDF digitalizado (imagem) | OCR local. Candidatos, a decidir no gate: **A)** `Windows.Media.Ocr` (nativo do Windows, nada a distribuir, exige binding WinRT); **B)** Tesseract embutido (Apache-2.0, ~30 MB + dados de idioma `por`); **C)** não fazer OCR | Depende da escolha; passa por `DEPENDENCY_REVIEW.md` |
| **3** | Vários documentos do mesmo cliente | Fusão por campo com origem e conflito explícitos; layouts aprendidos por perfil | Nenhuma |

Fora de escopo (descartado): LLM ou serviço em nuvem (viola local-first/LGPD), extração
"cega" sem tela de revisão, edição do PDF original.

### 2. Modelo de dados

Cada sugestão é um objeto imutável, nunca um valor já aplicado:

```
ExtracaoCampo {
  campo_id,            # id do campo do perfil (canônico)
  participante,        # índice 0..3 ou "global"
  valor,               # já normalizado (ex.: CPF formatado, data DD/MM/AAAA, moeda 1.234,56)
  confianca,           # 0..1
  origem: { arquivo_id, pagina, metodo: acroform | regex | ancora | ocr },
  alternativas: []     # outros candidatos, ordenados
}
```

Confiança: AcroForm ≈ 0,95; regex validado por dígito verificador ≈ 0,9; âncora de rótulo
≈ 0,8; regex sem validação ≈ 0,6; OCR multiplica por um fator de qualidade. Valores que
**falham** no validador do tipo (CPF/CNPJ/data/moeda) aparecem marcados, nunca aplicados.

### 3. Experiência

1. Na Etapa 1, por participante: **"Preencher a partir de PDF"** (seleção nativa de 1 a 5
   PDFs; mesmo mecanismo de seleção autorizada e de arrasto da Conversão).
2. Tela de **revisão** (modal ou página): tabela *campo · valor atual · valor encontrado ·
   confiança · origem (arquivo/página)*, com caixa por linha e **"Aplicar selecionados"**.
3. Regras: confiança < 0,8 começa **desmarcada**; campo que já tem valor diferente exige
   escolha explícita (nenhuma sobrescrita silenciosa); há **desfazer** da última aplicação;
   o ato de aplicar passa pelos mesmos `changed()`/validadores da digitação manual.
4. A Conferência (Etapa 2) não muda: continua mostrando só o que foi aplicado.

### 4. API local

- `POST /api/v1/extract` → `202 {job_id}`; mesmo modelo de trabalhos, `request_id`
  idempotente e cancelamento da ADR 0015. Corpo: `file_ids` (nova seleção `extract`,
  só `.pdf`), `profile_ids`, `participant`.
- `GET /api/v1/jobs/{id}` devolve `result.extractions[]` apenas ao shell autenticado.
- Limites: 20 MiB por arquivo, 50 páginas, 5 arquivos por pedido, 30 s por arquivo.
- O resultado vive só em memória, expira em 10 min e é descartado no cancelamento e ao
  encerrar a sessão.

### 5. Segurança (PDF é entrada não confiável)

- Leitura em **processo filho** com limite de tempo e memória: falha ou travamento do
  parser não derruba o app. Sem execução de JavaScript do PDF, sem abrir links/anexos.
- PDF criptografado ou corrompido → mensagem clara, sem tentar quebrar senha.
- Sem arquivos temporários com conteúdo do cliente; páginas rasterizadas (Fase 2) ficam
  em memória.
- Validação no **trust boundary**: o servidor revalida tudo que o front aplicar, como na
  geração (`/profiles/preview`).

### 6. Privacidade

- Nenhum dado sai da máquina; sem telemetria (`PRIVACIDADE.md`).
- Valores extraídos **não** entram em log, mensagem de erro, nome de arquivo nem
  resposta de erro. Cobertura por teste que varre `app.log` após uma extração.
- O dado só persiste se o usuário aplicar e gerar, exatamente como hoje.

### 7. Mapeamento por perfil

Chave opcional `extracao` em cada campo do perfil:

```json
{"id": "cpf_vendedor", "tipo": "CPF_CNPJ",
 "extracao": {"rotulos": ["CPF/CNPJ", "Inscrição"], "fonte": ["texto", "acroform"],
              "acroform": "CPF_VENDEDOR", "padrao": null}}
```

Sem a chave, vale o padrão por `tipo` (CPF, CNPJ, DATA, MOEDA, EMAIL, TELEFONE, CEP) com
âncora no `rotulo` do campo. O editor de perfis ganha o bloco "Extração" depois da Fase 1.

## Alternativas consideradas

- **Aplicar direto no rascunho** (sem revisão): descartada — erro silencioso em dado legal.
- **Só AcroForm**: seguro, mas cobre pouco; é a primeira etapa da Fase 1, não o fim.
- **OCR já na Fase 1**: aumenta pacote e superfície sem validar o valor com texto nativo.
- **Serviço remoto/LLM**: descartado por privacidade e licenciamento.

## Testes (por fase)

- **PDFs sintéticos** gerados por `reportlab` (texto, AcroForm, rótulos variados); nenhum
  dado real no repositório.
- Matriz de falsos positivos (números parecidos com CPF, datas inválidas).
- Casos hostis: PDF grande, com muitas páginas, criptografado, corrompido, com JS.
- Teste de log: nenhuma saída de `app.log` contém valor extraído.
- Smoke WebView2: revisão com aplicação parcial, conflito com valor existente, desfazer.

## Aceite da Fase 1

- Extrai CPF, CNPJ, data, e-mail, telefone, CEP e moeda de PDFs sintéticos com ≥ 98% de
  acerto no corpus de teste, e 0 sobrescritas sem confirmação.
- Parser isolado em processo filho com limites; cancelamento libera tudo.
- Nenhuma dependência nova; `pip check` limpo.

## Pendências de aceite (precisam de você)

1. **Quais documentos priorizar** — peço 3 a 5 amostras *anonimizadas* (ou descrição dos
   layouts) para calibrar as âncoras de rótulo.
2. **OCR (Fase 2)**: escolher entre `Windows.Media.Ocr`, Tesseract embutido ou nenhum.
3. **Onde fica o botão**: por participante (proposto) ou também no nível do trabalho.

## Arquivos previstos

`app/services/pdf_extraction.py` (puro, sem UI), `app/api/jobs.py` + `app/api/http.py`
(rota), `frontend/js/extracao.js` (revisão), `tests/test_pdf_extraction.py`,
`docs/PRIVACIDADE.md` (seção nova).
