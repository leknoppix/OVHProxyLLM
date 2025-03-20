# OVHProxyLLM

**OVHProxyLLM** est un proxy intelligent qui simplifie et unifie l'accès aux services d'intelligence artificielle d'OVH Cloud. Cette solution open-source facilite l'intégration des puissants modèles de langage et de génération d'images d'OVH dans vos applications.

## Description

OVHProxyLLM fonctionne comme une passerelle élégante entre vos applications et l'API OVH AI, offrant une interface standardisée compatible avec OpenAI et Ollama. Cette compatibilité permet d'utiliser facilement des interfaces comme OpenWebUI pour interagir avec les modèles d'OVH.

Le projet propose une solution clé en main pour accéder à une gamme diversifiée de modèles avancés :
- **Modèles de langage de pointe** : Mistral, Mixtral, Llama 3, DeepSeek et autres
- **Génération d'images** : Stable Diffusion XL
- **Capacités multimodales** : Analyse d'images avec DeepSeek

Développé en Python avec FastAPI, OVHProxyLLM se déploie facilement via Docker et s'intègre parfaitement avec OpenWebUI pour offrir une interface utilisateur intuitive.

Cette solution est idéale pour les développeurs, chercheurs et entreprises qui souhaitent exploiter la puissance des grands modèles de langage et de génération d'images hébergés par OVH, sans les complexités habituelles d'intégration API.

## Caractéristiques principales

- **Compatibilité étendue** : Interfaces API compatibles avec OpenAI et Ollama
- **Gestion intelligente des tokens** : Optimisation automatique des limites de tokens selon les modèles
- **Sécurité intégrée** : Gestion sécurisée des tokens d'authentification
- **Déploiement simplifié** : Configuration Docker prête à l'emploi
- **Interface utilisateur intuitive** : Intégration transparente avec OpenWebUI
- **Support multimodal** : Traitement de texte et d'images dans une solution unifiée

## Structure du projet

```
├── proxy/              # Dossier contenant le code source du proxy
│   ├── app.py          # Application FastAPI
│   ├── main.py         # Point d'entrée
│   ├── __init__.py     # Fichier d'initialisation du package
│   └── requirements.txt # Dépendances du proxy
├── Dockerfile          # Configuration pour construire l'image Docker
├── docker-compose.yml  # Configuration pour Docker Compose
└── README.md           # Documentation
```

## Fonctionnalités

- Proxy pour les APIs OVH AI
- Support de plusieurs modèles d'IA (Mistral, Llama, etc.)
- Endpoints compatibles avec l'API OpenAI et OpenWebUI
- Support de la génération d'images via Stable Diffusion XL
- Support multimodal pour le modèle DeepSeek

## Modèles disponibles

### Modèles de texte
- **mistral-7b-instruct-v0.3**: Version légère de Mistral optimisée pour les instructions
- **mixtral-8x7b-instruct-v0.1**: Modèle mixte MoE (Mixture of Experts) basé sur l'architecture Mistral
- **mistral-nemo-instruct-2407**: Dernière version du modèle Mistral avec des capacités améliorées
- **llama-3-1-8b-instruct**: Version légère de Llama 3.1 optimisée pour les instructions
- **llama-3-3-70b-instruct**: Version avancée de Llama 3.3 avec 70 milliards de paramètres
- **llama-3-1-70b-instruct**: Version avancée de Llama 3.1 avec 70 milliards de paramètres

### Modèle spécial: DeepSeek
- **deepseek-r1-distill-llama-70b**: Modèle DeepSeek R1 distillé basé sur Llama avec 70 milliards de paramètres
  - **Fonctionnalités spéciales**:
    - Support multimodal: peut interpréter des images via des URLs
    - Rôles supplémentaires: prend en charge les rôles "tool" et "developer" en plus des rôles standard
    - Support du streaming: permet de streamer les réponses token par token
    - Logprobs: peut retourner les probabilités logarithmiques des tokens générés
    - Paramètre Seed: permet de générer des réponses déterministes avec une même graine

### Modèle d'image
- **stable-diffusion-xl**: Modèle de génération d'images basé sur Stable Diffusion XL

## Endpoints disponibles

- `/v1/models` - Liste tous les modèles disponibles
- `/v1/chat/completions` - API de chat (comme ChatGPT)
- `/v1/completions` - API de complétion de texte
- `/v1/images/generations` - API de génération d'images
- `/api/models` - API compatible avec OpenWebUI/Ollama pour lister les modèles
- `/api/tags` - API compatible avec OpenWebUI/Ollama pour obtenir les tags des modèles
- `/api/chat` - API compatible avec OpenWebUI/Ollama pour le chat
- `/api/generate` - API compatible avec OpenWebUI/Ollama pour générer du texte
- `/api/images/generations` - API compatible avec OpenWebUI pour la génération d'images
- `/health` et `/api/health` - Endpoints de vérification de santé

## Configuration

Le token OVH est configuré directement dans le fichier `docker-compose.yml` :

```yaml
environment:
  - OVH_TOKEN_ENDPOINT=votre_token_ovh_ici
```

Assurez-vous de remplacer `votre_token_ovh_ici` par votre véritable token OVH avant de démarrer le conteneur.

## Déploiement avec Docker

### Prérequis

- Docker
- Docker Compose

### Installation

1. Cloner ce dépôt
   ```bash
   git clone https://github.com/leknoppix/OVHProxyLLM.git
   cd OVHProxyLLM
   ```

2. Modifier le fichier `docker-compose.yml` pour ajouter votre token OVH
   ```bash
   nano docker-compose.yml
   ```

3. Construire et démarrer les conteneurs :
   ```bash
   docker-compose up -d
   ```

### Développement local

Si vous souhaitez développer ou tester localement sans Docker :

1. Créer un environnement virtuel
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

2. Installer les dépendances
   ```bash
   pip install -r proxy/requirements.txt
   ```

3. Exécuter l'application
   ```bash
   cd proxy
   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

### Vérification

Le serveur sera accessible à l'adresse `http://localhost:8000`.

Pour vérifier que le serveur fonctionne correctement, vous pouvez exécuter :

```bash
curl http://localhost:8000/v1/models
```

## Utilisation

### Exemple avec curl

Requête de chat completion :
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-instruct-v0.3",
    "messages": [
      {"role": "system", "content": "Tu es un assistant intelligent."},
      {"role": "user", "content": "Bonjour, comment ça va ?"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

Requête de génération d'image :
```bash
curl -X POST http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Un chat jouant du piano dans un style impressionniste"
  }'
```

### Utilisation avec DeepSeek (Multimodal)

Le modèle DeepSeek supporte l'analyse d'images via des URLs :

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-distill-llama-70b",
    "messages": [
      {"role": "system", "content": "Tu es un assistant intelligent qui peut analyser des images."},
      {"role": "user", "content": "Que vois-tu sur cette image ? https://example.com/image.jpg"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

### Intégration avec OpenWebUI

Ce proxy est conçu pour s'intégrer parfaitement avec OpenWebUI. Vous pouvez configurer OpenWebUI pour utiliser ce proxy comme source d'IA en définissant l'URL du serveur Ollama comme suit :

```
http://proxy:8000
```

Ou en utilisant le `docker-compose.yml` fourni qui inclut déjà une configuration OpenWebUI prête à l'emploi.

## Obtenir des réponses complètes

Par défaut, le proxy est configuré pour permettre des réponses de taille moyenne (500 tokens) pour tous les modèles. Cependant, selon le modèle utilisé, le comportement peut varier :

- **DeepSeek** a tendance à générer des raisonnements détaillés et structurés.
- Les modèles **Llama** et **Mistral** peuvent avoir un style de réponse différent.

Pour obtenir des réponses plus complètes, vous pouvez augmenter le paramètre `max_tokens` dans vos requêtes :

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-distill-llama-70b",
    "messages": [
      {"role": "system", "content": "Tu es un assistant expert."},
      {"role": "user", "content": "Explique en détail comment fonctionne une blockchain."}
    ],
    "max_tokens": 1000,
    "temperature": 0.7
  }'
```

### Paramètres avancés

Certains modèles comme DeepSeek supportent des paramètres supplémentaires :

- **stream** : Permet de recevoir les réponses token par token (plus fluide)
- **logprobs** : Retourne les probabilités logarithmiques des tokens générés
- **seed** : Permet de générer des réponses déterministes avec une même graine

Exemple avec paramètres avancés :

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-distill-llama-70b",
    "messages": [
      {"role": "system", "content": "Tu es un assistant expert."},
      {"role": "user", "content": "Explique le concept d'intelligence artificielle."}
    ],
    "max_tokens": 800,
    "temperature": 0.7,
    "seed": 42,
    "stream": false,
    "logprobs": 5
  }'
```

## Licence

MIT