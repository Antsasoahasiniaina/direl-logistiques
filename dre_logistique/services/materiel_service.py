"""Service métier pour le matériel : création (UC4/UC5), modification et
archivage (soft-delete), avec gestion de la photo justificative et
génération du QR code.

Choix de conception : le matériel n'est jamais supprimé physiquement. Il est
basculé vers le statut 'archive' (comme utilisateur.actif ailleurs dans le
projet), pour ne jamais casser la traçabilité même sur un matériel qui n'a
encore aucun mouvement enregistré.
"""

import datetime
import os

from PIL import Image

from database.dao import materiel_dao, log_dao, reference_dao
from services import qr_service
from services.auth_service import Session

DOSSIER_PHOTOS = os.path.join(os.path.dirname(__file__), "..", "photos")


def _id_statut(libelle):
    for s in reference_dao.lister_statuts():
        if s["libelle"] == libelle:
            return s["id_statut"]
    raise ValueError(f"Statut inconnu : {libelle}")


def _sauvegarder_photo(code, chemin_source):
    """Copie et compresse la photo fournie (max 800px, JPEG) sous le nom du
    code du matériel. Retourne le chemin du fichier enregistré."""
    os.makedirs(DOSSIER_PHOTOS, exist_ok=True)
    chemin_dest = os.path.join(DOSSIER_PHOTOS, f"{code}.jpg")
    image = Image.open(chemin_source).convert("RGB")
    image.thumbnail((800, 800))
    image.save(chemin_dest, "JPEG", quality=85)
    return chemin_dest


def creer_materiel(designation, id_service, id_grade, id_statut_en_service,
                    date_acquisition=None, chemin_photo_source=None):
    code = qr_service.generer_code(designation)
    date_acquisition = date_acquisition or datetime.date.today()

    resultat = materiel_dao.creer(
        code=code, designation=designation, qr_code=code,
        date_acquisition=date_acquisition,
        id_service=id_service, id_grade=id_grade, id_statut=id_statut_en_service,
    )
    id_materiel = resultat["id_materiel"]
    chemin_etiquette = qr_service.sauvegarder_etiquette(code, designation)

    chemin_photo = None
    if chemin_photo_source:
        chemin_photo = _sauvegarder_photo(code, chemin_photo_source)
        materiel_dao.mettre_a_jour_photo(id_materiel, chemin_photo)

    if Session.utilisateur:
        log_dao.journaliser(Session.utilisateur["id_utilisateur"], "creation_materiel", code)

    return {"id_materiel": id_materiel, "code": code, "designation": designation,
            "etiquette": chemin_etiquette, "photo": chemin_photo}


def modifier_materiel(id_materiel, designation, id_service, id_grade,
                       chemin_photo_source=None):
    materiel_dao.mettre_a_jour(id_materiel, designation, id_service, id_grade)

    m = materiel_dao.trouver_par_id(id_materiel)
    if m:
        # La désignation a pu changer : on régénère l'étiquette pour que
        # toute future réimpression reflète le nouveau nom.
        qr_service.sauvegarder_etiquette(m["code"], designation)

    if chemin_photo_source:
        chemin_photo = _sauvegarder_photo(m["code"], chemin_photo_source)
        materiel_dao.mettre_a_jour_photo(id_materiel, chemin_photo)

    if Session.utilisateur:
        log_dao.journaliser(Session.utilisateur["id_utilisateur"], "modification_materiel",
                            f"materiel #{id_materiel}")


def archiver_materiel(id_materiel):
    """Archive le matériel (soft-delete) : il disparaît de la liste
    principale mais reste consultable dans les archives et restaurable.
    Aucune donnée n'est jamais perdue, contrairement à une suppression."""
    m = materiel_dao.trouver_par_id(id_materiel)
    materiel_dao.archiver(id_materiel, _id_statut("archive"))

    if Session.utilisateur and m:
        log_dao.journaliser(Session.utilisateur["id_utilisateur"], "archivage_materiel", m["code"])


def restaurer_materiel(id_materiel, statut_cible="en_service"):
    """Sort un matériel de l'archive et lui redonne le statut indiqué
    (en_service par défaut)."""
    m = materiel_dao.trouver_par_id(id_materiel)
    materiel_dao.restaurer(id_materiel, _id_statut(statut_cible))

    if Session.utilisateur and m:
        log_dao.journaliser(Session.utilisateur["id_utilisateur"], "restauration_materiel", m["code"])


def rechercher_par_qr(qr_code):
    return materiel_dao.trouver_par_qr(qr_code)


def lister_materiels():
    return materiel_dao.lister()


def lister_archives():
    return materiel_dao.lister_archives()


def compter_actifs():
    return materiel_dao.compter_actifs()