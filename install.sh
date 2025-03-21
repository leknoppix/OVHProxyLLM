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

# Vérifier si les packages Python requis sont déjà installés
check_python_packages() {
    echo -e "${YELLOW}Vérification des packages Python requis...${NC}"
    
    # Liste des packages à vérifier
    PACKAGES=("fastapi" "uvicorn" "requests" "dotenv" "PIL")
    MISSING_PACKAGES=()
    
    for pkg in "${PACKAGES[@]}"; do
        if ! $PYTHON_CMD -c "import $pkg" &> /dev/null; then
            MISSING_PACKAGES+=("$pkg")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
        echo -e "${GREEN}Tous les packages Python requis sont déjà installés.${NC}"
        return 0
    else
        echo -e "${YELLOW}Packages manquants: ${MISSING_PACKAGES[*]}${NC}"
        return 1
    fi
}

# Installer les dépendances Python
install_python_dependencies() {
    # Vérifier d'abord si tous les packages sont déjà installés
    if check_python_packages; then
        echo -e "${GREEN}Aucune installation supplémentaire n'est nécessaire.${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Installation des dépendances Python...${NC}"
    
    # Détecter le type de système
    IS_DEBIAN=0
    IS_ARCH=0
    
    if [ -f "/etc/debian_version" ]; then
        IS_DEBIAN=1
        echo -e "${BLUE}Système basé sur Debian/Ubuntu détecté.${NC}"
    elif [ -f "/etc/arch-release" ]; then
        IS_ARCH=1
        echo -e "${BLUE}Système Arch Linux détecté.${NC}"
    fi
    
    # Première tentative: installation utilisateur standard
    echo -e "${YELLOW}Tentative d'installation en mode utilisateur...${NC}"
    $PIP_CMD install --user -r requirements.txt &> /tmp/pip_install_log.txt
    
    # Vérifier si l'installation a réussi
    if check_python_packages; then
        echo -e "${GREEN}Dépendances Python installées avec succès en mode utilisateur.${NC}"
        # Ajouter ~/.local/bin au PATH si nécessaire
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo -e "${YELLOW}Ajout temporaire de ~/.local/bin au PATH pour cette session.${NC}"
            export PATH="$HOME/.local/bin:$PATH"
        fi
        return 0
    fi
    
    # Si la première tentative échoue à cause d'un environnement géré en externe
    if grep -q "externally-managed-environment" /tmp/pip_install_log.txt; then
        # Selon le type de système, proposer différentes solutions
        if [ $IS_DEBIAN -eq 1 ]; then
            echo -e "${YELLOW}Tentative d'installation avec --break-system-packages (Debian/Ubuntu)...${NC}"
            $PIP_CMD install --user --break-system-packages -r requirements.txt
            
            if check_python_packages; then
                echo -e "${GREEN}Dépendances Python installées avec succès.${NC}"
                return 0
            fi
            
            echo -e "${YELLOW}Installation via apt...${NC}"
            echo -e "${BLUE}Vous pouvez installer les packages via apt:${NC}"
            echo -e "${YELLOW}sudo apt install python3-fastapi python3-uvicorn python3-requests python3-dotenv python3-pil${NC}"
            
        elif [ $IS_ARCH -eq 1 ]; then
            echo -e "${YELLOW}Tentative d'installation avec --break-system-packages (Arch Linux)...${NC}"
            $PIP_CMD install --user --break-system-packages -r requirements.txt
            
            if check_python_packages; then
                echo -e "${GREEN}Dépendances Python installées avec succès.${NC}"
                return 0
            fi
            
            echo -e "${YELLOW}Installation via pacman...${NC}"
            echo -e "${BLUE}Vous pouvez installer les packages via pacman:${NC}"
            echo -e "${YELLOW}sudo pacman -S python-fastapi python-uvicorn python-requests python-dotenv python-pillow${NC}"
        else
            # Pour les autres systèmes
            echo -e "${YELLOW}Tentative d'installation avec --break-system-packages...${NC}"
            $PIP_CMD install --user --break-system-packages -r requirements.txt
            
            if check_python_packages; then
                echo -e "${GREEN}Dépendances Python installées avec succès.${NC}"
                return 0
            fi
        fi
    fi
    
    # Si aucune des méthodes n'a fonctionné
    echo -e "${RED}Échec de l'installation automatique des packages Python.${NC}"
    echo -e "${YELLOW}Options alternatives:${NC}"
    echo -e ""
    echo -e "1. ${YELLOW}Installer manuellement avec break-system-packages:${NC}"
    echo -e "   ${YELLOW}$PIP_CMD install --user --break-system-packages fastapi==0.104.1 uvicorn==0.23.2 requests==2.31.0 python-dotenv==1.0.0 Pillow==10.1.0${NC}"
    echo -e ""
    echo -e "2. ${YELLOW}Installer via le gestionnaire de paquets système:${NC}"
    
    if [ $IS_DEBIAN -eq 1 ]; then
        echo -e "   ${YELLOW}sudo apt install python3-fastapi python3-uvicorn python3-requests python3-dotenv python3-pil${NC}"
    elif [ $IS_ARCH -eq 1 ]; then
        echo -e "   ${YELLOW}sudo pacman -S python-fastapi python-uvicorn python-requests python-dotenv python-pillow${NC}"
    fi
    
    echo -e ""
    echo -e "3. ${BLUE}Continuer sans installation supplémentaire:${NC}"
    echo -e "   ${YELLOW}Si vous avez déjà installé les bibliothèques requises via d'autres méthodes, vous pouvez continuer.${NC}"
    echo -e ""
    
    # Demander à l'utilisateur s'il veut continuer ou non
    read -p "Voulez-vous continuer l'installation malgré ce problème? (o/n) " USER_CHOICE
    
    if [[ "$USER_CHOICE" == "o" || "$USER_CHOICE" == "O" || "$USER_CHOICE" == "oui" || "$USER_CHOICE" == "Oui" ]]; then
        echo -e "${YELLOW}Poursuite de l'installation...${NC}"
        return 0
    else
        echo -e "${RED}Installation interrompue.${NC}"
        exit 1
    fi
}

# Configurer le fichier .env dans le répertoire proxy
configure_proxy_env_file() {
    echo -e "${YELLOW}Configuration du fichier .env pour le proxy...${NC}"
    
    # Créer le répertoire proxy s'il n'existe pas
    mkdir -p proxy
    
    # Vérifier si le fichier .env existe
    if [ -f "proxy/.env" ]; then
        echo -e "Le fichier proxy/.env existe déjà."
    else
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
        
        echo -e "${GREEN}Fichier proxy/.env créé avec succès.${NC}"
    fi
}

# Configurer le fichier .env à la racine pour Cloudflare Tunnel
configure_cloudflare_tunnel() {
    echo -e "${YELLOW}Configuration de Cloudflare Tunnel...${NC}"
    
    # Vérifier si le fichier .env existe à la racine
    if [ -f ".env" ] && grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env; then
        echo -e "Le fichier .env avec configuration Cloudflare existe déjà."
        return 0
    fi
    
    # Demander si l'utilisateur souhaite configurer Cloudflare Tunnel
    echo -e "${BLUE}Souhaitez-vous configurer Cloudflare Tunnel pour exposer l'application sur Internet?${NC}"
    read -p "Configurer Cloudflare Tunnel? (o/n): " SETUP_CLOUDFLARE
    
    if [[ "$SETUP_CLOUDFLARE" == "o" || "$SETUP_CLOUDFLARE" == "O" || "$SETUP_CLOUDFLARE" == "oui" || "$SETUP_CLOUDFLARE" == "Oui" ]]; then
        echo -e "${BLUE}Pour utiliser Cloudflare Tunnel, vous avez besoin d'un token.${NC}"
        echo -e "${BLUE}Vous pouvez en créer un sur:${NC}"
        echo -e "${YELLOW}https://dash.cloudflare.com/?to=/:account/workers-and-pages${NC}"
        echo ""
        
        read -p "Entrez votre token Cloudflare Tunnel: " CLOUDFLARE_TOKEN
        
        # Créer ou mettre à jour le fichier .env à la racine
        if [ -f ".env" ]; then
            # Ajouter le token à un fichier existant
            if ! grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env; then
                echo "" >> .env
                echo "# Configuration Cloudflare Tunnel" >> .env
                echo "CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TOKEN}" >> .env
            else
                # Remplacer le token existant
                sed -i "s/CLOUDFLARE_TUNNEL_TOKEN=.*/CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TOKEN}/" .env
            fi
        else
            # Créer un nouveau fichier .env
            cat > .env << EOF
# Configuration Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TOKEN}
EOF
        fi
        
        echo -e "${GREEN}Configuration Cloudflare Tunnel terminée avec succès.${NC}"
        
        # Mettre à jour le fichier proxy/.env pour ajouter le token Cloudflare
        if [ -f "proxy/.env" ]; then
            if ! grep -q "CLOUDFLARE_TUNNEL_TOKEN" proxy/.env; then
                echo "" >> proxy/.env
                echo "# Configuration Cloudflare Tunnel" >> proxy/.env
                echo "CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TOKEN}" >> proxy/.env
            else
                # Remplacer le token existant
                sed -i "s/CLOUDFLARE_TUNNEL_TOKEN=.*/CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TOKEN}/" proxy/.env
            fi
        fi
    else
        echo -e "${YELLOW}Configuration de Cloudflare Tunnel ignorée.${NC}"
    fi
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
    
    if [ ! -d "proxy" ]; then
        echo -e "${RED}Attention: Répertoire proxy manquant.${NC}"
        echo -e "${YELLOW}Vérifiez que vous avez cloné le dépôt complet.${NC}"
        return 1
    fi
    
    # Vérifier un des fichiers principaux du module proxy (app.py ou main.py)
    if [ ! -f "proxy/app.py" ] && [ ! -f "proxy/main.py" ]; then
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
    
    # Configurer le fichier .env pour le proxy
    configure_proxy_env_file
    
    # Configurer Cloudflare Tunnel
    configure_cloudflare_tunnel
    
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
    
    # Afficher des instructions pour Cloudflare Tunnel si configuré
    if [ -f ".env" ] && grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env; then
        echo -e "${YELLOW}Votre application est configurée avec Cloudflare Tunnel et sera accessible via Internet.${NC}"
        echo -e "${YELLOW}Pour vérifier l'état du tunnel, consultez votre tableau de bord Cloudflare:${NC}"
        echo -e "${BLUE}https://dash.cloudflare.com/?to=/:account/workers-and-pages${NC}"
        echo ""
    fi
    
    echo -e "${YELLOW}Pour obtenir de l'aide:${NC}"
    echo -e "${BLUE}./ovh-llm-webui.sh help${NC}"
    echo ""
    echo -e "${YELLOW}Note: Les dépendances Python ont été installées en mode utilisateur.${NC}"
    echo -e "${YELLOW}Si vous rencontrez des problèmes, vérifiez que ~/.local/bin est dans votre PATH.${NC}"
}

# Exécuter la fonction principale
main 