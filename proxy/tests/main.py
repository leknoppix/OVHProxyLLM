#!/usr/bin/env python
"""
Point d'entrée principal pour exécuter les tests du proxy OVH LLM
"""

import sys
from proxy.tests.run_tests import run_all_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
