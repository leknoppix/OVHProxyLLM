#!/usr/bin/env python
"""
Script principal pour exécuter tous les tests du proxy OVH LLM
"""

import sys
import os
import importlib

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importer les modules de test
from proxy.tests import test_app, test_endpoints

def print_header(message):
    """Affiche un message de titre formaté"""
    print("\n" + "=" * 80)
    print("=" * ((80 - len(message)) // 2) + f" {message} " + "=" * ((80 - len(message)) // 2))
    print("=" * 80)

def run_all_tests():
    """Exécute tous les tests disponibles"""
    print_header("TESTS COMPLETS DU PROXY OVH LLM")
    
    # Exécuter les tests de base de l'application
    print_header("TESTS DE BASE DE L'APPLICATION")
    app_tests_success = test_app.run_all_tests()
    
    # Exécuter les tests des endpoints avec tous les modèles
    print_header("TESTS DES ENDPOINTS AVEC TOUS LES MODÈLES")
    endpoints_tests_success = test_endpoints.run_all_tests()
    
    # Résumé global
    print_header("RÉSUMÉ GLOBAL DES TESTS")
    if app_tests_success and endpoints_tests_success:
        print(" TOUS LES TESTS ONT RÉUSSI")
        return True
    else:
        print(" CERTAINS TESTS ONT ÉCHOUÉ")
        if not app_tests_success:
            print("  → Tests de base de l'application: ÉCHEC")
        if not endpoints_tests_success:
            print("  → Tests des endpoints avec tous les modèles: ÉCHEC")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
