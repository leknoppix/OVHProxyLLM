import uvicorn
from proxy.app import app

if __name__ == "__main__":
    print("Démarrage du serveur sur http://localhost:8000")
    print("Appuyez sur CTRL+C pour arrêter le serveur")
    uvicorn.run(app, host="0.0.0.0", port=8000) 