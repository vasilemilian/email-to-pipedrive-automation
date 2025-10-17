# Usa Python 3.11 slim
FROM python:3.11-slim

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutti i file dell'applicazione
COPY . .

# Esponi porta 8080 (richiesta da Cloud Run)
EXPOSE 8080

# Comando per avviare l'app
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app