"""Service de génération et de lecture des QR codes du matériel.

- generer_code() : construit un identifiant lisible (ex. MAT-LTP-0007)
- generer_image_qr() : encode ce code en image QR (bibliothèque qrcode)
- generer_image_etiquette() : compose l'étiquette imprimable complète
  (logo, en-tête DRE, QR code, nom, code)
- decoder_image() : décode un QR code depuis une image (webcam ou fichier),
  via pyzbar — utilisé par scan_view.py sur chaque frame de la caméra.
- imprimer_etiquette() : régénère l'étiquette (toujours à jour) puis
  l'envoie à l'imprimante par défaut.
"""

import os
import re
import subprocess
import sys

import qrcode
from PIL import Image, ImageDraw, ImageFont
from pyzbar.pyzbar import decode as _pyzbar_decode
from pyzbar.pyzbar import ZBarSymbol

from database.dao import materiel_dao

DOSSIER_ETIQUETTES = os.path.join(os.path.dirname(__file__), "..", "etiquettes")
CHEMIN_LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_minel.jpg")

# 472 x 649 px ≈ 4,0 x 5,5 cm à 300 DPI (taille demandée pour le collage sur matériel)
TAILLE_ETIQUETTE = (472, 649)


def _abreviation(designation, taille=3):
    lettres = re.sub(r"[^A-Za-z]", "", designation.split()[0]).upper()
    return (lettres + "XXX")[:taille]


def generer_code(designation):
    """Construit un code du type MAT-LAP-0007 à partir de la désignation
    et du nombre de matériels déjà enregistrés."""
    materiels = materiel_dao.lister(limite=1)
    dernier_id = materiels[0]["id_materiel"] if materiels else 0
    return f"MAT-{_abreviation(designation)}-{dernier_id + 1:04d}"


def generer_image_qr(contenu):
    """Retourne une image PIL contenant le QR code du contenu donné."""
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(contenu)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def _police(taille, gras=False):
    """Cherche une police TrueType disponible (Arial sous Windows, DejaVu
    sous Linux/macOS), avec repli sur la police bitmap par défaut de PIL
    si aucune n'est trouvée."""
    noms = ["arialbd.ttf", "DejaVuSans-Bold.ttf"] if gras else ["arial.ttf", "DejaVuSans.ttf"]
    for nom in noms:
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    return ImageFont.load_default()


def _decouper_texte(texte, police, largeur_max, dessin):
    """Découpe un texte en plusieurs lignes pour qu'il tienne dans
    largeur_max pixels avec la police donnée."""
    mots = texte.split()
    lignes, ligne = [], ""
    for mot in mots:
        essai = f"{ligne} {mot}".strip()
        if dessin.textlength(essai, font=police) <= largeur_max:
            ligne = essai
        else:
            if ligne:
                lignes.append(ligne)
            ligne = mot
    if ligne:
        lignes.append(ligne)
    return lignes


def generer_image_etiquette(code, designation):
    """Compose l'étiquette imprimable complète : cadre, logo, en-tête DRE,
    QR code, désignation et code — aux dimensions demandées pour le collage
    sur le matériel (472x649 px, 300 DPI)."""
    largeur, hauteur = TAILLE_ETIQUETTE
    etiquette = Image.new("RGB", (largeur, hauteur), "white")
    dessin = ImageDraw.Draw(etiquette)

    marge = 18
    dessin.rectangle([2, 2, largeur - 3, hauteur - 3], outline="black", width=2)

    y = marge + 8
    if os.path.exists(CHEMIN_LOGO):
        logo = Image.open(CHEMIN_LOGO).convert("RGBA")
        logo.thumbnail((70, 70))
        etiquette.paste(logo, ((largeur - logo.width) // 2, y), logo)
        y += logo.height + 10

    police_titre = _police(20, gras=True)
    police_sous_titre = _police(13)
    for texte, police in [("DIREL HAUTE MATSIATRA", police_titre),
                           ("Inventaire matériel", police_sous_titre)]:
        largeur_texte = dessin.textlength(texte, font=police)
        dessin.text(((largeur - largeur_texte) / 2, y), texte, font=police, fill="black")
        y += police.size + 6

    y += 8
    dessin.line([marge, y, largeur - marge, y], fill="black", width=1)
    y += 16

    taille_qr = 260
    qr_img = generer_image_qr(code).convert("RGB").resize((taille_qr, taille_qr))
    etiquette.paste(qr_img, ((largeur - taille_qr) // 2, y))
    y += taille_qr + 16

    dessin.line([marge, y, largeur - marge, y], fill="black", width=1)
    y += 16

    police_label = _police(12)
    police_nom = _police(13)
    police_code = _police(20, gras=True)

    dessin.text((marge, y), "Nom :", font=police_label, fill="black")
    y += police_label.size + 4
    for ligne in _decouper_texte(designation, police_nom, largeur - 2 * marge, dessin)[:2]:
        largeur_texte = dessin.textlength(ligne, font=police_nom)
        dessin.text(((largeur - largeur_texte) / 2, y), ligne, font=police_nom, fill="black")
        y += police_nom.size + 4

    y += 10
    dessin.text((marge, y), "Code :", font=police_label, fill="black")
    y += police_label.size + 4
    largeur_code = dessin.textlength(code, font=police_code)
    dessin.text(((largeur - largeur_code) / 2, y), code, font=police_code, fill="black")

    return etiquette


def sauvegarder_etiquette(code, designation):
    """Génère et enregistre l'étiquette complète sur disque (écrase un
    éventuel ancien fichier), retourne le chemin du fichier."""
    os.makedirs(DOSSIER_ETIQUETTES, exist_ok=True)
    chemin = os.path.join(DOSSIER_ETIQUETTES, f"{code}.png")
    generer_image_etiquette(code, designation).save(chemin, dpi=(300, 300))
    return chemin


def chemin_etiquette(code):
    return os.path.join(DOSSIER_ETIQUETTES, f"{code}.png")


def imprimer_etiquette(code, designation=""):
    """Régénère toujours l'étiquette avant impression (si la désignation est
    fournie) pour garantir qu'elle reflète le design et les données à jour —
    corrige le cas où une ancienne étiquette (QR brut, avant l'ajout du
    design complet) traînait sur le disque et était imprimée à répétition.
    Envoie ensuite à l'imprimante par défaut (Windows), ou ouvre avec la
    visionneuse système sur macOS/Linux."""
    if designation:
        chemin = sauvegarder_etiquette(code, designation)
    else:
        chemin = chemin_etiquette(code)
        if not os.path.exists(chemin):
            raise FileNotFoundError(f"Étiquette introuvable : {chemin}")

    if sys.platform == "win32":
        try:
            os.startfile(chemin, "print")
        except OSError:
            os.startfile(chemin)
    elif sys.platform == "darwin":
        subprocess.run(["open", chemin], check=True)
    else:
        subprocess.run(["xdg-open", chemin], check=True)

    return chemin


def decoder_image(image):
    """Décode les QR codes présents dans une image (PIL.Image ou tableau
    numpy issu d'OpenCV). Limité au symbole QRCODE : évite que zbar essaie
    aussi PDF417/Code128/etc. sur chaque frame caméra, ce qui génère des
    avertissements internes inoffensifs mais bruyants dans la console."""
    resultats = _pyzbar_decode(image, symbols=[ZBarSymbol.QRCODE])
    return [r.data.decode("utf-8") for r in resultats]