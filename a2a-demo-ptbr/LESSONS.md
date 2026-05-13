# Lições Aprendidas: Transferência de Arquivos A2A Híbrida

Este documento consolida o conhecimento técnico adquirido durante a implementação da transferência de arquivos PDF entre agentes ADK em uma arquitetura híbrida.

## 1. Arquitetura e Fluxo de Dados (Sequência)

O sucesso da transferência de arquivos pesados depende de um "triângulo" de integração entre o Gemini Enterprise (GE) App, o Google Cloud Storage (GCS) e os agentes.

```text
                               +-----------------------------+
                               |      GCS BUCKET             |
                               | (YOUR_PROJECT_ID-artifacts)     |
                               +-----------------------------+
                                   ^                ^
         (1) Upload Automático     |                | (5) Leitura via
             antes da chamada      |                |     LoadArtifactsTool
                                   |                |
  +------------+             +-----+-----+    +-----+------------+
  |  USUÁRIO   | --(PDF)-->  |  GE APP   |    | ANALYZER AGENT   |
  +------------+             +-----+-----+    | (Cloud Run)      |
                                   |          +------------------+
                                   | (2) Chamada    ^
                                   |     do Root    | (4) Mensagem A2A
                                   v                |     (Apenas Texto)
                             +-----------+          |
                             | ROOT AGENT| ---------+
                             | (Agent RE)|
                             +-----------+
                                (3) Regex Tag
                                    Capture
```

## 2. A Chave da Integração: `LOGS_BUCKET_NAME`

O Gemini Enterprise App não "adivinha" onde salvar os arquivos. A conexão é estabelecida via metadados:
1.  **Configuração:** Durante o deploy, definimos `LOGS_BUCKET_NAME=nome-do-bucket`.
2.  **Registro:** Ao publicar o agente no GE App, o ecossistema Google lê essa variável.
3.  **Ação:** O GE App passa a usar esse bucket como o "dropzone" para qualquer anexo naquela sessão de chat.
4.  **Estrutura:** O App cria automaticamente o caminho: `app/{user_id}/{session_id}/{filename}/0`.

## 3. Comportamento das Tags do GE App
O arquivo **não chega** como bytes (`inline_data`) para o Root Agent. O Vertex AI intercepta o anexo e injeta tags de marcação no prompt do usuário:
- **Exemplo:** `... analise este documento <start_of_user_uploaded_file: contrato.pdf> ...`
- **Solução:** Implementamos uma ferramenta (`salvar_contrato`) que usa **Regex** para capturar esse nome de arquivo navegando pelos eventos de sessão.

## 4. Mergulho Técnico: Eventos de Sessão e Captura de Arquivo

Para que o Root Agent saiba qual arquivo enviar ao Analisador, ele precisa consultar o histórico da conversa. No ADK, isso é feito através do `tool_context.session.events`.

### O que são os Eventos de Sessão?
Cada interação no chat (uma mensagem do usuário, uma resposta do modelo, uma chamada de ferramenta) é registrada como um `Event`. Cada evento contém `parts`, que podem ser texto, dados binários ou referências de arquivos.

### Anatomia de um Evento com Arquivo (JSON)
Diferente de um upload direto via API, no GE App o arquivo é "injetado" como texto no histórico. Veja como o Root Agent enxerga o evento:

```json
{
  "author": "user",
  "content": {
    "parts": [
      { "text": "Analise este arquivo: " },
      { "text": "\n<start_of_user_uploaded_file: contrato_v1.pdf>\n" },
      { "text": "<end_of_user_uploaded_file: contrato_v1.pdf>" }
    ]
  }
}
```

### Extração via Regex
Como o arquivo foi "textualizado" em tags, usamos o Regex `r"start_of_user_uploaded_file:\s*([^\s\n>]+)"` para extrair a string exata do nome do arquivo (ex: `contrato_v1.pdf`).
3.  **Resolução de Artefatos:** É importante notar que o Regex **não extrai o path completo do GCS** (ex: `gs://bucket/path...`). Ele captura apenas o **nome lógico** do arquivo.
4.  **A Mágica do Contexto:** Quando o Analisador recebe apenas a string `contrato.pdf` e chama `LoadArtifactsTool`, o `GcsArtifactService` do ADK entra em ação:
    -   Ele usa o `user_id` e o `session_id` que foram transportados automaticamente pelo protocolo A2A.
    -   Ele reconstrói o caminho físico no bucket: `app/{user_id}/{session_id}/contrato.pdf/0`.
    -   Essa abstração permite que os agentes troquem referências simples (nomes de arquivos) enquanto o ADK cuida da complexidade do storage.

Este padrão de "leitura de histórico" é a forma mais resiliente de integrar agentes ADK com interfaces que realizam pré-processamento de anexos, como o Gemini Enterprise.

## 5. Por que a Arquitetura Híbrida? (Cloud Run vs Agent Runtime)

| Recurso | Agent Runtime (RE) | Cloud Run |
| :--- | :--- | :--- |
| **Roteamento** | Gerenciado e Restrito | Livre / FastAPI Padrão |
| **Discovery A2A** | Frequentemente falha (404) | Nativo (`/.well-known/`) |
| **Protocolo REST** | Instável em alguns cenários | Suportado (mas JSON-RPC é melhor) |
| **Recomendação** | Ótimo para o Agente Root | **Ideal para Agentes Exposed** |

## 5. Troubleshooting de Protocolo e Identidade

### O "Bug do Localhost"
A função `to_a2a()` do ADK pode gerar um Agent Card apontando para `localhost:8000` se não receber um `app_url` explícito. Isso causa o erro genérico `Server disconnected` no cliente.
- **Lição:** Sempre injete a URL estável do serviço no construtor do servidor e no cliente.

### JSON-RPC: O Dialeto Seguro
Tentativas de usar REST (`/v1/message:send`) no Cloud Run apresentaram falhas de desserialização (Erros 500/403).
- **Lição:** Para A2A entre agentes Python, o transporte **`JSONRPC`** na raiz (`/`) provou ser o mais resiliente.

### Otimização de Payload
O protocolo A2A não foi feito para transportar megabytes de arquivos binários.
- **Estratégia:** Use um `genai_part_converter` customizado no Root Agent para remover bytes de PDFs do payload. Passe apenas a referência e deixe o agente de destino carregar do GCS.

---
*Documento gerado como referência de engenharia para o projeto adk-agents-cabral.*
