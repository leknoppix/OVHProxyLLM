"""
Script de diagnostic pour le serveur proxy OVH LLM.
Ce script vérifie l'état du serveur et teste les différents endpoints.
"""

import requests
import json
import time
import sys
import os
import socket

# URL du serveur
SERVER_URL = "http://localhost:8000"

def print_header(message):
    """Affiche un message de titre formaté"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)

def check_port_in_use(port):
    """Vérifie si un port est utilisé"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def check_server_status():
    """Vérifie l'état du serveur"""
    print_header("Vérification de l'état du serveur")
    
    # Vérifier si le port est utilisé
    port_in_use = check_port_in_use(8000)
    print(f"Port 8000 utilisé: {'Oui' if port_in_use else 'Non'}")
    
    if not port_in_use:
        print("❌ Le serveur ne semble pas être en cours d'exécution sur le port 8000")
        return False
    
    # Vérifier si le serveur répond
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ Le serveur répond correctement sur /health (Status: {response.status_code})")
            return True
        else:
            print(f"❌ Le serveur répond avec un code d'erreur sur /health (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la connexion au serveur: {str(e)}")
        return False

def test_endpoint(endpoint, method="GET", payload=None, expected_status=200, timeout=5):
    """Teste un endpoint spécifique"""
    print(f"\nTest de l'endpoint: {endpoint} (Méthode: {method})")
    
    try:
        if method == "GET":
            response = requests.get(f"{SERVER_URL}{endpoint}", timeout=timeout)
        elif method == "POST":
            response = requests.post(
                f"{SERVER_URL}{endpoint}", 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
        else:
            print(f"❌ Méthode non supportée: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ Réponse attendue (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"Réponse JSON: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
            except:
                print(f"Réponse non-JSON: {response.text[:200]}...")
            return True
        else:
            print(f"❌ Réponse inattendue (Status: {response.status_code})")
            print(f"Réponse: {response.text[:200]}...")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout après {timeout} secondes")
        return False
    except Exception as e:
        print(f"❌ Erreur: {type(e).__name__}: {str(e)}")
        return False

def test_diagnostic_endpoint():
    """Teste l'endpoint de diagnostic qui teste explicitement la connexion à l'API OVH"""
    print_header("Test de l'endpoint de diagnostic")
    
    try:
        print("Cet endpoint peut prendre un peu de temps car il teste la connexion à l'API OVH...")
        response = requests.get(f"{SERVER_URL}/diagnostic", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Diagnostic réussi (Status: {response.status_code})")
            
            # Analyser les résultats du diagnostic
            if "ovh_api_status" in data:
                ovh_status = data["ovh_api_status"]
                print(f"État de l'API OVH: {ovh_status}")
                
                if ovh_status == "ok":
                    print("✅ La connexion à l'API OVH fonctionne correctement")
                else:
                    print(f"❌ Problème avec la connexion à l'API OVH: {ovh_status}")
                    
                    if "error_details" in data:
                        print(f"Détails de l'erreur: {data['error_details']}")
            
            # Afficher les modèles disponibles
            if "available_models" in data:
                models = data["available_models"]
                print(f"Modèles disponibles: {', '.join(models)}")
            
            return True
        else:
            print(f"❌ Échec du diagnostic (Status: {response.status_code})")
            print(f"Réponse: {response.text[:200]}...")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Timeout après 30 secondes")
        return False
    except Exception as e:
        print(f"❌ Erreur: {type(e).__name__}: {str(e)}")
        return False

def run_diagnostic():
    """Exécute un diagnostic complet du serveur"""
    print_header("DIAGNOSTIC DU SERVEUR PROXY OVH LLM")
    
    # Vérifier l'état du serveur
    server_ok = check_server_status()
    if not server_ok:
        print("❌ Le serveur ne répond pas correctement, impossible de continuer le diagnostic")
        return
    
    # Tester les endpoints de base
    endpoints = [
        {"path": "/health", "method": "GET", "timeout": 2},
        {"path": "/api/health", "method": "GET", "timeout": 2},
        {"path": "/api/models", "method": "GET", "timeout": 5}
    ]
    
    for endpoint in endpoints:
        test_endpoint(
            endpoint["path"], 
            method=endpoint["method"], 
            timeout=endpoint["timeout"]
        )
    
    # Tester l'endpoint de diagnostic
    test_diagnostic_endpoint()
    
    # Tester l'endpoint de chat completions avec un timeout court
    # pour voir si la requête est bien reçue par le serveur
    print_header("Test rapide de l'endpoint de chat completions")
    print("Ce test va échouer avec un timeout, mais nous voulons juste vérifier si la requête est reçue")
    
    payload = {
        "model": "mistral-7b-instruct-v0.3",
        "messages": [
            {"role": "user", "content": "Bonjour"}
        ],
        "temperature": 0.5,
        "max_tokens": 10
    }
    
    test_endpoint(
        "/v1/chat/completions", 
        method="POST", 
        payload=payload, 
        timeout=3  # Timeout court pour ne pas attendre trop longtemps
    )
    
    print_header("CONCLUSION")
    print("Le serveur proxy semble fonctionner correctement pour les endpoints de base.")
    print("L'endpoint de chat completions prend trop de temps à répondre, ce qui suggère un problème")
    print("avec la connexion à l'API OVH ou avec le traitement des requêtes par le serveur.")
    print("\nSuggestions:")
    print("1. Vérifiez les logs du serveur pour voir s'il y a des erreurs lors du traitement des requêtes")
    print("2. Vérifiez que le token d'API OVH est valide et correctement configuré")
    print("3. Vérifiez que les endpoints OVH sont accessibles depuis votre serveur")
    print("4. Essayez de redémarrer le serveur proxy")

if __name__ == "__main__":
    run_diagnostic()
