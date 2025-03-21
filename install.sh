#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Bannière
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}= OVH LLM WebUI - Script d'installation =${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""

# Vérifier les prérequis
echo -e "${YELLOW}Vérification des prérequis...${NC}"

# Vérifier Python
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo -e "${RED}Python 3 n'est pas installé. Veuillez l'installer avant de continuer.${NC}"
    exit 1
else
    echo -e "${GREEN}Python version $python_version détectée.${NC}"
fi

# Vérifier pip
pip_version=$(pip3 --version 2>&1 | awk '{print $2}')
if [[ -z "$pip_version" ]]; then
    echo -e "${RED}pip n'est pas installé. Installation en cours...${NC}"
    apt-get update && apt-get install -y python3-pip || sudo apt-get update && sudo apt-get install -y python3-pip
    if [ $? -ne 0 ]; then
        echo -e "${RED}Impossible d'installer pip. Veuillez l'installer manuellement.${NC}"
        exit 1
    fi
    pip_version=$(pip3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}pip version $pip_version installé.${NC}"
else
    echo -e "${GREEN}pip version $pip_version détecté.${NC}"
fi

# Vérifier Docker
docker_version=$(docker --version 2>&1 | awk '{print $3}' | tr -d ',')
if [[ -z "$docker_version" ]]; then
    echo -e "${RED}Docker n'est pas installé. Veuillez l'installer avant de continuer.${NC}"
    echo -e "${YELLOW}Vous pouvez l'installer avec: curl -fsSL https://get.docker.com | sh${NC}"
    exit 1
else
    echo -e "${GREEN}Docker version $docker_version détecté.${NC}"
fi

# Vérifier Docker Compose
compose_version=$(docker-compose --version 2>&1 | awk '{print $3}' | tr -d ',')
if [[ -z "$compose_version" ]]; then
    echo -e "${RED}Docker Compose n'est pas installé. Veuillez l'installer avant de continuer.${NC}"
    exit 1
else
    echo -e "${GREEN}Docker Compose version $compose_version détecté.${NC}"
fi

# Création du fichier requirements.txt si nécessaire
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Création du fichier requirements.txt...${NC}"
    cat > requirements.txt << EOL
fastapi==0.104.1
uvicorn==0.23.2
requests==2.31.0
python-dotenv==1.0.0
Pillow==10.1.0
EOL
    echo -e "${GREEN}Fichier requirements.txt créé avec succès.${NC}"
fi

# Installation des dépendances Python
echo -e "${YELLOW}Installation des dépendances Python...${NC}"
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'installation des dépendances Python.${NC}"
    exit 1
fi
echo -e "${GREEN}Dépendances Python installées avec succès.${NC}"

# Vérification de l'existence du fichier .env
if [ ! -f "proxy/.env" ]; then
    echo -e "${YELLOW}Le fichier proxy/.env n'existe pas. Création d'un fichier .env par défaut...${NC}"
    
    # Demander le token OVH
    echo -e "${YELLOW}Veuillez entrer votre token OVH (ou laissez vide pour configurer plus tard) :${NC}"
    read -r OVH_TOKEN
    
    if [ -z "$OVH_TOKEN" ]; then
        OVH_TOKEN="VOTRE_TOKEN_ICI"
        echo -e "${YELLOW}Aucun token fourni. Vous devrez configurer le token plus tard avec ./ovh-llm-webui.sh token <votre_token>${NC}"
    fi
    
    # Créer le répertoire proxy s'il n'existe pas
    mkdir -p proxy
    
    # Créer le fichier .env
    echo -e "# Configuration du proxy OVH\nOVH_TOKEN_ENDPOINT=$OVH_TOKEN" > "proxy/.env"
    echo -e "${GREEN}Fichier proxy/.env créé avec succès.${NC}"
fi

# Ajouter les permissions d'exécution au script principal
chmod +x ovh-llm-webui.sh
echo -e "${GREEN}Permissions d'exécution ajoutées au script ovh-llm-webui.sh${NC}"

# Vérifier l'existence du module proxy
if [ ! -d "proxy" ] || [ ! -f "proxy/app.py" ]; then
    echo -e "${YELLOW}Le module proxy n'est pas complet. Vérifiez que vous avez bien cloné tout le répertoire.${NC}"
    echo -e "${YELLOW}Ou exécutez 'git clone https://github.com/votre-repo/ovh-llm-webui.git' pour obtenir la dernière version.${NC}"
fi

echo -e "${GREEN}Installation terminée avec succès!${NC}"
echo -e "${YELLOW}Vous pouvez maintenant démarrer l'application avec :${NC} ./ovh-llm-webui.sh start" 