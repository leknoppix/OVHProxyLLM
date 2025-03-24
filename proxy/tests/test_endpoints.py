#!/usr/bin/env python
"""
Script pour tester tous les endpoints de chat du proxy OVH LLM avec la question "Bonjour" pour tous les modu00e8les disponibles
"""

import requests
import json
import time
import sys

# Configuration
SERVER_URL = "http://localhost:8000"
TEST_PROMPT = "Bonjour"
TIMEOUT = 60  # Timeout en secondes
TEST_MODE = True  # Utiliser le mode test pour u00e9viter les timeouts

# Liste des modu00e8les disponibles (excluant stable-diffusion-xl qui est pour la gu00e9nu00e9ration d'images)
AVAILABLE_MODELS = [
    "mistral-7b-instruct-v0.3",
    "mixtral-8x7b-instruct-v0.1",
    "mistral-nemo-instruct-2407",
    "llama-3-1-8b-instruct",
    "llama-3-3-70b-instruct",
    "llama-3-1-70b-instruct",
    "deepseek-r1-distill-llama-70b",
    "mamba-codestral-7b-v0-1"
]

def print_header(message):
    """Affiche un message de titre formatu00e9"""
    print("\n" + "=" * 80)
    print("=" * ((80 - len(message)) // 2) + f" {message} " + "=" * ((80 - len(message)) // 2))
    print("=" * 80)

def test_openai_chat_completions(model):
    """Test de l'endpoint /v1/chat/completions (API OpenAI) avec un modu00e8le spu00e9cifique"""
    print_header(f"Test de /v1/chat/completions avec {model}")
    
    url = f"{SERVER_URL}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": TEST_PROMPT}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "test_mode": TEST_MODE
    }
    
    print(f"Envoi de la requu00eate u00e0 {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Temps de ru00e9ponse: {elapsed_time:.2f} secondes")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"Ru00e9ponse: {content[:150]}..." if len(content) > 150 else f"Ru00e9ponse: {content}")
            print("u2705 Ru00c9USSI")
            return True
        else:
            print(f"Ru00e9ponse d'erreur: {response.text[:200]}..." if len(response.text) > 200 else f"Ru00e9ponse d'erreur: {response.text}")
            print("u274c u00c9CHEC")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        print("u274c u00c9CHEC")
        return False

def test_openai_completions(model):
    """Test de l'endpoint /v1/completions (API OpenAI) avec un modu00e8le spu00e9cifique"""
    print_header(f"Test de /v1/completions avec {model}")
    
    url = f"{SERVER_URL}/v1/completions"
    payload = {
        "model": model,
        "prompt": TEST_PROMPT,
        "temperature": 0.7,
        "max_tokens": 100,
        "test_mode": TEST_MODE
    }
    
    print(f"Envoi de la requu00eate u00e0 {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Temps de ru00e9ponse: {elapsed_time:.2f} secondes")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("text", "")
            print(f"Ru00e9ponse: {content[:150]}..." if len(content) > 150 else f"Ru00e9ponse: {content}")
            print("u2705 Ru00c9USSI")
            return True
        else:
            print(f"Ru00e9ponse d'erreur: {response.text[:200]}..." if len(response.text) > 200 else f"Ru00e9ponse d'erreur: {response.text}")
            print("u274c u00c9CHEC")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        print("u274c u00c9CHEC")
        return False

def test_ollama_chat(model):
    """Test de l'endpoint /api/chat (API Ollama) avec un modu00e8le spu00e9cifique"""
    print_header(f"Test de /api/chat avec {model}")
    
    url = f"{SERVER_URL}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": TEST_PROMPT}
        ],
        "stream": False,
        "test_mode": TEST_MODE
    }
    
    print(f"Envoi de la requu00eate u00e0 {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Temps de ru00e9ponse: {elapsed_time:.2f} secondes")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")
            print(f"Ru00e9ponse: {content[:150]}..." if len(content) > 150 else f"Ru00e9ponse: {content}")
            print("u2705 Ru00c9USSI")
            return True
        else:
            print(f"Ru00e9ponse d'erreur: {response.text[:200]}..." if len(response.text) > 200 else f"Ru00e9ponse d'erreur: {response.text}")
            print("u274c u00c9CHEC")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        print("u274c u00c9CHEC")
        return False

def test_ollama_generate(model):
    """Test de l'endpoint /api/generate (API Ollama) avec un modu00e8le spu00e9cifique"""
    print_header(f"Test de /api/generate avec {model}")
    
    url = f"{SERVER_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": TEST_PROMPT,
        "stream": False,
        "test_mode": TEST_MODE
    }
    
    print(f"Envoi de la requu00eate u00e0 {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        elapsed_time = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Temps de ru00e9ponse: {elapsed_time:.2f} secondes")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("response", "")
            print(f"Ru00e9ponse: {content[:150]}..." if len(content) > 150 else f"Ru00e9ponse: {content}")
            print("u2705 Ru00c9USSI")
            return True
        else:
            print(f"Ru00e9ponse d'erreur: {response.text[:200]}..." if len(response.text) > 200 else f"Ru00e9ponse d'erreur: {response.text}")
            print("u274c u00c9CHEC")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        print("u274c u00c9CHEC")
        return False

def run_all_tests():
    """Exu00e9cute tous les tests pour tous les modu00e8les et affiche un ru00e9sumu00e9"""
    print_header("TESTS DE TOUS LES ENDPOINTS AVEC TOUS LES MODu00c8LES")
    
    # Vu00e9rifier d'abord si le serveur est accessible
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
    except Exception as e:
        print("u274c ERREUR: Le serveur n'est pas accessible. Assurez-vous que l'application est en cours d'exu00e9cution.")
        print("Commande suggu00e9ru00e9e: python main.py")
        return False
    
    # Initialiser les ru00e9sultats
    results = {}
    
    # Tester chaque modu00e8le avec chaque endpoint
    for model in AVAILABLE_MODELS:
        model_results = {
            "OpenAI Chat Completions": test_openai_chat_completions(model),
            "OpenAI Completions": test_openai_completions(model),
            "Ollama Chat": test_ollama_chat(model),
            "Ollama Generate": test_ollama_generate(model)
        }
        results[model] = model_results
    
    # Afficher le ru00e9sumu00e9
    print_header("Ru00c9SUMu00c9 DES TESTS")
    
    # Calculer les statistiques par modu00e8le
    model_success = {}
    for model, endpoints in results.items():
        success_count = sum(1 for success in endpoints.values() if success)
        total_count = len(endpoints)
        model_success[model] = (success_count, total_count)
        print(f"Modu00e8le {model}: {success_count}/{total_count} tests ru00e9ussis ({success_count/total_count*100:.0f}%)")
    
    # Calculer les statistiques par endpoint
    endpoint_success = {}
    for endpoint in ["OpenAI Chat Completions", "OpenAI Completions", "Ollama Chat", "Ollama Generate"]:
        success_count = sum(1 for model_results in results.values() if model_results.get(endpoint, False))
        total_count = len(results)
        endpoint_success[endpoint] = (success_count, total_count)
        print(f"Endpoint {endpoint}: {success_count}/{total_count} modu00e8les ru00e9ussis ({success_count/total_count*100:.0f}%)")
    
    # Ru00e9sultat global
    total_success = sum(success for model_results in results.values() for success in model_results.values())
    total_tests = sum(len(model_results) for model_results in results.values())
    success_rate = total_success / total_tests * 100 if total_tests > 0 else 0
    
    print(f"Ru00e9sultat global: {total_success}/{total_tests} tests ru00e9ussis ({success_rate:.0f}%)")
    print(f"Statut global: {'u2705 Ru00c9USSI' if success_rate >= 75 else 'u274c u00c9CHEC'}")
    
    return success_rate >= 75

if __name__ == "__main__":
    print_header("TESTS DES ENDPOINTS DU PROXY OVH LLM")
    success = run_all_tests()
    sys.exit(0 if success else 1)
