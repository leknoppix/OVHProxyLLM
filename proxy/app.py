from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import json
import logging
import asyncio
import base64
import io
from PIL import Image
import time

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pas besoin de load_dotenv si on utilise les variables d'environnement Docker directement

app = FastAPI()

# Configuration du CORS pour permettre les requêtes depuis OpenWebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le développement, en production, spécifiez les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour logger les requêtes et réponses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Requête entrante: {request.method} {request.url}")
    
    # Récupérer le corps de la requête
    body = await request.body()
    if body:
        try:
            logger.info(f"Corps de la requête: {body.decode()}")
        except:
            logger.info("Corps de la requête non décodable")
    
    # Traiter la requête
    response = await call_next(request)
    
    # Si c'est une réponse JSON
    if response.headers.get("content-type") == "application/json":
        # On ne peut pas directement lire le corps de la réponse après l'avoir envoyé
        # donc on ne peut pas le logger ici
        logger.info(f"Réponse: {response.status_code}")
    
    return response

# Récupérer le token d'authentification depuis la variable d'environnement
OVH_API_TOKEN = os.getenv('OVH_TOKEN_ENDPOINT')

# En mode développement, on peut fonctionner sans token
if not OVH_API_TOKEN:
    print("AVERTISSEMENT: La variable d'environnement OVH_TOKEN_ENDPOINT n'est pas définie.")
    print("Le serveur démarre en mode développement (les appels aux API OVH échoueront).")
    OVH_API_TOKEN = "dummy_token_for_development"
else:
    # Afficher les premiers caractères du token pour déboguer
    token_prefix = OVH_API_TOKEN[:20] if len(OVH_API_TOKEN) > 20 else OVH_API_TOKEN
    print(f"Token OVH récupéré: {token_prefix}... (longueur: {len(OVH_API_TOKEN)})")

# Liste des endpoints OVH pour chaque modèle
# Les noms des modèles doivent être ceux utilisés par l'API OVH
# Note: Ces clés peuvent être différentes des noms internes utilisés par l'API
endpoints = {
    "mistral-7b-instruct-v0.3": "https://mistral-7b-instruct-v0-3.endpoints.kepler.ai.cloud.ovh.net",
    "mixtral-8x7b-instruct-v0.1": "https://mixtral-8x7b-instruct-v01.endpoints.kepler.ai.cloud.ovh.net",
    "mistral-nemo-instruct-2407": "https://mistral-nemo-instruct-2407.endpoints.kepler.ai.cloud.ovh.net",
    "llama-3-1-8b-instruct": "https://llama-3-1-8b-instruct.endpoints.kepler.ai.cloud.ovh.net",
    "llama-3-3-70b-instruct": "https://llama-3-3-70b-instruct.endpoints.kepler.ai.cloud.ovh.net",
    "llama-3-1-70b-instruct": "https://llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net",
    "deepseek-r1-distill-llama-70b": "https://deepseek-r1-distill-llama-70b.endpoints.kepler.ai.cloud.ovh.net",
    "stable-diffusion-xl": "https://stable-diffusion-xl.endpoints.kepler.ai.cloud.ovh.net"
}

def send_request(endpoint: str, payload: dict, route: str):
    # Essayons différents formats d'URL possibles
    urls = []
    
    # Dictionnaire de correspondance entre nos noms de modèles et ceux d'OVH
    model_name_map = {
        "mistral-7b-instruct-v0.3": "Mistral-7B-Instruct-v0.3",
        "mixtral-8x7b-instruct-v0.1": "Mixtral-8x7B-Instruct-v0.1",
        "mistral-nemo-instruct-2407": "Mistral-Nemo-Instruct-2407",
        "llama-3-1-8b-instruct": "Llama-3.1-8B-Instruct",
        "llama-3-3-70b-instruct": "Meta-Llama-3_3-70B-Instruct",
        "llama-3-1-70b-instruct": "Meta-Llama-3_1-70B-Instruct",
        "deepseek-r1-distill-llama-70b": "DeepSeek-R1-Distill-Llama-70B"
    }
    
    # Traitement spécial pour le modèle DeepSeek qui supporte l'input multimodal
    if "model" in payload and payload["model"] == "deepseek-r1-distill-llama-70b" and "messages" in payload:
        # Vérifier si les messages contiennent des éléments multimodaux (images ou audio)
        # et les formater correctement selon la documentation DeepSeek
        for i, message in enumerate(payload["messages"]):
            # Vérifier si le rôle est supporté par DeepSeek (system, user, assistant, tool, developer)
            if "role" in message and message["role"] not in ["system", "user", "assistant", "tool", "developer"]:
                logger.warning(f"Rôle non supporté par DeepSeek: {message['role']}. Utilisation du rôle 'user' par défaut.")
                payload["messages"][i]["role"] = "user"
                
            # Si le contenu est une URL d'image, le transformer en format compatible DeepSeek
            if "content" in message and isinstance(message["content"], str) and (
                message["content"].startswith("http") and 
                any(ext in message["content"].lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"])
            ):
                payload["messages"][i]["content"] = [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": message["content"]
                        }
                    }
                ]
                logger.info(f"URL d'image détectée et formatée pour DeepSeek: {message['content']}")

    # S'assurer que le modèle n'a pas de suffixe :latest
    if "model" in payload and ":" in payload["model"]:
        payload["model"] = payload["model"].split(":")[0]
        logger.info(f"Suppression du suffixe :latest du modèle: {payload['model']}")
    
    # Remplacer le nom du modèle dans le payload par le nom exact utilisé par OVH
    if "model" in payload and payload["model"] in model_name_map:
        payload["model"] = model_name_map[payload["model"]]
    
    # Ajouter les options supplémentaires supportées par certains modèles
    # Pour éviter de les inclure si elles ne sont pas explicitement demandées
    if "stream" in payload:
        logger.info(f"Option 'stream' détectée avec la valeur: {payload['stream']}")
    
    if "logprobs" in payload:
        logger.info(f"Option 'logprobs' détectée avec la valeur: {payload['logprobs']}")
    
    if "seed" in payload:
        logger.info(f"Option 'seed' détectée avec la valeur: {payload['seed']}")
    
    if route == "chat":
        # Format possible 1 (original)
        urls.append(f"{endpoint}/api/openai_compat/v1/chat/completions")
        # Format possible 2 (standard OpenAI)
        urls.append(f"{endpoint}/v1/chat/completions")
        # Format possible 3 (sans le préfixe openai_compat)
        urls.append(f"{endpoint}/api/v1/chat/completions")
    elif route == "completions":
        # Format possible 1 (original)
        urls.append(f"{endpoint}/api/openai_compat/v1/completions")
        # Format possible 2 (standard OpenAI)
        urls.append(f"{endpoint}/v1/completions")
        # Format possible 3 (sans le préfixe openai_compat)
        urls.append(f"{endpoint}/api/v1/completions")
    else:
        raise ValueError("Route inconnue")

    headers = {
        "Authorization": f"Bearer {OVH_API_TOKEN}",
        "Content-Type": "application/json"
    }

    last_error = None
    
    # Essayons chaque URL jusqu'à ce que l'une d'elles fonctionne
    for url in urls:
        try:
            print(f"[DEBUG] Essai avec l'URL : {url}")
            print(f"[DEBUG] Headers : {headers}")
            print(f"[DEBUG] Payload : {payload}")
            
            # Ajouter un timeout pour éviter les blocages indéfinis
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"[DEBUG] Code de statut : {response.status_code}")
            print(f"[DEBUG] Réponse : {response.text}")
            
            if response.status_code == 200:
                return response.json()
            
            last_error = response
        except requests.exceptions.Timeout:
            print(f"[ERREUR] Timeout pour l'URL {url}")
            last_error = Exception(f"Timeout lors de la connexion à {url}")
        except Exception as e:
            print(f"[ERREUR] Exception pour l'URL {url}: {str(e)}")
            last_error = e
    
    # Si on est arrivé ici, aucune URL n'a fonctionné
    if isinstance(last_error, requests.Response):
        raise HTTPException(status_code=last_error.status_code, 
                           detail=f"Erreur HTTP: {last_error.status_code} - {last_error.text}")
    else:
        raise HTTPException(status_code=500, 
                           detail=f"Erreur de requête: {str(last_error)}")

def validate_json_data(data):
    """
    Vérifie que les données sont bien formatées en JSON et corrige les erreurs éventuelles
    """
    if isinstance(data, dict):
        for key, value in list(data.items()):  # Utiliser list() pour pouvoir modifier pendant l'itération
            if isinstance(value, (dict, list)):
                data[key] = validate_json_data(value)
            elif isinstance(key, str) and ":" in key:
                # Corriger les clés problématiques
                new_key = key.replace(":", "-")
                logger.warning(f"Clé JSON invalide détectée: '{key}' remplacée par '{new_key}'")
                data[new_key] = data.pop(key)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = validate_json_data(item)
    return data

@app.get("/v1/models")
async def list_models():
    model_list = [{"id": name, "object": "model"} for name in endpoints.keys()]
    # Valider le format JSON avant de l'envoyer
    model_list = validate_json_data(model_list)
    return JSONResponse(content={"object": "list", "data": model_list})

@app.post("/v1/chat/completions")
async def chat_completions(payload: dict = Body(...)):
    model_name = payload.get("model")
    messages = payload.get("messages")
    max_tokens = payload.get("max_tokens", 100)
    temperature = payload.get("temperature", 1.0)

    if not model_name or not messages:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'messages' sont requis.")
        
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    if ":" in model_name:
        model_name = model_name.split(":")[0]
        print(f"[INFO] Suffixe ':latest' supprimé du nom du modèle: {model_name}")

    if model_name not in endpoints:
        raise HTTPException(status_code=404, detail="Modèle non trouvé.")

    endpoint = endpoints[model_name]
    ovh_payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    return send_request(endpoint, ovh_payload, route="chat")

@app.post("/v1/completions")
async def completions(payload: dict = Body(...)):
    model_name = payload.get("model")
    prompt = payload.get("prompt")
    max_tokens = payload.get("max_tokens", 16)
    temperature = payload.get("temperature", 1.0)

    if not model_name or prompt is None:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'prompt' sont requis.")
        
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    if ":" in model_name:
        model_name = model_name.split(":")[0]
        print(f"[INFO] Suffixe ':latest' supprimé du nom du modèle: {model_name}")

    if model_name not in endpoints:
        raise HTTPException(status_code=404, detail="Modèle non trouvé.")

    endpoint = endpoints[model_name]
    ovh_payload = {
        "model": model_name,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    return send_request(endpoint, ovh_payload, route="completions")

@app.get("/test-ovh-connection")
async def test_ovh_connection():
    """
    Test la connexion avec les endpoints OVH et récupère les informations disponibles
    """
    results = {}
    
    # Tester chaque endpoint
    for model_name, endpoint in endpoints.items():
        try:
            # Essayer différentes URLs pour trouver la bonne
            possible_urls = [
                f"{endpoint}/v1/models",
                f"{endpoint}/api/v1/models",
                f"{endpoint}/api/openai_compat/v1/models",
                f"{endpoint}/"
            ]
            
            # Essayer chaque URL
            for url in possible_urls:
                try:
                    print(f"[DEBUG] Essai de connexion à {url}")
                    headers = {"Authorization": f"Bearer {OVH_API_TOKEN}"}
                    response = requests.get(url, headers=headers, timeout=5)
                    status = response.status_code
                    response_text = response.text
                    
                    results[f"{model_name} - {url}"] = {
                        "status": status,
                        "response": response_text
                    }
                    
                    # Si on a une réponse valide, on arrête de tester les autres URLs
                    if status == 200:
                        break
                except Exception as e:
                    results[f"{model_name} - {url}"] = {
                        "status": "error",
                        "response": str(e)
                    }
        except Exception as e:
            results[model_name] = {
                "status": "error",
                "response": str(e)
            }
    
    return results

@app.get("/fetch-ovh-models")
async def fetch_ovh_models():
    """
    Interroge les endpoints OVH pour récupérer la liste exacte des modèles disponibles
    """
    results = {}
    
    for model_name, endpoint in endpoints.items():
        try:
            url = f"{endpoint}/api/openai_compat/v1/models"
            print(f"[DEBUG] Récupération des modèles depuis {url}")
            
            headers = {"Authorization": f"Bearer {OVH_API_TOKEN}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            print(f"[DEBUG] Code de statut : {response.status_code}")
            print(f"[DEBUG] Réponse : {response.text}")
            
            if response.status_code == 200:
                results[model_name] = response.json()
            else:
                results[model_name] = {
                    "status": response.status_code,
                    "error": response.text
                }
        except Exception as e:
            results[model_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

# Endpoints pour la compatibilité avec OpenWebUI
@app.get("/api/models")
async def api_models():
    """
    Endpoint spécifique pour OpenWebUI qui retourne la liste des modèles
    """
    print("Requête pour /api/models reçue")
    
    models_list = []
    for model_name in endpoints.keys():
        # Ajouter ':latest' au nom du modèle pour OpenWebUI
        display_name = f"{model_name}:latest"
        model_info = {
            "id": display_name,
            "name": display_name,
            "model_id": display_name,
            "object": "model",
            "created": 1699891200,  # Date fixe pour tous les modèles
            "owned_by": "OVH AI",
            "root": model_name,
            "parent": None,
            "permission": []
        }
        models_list.append(model_info)
    
    print(f"Retour de /api/models: {len(models_list)} modèles")
    return JSONResponse(content={"data": models_list, "object": "list"})

@app.get("/api/tags")
async def list_tags():
    """
    Endpoint compatible avec Ollama pour lister les modèles disponibles
    """
    # Construire une réponse au format compatible avec Ollama et OpenWebUI
    ollama_models = []
    for model_name in endpoints.keys():
        # Ajouter ':latest' au nom du modèle pour OpenWebUI
        display_name = f"{model_name}:latest"
        model_data = {
            "name": display_name,  # Nom avec suffixe pour l'affichage
            "model": display_name, # Champ requis par OpenWebUI
            "modified_at": "2023-11-04T14:56:49.277302746-07:00",  # Date fictive
            "size": 0,  # Taille fictive
            "digest": f"sha256:{model_name}",  # Digest fictif
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
            }
        }
        print(f"Ajout du modèle: {model_data}")
        ollama_models.append(model_data)
    
    response_content = {"models": ollama_models}
    print(f"Réponse complète: {response_content}")
    return JSONResponse(content=response_content)

@app.post("/api/chat")
async def chat(payload: dict = Body(...)):
    """
    Endpoint compatible avec Ollama pour le chat
    """
    print(f"Requête de chat Ollama reçue: {payload}")
    
    # Extraire les informations nécessaires
    model_name = payload.get("model")
    messages = payload.get("messages", [])
    max_tokens = payload.get("max_tokens", 100)
    temperature = payload.get("temperature", 0.7)
    
    if not model_name or not messages:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'messages' sont requis.")
    
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    if ":" in model_name:
        model_name = model_name.split(":")[0]
        print(f"[INFO] Suppression du suffixe ':latest': {model_name}")
    
    if model_name not in endpoints:
        raise HTTPException(status_code=404, detail=f"Modèle '{model_name}' non trouvé.")
    
    # Convertir le format Ollama vers le format OpenAI pour notre API
    openai_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        openai_messages.append({"role": role, "content": content})
    
    # Utiliser l'endpoint existant de chat
    endpoint = endpoints[model_name]
    ovh_payload = {
        "model": model_name,
        "messages": openai_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    # Envoyer la requête à OVH
    try:
        response_data = send_request(endpoint, ovh_payload, route="chat")
        
        # Convertir la réponse OpenAI en format Ollama
        content = response_data["choices"][0]["message"]["content"]
        ollama_response = {
            "model": model_name,
            "created_at": response_data.get("created", ""),
            "message": {
                "role": "assistant",
                "content": content
            },
            "done": True
        }
        print(f"Réponse Ollama chat générée: {ollama_response}")
        return JSONResponse(content=ollama_response)
    except Exception as e:
        print(f"Erreur lors de la conversion de la réponse: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erreur de traitement: {str(e)}")

@app.post("/api/generate")
async def generate(payload: dict = Body(...)):
    """
    Endpoint compatible avec Ollama pour générer des réponses
    """
    print(f"Requête de génération Ollama reçue: {payload}")
    
    # Extraire les informations nécessaires
    model_name = payload.get("model")
    prompt = payload.get("prompt")
    system_prompt = payload.get("system", "Tu es un assistant intelligent.")
    max_tokens = payload.get("max_tokens", 100)
    temperature = payload.get("temperature", 0.7)
    
    if not model_name or not prompt:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'prompt' sont requis.")
    
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    if ":" in model_name:
        model_name = model_name.split(":")[0]
        print(f"[INFO] Suppression du suffixe ':latest': {model_name}")
    
    if model_name not in endpoints:
        raise HTTPException(status_code=404, detail=f"Modèle '{model_name}' non trouvé.")
    
    # Convertir le format Ollama vers le format OpenAI pour notre API
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # Utiliser l'endpoint existant de chat
    endpoint = endpoints[model_name]
    ovh_payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        # Envoyer la requête à OVH
        response_data = send_request(endpoint, ovh_payload, route="chat")
        
        # Convertir la réponse OpenAI en format Ollama
        content = response_data["choices"][0]["message"]["content"]
        ollama_response = {
            "model": model_name,
            "created_at": response_data.get("created", ""),
            "response": content,
            "done": True
        }
        print(f"Réponse Ollama générée: {ollama_response}")
        return JSONResponse(content=ollama_response)
    except Exception as e:
        print(f"Erreur lors de la génération: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erreur de traitement: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Endpoint de vérification de santé pour les healthchecks de Docker
    """
    print("Vérification de santé via /health")
    return {"status": "ok"}

@app.get("/api/health")
async def api_health_check():
    """
    Endpoint de vérification de santé pour OpenWebUI
    """
    print("Vérification de santé via /api/health")
    return {"status": "ok"}