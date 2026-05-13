# A2A Artifact Transfer Demo (pt-BR)

Este demo demonstra como transferir arquivos PDF pesados entre dois agentes ADK usando o protocolo A2A e o sistema de Artifacts do ADK.

## Estrutura

- **a2a-pdf-root:** Agente de recepção (Root). Recebe o PDF do usuário, salva-o com um UUID no namespace `user:` e delega a análise via A2A.
- **a2a-pdf-analyzer:** Agente remoto (Exposed). Recebe a referência do artefato, carrega o PDF do storage compartilhado e realiza a análise jurídica em Português-BR.

## Como Funciona a Transferência de Arquivos

Para evitar colisões e garantir que arquivos grandes não sobrecarreguem o canal de comunicação A2A:

1. O agente root salva o arquivo usando `context.save_artifact("user:contrato_{uuid}.pdf", part)`.
2. O nome do arquivo (referência) é passado como uma string no payload A2A.
3. O agente remoto usa `LoadArtifactsTool` para buscar o conteúdo do arquivo no `ArtifactService` compartilhado (GCS em produção).

## Passos para Implantação

1. **Deploy do Analyzer:**
   ```bash
   cd a2a-pdf-analyzer
   agents-cli deploy
   ```
   Anote a URL do serviço gerada pelo Agent Engine.

2. **Configuração do Root:**
   Edite `a2a-pdf-root/app/agent.py` e substitua `ANALYZER_AGENT_URL` pela URL do analyzer (ou defina a variável de ambiente `ANALYZER_AGENT_URL`).

3. **Deploy do Root:**
   ```bash
   cd a2a-pdf-root
   agents-cli deploy
   ```

4. **Registro:**
   Registre apenas o `a2a-pdf-root` no console do Gemini Enterprise App.

## Requisitos de Infraestrutura
Ambos os agentes devem estar configurados para usar o mesmo bucket do Google Cloud Storage em seu `GcsArtifactService` para que possam compartilhar os arquivos. O Agent Engine gerencia isso automaticamente se configurado no `agent_engine_app.py` ou via variáveis de ambiente.
