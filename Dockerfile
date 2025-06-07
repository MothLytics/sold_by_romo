FROM python:3.9-slim

WORKDIR /app

# Aggiunta dei file di sistema necessari
COPY requirements.txt .

# Installazione delle dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia dell'applicazione
COPY ./src /app/src
COPY ./templates /app/templates
COPY ./static /app/static
COPY ./sold_by_romo.db /app/sold_by_romo.db

# Esposizione della porta su cui Flask ascolterà
EXPOSE 5000

# Comando di avvio dell'applicazione
CMD ["python", "src/webapp.py"]
