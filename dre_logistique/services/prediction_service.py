"""Module d'aide à la décision (UC12 du diagramme de cas d'utilisation).

Volontairement basé sur des règles et des statistiques descriptives simples
(moyenne, tendance linéaire) plutôt que sur un modèle scikit-learn entraîné
sur des données insuffisantes — voir la discussion de conception du mémoire.
Ce module régénère l'ensemble des alertes à chaque exécution (vider() puis
recréation), plutôt que de les mettre à jour une à une.
"""

import datetime

import numpy as np
import pandas as pd

from database.dao import materiel_dao, mouvement_dao, alerte_dao

SEUIL_ANCIENNETE_ANS = 4
SEUIL_REMPLACEMENTS_6_MOIS = 3
SEUIL_STOCK_BAS = 3


def calculer_toutes_les_alertes():
    """Recalcule et enregistre toutes les alertes actives. À exécuter au
    démarrage de l'application et/ou périodiquement (ex. une fois par jour)."""
    alerte_dao.vider()
    _alerte_anciennete()
    _alerte_frequence_remplacement()
    _alerte_rupture_stock()
    _alerte_sur_consommation()


def _alerte_anciennete():
    materiels = materiel_dao.lister(limite=1000)
    aujourdhui = datetime.date.today()
    for m in materiels:
        if m["statut_libelle"] != "en_service":
            continue
        anciennete_ans = (aujourdhui - m["date_acquisition"]).days / 365.25
        if anciennete_ans >= SEUIL_ANCIENNETE_ANS:
            alerte_dao.creer(
                "anciennete",
                f"{m['code']} — {m['designation']} en service depuis "
                f"{anciennete_ans:.1f} ans (seuil : {SEUIL_ANCIENNETE_ANS} ans)",
                "eleve" if anciennete_ans >= SEUIL_ANCIENNETE_ANS + 1 else "moyen",
                id_materiel=m["id_materiel"],
            )


def _alerte_frequence_remplacement():
    recents = mouvement_dao.lister_recents(limite=500)
    if not recents:
        return
    df = pd.DataFrame(recents)
    df = df[df["type_mouvement"] == "remplacement"]
    if df.empty:
        return
    df["date_mouvement"] = pd.to_datetime(df["date_mouvement"])
    six_mois = pd.Timestamp.now() - pd.DateOffset(months=6)
    df = df[df["date_mouvement"] >= six_mois]

    compte = df.groupby("id_materiel").size()
    for id_materiel, nb in compte.items():
        if nb >= SEUIL_REMPLACEMENTS_6_MOIS:
            m = materiel_dao.trouver_par_id(id_materiel)
            if m:
                alerte_dao.creer(
                    "frequence_panne",
                    f"{m['code']} — {nb} remplacements en 6 mois, à investiguer",
                    "eleve",
                    id_materiel=id_materiel,
                )


def _alerte_rupture_stock():
    materiels = materiel_dao.lister(limite=1000)
    if not materiels:
        return
    df = pd.DataFrame(materiels)
    en_service = df[df["statut_libelle"] == "en_service"]
    compte_par_designation = en_service.groupby("designation").size()

    for designation, nb in compte_par_designation.items():
        if nb <= SEUIL_STOCK_BAS:
            niveau = "eleve" if nb <= 1 else "moyen"
            alerte_dao.creer(
                "rupture_stock",
                f"{designation} — seulement {nb} unité(s) en service, "
                f"réapprovisionnement conseillé",
                niveau,
            )


def _alerte_sur_consommation():
    """Compare le nombre de mouvements du mois en cours à la moyenne des
    3 mois précédents, par service, via une régression linéaire simple
    (numpy.polyfit) pour détecter une tendance à la hausse."""
    recents = mouvement_dao.lister_recents(limite=1000)
    if not recents:
        return
    df = pd.DataFrame(recents)
    df["date_mouvement"] = pd.to_datetime(df["date_mouvement"])
    df["mois"] = df["date_mouvement"].dt.to_period("M")
    df["service"] = df["service_dest_nom"].fillna(df["service_source_nom"])
    df = df.dropna(subset=["service"])

    for service, groupe in df.groupby("service"):
        par_mois = groupe.groupby("mois").size().sort_index()
        if len(par_mois) < 3:
            continue
        y = par_mois.values[-4:]
        x = np.arange(len(y))
        pente = np.polyfit(x, y, 1)[0]
        moyenne = y[:-1].mean()
        dernier = y[-1]
        if moyenne > 0 and dernier > moyenne * 1.3 and pente > 0:
            hausse_pct = (dernier / moyenne - 1) * 100
            alerte_dao.creer(
                "sur_consommation",
                f"Service {service} — {hausse_pct:.0f}% de mouvements en plus "
                f"que la moyenne des mois précédents",
                "moyen",
            )


def lister_alertes_actives():
    return alerte_dao.lister_actives()
