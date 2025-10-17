# 🚀 GUIDA DEPLOY GOOGLE CLOUD FUNCTIONS

## 📋 SETUP INIZIALE

### 1. Installa Google Cloud CLI
```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### 2. Login e configurazione
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region europe-west1
```

### 3. Crea progetto Google Cloud (se necessario)
```bash
gcloud projects create your-project-name
gcloud config set project your-project-name
```

## 🔐 CONFIGURAZIONE CREDENZIALI

### 1. Crea i secrets per le credenziali
```bash
# Pipedrive Domain
gcloud secrets create pipedrive-domain --data-file=-
# Inserisci: tuo-domain (senza .pipedrive.com)

# Pipedrive Token  
gcloud secrets create pipedrive-token --data-file=-
# Inserisci: il tuo API token

# Gmail Credentials (copia il file credentials.json)
gcloud secrets create gmail-credentials --data-file=credentials.json
```

### 2. Dai permessi alla Cloud Function
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## ☁️ DEPLOY DEL SISTEMA

### 1. Vai nella cartella cloud_deployment
```bash
cd cloud_deployment
```

### 2. Esegui il deploy
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows (PowerShell)
# Esegui i comandi manualmente dal file deploy.sh
```

### 3. Deploy manuale (se preferisci)
```bash
gcloud functions deploy email-to-pipedrive \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --region europe-west1 \
    --memory 256MB \
    --timeout 540s \
    --entry-point email_to_pipedrive \
    --source .
```

## ⏰ CONFIGURAZIONE SCHEDULER

### Crea job per esecuzione ogni minuto
```bash
FUNCTION_URL=$(gcloud functions describe email-to-pipedrive --region europe-west1 --format="value(httpsTrigger.url)")

gcloud scheduler jobs create http email-to-pipedrive-scheduler \
    --schedule="* * * * *" \
    --uri=$FUNCTION_URL \
    --http-method=POST \
    --location=europe-west1 \
    --description="Controlla email ogni minuto"
```

## 🧪 TEST DEL SISTEMA

### 1. Test manuale della function
```bash
# Ottieni URL
FUNCTION_URL=$(gcloud functions describe email-to-pipedrive --region europe-west1 --format="value(httpsTrigger.url)")

# Test con curl
curl -X POST $FUNCTION_URL
```

### 2. Monitora i logs
```bash
gcloud functions logs read email-to-pipedrive --region europe-west1 --limit=50
```

### 3. Test completo
1. Invia email DA vasilemilian00@gmail.com
2. Con allegato Excel che inizia con "DDE"
3. Aspetta 1 minuto
4. Controlla logs e Pipedrive

## 💰 COSTI STIMATI

### Google Cloud Functions - Livello gratuito:
- **2M invocazioni/mese**: GRATIS
- **400,000 GB-seconds**: GRATIS
- **200,000 GHz-seconds**: GRATIS

### Il nostro uso (1 controllo/minuto):
- **43,200 invocazioni/mese**: GRATIS ✅
- **Memoria**: ~10MB per 1s = 432 GB-seconds/mese: GRATIS ✅
- **CPU**: Minima: GRATIS ✅

**RISULTATO: COMPLETAMENTE GRATUITO! 🎉**

## 🔧 TROUBLESHOOTING

### Errore permessi
```bash
gcloud auth application-default login
```

### Errore API non abilitata
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Problemi Gmail
1. Verifica che credentials.json sia corretto
2. Controlla che Gmail API sia abilitata
3. Ricrea il token Gmail se necessario

### Debug logs
```bash
# Logs in tempo reale
gcloud functions logs tail email-to-pipedrive --region europe-west1

# Logs dettagliati
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=email-to-pipedrive" --limit=20 --format="table(timestamp,severity,textPayload)"
```

## 📱 MONITORAGGIO

### Dashboard Google Cloud
- **Functions**: https://console.cloud.google.com/functions
- **Scheduler**: https://console.cloud.google.com/cloudscheduler  
- **Logs**: https://console.cloud.google.com/logs
- **Secrets**: https://console.cloud.google.com/security/secret-manager

### Alerts (opzionale)
Configura alerting per errori o failures nella console Google Cloud.

## 🎯 RISULTATO FINALE

✅ **Sistema 24/7** - Funziona sempre, anche PC spento
✅ **Controllo ogni minuto** - Nessuna email persa  
✅ **Completamente gratuito** - Dentro i limiti free tier
✅ **Scalabile automaticamente** - Google gestisce tutto
✅ **Logs completi** - Monitoraggio facile
✅ **Sicuro** - Credenziali in Secret Manager