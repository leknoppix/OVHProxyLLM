# Tests du Proxy OVH LLM

Ce dossier contient les scripts de test pour vu00e9rifier le bon fonctionnement du proxy OVH LLM.

## Structure des tests

- `test_app.py` : Tests fonctionnels de base de l'application (santu00e9, liste des modu00e8les, etc.)
- `test_endpoints.py` : Tests de tous les endpoints avec tous les modu00e8les disponibles
- `quick_test.py` : Test rapide pour vu00e9rifier que l'application fonctionne correctement
- `run_tests.py` : Script principal pour exu00e9cuter tous les tests

## Exu00e9cution des tests

### Test rapide

Pour exu00e9cuter un test rapide de l'application :

```bash
python -m proxy.tests.quick_test
```

### Tests complets

Pour exu00e9cuter tous les tests :

```bash
python -m proxy.tests.run_tests
```

### Tests individuels

Pour exu00e9cuter uniquement les tests de base de l'application :

```bash
python -m proxy.tests.test_app
```

Pour exu00e9cuter uniquement les tests des endpoints avec tous les modu00e8les :

```bash
python -m proxy.tests.test_endpoints
```

## Exu00e9cution des tests dans Docker

Pour exu00e9cuter les tests dans le conteneur Docker :

```bash
# Test rapide
docker exec proxy python -m proxy.tests.quick_test

# Tous les tests
docker exec proxy python -m proxy.tests.run_tests

# Tests individuels
docker exec proxy python -m proxy.tests.test_app
docker exec proxy python -m proxy.tests.test_endpoints
```

## Configuration des tests

Les tests utilisent par du00e9faut l'URL `http://localhost:8000` pour accu00e9der u00e0 l'application. Si l'application est accessible u00e0 une autre URL, vous pouvez modifier la variable `SERVER_URL` dans les fichiers de test.
