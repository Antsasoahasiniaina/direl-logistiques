"""Point d'entrée de l'application DRE Logistique.

Lance la fenêtre principale, installe la sidebar et bascule entre les écrans
(Tableau de bord, Matériel, Scan QR, Alertes, Rapports, Paramètres).
"""

import os
import sys

# Coupe les avertissements natifs de la bibliothèque C++ ZBar
os.environ["ZBAR_NONE"] = "1"

# Redirige les flux d'erreurs secondaires vers le vide absolu du système
sys.stderr = open(os.devnull, 'w')

import datetime
import traceback

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps

from config import theme
from database import connexion
from services import auth_service, prediction_service
from ui.sidebar import Sidebar
from ui.login_view import LoginView
from ui.dashboard_view import DashboardView
from ui.materiel_view import MaterielView
from ui.scan_view import ScanView
from ui.alerte_view import AlerteView
from ui.rapport_view import RapportView
from ui.parametres_view import ParametresView

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo_minel.jpg")

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")  # remplacé par nos propres couleurs (config/theme.py)


class PlaceholderView(ctk.CTkFrame):
    """Écran temporaire pour les modules pas encore développés."""

    def __init__(self, master, titre, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        ctk.CTkLabel(
            self, text=titre, font=(theme.FONT_FAMILY, 22, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(pady=(40, 6))
        ctk.CTkLabel(
            self, text="Module en cours de développement.",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack()


class ErrorView(ctk.CTkFrame):
    """Affichée à la place d'un écran vide si sa construction plante — donne
    le détail de l'erreur pour un diagnostic immédiat, au lieu d'un blanc
    silencieux."""

    def __init__(self, master, titre, detail, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        ctk.CTkLabel(
            self, text=f"Erreur lors du chargement : {titre}",
            font=(theme.FONT_FAMILY, 18, "bold"), text_color=theme.COLOR_DANGER,
        ).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            self, text="Copiez ce message pour le diagnostic :",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(0, 10))
        zone = ctk.CTkTextbox(
            self, fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT_PRIMARY,
            wrap="word", font=("Consolas", 11),
        )
        zone.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        zone.insert("1.0", detail)
        zone.configure(state="disabled")


class App(ctk.CTk):
    VIEWS = {
        "dashboard": ("Tableau de bord", DashboardView),
        "materiel": ("Matériel", MaterielView),
        "scan": ("Scan QR", ScanView),
        "alertes": ("Alertes", AlerteView),
        "rapports": ("Rapports", RapportView),
        "parametres": ("Paramètres", ParametresView),
    }

    TAILLE_LOGIN = (760, 560)
    TAILLE_APP = (1200, 760)

    def __init__(self):
        super().__init__()
        self.title("DIREL Logistique — DIREL Haute Matsiatra")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._current_view = None
        self._header = None
        self._afficher_login()

    def _logo_arrondi(self, taille):
        """Charge le logo et lui applique un masque arrondi (coins ronds),
        pour un rendu compact façon badge — cohérent avec l'en-tête clair."""
        image_pil = Image.open(LOGO_PATH).convert("RGBA").resize((taille, taille))
        masque = Image.new("L", (taille, taille), 0)
        ImageDraw.Draw(masque).rounded_rectangle([0, 0, taille, taille], radius=taille * 0.28, fill=255)
        image_pil.putalpha(masque)
        return ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(taille, taille))

    def _build_header(self, utilisateur):
        """Bande d'en-tête compacte, claire, avec logo + titre + badge à
        gauche et utilisateur connecté à droite — surmontée d'un léger
        filet de séparation avec le contenu."""
        conteneur = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        conteneur.grid_propagate(False)

        separateur = ctk.CTkFrame(conteneur, height=1, fg_color=theme.COLOR_BORDER)
        separateur.pack(side="bottom", fill="x")

        header = ctk.CTkFrame(conteneur, fg_color=theme.COLOR_CARD, corner_radius=0, height=56)
        header.pack(side="top", fill="both", expand=True)
        header.pack_propagate(False)

        gauche = ctk.CTkFrame(header, fg_color="transparent")
        gauche.pack(side="left", padx=20)

        if os.path.exists(LOGO_PATH):
            self._logo_header = self._logo_arrondi(32)
            ctk.CTkLabel(gauche, image=self._logo_header, text="").pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            gauche, text="DIRECTION REGIONALE DE L'ELEVAGE", font=(theme.FONT_FAMILY, 15, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 8))

        badge = ctk.CTkLabel(
            gauche, text="Haute Matsiatra", font=(theme.FONT_FAMILY, 11, "bold"),
            text_color=theme.COLOR_TEXT_SECONDARY, fg_color=theme.COLOR_BG,
            corner_radius=theme.CORNER_RADIUS_CONTROL,
        )
        badge.pack(side="left", ipadx=8, ipady=2)

        droite = ctk.CTkFrame(header, fg_color="transparent")
        droite.pack(side="right", padx=20)

        nom_complet = f"{utilisateur['prenom']} {utilisateur['nom']}"
        initiales = (utilisateur["prenom"][:1] + utilisateur["nom"][:1]).upper()
        role_libelle = utilisateur.get("role_libelle", "").replace("_", " ").capitalize()

        avatar = ctk.CTkFrame(droite, width=34, height=34, corner_radius=17,
                               fg_color=theme.COLOR_ACCENT)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar, text=initiales, font=(theme.FONT_FAMILY, 12, "bold"), text_color="white",
        ).pack(expand=True)

        bloc_texte = ctk.CTkFrame(droite, fg_color="transparent")
        bloc_texte.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            bloc_texte, text=nom_complet, font=(theme.FONT_FAMILY, 13, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            bloc_texte, text=role_libelle, font=(theme.FONT_FAMILY, 11),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        return conteneur

    def _centrer_fenetre(self, largeur, hauteur):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - largeur) // 2
        y = (self.winfo_screenheight() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    def _afficher_login(self):
        if self._current_view is not None:
            self._current_view.destroy()

        self.resizable(False, False)
        self._centrer_fenetre(*self.TAILLE_LOGIN)

        login_view = LoginView(self, on_success=self._demarrer_application)
        login_view.grid(row=0, column=0, sticky="nsew")
        self._current_view = login_view

    def _demarrer_application(self, utilisateur):
        self._current_view.destroy()
        self._utilisateur = utilisateur
        prediction_service.calculer_toutes_les_alertes()

        self.resizable(True, True)
        self._centrer_fenetre(*self.TAILLE_APP)
        self.minsize(1000, 640)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self._header = self._build_header(utilisateur)
        self._header.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.sidebar = Sidebar(self, on_navigate=self.show_view, on_logout=self._deconnecter,
                                active="dashboard",
                                user_name=f"{utilisateur['prenom']} {utilisateur['nom']}")
        self.sidebar.grid(row=1, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color=theme.COLOR_BG, corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")

        self._current_view = None
        self.show_view("dashboard")

    def _deconnecter(self):
        auth_service.Session.deconnecter()
        self._header.destroy()
        self.sidebar.destroy()
        self.content.destroy()
        self._header = None
        self._current_view = None
        self._afficher_login()

    def show_view(self, key):
        if self._current_view is not None:
            self._current_view.destroy()

        titre, view_cls = self.VIEWS[key]
        try:
            if view_cls is None:
                self._current_view = PlaceholderView(self.content, titre)
            else:
                self._current_view = view_cls(self.content)
        except Exception:
            self._current_view = ErrorView(self.content, titre, traceback.format_exc())
        self._current_view.pack(fill="both", expand=True)


if __name__ == "__main__":
    connexion.initialiser_base()
    app = App()
    app.mainloop()