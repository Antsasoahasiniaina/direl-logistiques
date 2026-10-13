"""Génération des rapports PDF (ReportLab) et Excel (openpyxl) — UC14/UC15.

Types : inventaire, mouvements de période, alertes actives.
Les fichiers générés sont mémorisés dans rapports/historique.json pour
l'écran Rapports.
"""

import datetime
import json
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
import pandas as pd

from database.dao import materiel_dao, mouvement_dao, alerte_dao
from services.auth_service import Session
from services.prediction_service import SEUIL_STOCK_BAS

DOSSIER_RAPPORTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rapports"))
HISTORIQUE_PATH = os.path.join(DOSSIER_RAPPORTS, "historique.json")

TYPES_RAPPORT = {
    "Inventaire annuel": "inventaire",
    "Mouvements de la période": "mouvements",
    "Alertes actives": "alertes",
}
PERIODES = {
    "Année en cours": "annee",
    "Trimestre en cours": "trimestre",
    "Mois en cours": "mois",
}


def bornes_periode(cle_periode):
    """Retourne (debut inclus, fin exclusive, libellé) pour la période choisie."""
    aujourdhui = datetime.date.today()
    if cle_periode == "mois":
        debut = aujourdhui.replace(day=1)
        if debut.month == 12:
            fin = debut.replace(year=debut.year + 1, month=1)
        else:
            fin = debut.replace(month=debut.month + 1)
        libelle = debut.strftime("%B %Y")
    elif cle_periode == "trimestre":
        mois_debut = ((aujourdhui.month - 1) // 3) * 3 + 1
        debut = aujourdhui.replace(month=mois_debut, day=1)
        mois_fin = mois_debut + 3
        if mois_fin > 12:
            fin = datetime.date(debut.year + 1, mois_fin - 12, 1)
        else:
            fin = datetime.date(debut.year, mois_fin, 1)
        libelle = f"T{(mois_debut - 1) // 3 + 1} {debut.year}"
    else:
        debut = aujourdhui.replace(month=1, day=1)
        fin = datetime.date(debut.year + 1, 1, 1)
        libelle = str(debut.year)
    return debut, fin, libelle


def indicateurs(cle_periode="mois"):
    debut, fin, _ = bornes_periode(cle_periode)
    total_actif = materiel_dao.compter_actifs()
    mouvements = mouvement_dao.compter_entre(debut, fin)
    mois_actuel = mouvement_dao.compter_ce_mois()
    mois_prec = mouvement_dao.compter_mois_precedent()
    delta_mouv = mois_actuel - mois_prec
    return {
        "materiel_actif": total_actif,
        "stock_faible": compter_stock_faible(),
        "mouvements_periode": mouvements,
        "mouvements_ce_mois": mois_actuel,
        "delta_mouvements": delta_mouv,
    }


def compter_stock_faible():
    materiels = materiel_dao.lister(limite=1000)
    if not materiels:
        return 0
    df = pd.DataFrame(materiels)
    en_service = df[df["statut_libelle"] == "en_service"]
    if en_service.empty:
        return 0
    compte = en_service.groupby("designation").size()
    return int((compte <= SEUIL_STOCK_BAS).sum())


def analyse_par_service():
    donnees = mouvement_dao.repartition_par_service() or []
    total = sum(d["total"] for d in donnees) or 1
    couleurs = ["#0d9488", "#2563eb", "#7c3aed", "#d97706", "#16a34a"]
    resultats = []
    for i, d in enumerate(donnees):
        pct = round(100 * d["total"] / total)
        resultats.append((d["nom"], pct, couleurs[i % len(couleurs)], d["total"]))
    return resultats


def mouvements_hebdo(nb_semaines=5):
    lignes = mouvement_dao.par_semaine(nb_semaines) or []
    par_semaine = {}
    for r in lignes:
        cle = r["semaine"]
        if hasattr(cle, "date"):
            cle = cle.date()
        par_semaine[cle] = r
    aujourdhui = datetime.date.today()
    lundi = aujourdhui - datetime.timedelta(days=aujourdhui.weekday())
    labels, entrees, sorties = [], [], []
    for i in range(nb_semaines - 1, -1, -1):
        semaine = lundi - datetime.timedelta(weeks=i)
        labels.append(f"Sem. {semaine.isocalendar()[1]}")
        ligne = par_semaine.get(semaine)
        if ligne is None:
            entrees.append(0)
            sorties.append(0)
        else:
            entrees.append(int(ligne["entrees"] or 0))
            sorties.append(int(ligne["sorties"] or 0))
    return labels, entrees, sorties


def _signataire():
    if Session.utilisateur:
        return f"{Session.utilisateur['prenom']} {Session.utilisateur['nom']}"
    return "Directeur régional"


def _styles_entete():
    return getSampleStyleSheet()


def _tableau(lignes, largeurs, couleur_entete="#0f172a"):
    table = Table(lignes, colWidths=largeurs)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(couleur_entete)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _corps_inventaire(detaille):
    elements = []
    styles = _styles_entete()
    materiels = materiel_dao.lister(limite=1000 if detaille else 30)
    elements.append(Paragraph("Inventaire du matériel", styles["Heading2"]))
    lignes = [["Code", "Désignation", "Service", "Statut", "Acquisition"]]
    for m in materiels:
        date_acq = m["date_acquisition"].strftime("%d/%m/%Y") if m.get("date_acquisition") else "—"
        lignes.append([
            m["code"], m["designation"], m["service_nom"] or "—",
            m["statut_libelle"], date_acq,
        ])
    elements.append(_tableau(lignes, [2.8 * cm, 5.2 * cm, 4 * cm, 2.8 * cm, 2.8 * cm]))
    return elements


def _corps_mouvements(cle_periode, detaille):
    elements = []
    styles = _styles_entete()
    debut, fin, libelle = bornes_periode(cle_periode)
    elements.append(Paragraph(f"Mouvements — {libelle}", styles["Heading2"]))
    mouvements = mouvement_dao.lister_entre(debut, fin, limite=2000 if detaille else 40)
    lignes = [["Date", "Code", "Type", "Source", "Destination", "Agent"]]
    for mv in mouvements:
        lignes.append([
            mv["date_mouvement"].strftime("%d/%m/%Y"),
            mv["code"],
            mv["type_mouvement"],
            mv["service_source_nom"] or "—",
            mv["service_dest_nom"] or "—",
            f"{mv['agent_prenom']} {mv['agent_nom']}",
        ])
    if len(lignes) == 1:
        lignes.append(["—", "Aucun mouvement", "—", "—", "—", "—"])
    elements.append(_tableau(lignes, [2.4 * cm, 2.6 * cm, 2.8 * cm, 3.2 * cm, 3.2 * cm, 3.4 * cm]))
    return elements


def _corps_alertes(detaille):
    elements = []
    styles = _styles_entete()
    elements.append(Paragraph("Alertes actives", styles["Heading2"]))
    alertes = alerte_dao.lister_actives(limite=200 if detaille else 40)
    lignes = [["Niveau", "Type", "Matériel", "Message"]]
    for a in alertes:
        lignes.append([
            a["niveau_risque"],
            a["type_alerte"],
            a.get("code") or "—",
            (a["message"][:80] + "…") if len(a["message"]) > 80 else a["message"],
        ])
    if len(lignes) == 1:
        lignes.append(["—", "Aucune alerte", "—", "—"])
    elements.append(_tableau(lignes, [2.4 * cm, 3.4 * cm, 2.6 * cm, 9.2 * cm], "#dc2626"))
    return elements


def generer_rapport_pdf(chemin_fichier, type_rapport="inventaire",
                        periode="annee", detaille=True):
    styles = _styles_entete()
    doc = SimpleDocTemplate(chemin_fichier, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    elements = []
    _, _, libelle_periode = bornes_periode(periode)

    elements.append(Paragraph("République de Madagascar", styles["Normal"]))
    elements.append(Paragraph(
        "DRE Haute Matsiatra — Rapport logistique", styles["Title"]))
    elements.append(Paragraph(
        f"Généré le {datetime.date.today().strftime('%d/%m/%Y')} — période : {libelle_periode}",
        styles["Normal"]))
    elements.append(Spacer(1, 16))

    kpi = indicateurs(periode)
    resume = [
        ["Indicateur", "Valeur"],
        ["Matériel actif", str(kpi["materiel_actif"])],
        ["Désignations à stock faible", str(kpi["stock_faible"])],
        ["Mouvements sur la période", str(kpi["mouvements_periode"])],
    ]
    table_resume = Table(resume, colWidths=[8 * cm, 6 * cm])
    table_resume.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d9488")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table_resume)
    elements.append(Spacer(1, 16))

    if type_rapport == "mouvements":
        elements.extend(_corps_mouvements(periode, detaille))
    elif type_rapport == "alertes":
        elements.extend(_corps_alertes(detaille))
    else:
        elements.extend(_corps_inventaire(detaille))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph(
        f"Signé numériquement par : {_signataire()} — "
        f"{datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles["Normal"],
    ))
    doc.build(elements)
    _enregistrer_historique(os.path.basename(chemin_fichier), chemin_fichier, "PDF")
    return chemin_fichier


def generer_rapport_excel(chemin_fichier, type_rapport="inventaire",
                          periode="annee", detaille=True):
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    limite = 2000 if detaille else 40

    if type_rapport == "mouvements":
        feuille.title = "Mouvements"
        debut, fin, _ = bornes_periode(periode)
        feuille.append(["Date", "Code", "Désignation", "Type", "Source", "Destination", "Agent"])
        for mv in mouvement_dao.lister_entre(debut, fin, limite=limite):
            feuille.append([
                mv["date_mouvement"].strftime("%d/%m/%Y %H:%M"),
                mv["code"], mv["designation"], mv["type_mouvement"],
                mv["service_source_nom"] or "", mv["service_dest_nom"] or "",
                f"{mv['agent_prenom']} {mv['agent_nom']}",
            ])
    elif type_rapport == "alertes":
        feuille.title = "Alertes"
        feuille.append(["Niveau", "Type", "Code", "Désignation", "Message", "Date"])
        for a in alerte_dao.lister_actives(limite=limite):
            feuille.append([
                a["niveau_risque"], a["type_alerte"], a.get("code") or "",
                a.get("designation") or "", a["message"],
                a["date_generation"].strftime("%d/%m/%Y %H:%M") if a.get("date_generation") else "",
            ])
    else:
        feuille.title = "Inventaire"
        feuille.append(["Code", "Désignation", "Service", "Grade", "Statut", "Date d'acquisition"])
        for m in materiel_dao.lister(limite=1000 if detaille else 40):
            feuille.append([
                m["code"], m["designation"], m["service_nom"] or "",
                m.get("grade_libelle", ""), m["statut_libelle"],
                m["date_acquisition"].strftime("%d/%m/%Y") if m.get("date_acquisition") else "",
            ])

    classeur.save(chemin_fichier)
    _enregistrer_historique(os.path.basename(chemin_fichier), chemin_fichier, "Excel")
    return chemin_fichier


def _enregistrer_historique(nom, chemin, format_fichier):
    os.makedirs(DOSSIER_RAPPORTS, exist_ok=True)
    historique = lister_historique()
    historique.insert(0, {
        "nom": nom,
        "chemin": chemin,
        "format": format_fichier,
        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    with open(HISTORIQUE_PATH, "w", encoding="utf-8") as f:
        json.dump(historique[:20], f, ensure_ascii=False, indent=2)


def lister_historique():
    if not os.path.exists(HISTORIQUE_PATH):
        return []
    with open(HISTORIQUE_PATH, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
