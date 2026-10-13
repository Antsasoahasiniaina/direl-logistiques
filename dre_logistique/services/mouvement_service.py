"""Service métier des mouvements de matériel (UC8 à UC11 du diagramme de
cas d'utilisation) : affectation, transfert, remplacement, mise au rebut.

Chaque fonction : (1) enregistre le mouvement dans l'historique,
(2) met à jour l'état courant du matériel, (3) journalise l'action.
"""

from database.dao import materiel_dao, mouvement_dao, log_dao, reference_dao
from services.auth_service import Session


def _id_statut(libelle):
    for s in reference_dao.lister_statuts():
        if s["libelle"] == libelle:
            return s["id_statut"]
    raise ValueError(f"Statut inconnu : {libelle}")


def _utilisateur_courant():
    if not Session.utilisateur:
        raise PermissionError("Aucun utilisateur connecté.")
    return Session.utilisateur["id_utilisateur"]


def affecter(id_materiel, id_service, commentaire=""):
    """Première affectation d'un matériel à un service."""
    id_user = _utilisateur_courant()
    mouvement_dao.creer("affectation", id_materiel, id_user,
                         id_service_dest=id_service, commentaire=commentaire)
    materiel_dao.mettre_a_jour_service(id_materiel, id_service)
    log_dao.journaliser(id_user, "affectation_materiel", f"materiel #{id_materiel}")


def transferer(id_materiel, id_service_source, id_service_dest, commentaire=""):
    """Déplace un matériel d'un service vers un autre."""
    id_user = _utilisateur_courant()
    mouvement_dao.creer("transfert", id_materiel, id_user,
                         id_service_source=id_service_source,
                         id_service_dest=id_service_dest, commentaire=commentaire)
    materiel_dao.mettre_a_jour_service(id_materiel, id_service_dest)
    log_dao.journaliser(id_user, "transfert_materiel", f"materiel #{id_materiel}")


def remplacer(id_materiel_ancien, id_materiel_nouveau, commentaire=""):
    """Marque l'ancien matériel comme remplacé par le nouveau (association
    réflexive du MCD) et bascule son statut à 'hors_service'."""
    id_user = _utilisateur_courant()
    mouvement_dao.creer("remplacement", id_materiel_ancien, id_user, commentaire=commentaire)
    materiel_dao.mettre_a_jour_statut(
        id_materiel_ancien, _id_statut("hors_service"),
        id_materiel_remplacant=id_materiel_nouveau,
    )
    log_dao.journaliser(id_user, "remplacement_materiel",
                         f"materiel #{id_materiel_ancien} -> #{id_materiel_nouveau}")


def mettre_au_rebut(id_materiel, commentaire=""):
    id_user = _utilisateur_courant()
    mouvement_dao.creer("rebut", id_materiel, id_user, commentaire=commentaire)
    materiel_dao.mettre_a_jour_statut(id_materiel, _id_statut("rebut"))
    log_dao.journaliser(id_user, "rebut_materiel", f"materiel #{id_materiel}")


def historique(id_materiel):
    return mouvement_dao.historique_materiel(id_materiel)


def mouvements_recents(limite=20):
    return mouvement_dao.lister_recents(limite)

def compter_aujourdhui():
    return mouvement_dao.compter_aujourdhui()


def compter_cette_semaine():
    return mouvement_dao.compter_cette_semaine()


def compter_ce_mois():
    return mouvement_dao.compter_ce_mois()