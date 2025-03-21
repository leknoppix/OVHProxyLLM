# OVH LLM WebUI

Cette application vous permet d'accéder facilement aux modèles de langage (LLM) d'OVH via une interface web conviviale (OpenWebUI).

## Prérequis

- Python 3.8+ installé
- Docker et docker-compose installés
- Un token d'accès OVH (voir ci-dessous)

## Obtenir un token OVH

Pour utiliser cette application, vous avez besoin d'un token d'accès OVH. Rendez-vous sur cette URL pour en générer un :

```
https://kepler.ai.cloud.ovh.net/v1/oauth/ovh/authorize?iam_action=publicCloudProject:ai:endpoints/call
```

## Commandes disponibles

Le script `ovh-llm-webui.sh` permet de gérer facilement tous les aspects de l'application :

### Démarrer l'application

```bash
./ovh-llm-webui.sh start
```

### Arrêter l'application

```bash
./ovh-llm-webui.sh stop
```

### Redémarrer l'application

```bash
./ovh-llm-webui.sh restart
```

### Vérifier le statut

```bash
./ovh-llm-webui.sh status
```

### Voir les logs

```bash
./ovh-llm-webui.sh logs
```

### Mettre à jour le token OVH

```bash
./ovh-llm-webui.sh token <nouveau_token>
```

### Tester l'API

```bash
./ovh-llm-webui.sh test
```

### Afficher l'aide

```bash
./ovh-llm-webui.sh help
```

## Accès à l'interface web

Une fois démarrée, l'interface web est accessible à l'adresse :

```
http://localhost:3000
```

## Modèles disponibles

L'application donne accès aux modèles OVH suivants :

- mistral-7b-instruct-v0.3
- mixtral-8x7b-instruct-v0.1
- mistral-nemo-instruct-2407
- llama-3-1-8b-instruct
- llama-3-3-70b-instruct
- llama-3-1-70b-instruct
- deepseek-r1-distill-llama-70b
- mamba-codestral-7b-v0-1 (spécialisé pour le code)
- stable-diffusion-xl

### Modèles spécialisés

Certains modèles ont des capacités particulières :

- **mamba-codestral-7b-v0-1** : Modèle optimisé pour la génération de code et les questions techniques liées à la programmation
- **deepseek-r1-distill-llama-70b** : Modèle performant avec capacités visuelles (peut interpréter des images)
- **stable-diffusion-xl** : Modèle de génération d'images

## Dépannage

Si vous rencontrez des problèmes, vérifiez les points suivants :

1. Vérifiez que votre token OVH est valide
2. Consultez les logs avec `./ovh-llm-webui.sh logs`
3. Redémarrez l'application avec `./ovh-llm-webui.sh restart`

Si vous avez l'erreur "Forbidden: authentication failed", votre token est probablement expiré. Générez-en un nouveau et mettez-le à jour avec la commande `token`.