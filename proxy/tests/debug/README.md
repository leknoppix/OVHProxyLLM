# Scripts de test pour le du00e9bogage

Ce dossier contient des scripts de test spu00e9cifiques pour le du00e9bogage et l'analyse des performances du proxy OVH LLM. Ces scripts sont complu00e9mentaires u00e0 la suite de tests principale et peuvent u00eatre utilisu00e9s pour diagnostiquer des problu00e8mes spu00e9cifiques.

## Scripts disponibles

### test_chat.py

Script de test spu00e9cifique pour l'endpoint chat completions avec diffu00e9rentes configurations. Utile pour identifier des problu00e8mes spu00e9cifiques u00e0 certaines configurations.

```bash
python -m proxy.tests.debug.test_chat
```

### test_chat_simple.py

Version simplifiu00e9e pour tester rapidement l'endpoint chat completions avec un message court.

```bash
python -m proxy.tests.debug.test_chat_simple
```

### test_chat_debug.py

Version du00e9taillu00e9e avec journalisation pour du00e9boguer les problu00e8mes de l'endpoint chat completions. Les logs sont enregistru00e9s dans `/tmp/chat_test_debug.log`.

```bash
python -m proxy.tests.debug.test_chat_debug
```

### test_openai_direct.py

Teste l'accu00e8s direct u00e0 l'API OpenAI pour vu00e9rifier la compatibilitu00e9 du format.

```bash
python -m proxy.tests.debug.test_openai_direct
```

### test_ovh_direct.py

Teste l'accu00e8s direct u00e0 l'API OVH pour vu00e9rifier la connectivitu00e9 et l'authentification.

```bash
python -m proxy.tests.debug.test_ovh_direct
```

### test_server.py

Teste le serveur proxy dans son ensemble, vu00e9rifiant la disponibilitu00e9 et la ru00e9activitu00e9.

```bash
python -m proxy.tests.debug.test_server
```

## Utilisation dans Docker

Pour exu00e9cuter ces scripts dans le conteneur Docker :

```bash
docker exec proxy python -m proxy.tests.debug.test_chat_simple
```

## Note importante

Ces scripts sont principalement destinu00e9s au du00e9veloppement et au du00e9bogage. Pour les tests standard, utilisez plutu00f4t les scripts dans le dossier parent (`proxy.tests`).
