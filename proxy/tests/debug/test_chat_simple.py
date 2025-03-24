"""
Script de test simple pour l'endpoint chat completions de l'API OVH LLM.
Ce script teste l'endpoint avec un modèle spécifique et un message simple.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# URL du serveur
SERVER_URL = "http://localhost:8000"

def print_header(message):
    """Affiche un message de titre formaté"""
    header = "\n" + "=" * 80 + "\n" + f" {message} ".center(80, "=") + "\n" + "=" * 80
    print(header)

def test_chat_with_model(model="mistral-7b-instruct-v0.3", message="Bonjour, comment ça va?", max_tokens=20, temperature=0.5, timeout=90):
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
    
    print(f"Configuration du test:")
    print(f"- Modèle: {model}")
    print(f"- Message: {message}")
    print(f"- Max tokens: {max_tokens}")
    print(f"- Température: {temperature}")
    print(f"- Timeout: {timeout} secondes")
    
    try:
        print(f"Envoi de la requête à {SERVER_URL}/v1/chat/completions")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
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
                print(f"✅ Test réussi en {elapsed_time:.2f} secondes")
                print(f"Réponse: {content}")
                return True
            else:
                print(f"❌ Format de réponse inattendu: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ Erreur - Status code: {response.status_code}")
            print(f"Réponse: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT après {timeout} secondes")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print_header(f"TEST DE L'ENDPOINT CHAT COMPLETIONS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test avec un modèle simple et un message court
    test_chat_with_model(
        model="mistral-7b-instruct-v0.3",
        message="Bonjour, dis-moi bonjour en retour.",
        max_tokens=10,
        timeout=90
    )
