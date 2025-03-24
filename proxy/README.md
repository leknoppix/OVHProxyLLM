# Proxy OVH LLM

Ce module est un proxy qui permet d'accu00e9der aux modu00e8les de langage (LLM) d'OVH via une API compatible avec l'API OpenAI. Il facilite l'intu00e9gration des modu00e8les OVH dans des applications existantes qui supportent l'API OpenAI.

## Fonctionnalitu00e9s

- API compatible avec OpenAI pour les chat completions
- Support de plusieurs modu00e8les OVH (Mistral, Llama, etc.)
- Gestion des tokens d'authentification OVH
- Endpoints de diagnostic et de santu00e9
- Tests automatisu00e9s

## Structure du projet

```
proxy/
├── __init__.py
├── app.py             # Application principale FastAPI
├── main.py            # Point d'entru00e9e pour l'exu00e9cution
├── requirements.txt   # Du00e9pendances Python
└── tests/             # Tests automatisu00e9s
    ├── __init__.py
    ├── main.py        # Point d'entru00e9e pour les tests
    ├── quick_test.py  # Tests rapides des fonctionnalitu00e9s essentielles
    ├── run_tests.py   # Script pour exu00e9cuter tous les tests
    ├── test_app.py    # Tests de l'application
    ├── test_endpoints.py # Tests des endpoints
    └── debug/         # Tests de du00e9bogage
        ├── __init__.py
        ├── README.md  # Documentation des tests de du00e9bogage
        ├── test_chat.py
        ├── test_chat_debug.py
        ├── test_chat_simple.py
        ├── test_openai_direct.py
        ├── test_ovh_direct.py
        └── test_server.py
```

## Exu00e9cution des tests

### Tests rapides

Pour exu00e9cuter les tests rapides qui vu00e9rifient les fonctionnalitu00e9s essentielles :

```bash
python -m proxy.tests.quick_test
```

Dans Docker :

```bash
docker exec proxy python -m proxy.tests.quick_test
```

Pour du00e9sactiver le test de chat completions qui peut prendre du temps :

```bash
docker exec -e ENABLE_CHAT_TEST=false proxy python -m proxy.tests.quick_test
```

### Tests complets

Pour exu00e9cuter tous les tests :

```bash
python -m proxy.tests.run_tests
```

Dans Docker :

```bash
docker exec proxy python -m proxy.tests.run_tests
```

### Tests de du00e9bogage

Les tests de du00e9bogage sont utiles pour diagnostiquer des problu00e8mes spu00e9cifiques. Consultez le README dans le dossier `tests/debug` pour plus d'informations.

```bash
python -m proxy.tests.debug.test_chat_simple
```

## Du00e9veloppement

### Ajouter de nouveaux tests

Pour ajouter de nouveaux tests :

1. Cru00e9ez un nouveau fichier de test dans le dossier `tests`
2. Importez les modules nu00e9cessaires
3. Ajoutez vos fonctions de test
4. Mettez u00e0 jour `run_tests.py` pour inclure vos nouveaux tests

### Environnement de du00e9veloppement

Pour configurer un environnement de du00e9veloppement :

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Du00e9ploiement

Le proxy est du00e9ployu00e9 en tant que conteneur Docker dans l'architecture globale. Consultez le README principal du projet pour plus d'informations sur le du00e9ploiement.
