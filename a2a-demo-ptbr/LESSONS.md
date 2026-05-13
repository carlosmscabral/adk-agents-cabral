# Lições Aprendidas: Transferência de Arquivos A2A Híbrida

Este documento detalha os desafios técnicos e as soluções implementadas para permitir a transferência de arquivos PDF pesados entre agentes ADK usando o protocolo A2A em uma arquitetura híbrida (Agent Runtime + Cloud Run).

## 1. Comportamento do Gemini Enterprise (GE) App
Descobrimos que o GE App possui um comportamento de indexação automática que afeta como os arquivos são recebidos pelo agente:
- **Indexação Prévia:** Ao fazer o upload de um PDF no chat, o GE App salva o arquivo no bucket de artifacts compartilhado (`gs://.../app/{user_id}/{session_id}/...`) **antes** de chamar o Root Agent.
- **Tags de Arquivo:** O conteúdo do arquivo não chega como bytes (`inline_data`) para o Root Agent no prompt inicial. Em vez disso, o Vertex AI injeta tags de texto como `<start_of_user_uploaded_file: nome.pdf>`.
- **Solução:** A ferramenta `salvar_contrato` usa **Regex** para capturar o nome do arquivo diretamente dessas tags, permitindo que o Root Agent passe essa referência ao próximo agente sem precisar re-processar o arquivo.

## 2. A2A: Por que mover para o Cloud Run?
- **Restrições do Agent Runtime:** O ambiente gerenciado do Agent Runtime (Vertex AI) possui roteamento restrito que dificulta a exposição de caminhos padrão como `/.well-known/agent-card.json`.
- **Descoberta Nativa:** No Cloud Run, temos controle total sobre o servidor FastAPI, permitindo que os endpoints de descoberta A2A funcionem nativamente e sem redirecionamentos complexos que causavam erros 404.

## 3. O "Bug do Localhost" e Identidade do Card
- **O Problema:** Identificamos que a função `to_a2a()` do ADK, se não configurada com `app_url` explícito, pode gerar um Agent Card onde o campo `"url"` aponta para `http://localhost:8000`.
- **O Efeito:** O Root Agent baixava o card com sucesso, mas tentava enviar mensagens para o próprio `localhost` (dentro do seu container no Agent Runtime), resultando em erros genéricos de `Server disconnected`.
- **A Solução:** Forçamos a URL estável do Cloud Run tanto no servidor (`APP_URL`) quanto no cliente (bypass de card no Root Agent).

## 4. Estabilidade do Protocolo: JSON-RPC vs. REST
- **Falha no REST:** O endpoint REST v1 (`/v1/message:send`) mostrou-se instável em containers Cloud Run, apresentando erros de desserialização Protobuf (`Message type "a2a.v1.Message" has no field named "parts"`) que muitas vezes eram mascarados como erros 403 ou 500 pelo Google Frontend.
- **Vantagem do JSON-RPC:** O transporte **JSONRPC** (na raiz `/`) provou ser o método mais robusto e estável para a comunicação A2A entre os agentes, evitando conflitos de esquema de mensagem.

## 5. Otimização de Payload (TCP Disconnection)
- **Bytes Pesados:** Tentar enviar os bytes completos de um PDF dentro de uma mensagem A2A excede os limites de tamanho do payload e causa quedas de conexão TCP.
- **Solução:** Implementamos um conversor customizado (`genai_part_converter`) no Root Agent que remove partes de `inline_data` (PDF) do payload. O Analisador recebe apenas a referência e usa a ferramenta `load_artifacts` para ler o arquivo diretamente do GCS compartilhado.

## 6. IAM e Latência de Propagação
- **Delay no Acesso:** Mesmo ao tornar um serviço público via `gcloud`, existe uma latência de propagação de políticas IAM no GCP (60-120 segundos). Testes imediatos após o deploy podem falhar com 403 Forbidden falsos.
- **Bypass Estratégico:** "Chumbar" o objeto `AgentCard` no Root Agent elimina a dependência dessa fase de negociação inicial, tornando a inicialização do agente mais rápida e resiliente a falhas temporárias de rede ou IAM.

---
*Este setup serve como referência organizacional para transferências de arquivos pesados via A2A no ecossistema Gemini Enterprise.*
