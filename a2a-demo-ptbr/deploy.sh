#!/bin/bash
set -e

# === CONFIGURAÇÕES GLOBAIS ===
export PROJECT_ID="YOUR_PROJECT_ID"
export REGION="YOUR_REGION"
export BUCKET_NAME="YOUR_PROJECT_ID-artifacts"
export GE_APP_ID="YOUR_GE_APP_ID"

# Nomes de exibição
ANALYZER_NAME="a2a-pdf-analyzer"
ROOT_NAME="a2a-pdf-root"

# Variáveis de Telemetria Máxima
TELEMETRY_VARS="OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true,ADK_PLUGIN_LOGGING_ENABLE_CONTENT=1,GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,GOOGLE_CLOUD_AGENT_ENGINE_LOGGING_ENABLE_CONTENT=true,ADK_LOGGING_LEVEL=DEBUG"

echo "🚀 Iniciando deploy determinístico (HÍBRIDO: Cloud Run + Agent Runtime)"

# 1. Garantir que o bucket existe
gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID 2>/dev/null || echo "Bucket já existe."

# 2. Deploy do ANALYZER AGENT (Cloud Run)
echo "📦 Implantando Analyzer Agent no Cloud Run..."
cd a2a-pdf-analyzer
agents-cli deploy \
  --project $PROJECT_ID \
  --region $REGION \
  --no-confirm-project \
  --update-env-vars "$TELEMETRY_VARS,LOGS_BUCKET_NAME=$BUCKET_NAME"

# Capturar a URL REAL do Cloud Run
ANALYZER_URL=$(gcloud run services describe $ANALYZER_NAME --project=$PROJECT_ID --region=$REGION --format="value(status.url)")

# Fazer um update rápido para injetar a URL correta no APP_URL (necessário para o Agent Card)
echo "🔄 Atualizando APP_URL para: $ANALYZER_URL"
gcloud run services update $ANALYZER_NAME \
  --update-env-vars "APP_URL=$ANALYZER_URL,LOGS_BUCKET_NAME=$BUCKET_NAME,GOOGLE_CLOUD_LOCATION=$REGION,$TELEMETRY_VARS" \
  --project=$PROJECT_ID --region=$REGION --quiet

ANALYZER_A2A_URL="$ANALYZER_URL" # Agora apontamos para a raiz
echo "✅ Analyzer URL: $ANALYZER_A2A_URL"

cd ..

# 3. Deploy do ROOT AGENT (Agent Runtime)
echo "📦 Implantando Root Agent no Agent Runtime..."
cd a2a-pdf-root
agents-cli deploy \
  --project $PROJECT_ID \
  --region $REGION \
  --no-confirm-project \
  --update-env-vars "LOGS_BUCKET_NAME=$BUCKET_NAME,$TELEMETRY_VARS,ANALYZER_AGENT_URL=$ANALYZER_A2A_URL"

# Conceder permissão de invocador ao Root Agent (caso tenha sido recriado)
ROOT_SA="service-$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
echo "🔐 Concedendo permissão ao SA do Root ($ROOT_SA)..."
gcloud run services add-iam-policy-binding $ANALYZER_NAME \
  --member="serviceAccount:$ROOT_SA" \
  --role="roles/run.invoker" \
  --project=$PROJECT_ID \
  --region=$REGION \
  --quiet

cd ..

# 4. Publicar no Gemini Enterprise
echo "🌟 Publicando Root Agent no Gemini Enterprise ($GE_APP_ID)..."
cd a2a-pdf-root
agents-cli publish gemini-enterprise \
  --project-id $PROJECT_ID \
  --gemini-enterprise-app-id $GE_APP_ID
cd ..

echo "✅ Deploy híbrido concluído com sucesso!"
