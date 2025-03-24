"""
Script de test pour l'API OVH directement.
Ce script teste l'API OVH avec un modèle spécifique et un message simple.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def print_header(message):
    """Affiche un message de titre formaté"""
    header = "\n" + "=" * 80 + "\n" + f" {message} ".center(80, "=") + "\n" + "=" * 80
    print(header)

def test_ovh_chat(model="mistral-7b-instruct-v0.3", message="Bonjour, comment ça va?", max_tokens=20, temperature=0.5, timeout=90):
    """Teste l'API OVH directement"""
    print_header(f"Test direct avec l'API OVH - Modèle: {model}")
    
    # Récupérer le token OVH depuis la variable d'environnement
    ovh_token = os.environ.get("OVH_TOKEN_ENDPOINT", "")
    if not ovh_token:
        print("❌ ERREUR: La variable d'environnement OVH_TOKEN_ENDPOINT n'est pas définie.")
        return False
    
    # Construire l'URL en fonction du modèle
    base_url = ""
    if model == "mistral-7b-instruct-v0.3":
        base_url = "https://mistral-7b-instruct-v0-3.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1"
    elif model == "mixtral-8x7b-instruct-v0.1":
        base_url = "https://mixtral-8x7b-instruct-v01.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1"
    elif model == "llama-3-1-8b-instruct":
        base_url = "https://llama-3-1-8b-instruct.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1"
    else:
        # Format générique pour les autres modèles
        model_slug = model.lower().replace("-", "-").replace(".", "-")
        base_url = f"https://{model_slug}.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1"
    
    url = f"{base_url}/chat/completions"
    
    # Adapter le nom du modèle pour l'API OVH
    api_model_name = model
    if model == "mistral-7b-instruct-v0.3":
        api_model_name = "Mistral-7B-Instruct-v0.3"
    elif model == "mixtral-8x7b-instruct-v0.1":
        api_model_name = "Mixtral-8x7B-Instruct-v0.1"
    elif model == "llama-3-1-8b-instruct":
        api_model_name = "Llama-3.1-8B-Instruct"
    
    payload = {
        "model": api_model_name,
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ovh_token}"
    }
    
    print(f"Configuration du test:")
    print(f"- URL: {url}")
    print(f"- Modèle API: {api_model_name}")
    print(f"- Message: {message}")
    print(f"- Max tokens: {max_tokens}")
    print(f"- Température: {temperature}")
    print(f"- Timeout: {timeout} secondes")
    print(f"- Token OVH (premiers 10 caractères): {ovh_token[:10]}...")
    
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
    print_header(f"TEST DIRECT DE L'API OVH - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test avec un modèle simple et un message court
    test_ovh_chat(
        model="mistral-7b-instruct-v0.3",
        message="Bonjour, dis-moi bonjour en retour.",
        max_tokens=10,
        timeout=90
    )
