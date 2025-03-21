#!/bin/bash

# Définir des couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
# Utiliser le répertoire courant au lieu d'un chemin absolu
WORKSPACE_DIR="$(pwd)"
PROXY_PORT=8000
WEBUI_PORT=3000
LOG_DIR="/tmp/ovh-llm-logs"
PID_FILE="/tmp/ovh-proxy.pid"

# Déterminer les commandes python et docker-compose à utiliser
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Erreur: Ni python3 ni python ne sont installés. Veuillez installer Python 3.${NC}"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}Erreur: Docker Compose n'est pas installé. Veuillez l'installer.${NC}"
    exit 1
fi

# Créer le répertoire de logs s'il n'existe pas
mkdir -p $LOG_DIR

# Fonction pour afficher un message avec bannière
print_banner() {
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}= OVH LLM WebUI - Interface pour les modèles OVH LLM =${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    echo ""
}

# Fonction pour afficher le message d'aide
show_help() {
    echo -e "${GREEN}Usage:${NC} $0 [option]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  start       Démarrer le proxy et l'interface WebUI"
    echo "  stop        Arrêter le proxy et l'interface WebUI"
    echo "  restart     Redémarrer le proxy et l'interface WebUI"
    echo "  status      Afficher le statut des services"
    echo "  logs        Afficher les logs du proxy"
    echo "  token       Mettre à jour le token OVH"
    echo "  test        Tester le proxy avec une requête simple"
    echo "  help        Afficher ce message d'aide"
    echo ""
}

# Fonction pour démarrer le proxy Python
start_proxy() {
    echo -e "${YELLOW}Démarrage du proxy OVH...${NC}"
    
    # Vérifier si le proxy est déjà en cours d'exécution
    if [ -f "$PID_FILE" ] && ps -p $(cat $PID_FILE) > /dev/null; then
        echo -e "${RED}Le proxy est déjà en cours d'exécution avec PID $(cat $PID_FILE).${NC}"
        return 1
    fi
    
    # Tuer toute instance existante
    pkill -f "$PYTHON_CMD -m proxy.main" > /dev/null 2>&1 || true
    
    # Lancer le serveur avec nohup pour qu'il reste en arrière-plan
    # Utiliser le répertoire courant
    cd $WORKSPACE_DIR
    nohup $PYTHON_CMD -m proxy.main > $LOG_DIR/proxy.log 2>&1 &
    
    # Enregistrer le PID
    echo $! > $PID_FILE
    echo -e "${GREEN}Serveur proxy démarré avec PID $(cat $PID_FILE)${NC}"
    echo -e "${GREEN}Logs disponibles dans $LOG_DIR/proxy.log${NC}"
    
    # Attendre 3 secondes pour que le serveur démarre
    echo -e "${YELLOW}Attente du démarrage du serveur...${NC}"
    sleep 3
    
    # Vérifier que le serveur répond
    if curl -s http://localhost:$PROXY_PORT/health > /dev/null; then
        echo -e "${GREEN}Proxy démarré avec succès et accessible sur http://localhost:$PROXY_PORT${NC}"
        return 0
    else
        echo -e "${RED}Erreur: Le proxy ne répond pas. Vérifiez les logs: $LOG_DIR/proxy.log${NC}"
        echo -e "${YELLOW}Affichage des 10 dernières lignes des logs:${NC}"
        tail -n 10 $LOG_DIR/proxy.log
        return 1
    fi
}

# Fonction pour démarrer OpenWebUI
start_webui() {
    echo -e "${YELLOW}Démarrage de l'interface Web...${NC}"
    
    # Vérifier si docker est installé
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Erreur: Docker n'est pas installé.${NC}"
        return 1
    fi
    
    cd $WORKSPACE_DIR
    $COMPOSE_CMD up -d openwebui
    
    # Vérifier si le conteneur a bien démarré
    sleep 3
    if docker ps | grep -q openwebui; then
        echo -e "${GREEN}Interface Web démarrée avec succès et accessible sur http://localhost:$WEBUI_PORT${NC}"
        return 0
    else
        echo -e "${RED}Erreur: L'interface Web n'a pas démarré correctement. Vérifiez les logs:${NC}"
        echo -e "${YELLOW}docker logs openwebui${NC}"
        return 1
    fi
}

# Fonction pour arrêter le proxy
stop_proxy() {
    echo -e "${YELLOW}Arrêt du proxy OVH...${NC}"
    
    # Vérifier si le fichier PID existe
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        echo -e "${YELLOW}Arrêt du processus avec PID $PID...${NC}"
        kill $PID 2> /dev/null || true
        rm -f $PID_FILE
        echo -e "${GREEN}Proxy arrêté.${NC}"
    else
        # Essayer de trouver le processus sans le fichier PID
        PIDS=$(pgrep -f "$PYTHON_CMD -m proxy.main")
        if [ -n "$PIDS" ]; then
            echo -e "${YELLOW}Processus trouvés: $PIDS. Arrêt en cours...${NC}"
            pkill -f "$PYTHON_CMD -m proxy.main"
            echo -e "${GREEN}Proxy arrêté.${NC}"
        else
            echo -e "${YELLOW}Aucun processus de proxy trouvé.${NC}"
        fi
    fi
}

# Fonction pour arrêter OpenWebUI
stop_webui() {
    echo -e "${YELLOW}Arrêt de l'interface Web...${NC}"
    
    cd $WORKSPACE_DIR
    $COMPOSE_CMD stop openwebui
    
    echo -e "${GREEN}Interface Web arrêtée.${NC}"
}

# Fonction pour afficher le statut des services
show_status() {
    echo -e "${YELLOW}Statut des services:${NC}"
    
    # Vérifier le statut du proxy
    echo -e "${BLUE}Proxy OVH:${NC}"
    if [ -f "$PID_FILE" ] && ps -p $(cat $PID_FILE) > /dev/null; then
        echo -e "  Statut: ${GREEN}En cours d'exécution${NC} (PID: $(cat $PID_FILE))"
        HEALTH=$(curl -s http://localhost:$PROXY_PORT/health)
        if [ $? -eq 0 ]; then
            echo -e "  Santé:  ${GREEN}OK${NC} - $HEALTH"
        else
            echo -e "  Santé:  ${RED}ERREUR${NC} - Le service ne répond pas"
        fi
    else
        echo -e "  Statut: ${RED}Arrêté${NC}"
    fi
    
    # Vérifier le statut de OpenWebUI
    echo -e "${BLUE}Interface Web:${NC}"
    if docker ps | grep -q openwebui; then
        echo -e "  Statut: ${GREEN}En cours d'exécution${NC}"
        echo -e "  URL:    ${GREEN}http://localhost:$WEBUI_PORT${NC}"
    else
        echo -e "  Statut: ${RED}Arrêté${NC}"
    fi
}

# Fonction pour afficher les logs
show_logs() {
    if [ -f "$LOG_DIR/proxy.log" ]; then
        echo -e "${YELLOW}Dernières lignes des logs du proxy:${NC}"
        tail -n 50 $LOG_DIR/proxy.log
        echo ""
        echo -e "${YELLOW}Pour suivre les logs en temps réel:${NC} tail -f $LOG_DIR/proxy.log"
    else
        echo -e "${RED}Aucun fichier de log trouvé à $LOG_DIR/proxy.log${NC}"
    fi
}

# Fonction pour mettre à jour le token OVH
update_token() {
    if [ -z "$1" ]; then
        echo -e "${RED}Erreur: Token OVH non fourni.${NC}"
        echo -e "${YELLOW}Usage:${NC} $0 token <nouveau_token>"
        echo -e "${YELLOW}Pour obtenir un nouveau token, visitez:${NC}"
        echo -e "${BLUE}https://kepler.ai.cloud.ovh.net/v1/oauth/ovh/authorize?iam_action=publicCloudProject:ai:endpoints/call${NC}"
        return 1
    fi
    
    NEW_TOKEN=$1
    
    # Arrêter le proxy s'il est en cours d'exécution
    stop_proxy
    
    # Mettre à jour le token dans le fichier .env
    echo -e "${YELLOW}Mise à jour du token OVH...${NC}"
    mkdir -p "$WORKSPACE_DIR/proxy"
    echo -e "# Configuration du proxy OVH\nOVH_TOKEN_ENDPOINT=$NEW_TOKEN" > "$WORKSPACE_DIR/proxy/.env"
    
    # Redémarrer le proxy
    start_proxy
    
    echo -e "${GREEN}Token OVH mis à jour avec succès.${NC}"
}

# Fonction pour tester le proxy
test_proxy() {
    echo -e "${YELLOW}Test du proxy avec une requête simple...${NC}"
    
    RESPONSE=$(curl -s -X POST http://localhost:$PROXY_PORT/v1/chat/completions \
               -H "Content-Type: application/json" \
               -d '{"model":"mistral-nemo-instruct-2407","messages":[{"role":"user","content":"Bonjour"}],"max_tokens":50}')
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Test réussi. Réponse:${NC}"
        if command -v python3 &> /dev/null; then
            echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        else
            echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
        fi
    else
        echo -e "${RED}Erreur lors du test.${NC}"
    fi
}

# Menu principal
print_banner

case "$1" in
    start)
        start_proxy && start_webui
        # Afficher les instructions après le démarrage
        echo ""
        echo -e "${GREEN}Services démarrés avec succès!${NC}"
        echo -e "${YELLOW}Vous pouvez maintenant accéder à l'interface Web:${NC} http://localhost:$WEBUI_PORT"
        echo -e "${YELLOW}Proxy API disponible sur:${NC} http://localhost:$PROXY_PORT"
        ;;
    stop)
        stop_proxy
        stop_webui
        echo -e "${GREEN}Tous les services ont été arrêtés.${NC}"
        ;;
    restart)
        stop_proxy
        stop_webui
        echo "Redémarrage des services..."
        sleep 2
        start_proxy && start_webui
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    token)
        update_token "$2"
        ;;
    test)
        test_proxy
        ;;
    help|*)
        show_help
        ;;
esac

exit 0 