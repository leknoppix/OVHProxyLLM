# Configuration des Endpoints Alternatifs

Ce document explique comment configurer et utiliser des endpoints alternatifs pour le proxy OVH.

## Pourquoi utiliser des endpoints alternatifs ?

L'utilisation d'endpoints alternatifs peut être utile dans plusieurs scénarios :

1. **Répartition de charge** : Distribuer les requêtes sur plusieurs endpoints pour éviter les limitations de quota
2. **Redondance** : Avoir des endpoints de secours en cas de panne d'un endpoint principal
3. **Environnements multiples** : Accéder à différents environnements (développement, test, production)

## Configuration du token d'API

Le token d'API OVH est configuré comme variable d'environnement dans le fichier `.env` à la racine du projet :

```bash
# Token principal
OVH_TOKEN_ENDPOINT="votre_token_ovh"
```

Le même token est utilisé pour tous les endpoints OVH.

## Configuration des endpoints alternatifs

Les endpoints alternatifs sont configurés dans un fichier JSON nommé `endpoints_config.json`. Ce fichier doit être placé dans le même répertoire que le script `app.py`.

Exemple de structure du fichier :

```json
{
  "alternative_endpoints": {
    "mistral-7b-instruct-v0.3": [
      "https://mistral-7b-instruct-v0-3.endpoints.alternative1.ai.cloud.ovh.net",
      "https://mistral-7b-instruct-v0-3.endpoints.alternative2.ai.cloud.ovh.net"
    ],
    "mixtral-8x7b-instruct-v0.1": [
      "https://mixtral-8x7b-instruct-v01.endpoints.alternative1.ai.cloud.ovh.net"
    ]
  }
}
```

Chaque modèle peut avoir plusieurs endpoints alternatifs, spécifiés sous forme de liste d'URLs.

## Fonctionnement

Lorsqu'une requête est envoyée pour un modèle spécifique, le proxy essaie d'abord l'endpoint principal. Si celui-ci échoue (erreur d'authentification, quota dépassé, etc.), le proxy essaie automatiquement les endpoints alternatifs configurés pour ce modèle, dans l'ordre spécifié.

## Création du fichier de configuration

Vous pouvez créer le fichier `endpoints_config.json` en copiant et modifiant le fichier d'exemple fourni :

```bash
cp endpoints_config.json.example endpoints_config.json
```

Ensuite, modifiez le fichier pour y ajouter vos propres endpoints alternatifs.

## Vérification de la configuration

Au démarrage, le proxy affiche des informations sur le token et les endpoints chargés :

```
Token OVH récupéré: abcdefghij...12345 (longueur: 64)
Configuration des endpoints alternatifs chargée depuis endpoints_config.json
```

Vous pouvez également vérifier les modèles disponibles en accédant à l'endpoint `/v1/models`, qui affichera tous les modèles disponibles, y compris ceux accessibles via des endpoints alternatifs.
