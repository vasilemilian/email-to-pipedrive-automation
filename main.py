#!/usr/bin/env python3
"""
Google Cloud Function per automazione Email-to-Pipedrive
Funziona 24/7 senza PC acceso
"""

import os
import json
import datetime
import pandas as pd
from google.cloud import functions_v1
import requests
from email.utils import parsedate_to_datetime
import io
from base64 import urlsafe_b64decode
import sys

# Importa le nostre funzioni
from gmail_service import gmail_service
from pipedrive_operations import create_product_cloud
from excel_processor import process_excel_file

def email_to_pipedrive(request):
    """
    Cloud Function principale - eseguita ogni minuto da Cloud Scheduler
    """
    
    print("🚀 AVVIO CONTROLLO EMAIL CLOUD")
    print(f"⏰ Timestamp: {datetime.datetime.utcnow()}")
    
    try:
        # Controlla email recenti (ultimi 2 minuti)
        result = check_and_process_emails()
        
        if result:
            print(f"✅ EMAIL PROCESSATA: {result}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': f"Email processata: {result}",
                    'timestamp': datetime.datetime.utcnow().isoformat()
                })
            }
        else:
            print("ℹ️  Nessuna nuova email da processare")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': "Nessuna nuova email",
                    'timestamp': datetime.datetime.utcnow().isoformat()
                })
            }
            
    except Exception as e:
        print(f"❌ ERRORE: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.datetime.utcnow().isoformat()
            })
        }

def check_and_process_emails():
    """Controlla e processa nuove email"""
    
    # Configura Gmail service
    service = gmail_service()
    
    # Query per email DA TUTTI gli indirizzi monitorati con Excel
    query = "(from:vasilemilian00@gmail.com OR from:ja@ppl.top OR from:cy@ppl.top OR from:yw@ppl.top) has:attachment filename:xlsx"
    
    # Cerca email recenti
    current_time = datetime.datetime.utcnow()
    two_minutes_ago = current_time - datetime.timedelta(minutes=2)
    
    print(f"🔍 Cerco email dopo: {two_minutes_ago}")
    
    # Ottieni email
    msgs = service.users().messages().list(userId="me", q=query, maxResults=10).execute().get("messages", [])
    
    if not msgs:
        print("📭 Nessuna email trovata")
        return None
    
    # Controlla ogni email per timestamp
    for msg_ref in msgs:
        msg_id = msg_ref['id']
        msg = service.users().messages().get(userId="me", id=msg_id).execute()
        
        # Estrai data email
        email_date = None
        for header in msg['payload'].get('headers', []):
            if header['name'] == 'Date':
                try:
                    email_date = parsedate_to_datetime(header['value'])
                    break
                except:
                    continue
        
        if not email_date:
            continue
        
        # Controllo timing preciso
        time_diff = current_time - email_date.replace(tzinfo=None)
        minutes_old = time_diff.total_seconds() / 60
        
        print(f"📧 Email {msg_id}: {minutes_old:.1f} min fa")
        
        # Solo email fresche (ultimi 2 minuti)
        if minutes_old <= 2.0:
            print(f"✅ Email valida - processando...")
            
            # Estrai allegato Excel
            excel_file = extract_excel_from_email(msg, service, msg_id)
            
            if excel_file:
                # Processa Excel e crea prodotti
                result = process_excel_and_create_products(excel_file)
                return result
    
    return None

def extract_excel_from_email(msg, service, msg_id):
    """Estrae file Excel dall'email"""
    
    parts = (msg.get("payload") or {}).get("parts") or []
    
    def find_excel(parts):
        for p in parts:
            filename = p.get("filename", "")
            if filename.lower().endswith((".xlsx", ".xls")):
                # Controlla che inizi con "DDE"
                if not filename.upper().startswith("DDE"):
                    print(f"📄 Excel ignorato (non DDE): {filename}")
                    continue
                
                print(f"📊 Excel DDE trovato: {filename}")
                
                att_id = p["body"].get("attachmentId")
                if not att_id:
                    continue
                    
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=att_id
                ).execute()
                
                data = att["data"]
                file_bytes = io.BytesIO(urlsafe_b64decode(data))
                print(f"📥 Excel scaricato: {len(file_bytes.getvalue()):,} bytes")
                return file_bytes
                
            if "parts" in p:
                found = find_excel(p["parts"])
                if found:
                    return found
        return None
    
    return find_excel(parts)

def process_excel_and_create_products(excel_file):
    """Processa Excel e crea prodotti in Pipedrive"""
    
    try:
        # Estrai DDE dalla riga 2
        df_header = pd.read_excel(excel_file, nrows=5, header=None)
        dde_code = "DDE_DEFAULT"
        
        # Cerca DDE nella riga 2
        for col_idx, value in df_header.iloc[1].items():
            if pd.notna(value) and str(value).startswith('KF'):
                dde_code = str(value).strip()
                print(f"🏷️  DDE trovato: {dde_code}")
                break
        
        # Processa dati prodotti
        df = pd.read_excel(excel_file, skiprows=10)
        
        if 'NO.' not in df.columns:
            print("❌ Colonna NO. non trovata")
            return None
        
        # Ordina prodotti
        unique_values = df['NO.'].dropna().unique()
        numeric_products = []
        for val in unique_values:
            try:
                numeric_products.append(float(val))
            except (ValueError, TypeError):
                print(f"⚠️  Valore NO. ignorato: {val}")
        
        unique_products = sorted(numeric_products)
        print(f"🔢 Prodotti da creare: {len(unique_products)}")
        
        created_products = []
        
        # Crea ogni prodotto
        for idx, no_value in enumerate(unique_products):
            product_row = df[df['NO.'] == no_value].iloc[0]
            
            # Nome e descrizione
            full_description = str(product_row.get('Product description', f'Prodotto NO.{no_value}'))
            if pd.notna(full_description) and full_description != 'nan' and full_description.strip():
                desc_lines = full_description.split('\n')
                name = desc_lines[0].strip()[:200] if desc_lines else f'Prodotto NO.{no_value}'
                product_description = full_description.strip()[:1000]
            else:
                name = f'Prodotto NO.{no_value}'
                product_description = f'Prodotto NO.{no_value} - Codice: {dde_code}'
            
            # Prezzo
            price_raw = product_row.get(' Price quoted USD', 0)
            try:
                price = float(str(price_raw).replace('€', '').replace('$', '').replace(',', '.').strip())
            except:
                price = 0.0
            
            # Crea prodotto
            product_id = create_product_cloud(
                name=name,
                code=dde_code,
                price=price,
                description=product_description
            )
            
            if product_id:
                created_products.append({
                    'id': product_id,
                    'name': name,
                    'code': dde_code
                })
                print(f"✅ Prodotto creato: {product_id}")
        
        return {
            'products_created': len(created_products),
            'dde_code': dde_code,
            'products': created_products
        }
        
    except Exception as e:
        print(f"❌ Errore processing: {e}")
        raise e