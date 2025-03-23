# OVH LLM WebUI

Cette application vous permet d'accéder facilement aux modèles de langage (LLM) d'OVH via une interface web conviviale (OpenWebUI).

## Prérequis

- Python 3.8+ installé
- Docker et docker-compose installés
- Un token d'accès OVH (voir ci-dessous)
- Optionnel : Un token Cloudflare Tunnel pour l'accès public

## Obtenir un token OVH

Pour utiliser cette application, vous avez besoin d'un token d'accès OVH. Rendez-vous sur cette URL pour en générer un :

```
https://kepler.ai.cloud.ovh.net/v1/oauth/ovh/authorize?iam_action=publicCloudProject:ai:endpoints/call
```

## Installation

### Installation rapide

Pour une installation rapide, utilisez le script d'installation fourni :

```bash
# Cloner le dépôt
git clone https://github.com/votre-repo/ovh-llm-webui.git
cd ovh-llm-webui

# Exécuter le script d'installation
./install.sh
```

Le script d'installation vérifie les prérequis, installe les dépendances Python et vous guide dans la configuration initiale.

### Déploiement sur un nouveau serveur

Pour déployer l'application sur un nouveau serveur, suivez ces étapes :

1. Clonez le dépôt sur votre serveur :
   ```bash
   git clone https://github.com/votre-repo/ovh-llm-webui.git
   cd ovh-llm-webui
   ```

2. Exécutez le script d'installation :
   ```bash
   ./install.sh
   ```

3. Suivez les instructions pour configurer votre token OVH.

4. Démarrez l'application :
   ```bash
   ./ovh-llm-webui.sh start
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

### Gérer Cloudflare Tunnel

```bash
./ovh-llm-webui.sh tunnel start     # Démarrer le tunnel
./ovh-llm-webui.sh tunnel stop      # Arrêter le tunnel
./ovh-llm-webui.sh tunnel restart   # Redémarrer le tunnel
./ovh-llm-webui.sh tunnel status    # Vérifier le statut du tunnel
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

## Accès public via Cloudflare Tunnel

L'application prend en charge Cloudflare Tunnel pour exposer votre interface web sur Internet de manière sécurisée sans avoir à configurer des ports ou DNS manuellement.

### Configuration de Cloudflare Tunnel

1. Créez un tunnel sur [Cloudflare Zero Trust Dashboard](https://dash.cloudflare.com/?to=/:account/workers-and-pages)
2. Obtenez votre token Cloudflare Tunnel
3. Lors de l'installation, choisissez d'activer Cloudflare Tunnel et entrez votre token
4. Ou configurez manuellement en ajoutant dans le fichier `.env` à la racine :
   ```
   CLOUDFLARE_TUNNEL_TOKEN=votre_token_cloudflare
   ```

Une fois configuré, le tunnel démarrera automatiquement avec l'application. Vous pouvez vérifier le statut avec :
```bash
./ovh-llm-webui.sh tunnel status
```

L'URL publique de votre application sera visible dans votre tableau de bord Cloudflare.

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

### Problèmes avec Cloudflare Tunnel

Si le tunnel ne démarre pas correctement :
1. Vérifiez les logs avec `docker logs cloudflared`
2. Assurez-vous que votre token est valide
3. Redémarrez le tunnel avec `./ovh-llm-webui.sh tunnel restart`

### Erreur "No such file or directory"

Si vous rencontrez l'erreur `cd: /home/public_html/webui: No such file or directory`, cela signifie que vous exécutez le script depuis un chemin différent de celui qui était codé en dur. Notre nouvelle version du script utilise le répertoire courant, donc assurez-vous de lancer le script depuis le répertoire où se trouve les fichiers de l'application.