"""
Script de test pour l'API OpenAI directement.
Ce script teste l'API OpenAI avec un modèle spécifique et un message simple.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

def print_header(message):
    """Affiche un message de titre formaté"""
    header = "\n" + "=" * 80 + "\n" + f" {message} ".center(80, "=") + "\n" + "=" * 80
    print(header)

def test_openai_chat(message="Bonjour, comment ça va?", max_tokens=20, temperature=0.5, timeout=90):
    """Teste l'API OpenAI directement"""
    print_header(f"Test avec l'API OpenAI")
    
    # URL de l'API OpenAI
    url = "https://api.openai.com/v1/chat/completions"
    
    # Récupérer la clé API OpenAI depuis la variable d'environnement
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("❌ ERREUR: La variable d'environnement OPENAI_API_KEY n'est pas définie.")
        return False
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"Configuration du test:")
    print(f"- Modèle: gpt-3.5-turbo")
    print(f"- Message: {message}")
    print(f"- Max tokens: {max_tokens}")
    print(f"- Température: {temperature}")
    print(f"- Timeout: {timeout} secondes")
    
    try:
        print(f"Envoi de la requête à {url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        start_time = time.time()
        response = requests.post(
            url, 
            json=payload,
            headers=headers,
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
    print_header(f"TEST DE L'API OPENAI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test avec un message court
    test_openai_chat(
        message="Bonjour, dis-moi bonjour en retour.",
        max_tokens=10,
        timeout=90
    )
