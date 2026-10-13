"""Gestion de la connexion PostgreSQL.

Fournit une connexion partagée (pattern singleton simple, suffisant pour une
application desktop mono-utilisateur) et une fonction d'initialisation qui
crée les tables et les données de référence si elles n'existent pas encore
— utile au premier lancement en environnement hors ligne.
"""

import os

import psycopg2
import psycopg2.extras
import bcrypt

from config import settings

_connexion = None


def obtenir_connexion():
    """Retourne la connexion PostgreSQL partagée, en l'ouvrant si besoin."""
    global _connexion
    if _connexion is None or _connexion.closed:
        _connexion = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
    return _connexion


def executer(requete, params=None, fetch=None):
    """Exécute une requête SQL et commit. fetch='one' | 'all' | None."""
    conn = obtenir_connexion()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(requete, params or ())
        resultat = None
        if fetch == "one":
            resultat = cur.fetchone()
        elif fetch == "all":
            resultat = cur.fetchall()
        conn.commit()
        return resultat


def initialiser_base():
    """Crée les tables (schema.sql) et les données de référence (seed.sql)
    si elles n'existent pas encore, puis crée un compte admin par défaut."""
    base_dir = os.path.dirname(__file__)
    conn = obtenir_connexion()

    with open(os.path.join(base_dir, "schema.sql"), encoding="utf-8") as f:
        with conn.cursor() as cur:
            cur.execute(f.read())
        conn.commit()

    with open(os.path.join(base_dir, "seed.sql"), encoding="utf-8") as f:
        with conn.cursor() as cur:
            cur.execute(f.read())
        conn.commit()

    _creer_admin_par_defaut()


def _creer_admin_par_defaut():
    """Crée un compte admin/admin123 si aucun utilisateur n'existe encore."""
    existe = executer("SELECT COUNT(*) AS n FROM utilisateur", fetch="one")
    if existe and existe["n"] > 0:
        return

    id_role_admin = executer(
        "SELECT id_role FROM role WHERE libelle = 'admin'", fetch="one"
    )["id_role"]

    mot_de_passe_hache = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    executer(
        """INSERT INTO utilisateur (nom, prenom, login, mot_de_passe, id_role)
           VALUES (%s, %s, %s, %s, %s)""",
        ("Administrateur", "DRE", "admin", mot_de_passe_hache, id_role_admin),
    )
    print("Compte par défaut créé : login='admin' / mot de passe='admin123'")
