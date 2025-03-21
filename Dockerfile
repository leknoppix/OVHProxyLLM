FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y wget && apt-get clean

# Copier le contenu du répertoire proxy
COPY proxy/ /app/proxy/

# Installer les dépendances
WORKDIR /app/proxy
RUN pip install --no-cache-dir -r requirements.txt

# Retourner au répertoire principal
WORKDIR /app

# Exposer le port 8000
EXPOSE 8000

# Commande de démarrage
CMD ["python", "-m", "proxy.main"] 