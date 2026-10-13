"""Service d'authentification.

Vérifie les identifiants avec bcrypt (jamais de mot de passe en clair en
base) et journalise chaque connexion pour l'audit (module Sécurité).
"""

import bcrypt

from database.dao import utilisateur_dao, log_dao


class Session:
    """Représente l'utilisateur actuellement connecté (une seule session
    à la fois, cohérent avec une application desktop mono-poste)."""
    utilisateur = None

    @classmethod
    def est_connecte(cls):
        return cls.utilisateur is not None

    @classmethod
    def role(cls):
        return cls.utilisateur["role_libelle"] if cls.utilisateur else None

    @classmethod
    def deconnecter(cls):
        cls.utilisateur = None


def se_connecter(login, mot_de_passe):
    """Retourne (True, utilisateur) si les identifiants sont valides,
    sinon (False, message_erreur)."""
    utilisateur = utilisateur_dao.trouver_par_login(login)
    if utilisateur is None:
        return False, "Identifiants incorrects."

    hache = utilisateur["mot_de_passe"].encode()
    if not bcrypt.checkpw(mot_de_passe.encode(), hache):
        return False, "Identifiants incorrects."

    Session.utilisateur = utilisateur
    log_dao.journaliser(utilisateur["id_utilisateur"], "connexion", login)
    return True, utilisateur


def hacher_mot_de_passe(mot_de_passe):
    return bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt()).decode()
