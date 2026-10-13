"""Icônes vectorielles générées avec Pillow — aucun fichier image externe,
aucune dépendance à une librairie d'icônes tierce. Point d'entrée unique
pour toute icône affichée dans l'application (sidebar, boutons, cartes KPI),
ce qui garantit un style de trait cohérent partout (épaisseur, arrondis).

Chaque fonction retourne un customtkinter.CTkImage prêt à être passé au
paramètre `image=` d'un CTkButton/CTkLabel (avec compound="left" pour un
bouton texte + icône).
"""

import math

from PIL import Image, ImageDraw
import customtkinter as ctk

_SURECHANTILLONNAGE = 3  # dessiné en haute résolution puis réduit -> anti-crénelage
_EPAISSEUR_BASE = 1.8


def _image_vierge(taille):
    dim = int(taille * _SURECHANTILLONNAGE)
    return Image.new("RGBA", (dim, dim), (0, 0, 0, 0)), dim


def _vers_ctkimage(image_haute_res, taille):
    image_finale = image_haute_res.resize((taille, taille), Image.LANCZOS)
    return ctk.CTkImage(light_image=image_finale, dark_image=image_finale, size=(taille, taille))


def _trait(d):
    return max(1, int(_EPAISSEUR_BASE * _SURECHANTILLONNAGE))


# ---------------------------------------------------------------------------
# Icônes de navigation (sidebar)
# ---------------------------------------------------------------------------

def icone_tableau_bord(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    marge, ecart = d * 0.10, d * 0.10
    cote = (d - marge * 2 - ecart) / 2
    for x, y in [(marge, marge), (marge + cote + ecart, marge),
                 (marge, marge + cote + ecart), (marge + cote + ecart, marge + cote + ecart)]:
        dr.rounded_rectangle([x, y, x + cote, y + cote], radius=d * 0.06, outline=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_scan(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    m, l = d * 0.12, d * 0.26
    for pts in ([(m, m + l), (m, m), (m + l, m)],
                [(d - m - l, m), (d - m, m), (d - m, m + l)],
                [(m, d - m - l), (m, d - m), (m + l, d - m)],
                [(d - m - l, d - m), (d - m, d - m), (d - m, d - m - l)]):
        dr.line(pts, fill=couleur, width=w, joint="curve")
    return _vers_ctkimage(img, taille)


def icone_cloche(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.arc([d * 0.16, d * 0.08, d * 0.84, d * 0.78], start=180, end=360, fill=couleur, width=w)
    dr.line([d * 0.16, d * 0.43, d * 0.16, d * 0.66], fill=couleur, width=w)
    dr.line([d * 0.84, d * 0.43, d * 0.84, d * 0.66], fill=couleur, width=w)
    dr.line([d * 0.12, d * 0.66, d * 0.88, d * 0.66], fill=couleur, width=w)
    dr.ellipse([d * 0.42, d * 0.74, d * 0.58, d * 0.90], outline=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_rapport(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.rounded_rectangle([d * 0.20, d * 0.08, d * 0.80, d * 0.92], radius=d * 0.06, outline=couleur, width=w)
    for i, y in enumerate((0.34, 0.50, 0.66)):
        fin = 0.66 if i < 2 else 0.55
        dr.line([d * 0.32, d * y, d * fin, d * y], fill=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_parametres(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    cx, cy, r_int, r_ext = d / 2, d / 2, d * 0.16, d * 0.40
    dr.ellipse([cx - r_int, cy - r_int, cx + r_int, cy + r_int], outline=couleur, width=w)
    for i in range(8):
        angle = math.radians(i * 45)
        x1, y1 = cx + r_int * 1.3 * math.cos(angle), cy + r_int * 1.3 * math.sin(angle)
        x2, y2 = cx + r_ext * math.cos(angle), cy + r_ext * math.sin(angle)
        dr.line([x1, y1, x2, y2], fill=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_deconnexion(couleur, taille=18):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.rounded_rectangle([d * 0.14, d * 0.12, d * 0.54, d * 0.88], radius=d * 0.05, outline=couleur, width=w)
    dr.line([d * 0.40, d * 0.5, d * 0.88, d * 0.5], fill=couleur, width=w)
    dr.line([d * 0.68, d * 0.30, d * 0.88, d * 0.5], fill=couleur, width=w)
    dr.line([d * 0.68, d * 0.70, d * 0.88, d * 0.5], fill=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_crayon(couleur, taille=16):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.line([d * 0.18, d * 0.82, d * 0.62, d * 0.38], fill=couleur, width=w)
    dr.polygon([(d * 0.62, d * 0.38), (d * 0.78, d * 0.22), (d * 0.88, d * 0.32), (d * 0.72, d * 0.48)],
               outline=couleur, width=w)
    dr.line([d * 0.14, d * 0.86, d * 0.20, d * 0.80, d * 0.24, d * 0.86], fill=couleur, width=w, joint="curve")
    return _vers_ctkimage(img, taille)


def icone_archiver(couleur, taille=16):
    """Boîte + flèche vers le bas : symbolise le rangement en archive
    (soft-delete), plutôt qu'une poubelle qui suggère une perte définitive."""
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.rounded_rectangle([d * 0.16, d * 0.58, d * 0.84, d * 0.86], radius=d * 0.05, outline=couleur, width=w)
    dr.line([d * 0.5, d * 0.12, d * 0.5, d * 0.50], fill=couleur, width=w)
    dr.polygon([(d * 0.34, d * 0.36), (d * 0.5, d * 0.54), (d * 0.66, d * 0.36)], outline=couleur, width=w)
    return _vers_ctkimage(img, taille)


# ---------------------------------------------------------------------------
# Icônes des cartes KPI (tableau de bord) — traits plus épais, fond coloré
# ---------------------------------------------------------------------------

def icone_boite(couleur, taille=24):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.rectangle([d * 0.18, d * 0.36, d * 0.82, d * 0.82], outline=couleur, width=w)
    dr.line([d * 0.18, d * 0.36, d * 0.50, d * 0.16], fill=couleur, width=w)
    dr.line([d * 0.82, d * 0.36, d * 0.50, d * 0.16], fill=couleur, width=w)
    dr.line([d * 0.50, d * 0.16, d * 0.50, d * 0.82], fill=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_alerte(couleur, taille=24):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.polygon([(d * 0.5, d * 0.12), (d * 0.90, d * 0.84), (d * 0.10, d * 0.84)],
               outline=couleur, width=w)
    dr.line([d * 0.5, d * 0.38, d * 0.5, d * 0.62], fill=couleur, width=w)
    dr.ellipse([d * 0.46, d * 0.68, d * 0.54, d * 0.76], fill=couleur)
    return _vers_ctkimage(img, taille)


def icone_mouvement(couleur, taille=24):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.rectangle([d * 0.12, d * 0.40, d * 0.60, d * 0.72], outline=couleur, width=w)
    dr.polygon([(d * 0.60, d * 0.50), (d * 0.80, d * 0.50), (d * 0.90, d * 0.62),
                (d * 0.90, d * 0.72), (d * 0.60, d * 0.72)], outline=couleur, width=w)
    dr.ellipse([d * 0.22, d * 0.70, d * 0.38, d * 0.86], outline=couleur, width=w)
    dr.ellipse([d * 0.68, d * 0.70, d * 0.84, d * 0.86], outline=couleur, width=w)
    return _vers_ctkimage(img, taille)


def icone_rotation(couleur, taille=24):
    img, d = _image_vierge(taille)
    dr = ImageDraw.Draw(img)
    w = _trait(d)
    dr.arc([d * 0.18, d * 0.18, d * 0.82, d * 0.82], start=30, end=300, fill=couleur, width=w)
    dr.polygon([(d * 0.72, d * 0.10), (d * 0.92, d * 0.22), (d * 0.72, d * 0.34)], fill=couleur)
    return _vers_ctkimage(img, taille)