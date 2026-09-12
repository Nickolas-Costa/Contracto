# Especificação — preparação para WebView e integração futura

## Objetivo e limite da fase

Esta fase entrega o contrato local entre uma interface WebView e o núcleo Python existente. Não entrega site público, API exposta à internet, login corporativo ou armazenamento de documentos em nuvem.

O resultado é uma aplicação desktop local-first, cujas operações podem ser chamadas por HTTP loopback. A mesma fronteira permitirá, mais adiante, um agente local integrado a sistemas de uma empresa.

## Dependências e ambientes suportados

| Componente | Necessário no desktop WebView | Consequência fora desse ambiente |
|---|---|---|
| Python empacotado, FastAPI, Uvicorn e pywebview | Sim, distribuídos com o aplicativo | Não devem ser pré-requisitos para o usuário final |
| WebView2 | Sim, para o shell Windows | O instalador deve detectar ou orientar a instalação |
| Ghostscript embutido | Somente ao solicitar PDF/A | A operação retorna capacidade indisponível; gerar PDF simples continua possível |
| Microsoft Word + pywin32/COM | Somente ao enviar RTF para conversão | RTF falha de forma explícita; PDF e geração de AcroForm continuam disponíveis |
| CustomTkinter/Tk | Não, após a nova tela substituir a atual | Permanece apenas durante a convivência com a UI legada |
| pypdf, pikepdf, lxml, Pillow e pypdfium2 | Sim, no núcleo empacotado | Geração, validação ou pré-visualização deixam de funcionar se forem removidos |

O Word é o principal limite para uma execução hospedada: COM exige Windows, uma instalação licenciada do Word e uma sessão apta a automatizá-lo. Em agente local isso permanece viável. Em servidor, torna-se uma decisão operacional e de licenciamento, não apenas uma dependência Python.

## Modelo de operações

As etapas são uma apresentação do desktop atual. A API deve expor capacidades componíveis, sem obrigar quem a chama a reproduzir a navegação visual.

```text
compor perfil ─┐
gerar PDFs ────┼──> trabalho de processamento opcional ──> resultado
anexar PDFs ──┘      (converter PDF/A, organizar pastas, renomear)
```

`gerar documentos` é suficiente para formulários simples. `processar` recebe os PDFs gerados e anexos quando o chamador precisa de PDF/A ou da estrutura de dossiê. Assim, a atual Etapa 2 deixa de ser uma obrigação da API e vira uma operação explícita.

## Contratos mínimos da API local

As rotas ficam em `/api/v1`, exigem `Authorization: Bearer <token>` e aceitam somente chamadas originadas pelo shell local autorizado.

| Rota | Uso | Resultado |
|---|---|---|
| `GET /health` | confirmar processo e versão | versão e estado do servidor |
| `GET /capabilities` | informar Word, Ghostscript e formatos disponíveis | capacidades, sem caminhos sensíveis |
| `POST /profiles/compose` | validar e combinar perfis simples | perfil combinado e incompatibilidades |
| `POST /jobs/generate` | gerar documentos de participantes e perfil | `job_id` |
| `POST /jobs/process` | converter/organizar PDFs e anexos, se solicitado | `job_id` |
| `GET /jobs/{job_id}` | acompanhar progresso e erros | estado, progresso e resultado seguro |
| `POST /jobs/{job_id}/cancel` | cancelar trabalho em andamento | estado atualizado |

Pedidos não recebem `Path` arbitrário vindo da interface. Para arquivos e pastas, o shell usa o port de diálogos e envia identificadores temporários de seleção ou o servidor valida que o destino está em diretório permitido pelo usuário. Respostas nunca retornam caminhos absolutos, token, CPF/CNPJ ou dados de formulário nos logs.

## Requisitos para o agente implementar antes da primeira tela

1. Criar `app/server.py` e `app/api/` sem importar `ui/` ou Tk.
2. Iniciar Uvicorn em porta livre de loopback e manter o token somente em memória.
3. Criar modelos Pydantic para requisições, resultados, erros e estado de trabalho.
4. Adaptar `QueueManager` para uma fachada de trabalhos da API; cada trabalho precisa de identificador não previsível, progresso, cancelamento e limpeza ao encerrar.
5. Implementar `GET /capabilities` para Word, Ghostscript e formatos, sem iniciar Word.
6. Implementar o port de diálogos WebView sem alterar os serviços.
7. Rejeitar origem, token, método, corpo e caminho inválidos antes de chamar serviços.
8. Encerrar o servidor ao fechar o shell e invalidar todos os tokens e trabalhos pendentes.
9. Criar testes de integração HTTP para autenticação, origem inválida, cancelamento, geração simples, processamento opcional, Word ausente e Ghostscript ausente.
10. Atualizar build e manual de teste para WebView2, porta loopback e diagnóstico local.

## Critérios de aceite da fase

- O servidor escuta apenas em `127.0.0.1` e não aceita pedido sem token válido.
- Uma chamada de formulário simples gera arquivos sem passar pelo fluxo visual da Etapa 2.
- Uma chamada de processamento converte/organiza arquivos e pode ser cancelada.
- Word ausente não impede os endpoints que trabalham somente com PDF.
- Ghostscript ausente não impede PDF simples e devolve erro acionável ao pedir PDF/A.
- A suíte atual continua passando e os novos testes HTTP cobrem sucesso, erro e cancelamento.
- Nenhum log de API contém token, CPF, CNPJ, e-mail, conteúdo de formulário ou caminho absoluto.

## Evolução empresarial hospedada

A API hospedada permanece fora desta fase, conforme ADR 0006. Antes dela, é necessária descoberta comercial: quem opera o agente, quais sistemas se integram, volume, SLA, modelo de cobrança, retenção de documentos e suporte. O primeiro produto recomendado é um conector autenticado entre o sistema da empresa e o agente local Windows; o agente executa Word, Ghostscript e I/O.

Somente depois devem ser especificados API pública, identidade corporativa, isolamento por empresa, retenção e eliminação de arquivos, auditoria, limites, fila persistente, observabilidade, contratos LGPD e a estratégia legal para automação do Word em infraestrutura de servidor.
