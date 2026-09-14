# ADR 0013 — Bootstrap recuperável e origem imutável da ponte

Status: aceita e implementada em 14/09/2026. Consolida ADR-QA-BOOT.

## Contexto

A primeira UI podia marcar o bootstrap como concluído após falha HTTP. A ponte também não deve permitir que o JavaScript amplie suas próprias origens confiáveis.

## Decisão

Definir a URL confiável no construtor Python, antes de expor a ponte. A UI real aceita somente sua URL exata; diagnóstico sem URL tem política separada. Nenhum método público permite alterar essa política. Verificar a origem antes das operações e novamente após leitura de PDF. Separar handlers já vinculados, conexão em andamento e prontidão; retry consulta saúde e reutiliza os handlers existentes.

## Consequências e evidência

Navegação externa perde acesso. Eventos repetidos não duplicam handlers. Testes da bridge verificam allowlist pública e origem; frontend_behavior.cjs reproduz 503 seguido de 200. A proteção não cobre processos maliciosos na mesma conta Windows. Complementa ADRs 0005 e 0011.
