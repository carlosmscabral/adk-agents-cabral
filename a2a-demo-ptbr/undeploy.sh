#!/bin/bash
# Configurações de Ambiente
PROJECT_ID="vibe-cabral"
REGION="us-east1"

echo "🗑️ Iniciando undeploy híbrido..."

# 1. Deletar Root (Agent Runtime / Reasoning Engine)
if [ -f "a2a-pdf-root/deployment_metadata.json" ]; then
    ROOT_ID=$(python3 -c "import json, sys; 
try:
    meta=json.load(open('a2a-pdf-root/deployment_metadata.json'))
    print(meta.get('remote_agent_runtime_id', '') if meta.get('remote_agent_runtime_id') != 'None' else '')
except:
    print('')
")
    if [ ! -z "$ROOT_ID" ]; then
        echo "Deletando Reasoning Engine (Root): $ROOT_ID..."
        gcloud ai reasoning-engines delete $ROOT_ID --project=$PROJECT_ID --location=$REGION --quiet || echo "Root já removido ou falha."
    fi
    echo '{"remote_agent_runtime_id": "None", "deployment_timestamp": "None"}' > "a2a-pdf-root/deployment_metadata.json"
fi

# 2. Deletar Analyzer (Cloud Run e possível Reasoning Engine residual)
if [ -f "a2a-pdf-analyzer/deployment_metadata.json" ]; then
    ANALYZER_ID=$(python3 -c "import json, sys; 
try:
    meta=json.load(open('a2a-pdf-analyzer/deployment_metadata.json'))
    print(meta.get('remote_agent_runtime_id', '') if meta.get('remote_agent_runtime_id') != 'None' else '')
except:
    print('')
")
    if [ ! -z "$ANALYZER_ID" ]; then
        echo "Deletando Reasoning Engine (Analyzer residual): $ANALYZER_ID..."
        gcloud ai reasoning-engines delete $ANALYZER_ID --project=$PROJECT_ID --location=$REGION --quiet || echo "Analyzer RE já removido ou falha."
    fi
    echo '{"remote_agent_runtime_id": "None", "deployment_timestamp": "None"}' > "a2a-pdf-analyzer/deployment_metadata.json"
fi

echo "Deletando Analyzer no Cloud Run..."
gcloud run services delete a2a-pdf-analyzer --project=$PROJECT_ID --region=$REGION --quiet || echo "Analyzer Cloud Run já removido."

echo "✅ Undeploy concluído."
