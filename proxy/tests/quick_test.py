#!/usr/bin/env python
"""
Script de test rapide pour vérifier que le proxy OVH LLM fonctionne correctement
"""

import sys
import requests
import json
import time
import os
import socket

# Déterminer si nous sommes dans un conteneur Docker
def is_running_in_docker():
    # Vérifier si le fichier /.dockerenv existe (présent dans les conteneurs Docker)
    return os.path.exists('/.dockerenv')

# Configuration
# Si nous sommes dans Docker, utiliser le nom du service comme hôte
if is_running_in_docker():
    # Dans Docker, le service est accessible via son nom de service
    SERVER_URL = "http://proxy:8000"
    print("Exécution dans un conteneur Docker, utilisation de l'URL: {}".format(SERVER_URL))
    # Afficher le nom d'hôte pour le débogage
    print("Nom d'hôte: {}".format(socket.gethostname()))
else:
    SERVER_URL = "http://localhost:8000"
    print("Exécution en local, utilisation de l'URL: {}".format(SERVER_URL))

TEST_MODEL = "mistral-7b-instruct-v0.3"
TEST_PROMPT = "Bonjour"

def print_header(message):
    """Affiche un message de titre formaté"""
    print("\n" + "=" * 80)
    print("=" * ((80 - len(message)) // 2) + f" {message} " + "=" * ((80 - len(message)) // 2))
    print("=" * 80)

def test_health():
    """Test de l'endpoint de vérification de santé"""
    print("Test de l'endpoint de vérification de santé...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200 and response.json().get("status") == "ok":
            print("✅ Endpoint de vérification de santé: OK")
            return True
        else:
            print(f"❌ Endpoint de vérification de santé: ÉCHEC (Status code: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Endpoint de vérification de santé: ÉCHEC ({str(e)})")
        return False

def test_models():
    """Test de l'endpoint de liste des modèles"""
    print("Test de l'endpoint de liste des modèles...")
    try:
        response = requests.get(f"{SERVER_URL}/api/models", timeout=5)
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_count = len(models)
            print(f"✅ Endpoint de liste des modèles: OK ({model_count} modèles disponibles)")
            return True
        else:
            print(f"❌ Endpoint de liste des modèles: ÉCHEC (Status code: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Endpoint de liste des modèles: ÉCHEC ({str(e)})")
        return False

def test_chat_completions():
    """Test de l'endpoint de chat completions"""
    print(f"Test de l'endpoint de chat completions avec le modèle {TEST_MODEL}...")
    payload = {
        "model": TEST_MODEL,
        "messages": [
            {"role": "user", "content": TEST_PROMPT}
        ],
        "temperature": 0.7,
        "max_tokens": 10,  # Réduire le nombre de tokens pour accélérer la réponse
        "test_mode": True
    }
    try:
        print(f"Envoi de la requête à {SERVER_URL}/v1/chat/completions avec payload: {json.dumps(payload, indent=2)}")
        start_time = time.time()
        response = requests.post(f"{SERVER_URL}/v1/chat/completions", json=payload, timeout=30)
        elapsed_time = time.time() - start_time
        if response.status_code == 200:
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Endpoint de chat completions: OK ({elapsed_time:.2f}s)")
            print(f"   Réponse: {content[:100]}..." if len(content) > 100 else f"   Réponse: {content}")
            return True
        else:
            print(f"❌ Endpoint de chat completions: ÉCHEC (Status code: {response.status_code})")
            print(f"   Réponse: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Endpoint de chat completions: ÉCHEC ({str(e)})")
        return False

def run_quick_tests():
    """Exécute les tests rapides"""
    print_header("TEST RAPIDE DU PROXY OVH LLM")
    
    health_ok = test_health()
    models_ok = test_models()
    
    # Rendre le test de chat completions optionnel
    chat_test_enabled = os.environ.get("ENABLE_CHAT_TEST", "true").lower() == "true"
    if chat_test_enabled:
        chat_ok = test_chat_completions()
    else:
        print("Test de chat completions désactivé.")
        chat_ok = True
    
    print_header("RÉSUMÉ DES TESTS RAPIDES")
    if health_ok and models_ok and chat_ok:
        print("✅ Tous les tests ont réussi! Le proxy OVH LLM fonctionne correctement.")
        return True
    else:
        print("❌ Certains tests ont échoué. Veuillez vérifier les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)
