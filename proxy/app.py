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

# Charger les variables d'environnement depuis le fichier .env à la racine
root_env_path = Path(__file__).parent.parent / '.env'
if root_env_path.exists():
    print(f"Chargement des variables d'environnement depuis {root_env_path}")
    load_dotenv(dotenv_path=root_env_path)
else:
    print(f"Fichier .env non trouvé à {root_env_path}, utilisation des variables d'environnement système")
    load_dotenv()  # Charger depuis le .env dans le répertoire courant s'il existe

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

# Si le token n'est pas trouvé, essayer de le charger depuis le fichier .env
if not OVH_API_TOKEN:
    try:
        from dotenv import load_dotenv
        # Essayer de charger depuis le répertoire courant
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Chargement des variables d'environnement depuis {env_path.absolute()}")
            OVH_API_TOKEN = os.getenv('OVH_TOKEN_ENDPOINT') or os.getenv('OVH_API_TOKEN')
        
        # Si toujours pas de token, essayer de charger depuis le répertoire parent
        if not OVH_API_TOKEN:
            parent_env_path = Path('../.env')
            if parent_env_path.exists():
                load_dotenv(parent_env_path)
                print(f"Chargement des variables d'environnement depuis {parent_env_path.absolute()}")
                OVH_API_TOKEN = os.getenv('OVH_TOKEN_ENDPOINT') or os.getenv('OVH_API_TOKEN')
    except Exception as e:
        print(f"Erreur lors du chargement du fichier .env: {str(e)}")

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

# Configuration des endpoints alternatifs
# Format: {modèle: [endpoint_url1, endpoint_url2, ...]}
alternative_endpoints = {
    # Exemple: "mistral-7b-instruct-v0.3": [
    #     "https://mistral-7b-instruct-v0-3.endpoints.alternative1.ai.cloud.ovh.net",
    #     "https://mistral-7b-instruct-v0-3.endpoints.alternative2.ai.cloud.ovh.net"
    # ]
}

# Charger la configuration des endpoints alternatifs depuis un fichier JSON si disponible
endpoints_config_path = Path('endpoints_config.json')
if endpoints_config_path.exists():
    try:
        with open(endpoints_config_path, 'r') as f:
            config = json.load(f)
            if "alternative_endpoints" in config:
                for model, alt_endpoints in config["alternative_endpoints"].items():
                    if model not in alternative_endpoints:
                        alternative_endpoints[model] = []
                    for endpoint_data in alt_endpoints:
                        if isinstance(endpoint_data, list) and len(endpoint_data) >= 1:
                            # Ignorer l'index du token car nous utilisons le même token pour tous les endpoints
                            alternative_endpoints[model].append(endpoint_data[0])
                        elif isinstance(endpoint_data, str):
                            alternative_endpoints[model].append(endpoint_data)
                        else:
                            print(f"Format incorrect pour l'endpoint alternatif: {endpoint_data}")
            print(f"Configuration des endpoints alternatifs chargée depuis {endpoints_config_path}")
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration des endpoints: {str(e)}")

def send_request(endpoint: str, payload: dict, route: str):
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
    
    # MODIFICATION: Augmenter les timeouts pour tous les modèles
    request_timeout = 120 if is_deepseek else 60  # 120 secondes pour DeepSeek, 60 pour les autres
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
    
    # MODIFICATION: Simplifier la gestion des URLs et utiliser uniquement le format correct
    # d'après la documentation OpenAPI d'OVH
    if route == "chat":
        # Format standard selon la documentation OpenAPI d'OVH
        url = f"{endpoint}/api/openai_compat/v1/chat/completions"
    elif route == "completions":
        # Format standard selon la documentation OpenAPI d'OVH
        url = f"{endpoint}/api/openai_compat/v1/completions"
    else:
        error_msg = f"Route inconnue: {route}"
        debug_log(f"Erreur finale: {error_msg}")
        raise ValueError(error_msg)

    debug_log(f"URL utilisée pour {route}: {url}")

    # Préparer la liste des endpoints à essayer
    endpoints_to_try = [(endpoint, 0)]  # Le tuple contient (endpoint_url, token_index)
    
    # Ajouter les endpoints alternatifs si disponibles pour ce modèle
    if model_name_original in alternative_endpoints:
        endpoints_to_try.extend([(alt_endpoint, 0) for alt_endpoint in alternative_endpoints[model_name_original]])
        debug_log(f"Endpoints alternatifs disponibles pour {model_name_original}: {len(alternative_endpoints[model_name_original])}")
    
    last_error = None
    
    # Variables pour le mécanisme de retry
    max_retries = 3 if is_deepseek else 2  # Plus de retries pour DeepSeek
    backoff_factor = 2  # Facteur multiplicatif pour le délai entre retries
    
    # AJOUT: Simplifier le payload pour le premier essai si c'est une requête complexe
    simplified_payload = None
    if "messages" in payload and len(payload["messages"]) > 1:
        # Créer une version simplifiée du payload pour le premier essai
        simplified_payload = payload.copy()
        # Garder seulement le dernier message utilisateur
        user_messages = [msg for msg in payload["messages"] if msg.get("role") == "user"]
        if user_messages:
            simplified_payload["messages"] = [{"role": "user", "content": user_messages[-1].get("content", "")}]
            # Réduire max_tokens pour accélérer la réponse
            if "max_tokens" in simplified_payload:
                simplified_payload["max_tokens"] = min(simplified_payload["max_tokens"], 50)
            debug_log(f"Payload simplifié créé pour le premier essai: {json.dumps(simplified_payload, ensure_ascii=False)}")
    
    # Essayer chaque endpoint disponible
    for current_endpoint, token_index in endpoints_to_try:
        # Sélectionner le token approprié
        current_token = OVH_API_TOKEN
        
        # Construire l'URL complète
        if route == "chat":
            current_url = f"{current_endpoint}/api/openai_compat/v1/chat/completions"
        elif route == "completions":
            current_url = f"{current_endpoint}/api/openai_compat/v1/completions"
        else:
            continue  # Ignorer cet endpoint si la route est inconnue
        
        debug_log(f"Essai avec l'endpoint: {current_endpoint}")
        
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json"
        }
        
        # Test direct avec requests pour vérifier que le token fonctionne
        test_url = f"{current_endpoint}/api/openai_compat/v1/models"
        debug_log(f"Test direct avec requests à l'URL : {test_url}")
        try:
            test_response = requests.get(test_url, headers=headers, timeout=10)
            debug_log(f"Test direct: statut = {test_response.status_code}")
            debug_log(f"Test direct: réponse = {test_response.text[:500]}")  # Augmenter la taille du log
            
            # Vérifier explicitement si le token est valide
            if test_response.status_code == 401:
                debug_log(f"ERREUR: Le token d'API OVH {token_index} semble être invalide (401 Unauthorized)")
                continue  # Essayer le prochain endpoint
            elif test_response.status_code == 403:
                debug_log(f"ERREUR: Le token d'API OVH {token_index} n'a pas les permissions nécessaires (403 Forbidden)")
                continue  # Essayer le prochain endpoint
            elif test_response.status_code >= 400:
                debug_log(f"ERREUR: Problème avec l'API OVH (Status: {test_response.status_code})")
                continue  # Essayer le prochain endpoint
        except Exception as e:
            debug_log(f"ERREUR: Exception lors du test direct: {str(e)}")
            continue  # Essayer le prochain endpoint
        
        debug_log(f"Trying URL for {route}: {current_url}")
        
        # AJOUT: Essayer d'abord avec un payload simplifié si disponible
        if simplified_payload is not None:
            try:
                debug_log(f"Essai initial avec payload simplifié à l'URL : {current_url}")
                debug_log(f"Headers : {headers}")
                debug_log(f"Payload simplifié : {json.dumps(simplified_payload, ensure_ascii=False)}")
                
                # Utiliser un timeout plus court pour ce test
                test_timeout = 15
                debug_log(f"Timeout pour test simplifié: {test_timeout} secondes")
                response = requests.post(current_url, json=simplified_payload, headers=headers, timeout=test_timeout)
                debug_log(f"Test simplifié - Code de statut : {response.status_code}")
                
                if response.status_code == 200:
                    debug_log("Test simplifié réussi! L'API OVH fonctionne.")
                    # Ne pas retourner cette réponse, continuer avec le payload complet
                else:
                    debug_log(f"Test simplifié échoué avec status {response.status_code}")
                    if response.status_code == 401 or response.status_code == 403:
                        continue  # Problème d'authentification, essayer le prochain endpoint
            except Exception as e:
                debug_log(f"Exception lors du test simplifié: {str(e)}")
                # Continuer avec le payload complet
        
        # Essayer avec le payload complet
        retry_count = 0
        while retry_count < max_retries:
            try:
                debug_log(f"Essai avec l'URL : {current_url} (tentative {retry_count+1}/{max_retries})")
                debug_log(f"Headers : {headers}")
                debug_log(f"Payload : {json.dumps(payload, ensure_ascii=False)}")
                
                # Ajouter un timeout pour éviter les blocages indéfinis
                debug_log(f"Timeout configuré: {request_timeout} secondes")
                response = requests.post(current_url, json=payload, headers=headers, timeout=request_timeout)
                debug_log(f"Code de statut : {response.status_code}")
                
                # AJOUT: Log plus détaillé de la réponse
                if len(response.text) > 1000:
                    debug_log(f"Réponse (tronquée) : {response.text[:1000]}...")
                else:
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
                
                # Gestion spécifique des erreurs d'authentification
                if response.status_code == 401 or response.status_code == 403:
                    debug_log(f"ERREUR: Token d'API OVH {token_index} invalide ({response.status_code})")
                    break  # Sortir de la boucle de retry et essayer le prochain endpoint
                
                # Gestion spécifique des erreurs de quota
                if response.status_code == 429:
                    debug_log(f"ERREUR: Quota d'API OVH {token_index} dépassé (429 Too Many Requests)")
                    break  # Sortir de la boucle de retry et essayer le prochain endpoint
                
                last_error = response
                break  # Sortir de la boucle de retry si l'erreur n'est pas récupérable
            except requests.exceptions.Timeout:
                debug_log(f"Timeout pour l'URL {current_url} (tentative {retry_count+1}/{max_retries})")
                retry_count += 1
                if retry_count < max_retries:
                    # Backoff exponentiel avec jitter pour les timeouts
                    delay = (backoff_factor ** retry_count) + random.uniform(0, 1)
                    debug_log(f"Timeout: nouvelle tentative dans {delay:.2f} secondes...")
                    time.sleep(delay)
                    continue
                last_error = Exception(f"Timeout lors de la connexion à {current_url} après {max_retries} tentatives")
                break
            except Exception as e:
                debug_log(f"Exception pour l'URL {current_url}: {str(e)}")
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
    
    # Si on est arrivé ici, aucun endpoint n'a fonctionné
    if isinstance(last_error, requests.Response):
        error_msg = f"Erreur HTTP: {last_error.status_code} - {last_error.text}"
        debug_log(f"Erreur finale: {error_msg}")
        raise HTTPException(status_code=last_error.status_code, detail=error_msg)
    else:
        error_msg = f"Erreur de requête: {str(last_error) if last_error else 'Tous les endpoints ont échoué'}"
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
    # Créer une liste unique de modèles disponibles
    available_models = set(endpoints.keys())
    
    # Ajouter les modèles des endpoints alternatifs
    for model in alternative_endpoints.keys():
        available_models.add(model)
    
    model_list = [{"id": name, "object": "model"} for name in sorted(available_models)]
    
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
    print(f"[DEBUG] Requête reçue sur /v1/chat/completions avec payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
    try:
        # Vu00e9rifier si nous sommes en mode test
        test_mode = payload.get("test_mode", False)
        
        # Si nous sommes en mode test, renvoyer une ru00e9ponse immu00e9diate pour les tests
        if test_mode:
            debug_log("Mode test activu00e9, renvoi d'une ru00e9ponse immu00e9diate")
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload.get("model", "test-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Ceci est une ru00e9ponse de test automatique. Le mode test est activu00e9."
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 15,
                    "total_tokens": 25
                }
            }
        
        model_name = payload.get("model")
        messages = payload.get("messages")
        
        print(f"[DEBUG] Modèle demandé: {model_name}")
        print(f"[DEBUG] Messages: {json.dumps(messages, ensure_ascii=False)[:500]}")
        
        # Utiliser la valeur spécifique au modèle ou la valeur par défaut
        default_max_tokens = DEFAULT_MAX_TOKENS.get(model_name, DEFAULT_MAX_TOKENS["default"])
        max_tokens = payload.get("max_tokens", default_max_tokens)
        temperature = payload.get("temperature", 1.0)

        print(f"[DEBUG] max_tokens: {max_tokens}, temperature: {temperature}")
        
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
            print(f"[DEBUG] Envoi de la requête à l'endpoint {endpoint} avec route 'chat'")
            result = send_request(endpoint, ovh_payload, route="chat")
            print(f"[DEBUG] Requête envoyée avec succès, résultat reçu")
            
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
        print(f"[DEBUG] Envoi de la requête à l'endpoint {endpoint} avec route 'chat'")
        result = send_request(endpoint, ovh_payload, route="chat")
        print(f"[DEBUG] Requête envoyée avec succès, résultat reçu")
        
        # Si c'est DeepSeek, loggons la réponse
        if "deepseek" in model_name:
            debug_log(f"Réponse DeepSeek: {json.dumps(result, ensure_ascii=False)}")
        
        # Convertir la réponse OpenAI en format Ollama
        content = result["choices"][0]["message"]["content"]
        
        # Post-traitement spécial pour DeepSeek - nettoyer les balises <think></think>
        if model_name == "deepseek-r1-distill-llama-70b":
            # Utiliser une regex pour supprimer les balises et leur contenu
            original_content = content
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            debug_log(f"DeepSeek: Nettoyage des balises <think> effectué. Longueur avant: {len(original_content)}, Longueur après: {len(content)}")
        
        ollama_response = {
            "model": model_name,
            "created_at": result.get("created", ""),
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
        "status": "ok",
        "timestamp": time.time(),
        "server_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "api_token_length": len(OVH_API_TOKEN) if OVH_API_TOKEN else 0,
            "api_token_prefix": OVH_API_TOKEN[:5] + "..." if OVH_API_TOKEN and len(OVH_API_TOKEN) > 10 else "Non défini",
            "endpoints_count": len(endpoints),
            "alternative_endpoints_count": sum(len(endpoints) for endpoints in alternative_endpoints.values())
        },
        "endpoints_status": {},
        "models_available": []
    }
    
    # Tester chaque endpoint principal
    for model_name, endpoint_url in endpoints.items():
        # Construire l'URL de test
        test_url = f"{endpoint_url}/api/openai_compat/v1/models"
        
        # Préparer les headers
        headers = {
            "Authorization": f"Bearer {OVH_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Tester la connexion
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            
            # Enregistrer le résultat
            results["endpoints_status"][model_name] = {
                "url": endpoint_url,
                "status_code": response.status_code,
                "status": "ok" if response.status_code == 200 else "error",
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
            
            # Si la réponse est OK, essayer de parser les modèles disponibles
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data:
                        for model in data["data"]:
                            if model.get("id") not in results["models_available"]:
                                results["models_available"].append(model.get("id"))
                except Exception as e:
                    results["endpoints_status"][model_name]["parse_error"] = str(e)
        except requests.exceptions.Timeout:
            results["endpoints_status"][model_name] = {
                "url": endpoint_url,
                "status": "timeout",
                "error": "La requête a expiré après 10 secondes"
            }
        except Exception as e:
            results["endpoints_status"][model_name] = {
                "url": endpoint_url,
                "status": "error",
                "error": str(e)
            }
    
    # Effectuer un test simple avec un modèle de base pour vérifier l'authentification
    test_model = "mistral-7b-instruct-v0.3"  # Modèle de base pour le test
    if test_model in endpoints:
        endpoint_url = endpoints[test_model]
        test_url = f"{endpoint_url}/api/openai_compat/v1/chat/completions"
        
        payload = {
            "model": "Mistral-7B-Instruct-v0.3",
            "messages": [
                {"role": "user", "content": "Bonjour"}
            ],
            "max_tokens": 10,
            "temperature": 0.5
        }
        
        headers = {
            "Authorization": f"Bearer {OVH_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(test_url, json=payload, headers=headers, timeout=15)
            
            results["authentication_test"] = {
                "model": test_model,
                "status_code": response.status_code,
                "status": "ok" if response.status_code == 200 else "error",
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        results["authentication_test"]["response_content"] = content
                except Exception as e:
                    results["authentication_test"]["parse_error"] = str(e)
        except requests.exceptions.Timeout:
            results["authentication_test"] = {
                "model": test_model,
                "status": "timeout",
                "error": "La requête a expiré après 15 secondes"
            }
        except Exception as e:
            results["authentication_test"] = {
                "model": test_model,
                "status": "error",
                "error": str(e)
            }
    
    # Vérifier l'état global
    if all(status["status"] == "ok" for status in results["endpoints_status"].values() if "status" in status):
        results["status"] = "ok"
    else:
        results["status"] = "error"
        
    return results

@app.get("/api/endpoints/status")
def endpoints_status():
    """
    Endpoint qui vérifie l'état de tous les endpoints OVH en temps réel
    et retourne un résumé de leur disponibilité.
    """
    results = {
        "status": "ok",
        "timestamp": time.time(),
        "endpoints": {}
    }
    
    # Fonction pour vérifier un endpoint
    def check_endpoint(model_name, endpoint_url):
        # Construire l'URL de test
        test_url = f"{endpoint_url}/api/openai_compat/v1/models"
        
        # Préparer les headers
        headers = {
            "Authorization": f"Bearer {OVH_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            # Utiliser requests pour les requêtes synchrones
            start_time = time.time()
            response = requests.get(test_url, headers=headers, timeout=5.0)
            elapsed_time = time.time() - start_time
            
            return {
                "model": model_name,
                "url": endpoint_url,
                "status_code": response.status_code,
                "status": "ok" if response.status_code == 200 else "error",
                "response_time_ms": round(elapsed_time * 1000)
            }
        except Exception as e:
            return {
                "model": model_name,
                "url": endpoint_url,
                "status": "error",
                "error": str(e)
            }
    
    # Vérifier chaque endpoint
    for model_name, endpoint_url in endpoints.items():
        try:
            result = check_endpoint(model_name, endpoint_url)
            model_name = result.pop("model", "unknown")
            results["endpoints"][model_name] = result
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'endpoint {model_name}: {str(e)}")
            results["endpoints"][model_name] = {
                "url": endpoint_url,
                "status": "error",
                "error": str(e)
            }
    
    # Vérifier l'état global
    if not results["endpoints"]:
        results["status"] = "error"
        results["message"] = "Aucun endpoint n'a pu être vérifié"
    elif all(endpoint.get("status") == "ok" for endpoint in results["endpoints"].values()):
        results["status"] = "ok"
    else:
        results["status"] = "partial"
        results["message"] = "Certains endpoints sont indisponibles"
    
    return results