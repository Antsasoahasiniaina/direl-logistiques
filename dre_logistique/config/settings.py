"""Paramètres de connexion PostgreSQL.

En production, ces valeurs peuvent être surchargées par des variables
d'environnement (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) pour éviter
de coder les identifiants en dur.
"""

import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "dre_logistique")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
