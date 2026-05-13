# A2A Hybrid Artifact Transfer Demo (pt-BR)

Este demo demonstra como transferir arquivos PDF pesados entre dois agentes ADK usando o protocolo A2A em uma **arquitetura híbrida** (Agent Runtime + Cloud Run), otimizada para o Gemini Enterprise App.

## Arquitetura

- **a2a-pdf-root (Agent Runtime):** Agente de recepção. Identifica o PDF enviado pelo usuário (indexado automaticamente pelo GE App), extrai o nome do arquivo via Regex e delega a análise via A2A.
- **a2a-pdf-analyzer (Cloud Run):** Agente remoto especialista. Recebe a referência do arquivo, carrega-o do bucket GCS compartilhado via `LoadArtifactsTool` e realiza a análise jurídica.

## Destaques Técnicos

1.  **Híbrido:** O agente receptor roda no Agent Runtime (nativo do Gemini Enterprise), enquanto o agente analisador roda no Cloud Run para garantir descoberta A2A nativa (`/.well-known`).
2.  **Payload Leve:** Implementação de conversor de partes que remove os bytes do PDF da mensagem A2A, evitando erros de desconexão TCP.
3.  **Identificação Nativa:** Integração com as tags do Gemini Enterprise App (`<start_of_user_uploaded_file>`).
4.  **Storage Compartilhado:** Uso de um bucket GCS global para persistência de artefatos entre diferentes infraestruturas de agentes.

## Como Executar

### 1. Configuração de Variáveis
Edite o arquivo `deploy.sh` na raiz deste diretório para configurar seu `PROJECT_ID`, `REGION` e `GE_APP_ID`.

### 2. Deploy Automatizado
Execute o script de deploy para subir toda a infraestrutura e configurar as permissões IAM necessárias:
```bash
./deploy.sh
```

### 3. Registro
O script já realiza a publicação do Root Agent no Gemini Enterprise. Basta acessar o console e validar a integração.

## Documentação Detalhada
Para entender todos os desafios técnicos superados neste demo, leia o arquivo [LESSONS.md](./LESSONS.md).
