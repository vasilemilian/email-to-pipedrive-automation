#!/bin/bash
# Script per deploy su Google Cloud Functions

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 DEPLOY SISTEMA EMAIL-TO-PIPEDRIVE SU GOOGLE CLOUD${NC}"
echo "========================================================"

# Verifica che gcloud sia installato
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI non installato!${NC}"
    echo "Installa da: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verifica login
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}🔐 Effettua login a Google Cloud...${NC}"
    gcloud auth login
fi

# Imposta variabili
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Nessun progetto Google Cloud configurato!${NC}"
    echo "Esegui: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

FUNCTION_NAME="email-to-pipedrive"
REGION="europe-west1"  # Regione europea
RUNTIME="python39"

echo -e "${GREEN}📋 Configurazione:${NC}"
echo "   Progetto: $PROJECT_ID"
echo "   Funzione: $FUNCTION_NAME"
echo "   Regione: $REGION"
echo ""

# Abilita API necessarie
echo -e "${YELLOW}🔧 Abilitazione API Google Cloud...${NC}"
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable gmail.googleapis.com

# Deploy della Cloud Function
echo -e "${YELLOW}☁️  Deploy Cloud Function...${NC}"
gcloud functions deploy $FUNCTION_NAME \
    --runtime $RUNTIME \
    --trigger-http \
    --allow-unauthenticated \
    --region $REGION \
    --memory 256MB \
    --timeout 540s \
    --entry-point email_to_pipedrive \
    --source .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cloud Function deployata con successo!${NC}"
else
    echo -e "${RED}❌ Errore durante il deploy della Cloud Function${NC}"
    exit 1
fi

# Ottieni URL della function
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region $REGION --format="value(httpsTrigger.url)")
echo -e "${GREEN}🌐 URL Function: $FUNCTION_URL${NC}"

# Crea Cloud Scheduler job (ogni minuto)
echo -e "${YELLOW}⏰ Creazione job Cloud Scheduler...${NC}"
gcloud scheduler jobs create http email-to-pipedrive-scheduler \
    --schedule="* * * * *" \
    --uri=$FUNCTION_URL \
    --http-method=POST \
    --location=$REGION \
    --description="Controlla email ogni minuto per automazione Pipedrive" \
    2>/dev/null || echo -e "${YELLOW}⚠️  Job scheduler già esistente${NC}"

echo ""
echo -e "${GREEN}🎉 SISTEMA DEPLOYATO CON SUCCESSO!${NC}"
echo "========================================================"
echo -e "${GREEN}✅ Sistema attivo 24/7 su Google Cloud${NC}"
echo -e "${GREEN}✅ Controllo email ogni minuto${NC}"
echo -e "${GREEN}✅ Nessun costo quando non in uso${NC}"
echo ""
echo -e "${YELLOW}📋 PROSSIMI PASSI:${NC}"
echo "1. Configura i secrets (credenziali)"
echo "2. Testa la function"
echo "3. Monitora i logs"
echo ""
echo -e "${YELLOW}🔗 Links utili:${NC}"
echo "   Function: https://console.cloud.google.com/functions/details/$REGION/$FUNCTION_NAME?project=$PROJECT_ID"
echo "   Scheduler: https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
echo "   Logs: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"