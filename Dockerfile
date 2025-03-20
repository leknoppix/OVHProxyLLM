FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y wget && apt-get clean

# Copier le fichier de dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script Python
COPY script.py .

# Exposer le port 8000
EXPOSE 8000

# Commande de démarrage
CMD ["python", "script.py"] 