#!/bin/bash

# Définir des couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables pour suivre les dépendances manquantes
MISSING_DEPS=0

# Affiche une bannière
print_banner() {
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}= OVH LLM WebUI - Script d'installation =${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    echo ""
}

# Vérification des prérequis sans installation automatique
check_prerequisites() {
    echo -e "${YELLOW}Vérification des prérequis...${NC}"
    
    # Vérifier Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        echo -e "Python version ${GREEN}$PYTHON_VERSION${NC} détectée."
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version | awk '{print $2}')
        echo -e "Python version ${GREEN}$PYTHON_VERSION${NC} détectée."
    else
        echo -e "${RED}[MANQUANT] Python n'est pas installé.${NC}"
        MISSING_DEPS=1
    fi
    
    # Vérifier pip
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        PIP_VERSION=$(pip3 --version | awk '{print $2}')
        echo -e "pip version ${GREEN}$PIP_VERSION${NC} détecté avec la commande 'pip3'."
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        PIP_VERSION=$(pip --version | awk '{print $2}')
        echo -e "pip version ${GREEN}$PIP_VERSION${NC} détecté avec la commande 'pip'."
    else
        echo -e "${RED}[MANQUANT] pip n'est pas installé.${NC}"
        MISSING_DEPS=1
    fi
    
    # Vérifier Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
        echo -e "Docker version ${GREEN}$DOCKER_VERSION${NC} détecté."
    else
        echo -e "${RED}[MANQUANT] Docker n'est pas installé.${NC}"
        MISSING_DEPS=1
    fi
    
    # Vérifier Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | tr -d ',')
        echo -e "Docker Compose version ${GREEN}$COMPOSE_VERSION${NC} détecté."
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}' | tr -d ',')
        echo -e "Docker Compose version ${GREEN}$COMPOSE_VERSION${NC} détecté."
    else
        echo -e "${RED}[MANQUANT] Docker Compose n'est pas installé.${NC}"
        MISSING_DEPS=1
    fi
    
    # Afficher des instructions si des dépendances sont manquantes
    if [ $MISSING_DEPS -ne 0 ]; then
        echo ""
        echo -e "${RED}Certaines dépendances requises sont manquantes.${NC}"
        echo -e "${YELLOW}Veuillez installer les dépendances manquantes avant de continuer:${NC}"
        echo ""
        
        if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
            echo -e "${BLUE}Pour installer Python:${NC}"
            echo -e "  - Ubuntu/Debian: ${YELLOW}sudo apt install python3 python3-pip${NC}"
            echo -e "  - CentOS/RHEL: ${YELLOW}sudo dnf install python3 python3-pip${NC}"
            echo -e "  - Arch Linux: ${YELLOW}sudo pacman -S python python-pip${NC}"
            echo -e "  - Windows: ${YELLOW}Téléchargez depuis https://www.python.org/downloads/${NC}"
            echo ""
        fi
        
        if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
            echo -e "${BLUE}Pour installer pip:${NC}"
            echo -e "  - Ubuntu/Debian: ${YELLOW}sudo apt install python3-pip${NC}"
            echo -e "  - CentOS/RHEL: ${YELLOW}sudo dnf install python3-pip${NC}"
            echo -e "  - Arch Linux: ${YELLOW}sudo pacman -S python-pip${NC}"
            echo ""
        fi
        
        if ! command -v docker &> /dev/null; then
            echo -e "${BLUE}Pour installer Docker:${NC}"
            echo -e "  - Toutes plateformes: ${YELLOW}https://docs.docker.com/get-docker/${NC}"
            echo ""
        fi
        
        if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
            echo -e "${BLUE}Pour installer Docker Compose:${NC}"
            echo -e "  - Toutes plateformes: ${YELLOW}https://docs.docker.com/compose/install/${NC}"
            echo ""
        fi
        
        echo -e "${YELLOW}Une fois les dépendances installées, relancez ce script.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Tous les prérequis sont installés!${NC}"
    echo ""
}

# Créer le fichier requirements.txt
create_requirements_file() {
    echo -e "${YELLOW}Création du fichier requirements.txt...${NC}"
    
    if [ -f "requirements.txt" ]; then
        echo -e "Le fichier requirements.txt existe déjà."
        return 0
    fi
    
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.23.2
requests==2.31.0
python-dotenv==1.0.0
Pillow==10.1.0
EOF
    
    echo -e "${GREEN}Fichier requirements.txt créé avec succès.${NC}"
}

# Installer les dépendances Python
install_python_dependencies() {
    echo -e "${YELLOW}Installation des dépendances Python en mode utilisateur...${NC}"
    
    # Mettre à jour pip
    $PIP_CMD install --user --upgrade pip
    
    # Installer les dépendances
    $PIP_CMD install --user -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Erreur lors de l'installation des dépendances Python.${NC}"
        echo -e "${YELLOW}Si vous utilisez Arch Linux ou un système avec un environnement Python géré:${NC}"
        
        echo -e "${BLUE}Options alternatives:${NC}"
        echo -e "1. ${YELLOW}Utiliser l'option --break-system-packages:${NC}"
        echo -e "   ${YELLOW}$PIP_CMD install --user --break-system-packages -r requirements.txt${NC}"
        echo -e ""
        echo -e "2. ${YELLOW}Installer les packages via votre gestionnaire de paquets:${NC}"
        echo -e "   Sur Arch Linux: ${YELLOW}sudo pacman -S python-fastapi python-uvicorn python-requests python-dotenv python-pillow${NC}"
        
        exit 1
    fi
    
    # Vérifier que les packages sont bien installés
    echo -e "${YELLOW}Vérification de l'installation des packages...${NC}"
    if $PYTHON_CMD -c "import fastapi, uvicorn, requests, dotenv, PIL" &> /dev/null; then
        echo -e "${GREEN}Tous les packages nécessaires sont installés.${NC}"
    else
        echo -e "${YELLOW}Attention: Certains packages ne semblent pas correctement installés.${NC}"
        echo -e "${YELLOW}Utilisez la commande suivante pour voir le chemin de recherche Python:${NC}"
        echo -e "${BLUE}$PYTHON_CMD -c 'import sys; print(sys.path)'${NC}"
    fi
    
    echo -e "${GREEN}Dépendances Python installées avec succès en mode utilisateur.${NC}"
    echo -e "${YELLOW}Note: Pour exécuter le proxy, assurez-vous que ~/.local/bin est dans votre PATH.${NC}"
    
    # Ajouter ~/.local/bin au PATH si nécessaire
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}Ajout temporaire de ~/.local/bin au PATH pour cette session.${NC}"
        export PATH="$HOME/.local/bin:$PATH"
    fi
}

# Configurer le fichier .env
configure_env_file() {
    echo -e "${YELLOW}Configuration du fichier .env...${NC}"
    
    # Créer le répertoire proxy s'il n'existe pas
    mkdir -p proxy
    
    # Vérifier si le fichier .env existe
    if [ -f "proxy/.env" ]; then
        echo -e "Le fichier .env existe déjà."
        return 0
    fi
    
    # Demander le token OVH
    echo -e "${BLUE}Pour utiliser les modèles OVH LLM, vous avez besoin d'un token.${NC}"
    echo -e "${BLUE}Vous pouvez l'obtenir ici:${NC}"
    echo -e "${YELLOW}https://kepler.ai.cloud.ovh.net/v1/oauth/ovh/authorize?iam_action=publicCloudProject:ai:endpoints/call${NC}"
    echo ""
    
    read -p "Entrez votre token OVH (ou laissez vide pour configurer plus tard): " OVH_TOKEN
    
    # Créer le fichier .env
    cat > proxy/.env << EOF
# Configuration du proxy OVH
OVH_TOKEN_ENDPOINT=${OVH_TOKEN}
EOF
    
    echo -e "${GREEN}Fichier .env créé avec succès.${NC}"
}

# Rendre le script principal exécutable
make_script_executable() {
    echo -e "${YELLOW}Configuration des permissions d'exécution...${NC}"
    
    if [ -f "ovh-llm-webui.sh" ]; then
        chmod +x ovh-llm-webui.sh
        echo -e "${GREEN}Script principal rendu exécutable.${NC}"
    else
        echo -e "${RED}Attention: Script principal 'ovh-llm-webui.sh' non trouvé.${NC}"
        echo -e "${YELLOW}Vérifiez que vous avez cloné le dépôt complet.${NC}"
    fi
}

# Vérifier l'intégrité du module proxy
check_proxy_module() {
    echo -e "${YELLOW}Vérification de l'intégrité du module proxy...${NC}"
    
    if [ ! -d "proxy" ] || [ ! -f "proxy/app.py" ]; then
        echo -e "${RED}Attention: Module proxy incomplet ou manquant.${NC}"
        echo -e "${YELLOW}Vérifiez que vous avez cloné le dépôt complet ou utilisez:${NC}"
        echo -e "${YELLOW}git clone [URL_REPO] && cd [NOM_REPO]${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Module proxy trouvé.${NC}"
    return 0
}

# Fonction principale
main() {
    print_banner
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Créer le fichier requirements.txt
    create_requirements_file
    
    # Installer les dépendances Python
    install_python_dependencies
    
    # Configurer le fichier .env
    configure_env_file
    
    # Rendre le script principal exécutable
    make_script_executable
    
    # Vérifier l'intégrité du module proxy
    check_proxy_module
    
    # Message de succès
    echo ""
    echo -e "${GREEN}=======================================================${NC}"
    echo -e "${GREEN}Installation terminée avec succès!${NC}"
    echo -e "${GREEN}=======================================================${NC}"
    echo ""
    echo -e "${YELLOW}Pour démarrer l'application:${NC}"
    echo -e "${BLUE}./ovh-llm-webui.sh start${NC}"
    echo ""
    echo -e "${YELLOW}Si vous n'avez pas encore configuré votre token OVH:${NC}"
    echo -e "${BLUE}./ovh-llm-webui.sh token [VOTRE_TOKEN]${NC}"
    echo ""
    echo -e "${YELLOW}Pour obtenir de l'aide:${NC}"
    echo -e "${BLUE}./ovh-llm-webui.sh help${NC}"
    echo ""
    echo -e "${YELLOW}Note: Les dépendances Python ont été installées en mode utilisateur.${NC}"
    echo -e "${YELLOW}Si vous rencontrez des problèmes, vérifiez que ~/.local/bin est dans votre PATH.${NC}"
}

# Exécuter la fonction principale
main 