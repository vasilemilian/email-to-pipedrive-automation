#!/usr/bin/env python3
"""
Flask app wrapper per Cloud Run
"""
import os
from flask import Flask, request, jsonify
from main import email_to_pipedrive

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def trigger_email_check():
    """Endpoint per triggere il controllo email"""
    try:
        # Esegui il controllo email
        result = email_to_pipedrive(request)
        return jsonify({"status": "success", "message": "Email check completed", "result": str(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "email-to-pipedrive"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)