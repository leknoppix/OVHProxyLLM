import uvicorn
import os
import sys

# Configuration de uvicorn pour des logs plus détaillés
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(levelname)s - %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": "/tmp/uvicorn_error.log",  # Fichier de log d'erreurs
        },
        "access_file": {
            "formatter": "access",
            "class": "logging.FileHandler",
            "filename": "/tmp/uvicorn_access.log",  # Fichier de log d'accès
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "file"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access", "access_file"], "level": "INFO", "propagate": False},
    },
}

try:
    # Essayer d'importer depuis le package proxy (pour Docker)
    from proxy.app import app
except ImportError:
    # Si ça ne fonctionne pas, essayer d'importer directement (pour le développement local)
    from app import app

if __name__ == "__main__":
    print("Démarrage du serveur sur http://localhost:8000")
    print("Appuyez sur CTRL+C pour arrêter le serveur")
    
    # S'assurer que l'adresse d'écoute est correcte
    host = "0.0.0.0"  # Écouter sur toutes les interfaces réseau
    port = int(os.environ.get("PORT", 8000))
    
    # Démarrer le serveur avec la configuration des logs
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_config=log_config,
        log_level="debug",
        timeout_keep_alive=120  # Augmenter le timeout pour les connexions persistantes
    ) 