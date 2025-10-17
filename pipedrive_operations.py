#!/usr/bin/env python3
"""
Pipedrive operations per Google Cloud Functions
"""

import os
import requests
import time
from google.cloud import secretmanager

def get_pipedrive_credentials():
    """Recupera credenziali Pipedrive da environment o Secret Manager"""
    
    if os.getenv('GOOGLE_CLOUD_PROJECT'):
        # In cloud, usa Secret Manager
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            
            # Recupera domain
            domain_secret = f"projects/{project_id}/secrets/pipedrive-domain/versions/latest"
            domain_response = client.access_secret_version(request={"name": domain_secret})
            domain = domain_response.payload.data.decode("UTF-8")
            
            # Recupera token
            token_secret = f"projects/{project_id}/secrets/pipedrive-token/versions/latest"
            token_response = client.access_secret_version(request={"name": token_secret})
            token = token_response.payload.data.decode("UTF-8")
            
            return domain, token
        except Exception as e:
            print(f"❌ Errore recupero credenziali Pipedrive: {e}")
            return None, None
    else:
        # Locale, usa file .env
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("PD_DOMAIN"), os.getenv("PD_API_TOKEN")

def create_product_cloud(name, code, price=0, description="", unit="pz"):
    """Crea prodotto in Pipedrive da Cloud Function"""
    
    domain, token = get_pipedrive_credentials()
    
    if not domain or not token:
        raise Exception("Credenziali Pipedrive non configurate")
    
    url = f"https://{domain}.pipedrive.com/api/v1/products?api_token={token}"
    
    # Corpo richiesta
    body = {
        "name": name,
        "code": code,
        "visible_to": "3"
    }
    
    # Aggiungi descrizione se presente
    if description and description.strip():
        body["description"] = description.strip()
    
    # Aggiungi prezzo se presente
    if price > 0:
        body["prices"] = [{"currency": "USD", "price": price}]
    
    # Aggiungi unità
    if unit != "pz":
        body["unit"] = unit
    
    # Richiesta con retry
    for attempt in range(3):
        try:
            response = requests.post(
                url, 
                json=body, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 429:
                # Rate limit, aspetta
                time.sleep(2)
                continue
            
            response.raise_for_status()
            
            result = response.json()
            product_id = result.get("data", {}).get("id")
            
            if product_id:
                print(f"✅ Prodotto creato ID: {product_id}")
                return product_id
            else:
                raise Exception(f"Risposta API invalida: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Tentativo {attempt + 1} fallito: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                raise e
    
    return None