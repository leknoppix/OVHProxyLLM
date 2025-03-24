"""
Script de test détaillé pour l'endpoint chat completions de l'API OVH LLM.
Ce script teste l'endpoint avec différentes configurations et enregistre les résultats.
"""

import requests
import json
import time
import sys
import os
import logging
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/chat_test_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL du serveur
SERVER_URL = "http://localhost:8000"

def print_header(message):
    """Affiche un message de titre formaté"""
    header = "\n" + "=" * 80 + "\n" + f" {message} ".center(80, "=") + "\n" + "=" * 80
    logger.info(header)
    print(header)

def test_chat_with_model(model, message="Bonjour", max_tokens=20, temperature=0.5, timeout=60):
    """Teste l'endpoint chat completions avec un modèle spécifique"""
    print_header(f"Test avec le modèle: {model}")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    logger.info(f"Configuration du test:")
    logger.info(f"- Modèle: {model}")
    logger.info(f"- Message: {message}")
    logger.info(f"- Max tokens: {max_tokens}")
    logger.info(f"- Température: {temperature}")
    logger.info(f"- Timeout: {timeout} secondes")
    
    try:
        logger.info(f"Envoi de la requête à {SERVER_URL}/v1/chat/completions")
        logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/v1/chat/completions", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        elapsed_time = time.time() - start_time
        
        logger.info(f"Temps de réponse: {elapsed_time:.2f} secondes")
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Réponse JSON: {json.dumps(data, ensure_ascii=False)}")
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                logger.info(f"Contenu de la réponse: {content}")
                print(f"✅ Test réussi en {elapsed_time:.2f} secondes")
                print(f"Réponse: {content}")
                return True
            else:
                logger.warning(f"Format de réponse inattendu: {json.dumps(data, indent=2)}")
                print(f"❌ Format de réponse inattendu")
                return False
        else:
            logger.error(f"Erreur - Status code: {response.status_code}")
            logger.error(f"Réponse: {response.text}")
            print(f"❌ Erreur - Status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"TIMEOUT après {timeout} secondes")
        print(f"❌ TIMEOUT après {timeout} secondes")
        return False
    except Exception as e:
        logger.error(f"ERREUR: {type(e).__name__}: {str(e)}")
        print(f"❌ ERREUR: {type(e).__name__}: {str(e)}")
        return False

def test_diagnostic():
    """Teste l'endpoint de diagnostic pour voir si l'API OVH est accessible"""
    print_header("Test de l'endpoint de diagnostic")
    
    try:
        logger.info("Envoi de la requête à /diagnostic")
        
        start_time = time.time()
        response = requests.get(f"{SERVER_URL}/diagnostic", timeout=30)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Temps de réponse: {elapsed_time:.2f} secondes")
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Réponse JSON: {json.dumps(data, ensure_ascii=False)}")
            
            # Analyser les résultats du diagnostic
            if "ovh_api_status" in data:
                ovh_status = data["ovh_api_status"]
                logger.info(f"État de l'API OVH: {ovh_status}")
                
                if ovh_status == "ok":
                    print(f"✅ La connexion à l'API OVH fonctionne correctement")
                    return True
                else:
                    logger.error(f"Problème avec la connexion à l'API OVH: {ovh_status}")
                    if "error_details" in data:
                        logger.error(f"Détails de l'erreur: {data['error_details']}")
                    print(f"❌ Problème avec la connexion à l'API OVH: {ovh_status}")
                    return False
            else:
                logger.warning("Pas d'information sur l'état de l'API OVH dans la réponse")
                print("⚠️ Pas d'information sur l'état de l'API OVH dans la réponse")
                return False
        else:
            logger.error(f"Erreur - Status code: {response.status_code}")
            logger.error(f"Réponse: {response.text}")
            print(f"❌ Erreur - Status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"ERREUR: {type(e).__name__}: {str(e)}")
        print(f"❌ ERREUR: {type(e).__name__}: {str(e)}")
        return False

def run_tests():
    """Exécute une série de tests avec différentes configurations"""
    print_header(f"TESTS DE L'ENDPOINT CHAT COMPLETIONS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Vérifier que le serveur est accessible
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code != 200:
            logger.error(f"Le serveur n'est pas accessible correctement. Status code: {response.status_code}")
            print(f"❌ ERREUR: Le serveur n'est pas accessible correctement. Status code: {response.status_code}")
            return
    except Exception as e:
        logger.error(f"Le serveur n'est pas accessible. {str(e)}")
        print(f"❌ ERREUR: Le serveur n'est pas accessible. {str(e)}")
        return
    
    logger.info("Le serveur est accessible")
    print("✅ Le serveur est accessible")
    
    # Test 2: Vérifier l'état de l'API OVH via l'endpoint de diagnostic
    api_ok = test_diagnostic()
    
    if not api_ok:
        logger.warning("L'API OVH semble avoir des problèmes, les tests de chat risquent d'échouer")
        print("⚠️ L'API OVH semble avoir des problèmes, les tests de chat risquent d'échouer")
    
    # Liste des modèles à tester
    models = [
        "llama-3-1-8b-instruct",
        "mistral-7b-instruct-v0.3"
    ]
    
    # Tester chaque modèle
    results = {}
    for model in models:
        # Test avec une requête simple et un timeout long
        result = test_chat_with_model(
            model=model,
            message="Bonjour",
            max_tokens=10,
            timeout=90  # Timeout très long pour s'assurer d'avoir une réponse
        )
        results[model] = result
    
    # Afficher le résumé
    print_header("RÉSUMÉ DES TESTS")
    for model, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"{status} - Test avec le modèle {model}")
        print(f"{status} - Test avec le modèle {model}")
    
    # Résultat global
    if any(results.values()):
        logger.info("Au moins un test a réussi")
        print("\n✅ Au moins un test a réussi")
    else:
        logger.error("Tous les tests ont échoué")
        print("\n❌ Tous les tests ont échoué")
        
    # Suggestions pour résoudre les problèmes
    if not all(results.values()):
        print("\nSuggestions pour résoudre les problèmes:")
        print("1. Vérifiez que le token d'API OVH est valide et correctement configuré")
        print("2. Vérifiez que les endpoints OVH sont accessibles depuis votre serveur")
        print("3. Examinez les logs du serveur pour voir s'il y a des erreurs spécifiques")
        print("4. Essayez de redémarrer le serveur proxy")
        print("5. Vérifiez si votre quota d'API OVH n'est pas épuisé")

if __name__ == "__main__":
    run_tests()
