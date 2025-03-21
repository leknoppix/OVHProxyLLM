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
from dotenv import load_dotenv
import sys
from pathlib import Path
import re
import random

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter un fichier de log
file_handler = logging.FileHandler('/tmp/proxy_debug.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

# Fonction de log de debug personnalisée
def debug_log(message):
    logger.debug(message)
    with open('/tmp/proxy_debug.log', 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - DEBUG - {message}\n")

# Chargement des variables d'environnement
# Essayer de charger depuis le répertoire parent si on est dans le dossier proxy
dotenv_path = Path('../.env')
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Variables d'environnement chargées depuis {dotenv_path}")
else:
    # Sinon, charger depuis le répertoire courant
    load_dotenv()
    print(f"Variables d'environnement chargées depuis le répertoire courant")

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
            # Tronquer les requêtes très longues pour éviter de remplir les logs
            body_str = body.decode()
            if len(body_str) > 2000:  # Augmenter la taille pour voir plus de contexte
                logger.info(f"Corps de la requête (tronqué): {body_str[:2000]}...")
            else:
                logger.info(f"Corps de la requête: {body_str}")
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
# Essayer d'abord OVH_TOKEN_ENDPOINT (défini dans le conteneur) puis OVH_API_TOKEN (pour compatibilité)
OVH_API_TOKEN = os.getenv('OVH_TOKEN_ENDPOINT') or os.getenv('OVH_API_TOKEN')

# En mode développement, on peut fonctionner sans token
if not OVH_API_TOKEN:
    print("AVERTISSEMENT: Aucune variable d'environnement OVH_TOKEN_ENDPOINT ou OVH_API_TOKEN n'est définie.")
    print("Le serveur démarre en mode développement (les appels aux API OVH échoueront).")
    OVH_API_TOKEN = "dummy_token_for_development"
else:
    # Afficher les premiers caractères du token pour déboguer
    token_prefix = OVH_API_TOKEN[:10] if len(OVH_API_TOKEN) > 10 else OVH_API_TOKEN
    token_suffix = OVH_API_TOKEN[-5:] if len(OVH_API_TOKEN) > 5 else ""
    print(f"Token OVH récupéré: {token_prefix}...{token_suffix} (longueur: {len(OVH_API_TOKEN)})")

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
    "mamba-codestral-7b-v0-1": "https://mamba-codestral-7b-v0-1.endpoints.kepler.ai.cloud.ovh.net",
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
        "deepseek-r1-distill-llama-70b": "DeepSeek-R1-Distill-Llama-70B",
        "mamba-codestral-7b-v0-1": "mamba-codestral-7B-v0.1"
    }
    
    # Log supplémentaire pour le débogage
    debug_log(f"OVH TOKEN - Longueur du token: {len(OVH_API_TOKEN)}")
    debug_log(f"OVH TOKEN - 10 premiers caractères: {OVH_API_TOKEN[:10]}")
    debug_log(f"OVH TOKEN - 10 derniers caractères: {OVH_API_TOKEN[-10:]}")
    
    # Vérifier si c'est DeepSeek pour ajuster le timeout
    is_deepseek = payload.get("model", "").lower() == "deepseek-r1-distill-llama-70b"
    request_timeout = 90 if is_deepseek else 30  # 90 secondes pour DeepSeek, 30 pour les autres
    debug_log(f"Timeout configuré pour {payload.get('model')}: {request_timeout} secondes")
    
    # Vérifiez si la requête est pour une explication détaillée et réduisez la température pour DeepSeek
    if is_deepseek:
        request_text = ""
        if "messages" in payload:
            request_text = " ".join([msg.get("content", "") for msg in payload["messages"] if isinstance(msg.get("content", ""), str)])
        if any(keyword in request_text.lower() for keyword in ["détail", "expliqu", "comment", "fonctionne"]):
            # Réduire la température pour les explications détaillées avec DeepSeek
            payload["temperature"] = 0.5  # Valeur plus faible pour une sortie plus déterministe
            debug_log(f"DeepSeek: Détection de requête d'explication détaillée, température réduite à {payload['temperature']}")
    
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
        debug_log(f"Suppression du suffixe :latest du modèle: {payload['model']}")
    
    # Remplacer le nom du modèle dans le payload par le nom exact utilisé par OVH
    model_name_original = payload.get("model", "")
    if "model" in payload and payload["model"] in model_name_map:
        payload["model"] = model_name_map[payload["model"]]
        debug_log(f"Conversion du nom de modèle: {model_name_original} -> {payload['model']}")
    
    # Ajouter les options supplémentaires supportées par certains modèles
    # Pour éviter de les inclure si elles ne sont pas explicitement demandées
    if "stream" in payload:
        debug_log(f"Option 'stream' détectée avec la valeur: {payload['stream']}")
    
    if "logprobs" in payload:
        debug_log(f"Option 'logprobs' détectée avec la valeur: {payload['logprobs']}")
    
    if "seed" in payload:
        debug_log(f"Option 'seed' détectée avec la valeur: {payload['seed']}")
    
    # Traitement spécial pour DeepSeek
    is_deepseek = model_name_original == "deepseek-r1-distill-llama-70b"
    
    if route == "chat":
        if is_deepseek:
            # Pour DeepSeek, utiliser uniquement l'URL qui fonctionne
            urls = [f"{endpoint}/api/openai_compat/v1/chat/completions"]
        else:
            # Format possible 1 (original)
            urls.append(f"{endpoint}/api/openai_compat/v1/chat/completions")
            # Format possible 2 (standard OpenAI)
            urls.append(f"{endpoint}/v1/chat/completions")
            # Format possible 3 (sans le préfixe openai_compat)
            urls.append(f"{endpoint}/api/v1/chat/completions")
    elif route == "completions":
        if is_deepseek:
            # Pour DeepSeek, utiliser uniquement l'URL qui fonctionne
            urls = [f"{endpoint}/api/openai_compat/v1/completions"]
        else:
            # Format possible 1 (original)
            urls.append(f"{endpoint}/api/openai_compat/v1/completions")
            # Format possible 2 (standard OpenAI)
            urls.append(f"{endpoint}/v1/completions")
            # Format possible 3 (sans le préfixe openai_compat)
            urls.append(f"{endpoint}/api/v1/completions")
    else:
        error_msg = f"Route inconnue: {route}"
        debug_log(error_msg)
        raise ValueError(error_msg)

    headers = {
        "Authorization": f"Bearer {OVH_API_TOKEN}",
        "Content-Type": "application/json"
    }

    last_error = None
    
    # Test direct avec requests pour vérifier que le token fonctionne
    test_url = f"{endpoint}/api/openai_compat/v1/models"
    debug_log(f"Test direct avec requests à l'URL : {test_url}")
    try:
        test_response = requests.get(test_url, headers=headers, timeout=5)
        debug_log(f"Test direct: statut = {test_response.status_code}")
        debug_log(f"Test direct: réponse = {test_response.text[:100]}")
    except Exception as e:
        debug_log(f"Exception lors du test direct: {str(e)}")
    
    debug_log(f"Trying all possible URLs for {route}: {urls}")
    
    # Variables pour le mécanisme de retry
    max_retries = 3 if is_deepseek else 2  # Plus de retries pour DeepSeek
    backoff_factor = 2  # Facteur multiplicatif pour le délai entre retries
    
    # Essayons chaque URL jusqu'à ce que l'une d'elles fonctionne
    for url in urls:
        retry_count = 0
        while retry_count < max_retries:
            try:
                debug_log(f"Essai avec l'URL : {url} (tentative {retry_count+1}/{max_retries})")
                debug_log(f"Headers : {headers}")
                debug_log(f"Payload : {json.dumps(payload, ensure_ascii=False)}")
                
                # Ajouter un timeout pour éviter les blocages indéfinis
                # Utiliser un timeout plus long pour DeepSeek
                debug_log(f"Timeout configuré: {request_timeout} secondes")
                response = requests.post(url, json=payload, headers=headers, timeout=request_timeout)
                debug_log(f"Code de statut : {response.status_code}")
                debug_log(f"Réponse : {response.text}")
                
                if response.status_code == 200:
                    return response.json()
                
                # Si on a un code d'erreur 500 ou supérieur, on fait un retry
                if response.status_code >= 500:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Backoff exponentiel avec jitter (aléatoire)
                        delay = (backoff_factor ** retry_count) + random.uniform(0, 1)
                        debug_log(f"Erreur serveur: {response.status_code}, retry dans {delay:.2f} secondes...")
                        time.sleep(delay)
                        continue
                
                last_error = response
                break  # Sortir de la boucle de retry si l'erreur n'est pas récupérable
            except requests.exceptions.Timeout:
                debug_log(f"Timeout pour l'URL {url} (tentative {retry_count+1}/{max_retries})")
                retry_count += 1
                if retry_count < max_retries:
                    # Backoff exponentiel avec jitter pour les timeouts
                    delay = (backoff_factor ** retry_count) + random.uniform(0, 1)
                    debug_log(f"Timeout: nouvelle tentative dans {delay:.2f} secondes...")
                    time.sleep(delay)
                    continue
                last_error = Exception(f"Timeout lors de la connexion à {url} après {max_retries} tentatives")
                break
            except Exception as e:
                debug_log(f"Exception pour l'URL {url}: {str(e)}")
                debug_log(f"Exception type: {type(e)}")
                debug_log(f"Exception details: {repr(e)}")
                retry_count += 1
                if retry_count < max_retries and isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout)):
                    # Backoff exponentiel pour les erreurs de connexion
                    delay = (backoff_factor ** retry_count) + random.uniform(0, 1)
                    debug_log(f"Erreur de connexion: nouvelle tentative dans {delay:.2f} secondes...")
                    time.sleep(delay)
                    continue
                last_error = e
                break
    
    # Si on est arrivé ici, aucune URL n'a fonctionné
    if isinstance(last_error, requests.Response):
        error_msg = f"Erreur HTTP: {last_error.status_code} - {last_error.text}"
        debug_log(f"Erreur finale: {error_msg}")
        raise HTTPException(status_code=last_error.status_code, detail=error_msg)
    else:
        error_msg = f"Erreur de requête: {str(last_error)}"
        debug_log(f"Erreur finale: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

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

# Augmenter encore les valeurs max_tokens par défaut pour tous les modèles
DEFAULT_MAX_TOKENS = {
    "deepseek-r1-distill-llama-70b": 2000,  # DeepSeek est particulièrement bavard
    "llama-3-3-70b-instruct": 1500,
    "llama-3-1-70b-instruct": 1500,
    "mixtral-8x7b-instruct-v0.1": 1000,
    "mamba-codestral-7b-v0-1": 2500,  # Valeur élevée pour la génération de code
    "default": 500  # Valeur par défaut pour les autres modèles
}

@app.post("/v1/chat/completions")
async def chat_completions(payload: dict = Body(...)):
    try:
        model_name = payload.get("model")
        messages = payload.get("messages")
        
        # Utiliser la valeur spécifique au modèle ou la valeur par défaut
        default_max_tokens = DEFAULT_MAX_TOKENS.get(model_name, DEFAULT_MAX_TOKENS["default"])
        max_tokens = payload.get("max_tokens", default_max_tokens)
        temperature = payload.get("temperature", 1.0)

        # Forcer une valeur élevée de max_tokens pour les questions détaillées
        request_text = " ".join([msg.get("content", "") for msg in messages if isinstance(msg.get("content", ""), str)])
        
        # Détection des requêtes d'explication détaillée
        if any(keyword in request_text.lower() for keyword in ["détail", "expliqu", "comment fonctionne", "explique"]):
            # Utiliser au moins 1500 tokens pour les demandes d'explications détaillées
            max_tokens = max(max_tokens, 1500)
            debug_log(f"Détection d'une demande d'explication détaillée, augmentation de max_tokens à {max_tokens}")
        
        # Détection des requêtes de code
        if model_name == "mamba-codestral-7b-v0-1" or any(keyword in request_text.lower() for keyword in ["code", "programme", "script", "fonction", "class", "api", "développe"]):
            # Réduire la température pour le code pour plus de précision
            if "temperature" not in payload:
                temperature = 0.2
                debug_log(f"Détection d'une demande de code, réduction de la température à {temperature}")
            # S'assurer d'avoir suffisamment de tokens pour le code
            if model_name == "mamba-codestral-7b-v0-1":
                max_tokens = max(max_tokens, 2500)
                debug_log(f"Utilisation du modèle de code, augmentation de max_tokens à {max_tokens}")

        if not model_name or not messages:
            return JSONResponse(
                status_code=422, 
                content={"error": "Les champs 'model' et 'messages' sont requis."}
            )
            
        # Supprimer le suffixe ':latest' ajouté par OpenWebUI
        original_model = model_name
        if ":" in model_name:
            model_name = model_name.split(":")[0]
            print(f"[INFO] Suffixe ':latest' supprimé du nom du modèle: {model_name}")

        if model_name not in endpoints:
            return JSONResponse(
                status_code=404, 
                content={"error": f"Modèle '{model_name}' non trouvé."}
            )

        endpoint = endpoints[model_name]
        ovh_payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Si c'est DeepSeek, ajoutons des logs de débogage supplémentaires
        if model_name == "deepseek-r1-distill-llama-70b":
            debug_log(f"Requête DeepSeek via API standard - Modèle: {original_model}")
            debug_log(f"Payload pour DeepSeek: {json.dumps(ovh_payload, ensure_ascii=False)}")
        
        # Essayer d'envoyer la requête, mais capturer toute exception
        try:
            result = send_request(endpoint, ovh_payload, route="chat")
            
            # Si c'est DeepSeek, loggons la réponse
            if model_name == "deepseek-r1-distill-llama-70b":
                debug_log(f"Réponse DeepSeek (API standard): {json.dumps(result, ensure_ascii=False)}")
            
            # Post-traitement spécial pour DeepSeek
            if model_name == "deepseek-r1-distill-llama-70b" and "choices" in result:
                for choice in result["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        # Nettoyer les balises <think></think> dans la réponse
                        content = choice["message"]["content"]
                        # Utiliser une regex pour supprimer les balises et leur contenu
                        cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                        choice["message"]["content"] = cleaned_content
                        debug_log(f"DeepSeek: Nettoyage des balises <think> effectué. Longueur avant: {len(content)}, Longueur après: {len(cleaned_content)}")
            
            # Si c'est DeepSeek, loggons la réponse après traitement
            if model_name == "deepseek-r1-distill-llama-70b":
                debug_log(f"Réponse DeepSeek après traitement: {json.dumps(result, ensure_ascii=False)}")
            
            return result
        except Exception as e:
            # Récupérer les détails de l'erreur
            if isinstance(e, HTTPException):
                error_detail = str(e.detail)
                status_code = e.status_code
            else:
                error_detail = str(e)
                status_code = 500
                
            # Retourner un message d'erreur détaillé au lieu de lever une exception
            return JSONResponse(
                status_code=status_code, 
                content={
                    "error": "Échec de l'appel API", 
                    "detail": error_detail,
                    "model": model_name,
                    "endpoint": endpoint
                }
            )
    except Exception as outer_e:
        # Attraper les erreurs inattendues
        return JSONResponse(
            status_code=500, 
            content={
                "error": "Erreur inattendue", 
                "detail": str(outer_e)
            }
        )

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
    
    # Utiliser la valeur spécifique au modèle ou la valeur par défaut
    default_max_tokens = DEFAULT_MAX_TOKENS.get(model_name.split(":")[0] if ":" in model_name else model_name, 
                                             DEFAULT_MAX_TOKENS["default"])
    max_tokens = payload.get("max_tokens", default_max_tokens)
    temperature = payload.get("temperature", 0.7)
    
    # Récupérer le nom du modèle sans le suffixe
    clean_model_name = model_name.split(":")[0] if ":" in model_name else model_name
    
    # Forcer une valeur élevée de max_tokens pour les questions détaillées
    request_text = " ".join([msg.get("content", "") for msg in messages if isinstance(msg.get("content", ""), str)])
    
    # Détection des requêtes d'explication détaillée
    if any(keyword in request_text.lower() for keyword in ["détail", "expliqu", "comment fonctionne", "explique"]):
        # Utiliser au moins 1500 tokens pour les demandes d'explications détaillées
        max_tokens = max(max_tokens, 1500)
        debug_log(f"Détection d'une demande d'explication détaillée, augmentation de max_tokens à {max_tokens}")
    
    # Détection des requêtes de code
    if clean_model_name == "mamba-codestral-7b-v0-1" or any(keyword in request_text.lower() for keyword in ["code", "programme", "script", "fonction", "class", "api", "développe"]):
        # Réduire la température pour le code pour plus de précision
        if "temperature" not in payload:
            temperature = 0.2
            debug_log(f"Détection d'une demande de code, réduction de la température à {temperature}")
        # S'assurer d'avoir suffisamment de tokens pour le code
        if clean_model_name == "mamba-codestral-7b-v0-1":
            max_tokens = max(max_tokens, 2500)
            debug_log(f"Utilisation du modèle de code, augmentation de max_tokens à {max_tokens}")
    
    if not model_name or not messages:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'messages' sont requis.")
    
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    original_model = model_name
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
    
    # Si c'est DeepSeek, ajoutons des logs de débogage supplémentaires
    if "deepseek" in model_name:
        debug_log(f"Requête DeepSeek via OpenWebUI - Modèle: {original_model}")
        debug_log(f"Payload pour DeepSeek: {json.dumps(ovh_payload, ensure_ascii=False)}")
    
    # Envoyer la requête à OVH
    try:
        response_data = send_request(endpoint, ovh_payload, route="chat")
        
        # Si c'est DeepSeek, loggons la réponse
        if "deepseek" in model_name:
            debug_log(f"Réponse DeepSeek: {json.dumps(response_data, ensure_ascii=False)}")
        
        # Convertir la réponse OpenAI en format Ollama
        content = response_data["choices"][0]["message"]["content"]
        
        # Post-traitement spécial pour DeepSeek - nettoyer les balises <think></think>
        if model_name == "deepseek-r1-distill-llama-70b":
            # Utiliser une regex pour supprimer les balises et leur contenu
            original_content = content
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            debug_log(f"DeepSeek (api/chat): Nettoyage des balises <think> effectué. Longueur avant: {len(original_content)}, Longueur après: {len(content)}")
        
        ollama_response = {
            "model": model_name,
            "created_at": response_data.get("created", ""),
            "message": {
                "role": "assistant",
                "content": content
            },
            "done": True
        }
        if "deepseek" in model_name:
            debug_log(f"Réponse Ollama DeepSeek: {json.dumps(ollama_response, ensure_ascii=False)}")
        
        print(f"Réponse Ollama chat générée avec {len(content)} caractères")
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
    
    # Utiliser la valeur spécifique au modèle ou la valeur par défaut
    default_max_tokens = DEFAULT_MAX_TOKENS.get(model_name.split(":")[0] if ":" in model_name else model_name, 
                                             DEFAULT_MAX_TOKENS["default"])
    max_tokens = payload.get("max_tokens", default_max_tokens)
    temperature = payload.get("temperature", 0.7)
    
    # Récupérer le nom du modèle sans le suffixe
    clean_model_name = model_name.split(":")[0] if ":" in model_name else model_name
    
    # Forcer une valeur élevée de max_tokens pour les questions détaillées
    request_text = prompt if isinstance(prompt, str) else ""
    
    # Détection des requêtes d'explication détaillée
    if any(keyword in request_text.lower() for keyword in ["détail", "expliqu", "comment fonctionne", "explique"]):
        # Utiliser au moins 1500 tokens pour les demandes d'explications détaillées
        max_tokens = max(max_tokens, 1500)
        debug_log(f"Détection d'une demande d'explication détaillée, augmentation de max_tokens à {max_tokens}")
    
    # Détection des requêtes de code
    if clean_model_name == "mamba-codestral-7b-v0-1" or any(keyword in request_text.lower() for keyword in ["code", "programme", "script", "fonction", "class", "api", "développe"]):
        # Réduire la température pour le code pour plus de précision
        if "temperature" not in payload:
            temperature = 0.2
            debug_log(f"Détection d'une demande de code, réduction de la température à {temperature}")
        # S'assurer d'avoir suffisamment de tokens pour le code
        if clean_model_name == "mamba-codestral-7b-v0-1":
            max_tokens = max(max_tokens, 2500)
            debug_log(f"Utilisation du modèle de code, augmentation de max_tokens à {max_tokens}")
            
            # Ajouter un système prompt spécifique pour le code si nécessaire
            if "system" not in payload:
                system_prompt = "Tu es un expert en programmation. Réponds avec du code bien structuré, commenté et optimisé."
                debug_log(f"Ajout d'un system prompt spécifique pour le modèle de code")
    
    if not model_name or not prompt:
        raise HTTPException(status_code=422, detail="Les champs 'model' et 'prompt' sont requis.")
    
    # Supprimer le suffixe ':latest' ajouté par OpenWebUI
    original_model = model_name
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
    
    # Si c'est DeepSeek, ajoutons des logs de débogage supplémentaires
    if "deepseek" in model_name:
        debug_log(f"Requête DeepSeek via OpenWebUI (generate) - Modèle: {original_model}")
        debug_log(f"Payload pour DeepSeek: {json.dumps(ovh_payload, ensure_ascii=False)}")
    
    try:
        # Envoyer la requête à OVH
        response_data = send_request(endpoint, ovh_payload, route="chat")
        
        # Si c'est DeepSeek, loggons la réponse
        if "deepseek" in model_name:
            debug_log(f"Réponse DeepSeek (generate): {json.dumps(response_data, ensure_ascii=False)}")
        
        # Convertir la réponse OpenAI en format Ollama
        content = response_data["choices"][0]["message"]["content"]
        
        # Post-traitement spécial pour DeepSeek - nettoyer les balises <think></think>
        if model_name == "deepseek-r1-distill-llama-70b":
            # Utiliser une regex pour supprimer les balises et leur contenu
            original_content = content
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            debug_log(f"DeepSeek (api/generate): Nettoyage des balises <think> effectué. Longueur avant: {len(original_content)}, Longueur après: {len(content)}")
        
        ollama_response = {
            "model": model_name,
            "created_at": response_data.get("created", ""),
            "response": content,
            "done": True
        }
        
        if "deepseek" in model_name:
            debug_log(f"Réponse Ollama DeepSeek (generate): {json.dumps(ollama_response, ensure_ascii=False)}")
        
        print(f"Réponse Ollama generate générée avec {len(content)} caractères")
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

@app.get("/diagnostic")
async def diagnostic():
    """
    Route de diagnostic qui teste explicitement la connexion à l'API OVH
    et retourne les résultats détaillés pour comprendre le problème.
    """
    results = {
        "environment": {},
        "token_info": {},
        "direct_test": {},
        "api_calls": []
    }
    
    # Définition du mapping des modèles ici
    model_name_map = {
        "mistral-7b-instruct-v0.3": "Mistral-7B-Instruct-v0.3",
        "mixtral-8x7b-instruct-v0.1": "Mixtral-8x7B-Instruct-v0.1",
        "mistral-nemo-instruct-2407": "Mistral-Nemo-Instruct-2407",
        "llama-3-1-8b-instruct": "Llama-3.1-8B-Instruct",
        "llama-3-3-70b-instruct": "Meta-Llama-3_3-70B-Instruct",
        "llama-3-1-70b-instruct": "Meta-Llama-3_1-70B-Instruct",
        "deepseek-r1-distill-llama-70b": "DeepSeek-R1-Distill-Llama-70B",
        "mamba-codestral-7b-v0-1": "mamba-codestral-7B-v0.1"
    }
    
    # 1. Informations sur l'environnement
    results["environment"]["working_directory"] = os.getcwd()
    results["environment"]["environment_vars"] = {k: v[:10] + "..." + v[-10:] if len(v) > 20 else v 
                                               for k, v in os.environ.items() 
                                               if "TOKEN" in k or "OVH" in k or "API" in k}
    
    # 2. Informations sur le token
    # Essayer d'abord OVH_API_TOKEN, puis OVH_TOKEN_ENDPOINT comme fallback
    token = os.environ.get("OVH_API_TOKEN", os.environ.get("OVH_TOKEN_ENDPOINT", ""))
    results["token_info"]["length"] = len(token)
    results["token_info"]["first_10_chars"] = token[:10] if token else ""
    results["token_info"]["last_10_chars"] = token[-10:] if token else ""
    
    # 3. Test direct avec le token récupéré
    for model_name, endpoint in endpoints.items():
        test_url = f"{endpoint}/api/openai_compat/v1/models"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        try:
            test_response = requests.get(test_url, headers=headers, timeout=5)
            results["api_calls"].append({
                "model": model_name,
                "url": test_url,
                "status_code": test_response.status_code,
                "response": test_response.text[:200] if test_response.status_code == 200 else test_response.text
            })
            
            # Si le premier test réussit, essayons une requête de chat simple
            if test_response.status_code == 200:
                chat_url = f"{endpoint}/api/openai_compat/v1/chat/completions"
                payload = {
                    "model": model_name_map.get(model_name, model_name),
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 10
                }
                
                try:
                    chat_response = requests.post(chat_url, headers=headers, json=payload, timeout=10)
                    results["api_calls"].append({
                        "model": model_name,
                        "url": chat_url,
                        "payload": payload,
                        "status_code": chat_response.status_code,
                        "response": chat_response.text[:200] if chat_response.status_code == 200 else chat_response.text
                    })
                except Exception as e:
                    results["api_calls"].append({
                        "model": model_name,
                        "url": chat_url,
                        "error": str(e)
                    })
        except Exception as e:
            results["api_calls"].append({
                "model": model_name,
                "url": test_url,
                "error": str(e)
            })
    
    return results