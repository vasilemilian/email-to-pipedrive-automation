#!/usr/bin/env python3
"""
Gmail service per Google Cloud Functions
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.cloud import secretmanager

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def gmail_service():
    """Crea servizio Gmail usando credenziali cloud"""
    
    creds = None
    
    # In Cloud, usa Secret Manager per le credenziali
    if os.getenv('GOOGLE_CLOUD_PROJECT'):
        creds = get_credentials_from_secret_manager()
    else:
        # Fallback locale per test
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # Se non ci sono credenziali valide, richiedi autorizzazione
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Per il primo setup, usa il flow locale
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva le credenziali per future esecuzioni
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            save_credentials_to_secret_manager(creds)
        else:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    
    return build("gmail", "v1", credentials=creds)

def get_credentials_from_secret_manager():
    """Recupera credenziali da Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        secret_name = "gmail-credentials"
        
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        
        secret_data = response.payload.data.decode("UTF-8")
        creds_info = json.loads(secret_data)
        
        return Credentials.from_authorized_user_info(creds_info, SCOPES)
    except Exception as e:
        print(f"Errore recupero credenziali: {e}")
        return None

def save_credentials_to_secret_manager(creds):
    """Salva credenziali in Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        secret_id = "gmail-credentials"
        
        # Crea il secret se non esiste
        try:
            parent = f"projects/{project_id}"
            secret = {"replication": {"automatic": {}}}
            client.create_secret(
                request={"parent": parent, "secret_id": secret_id, "secret": secret}
            )
        except:
            pass  # Secret già esiste
        
        # Salva la nuova versione
        parent = f"projects/{project_id}/secrets/{secret_id}"
        payload = creds.to_json().encode("UTF-8")
        
        client.add_secret_version(
            request={"parent": parent, "payload": {"data": payload}}
        )
        
        print("✅ Credenziali salvate in Secret Manager")
    except Exception as e:
        print(f"❌ Errore salvataggio credenziali: {e}")