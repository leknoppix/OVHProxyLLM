#!/usr/bin/env python
"""
Tests fonctionnels de l'application proxy OVH LLM
"""

import requests
import json
import sys
import os

# Configuration
SERVER_URL = "http://localhost:8000"  # URL du serveur à tester

def print_header(message):
    """Affiche un message de titre formaté"""
    print("\n" + "=" * 80)
    print("=" * ((80 - len(message)) // 2) + f" {message} " + "=" * ((80 - len(message)) // 2))
    print("=" * 80)

def test_health_check():
    """Test de l'endpoint de vérification de santé"""
    print_header("Test de l'endpoint de vérification de santé")
    
    url = f"{SERVER_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code reçu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse reçue: {json.dumps(data)}")
            
            # Vérifier que la réponse est correcte
            assert data.get("status") == "ok", "Le statut n'est pas 'ok'"
            
            print("✅ RÉUSSI - Vérification de santé")
            print(f"  → Status code: {response.status_code}, Réponse: {json.dumps(data)}")
            return True
        else:
            print("❌ ÉCHEC - Vérification de santé")
            print(f"  → Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception détaillée: {e.__class__.__name__}: {str(e)}")
        print("❌ ÉCHEC - Vérification de santé")
        print(f"  → Erreur: {str(e)}")
        return False

def test_api_health_check():
    """Test de l'endpoint de vérification de santé pour OpenWebUI"""
    print_header("Test de l'endpoint de vérification de santé pour OpenWebUI")
    
    url = f"{SERVER_URL}/api/health"
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code reçu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse reçue: {json.dumps(data)}")
            
            # Vérifier que la réponse est correcte
            assert data.get("status") == "ok", "Le statut n'est pas 'ok'"
            
            print("✅ RÉUSSI - Vérification de santé API")
            print(f"  → Status code: {response.status_code}, Réponse: {json.dumps(data)}")
            return True
        else:
            print("❌ ÉCHEC - Vérification de santé API")
            print(f"  → Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception détaillée: {e.__class__.__name__}: {str(e)}")
        print("❌ ÉCHEC - Vérification de santé API")
        print(f"  → Erreur: {str(e)}")
        return False

def test_list_models():
    """Test de l'endpoint de liste des modèles"""
    print_header("Test de l'endpoint de liste des modèles")
    
    url = f"{SERVER_URL}/api/models"
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code reçu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            model_count = len(models)
            print(f"Nombre de modèles reçus: {model_count}")
            
            # Vérifier qu'il y a au moins un modèle
            assert model_count > 0, "Aucun modèle n'a été retourné"
            
            print("✅ RÉUSSI - Liste des modèles")
            print(f"  → Status code: {response.status_code}, Nombre de modèles: {model_count}")
            return True
        else:
            print("❌ ÉCHEC - Liste des modèles")
            print(f"  → Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception détaillée: {e.__class__.__name__}: {str(e)}")
        print("❌ ÉCHEC - Liste des modèles")
        print(f"  → Erreur: {str(e)}")
        return False

def test_diagnostic():
    """Test de l'endpoint de diagnostic"""
    print_header("Test de l'endpoint de diagnostic")
    
    url = f"{SERVER_URL}/diagnostic"
    try:
        response = requests.get(url, timeout=10)  # Timeout plus long pour le diagnostic
        print(f"Status code reçu: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ RÉUSSI - Diagnostic")
            print(f"  → Status code: {response.status_code}, Diagnostic effectué")
            return True
        else:
            print("❌ ÉCHEC - Diagnostic")
            print(f"  → Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception détaillée: {e.__class__.__name__}: {str(e)}")
        print("❌ ÉCHEC - Diagnostic")
        print(f"  → Erreur: {str(e)}")
        return False

def test_chat_completions():
    """Test de l'endpoint de chat completions"""
    print_header("Test de l'endpoint de chat completions")
    
    url = f"{SERVER_URL}/v1/chat/completions"
    payload = {
        "model": "mistral-7b-instruct-v0.3",
        "messages": [
            {"role": "user", "content": "Bonjour, comment ça va?"}
        ],
        "temperature": 0.5,
        "max_tokens": 20,
        "test_mode": True  # Activer le mode test pour éviter les appels à l'API externe
    }
    
    print(f"Envoi de la requête à {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status code reçu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse reçue: {json.dumps(data)}...")
            
            # Vérifier que la réponse a le bon format
            assert "choices" in data, "La réponse ne contient pas de 'choices'"
            assert len(data["choices"]) > 0, "Aucun choix dans la réponse"
            assert "message" in data["choices"][0], "Le premier choix ne contient pas de 'message'"
            assert "content" in data["choices"][0]["message"], "Le message ne contient pas de 'content'"
            
            content = data["choices"][0]["message"]["content"]
            print("✅ RÉUSSI - Chat completions")
            print(f"  → Réponse: {content[:100]}...")
            return True
        else:
            print(f"Réponse d'erreur: {response.text}")
            print("❌ ÉCHEC - Chat completions")
            print(f"  → Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception détaillée: {e.__class__.__name__}: {str(e)}")
        print("❌ ÉCHEC - Chat completions")
        print(f"  → Erreur: {str(e)}")
        return False

def run_all_tests():
    """
    Exécute tous les tests et affiche un résumé
    """
    print("\n" + "=" * 80)
    print("=" * 30 + " DÉBUT DES TESTS " + "=" * 30)
    print("=" * 80)
    
    # Vérifier d'abord si le serveur est accessible
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
    except Exception as e:
        print("❌ ERREUR: Le serveur n'est pas accessible. Assurez-vous que l'application est en cours d'exécution.")
        print("Commande suggérée: python main.py")
        return False
    
    # Exécuter les tests de base
    health_check_success = test_health_check()
    api_health_check_success = test_api_health_check()
    list_models_success = test_list_models()
    diagnostic_success = test_diagnostic()
    
    # Exécuter les tests d'API
    chat_completions_success = test_chat_completions()
    
    # Résumé des tests
    print("\n" + "=" * 80)
    print("=" * 30 + " RÉSUMÉ DES TESTS " + "=" * 30)
    print("=" * 80)
    
    # Vérifier les tests de base
    basic_tests_success = health_check_success and api_health_check_success and list_models_success and diagnostic_success
    if basic_tests_success:
        print("Tests de base: ✅ RÉUSSI")
    else:
        print("Tests de base: ❌ ÉCHEC")
    
    # Vérifier les tests d'API
    api_tests_success = chat_completions_success
    if api_tests_success:
        print("Test de l'API: ✅ RÉUSSI")
    else:
        print("Test de l'API: ❌ ÉCHEC")
    
    # Résultat global
    all_success = basic_tests_success and api_tests_success
    if all_success:
        print("Résultat global: ✅ RÉUSSI")
    else:
        print("Résultat global: ❌ ÉCHEC")
    
    return all_success

if __name__ == "__main__":
    print_header("TESTS FONCTIONNELS DE L'APPLICATION PROXY OVH LLM")
    success = run_all_tests()
    sys.exit(0 if success else 1)
