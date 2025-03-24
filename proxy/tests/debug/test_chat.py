"""
Script de test spécifique pour l'endpoint chat completions de l'API OVH LLM.
Ce script teste différentes configurations pour identifier le problème.
"""

import requests
import json
import time
import sys
import os

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# URL du serveur
SERVER_URL = "http://localhost:8000"

def print_header(message):
    """Affiche un message de titre formaté"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)

def test_chat_with_config(model, messages, max_tokens=20, temperature=0.5, timeout=10, test_name="Test par défaut"):
    """Teste l'endpoint chat completions avec une configuration spécifique"""
    print_header(f"Test: {test_name}")
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    print(f"Configuration du test:")
    print(f"- Modèle: {model}")
    print(f"- Nombre de messages: {len(messages)}")
    print(f"- Max tokens: {max_tokens}")
    print(f"- Température: {temperature}")
    print(f"- Timeout: {timeout} secondes")
    
    try:
        print(f"\nEnvoi de la requête à {SERVER_URL}/v1/chat/completions")
        
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/v1/chat/completions", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        elapsed_time = time.time() - start_time
        
        print(f"Temps de réponse: {elapsed_time:.2f} secondes")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                print(f"Réponse reçue: {content}")
                return True
            else:
                print(f"Format de réponse inattendu: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"Erreur - Status code: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"TIMEOUT après {timeout} secondes")
        return False
    except Exception as e:
        print(f"ERREUR: {type(e).__name__}: {str(e)}")
        return False

def run_tests():
    """Exécute une série de tests avec différentes configurations"""
    print_header("TESTS DE L'ENDPOINT CHAT COMPLETIONS")
    
    # Test 1: Vérifier que le serveur est accessible
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ ERREUR: Le serveur n'est pas accessible correctement. Status code: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ ERREUR: Le serveur n'est pas accessible. {str(e)}")
        return
    
    print("✅ Le serveur est accessible")
    
    # Liste des tests à exécuter
    tests = [
        {
            "name": "Test minimal avec llama-3-1-8b-instruct",
            "model": "llama-3-1-8b-instruct",
            "messages": [{"role": "user", "content": "Bonjour"}],
            "max_tokens": 10,
            "timeout": 15
        },
        {
            "name": "Test minimal avec mistral-7b-instruct-v0.3",
            "model": "mistral-7b-instruct-v0.3",
            "messages": [{"role": "user", "content": "Bonjour"}],
            "max_tokens": 10,
            "timeout": 15
        },
        {
            "name": "Test avec l'endpoint Ollama compatible",
            "use_ollama_endpoint": True,
            "model": "mistral-7b-instruct-v0.3",
            "messages": [{"role": "user", "content": "Bonjour"}],
            "max_tokens": 10,
            "timeout": 15
        }
    ]
    
    # Exécuter les tests
    results = []
    for test in tests:
        if test.get("use_ollama_endpoint", False):
            # Test avec l'endpoint Ollama compatible
            print_header(f"Test: {test['name']}")
            
            payload = {
                "model": test["model"],
                "prompt": test["messages"][0]["content"],
                "options": {
                    "temperature": test.get("temperature", 0.5),
                    "num_predict": test.get("max_tokens", 10)
                }
            }
            
            try:
                print(f"\nEnvoi de la requête à {SERVER_URL}/api/chat")
                
                start_time = time.time()
                response = requests.post(
                    f"{SERVER_URL}/api/chat", 
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=test.get("timeout", 15)
                )
                elapsed_time = time.time() - start_time
                
                print(f"Temps de réponse: {elapsed_time:.2f} secondes")
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Réponse reçue: {json.dumps(data, indent=2)}")
                    results.append(True)
                else:
                    print(f"Erreur - Status code: {response.status_code}")
                    print(f"Réponse: {response.text}")
                    results.append(False)
            except Exception as e:
                print(f"ERREUR: {type(e).__name__}: {str(e)}")
                results.append(False)
        else:
            # Test standard avec l'endpoint OpenAI compatible
            result = test_chat_with_config(
                model=test["model"],
                messages=test["messages"],
                max_tokens=test.get("max_tokens", 20),
                temperature=test.get("temperature", 0.5),
                timeout=test.get("timeout", 10),
                test_name=test["name"]
            )
            results.append(result)
    
    # Afficher le résumé
    print_header("RÉSUMÉ DES TESTS")
    for i, test in enumerate(tests):
        status = "✅ RÉUSSI" if results[i] else "❌ ÉCHEC"
        print(f"{status} - {test['name']}")
    
    # Résultat global
    if any(results):
        print("\n✅ Au moins un test a réussi")
    else:
        print("\n❌ Tous les tests ont échoué")

if __name__ == "__main__":
    run_tests()
