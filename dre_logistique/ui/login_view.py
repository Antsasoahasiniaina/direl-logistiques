import os
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from config import theme
from services import auth_service

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_minel.jpg")


def _icone_utilisateur(master, couleur):
    c = tk.Canvas(master, width=18, height=18, highlightthickness=0, bg=theme.COLOR_CARD)
    c.create_oval(6, 2, 12, 8, outline=couleur, width=1.4)
    c.create_arc(3, 8, 15, 19, start=0, extent=180, style="arc", outline=couleur, width=1.4)
    return c


def _icone_cadenas(master, couleur):
    c = tk.Canvas(master, width=18, height=18, highlightthickness=0, bg=theme.COLOR_CARD)
    c.create_rectangle(4, 9, 14, 17, outline=couleur, width=1.4)
    c.create_arc(6, 2, 12, 12, start=0, extent=180, style="arc", outline=couleur, width=1.4)
    return c


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_success, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self.on_success = on_success
        self.afficher_mdp = False

        carte = ctk.CTkFrame(self, fg_color="transparent")
        carte.place(relx=0.5, rely=0.5, anchor="center")

        self._build_panneau_marque(carte)
        self._build_panneau_formulaire(carte)

    def _build_panneau_marque(self, carte):
        panneau = ctk.CTkFrame(carte, fg_color=theme.COLOR_SIDEBAR,
                                corner_radius=20, width=300, height=440)
        panneau.grid(row=0, column=0, sticky="nsew")
        panneau.grid_propagate(False)

        ctk.CTkFrame(panneau, fg_color=theme.COLOR_SIDEBAR_HOVER, corner_radius=90,
                     width=180, height=180).place(x=-60, y=-60)
        ctk.CTkFrame(panneau, fg_color=theme.COLOR_ACCENT, corner_radius=70,
                     width=140, height=140).place(x=190, y=320)

        contenu = ctk.CTkFrame(panneau, fg_color="transparent")
        contenu.place(relx=0.5, rely=0.42, anchor="center")

        if os.path.exists(LOGO_PATH):
            image_pil = Image.open(LOGO_PATH)
            logo_ctk = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(110, 110))
            ctk.CTkLabel(contenu, image=logo_ctk, text="").pack(pady=(0, 18))

        ctk.CTkLabel(
            contenu, text="BIENVENUE", font=(theme.FONT_FAMILY, 22, "bold"),
            text_color="white",
        ).pack(anchor="w")
        ctk.CTkLabel(
            contenu, text="DRE HAUTE MATSIATRA", font=(theme.FONT_FAMILY, 12, "bold"),
            text_color=theme.COLOR_ACCENT,
        ).pack(anchor="w", pady=(2, 14))
        ctk.CTkLabel(
            contenu, text="République de Madagascar\nSystème de gestion logistique\ndu matériel",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_SIDEBAR_TEXT_MUTED,
            justify="left",
        ).pack(anchor="w")

    def _build_panneau_formulaire(self, carte):
        panneau = ctk.CTkFrame(carte, fg_color=theme.COLOR_CARD,
                                corner_radius=20, width=380, height=440)
        panneau.grid(row=0, column=1, sticky="nsew")
        panneau.grid_propagate(False)

        contenu = ctk.CTkFrame(panneau, fg_color="transparent")
        contenu.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            contenu, text="Connexion", font=(theme.FONT_FAMILY, 21, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(
            contenu, text="Accédez à votre espace de gestion",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 22))

        ctk.CTkLabel(contenu, text="Identifiant", font=(theme.FONT_FAMILY, 11),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        champ_login = ctk.CTkFrame(contenu, fg_color=theme.COLOR_CARD, border_width=1,
                                    border_color=theme.COLOR_BORDER,
                                    corner_radius=theme.CORNER_RADIUS_CONTROL,
                                    width=280, height=38)
        champ_login.pack(anchor="w", pady=(0, 14))
        champ_login.pack_propagate(False)
        _icone_utilisateur(champ_login, theme.COLOR_TEXT_SECONDARY).pack(side="left", padx=(10, 4))
        self.champ_login = ctk.CTkEntry(champ_login, border_width=0, fg_color=theme.COLOR_CARD,
                                         placeholder_text="ex. admin")
        self.champ_login.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(contenu, text="Mot de passe", font=(theme.FONT_FAMILY, 11),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        champ_mdp = ctk.CTkFrame(contenu, fg_color=theme.COLOR_CARD, border_width=1,
                                  border_color=theme.COLOR_BORDER,
                                  corner_radius=theme.CORNER_RADIUS_CONTROL,
                                  width=280, height=38)
        champ_mdp.pack(anchor="w", pady=(0, 4))
        champ_mdp.pack_propagate(False)
        _icone_cadenas(champ_mdp, theme.COLOR_TEXT_SECONDARY).pack(side="left", padx=(10, 4))
        self.champ_mdp = ctk.CTkEntry(champ_mdp, border_width=0, fg_color=theme.COLOR_CARD, show="•")
        self.champ_mdp.pack(side="left", fill="both", expand=True)
        self.champ_mdp.bind("<Return>", lambda e: self._tenter_connexion())
        self.bouton_afficher = ctk.CTkLabel(
            champ_mdp, text="Afficher", font=(theme.FONT_FAMILY, 10, "bold"),
            text_color=theme.COLOR_ACCENT, cursor="hand2",
        )
        self.bouton_afficher.pack(side="left", padx=(0, 10))
        self.bouton_afficher.bind("<Button-1>", lambda e: self._basculer_affichage_mdp())

        self.label_erreur = ctk.CTkLabel(
            contenu, text="", font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_DANGER,
            wraplength=280, justify="left",
        )
        self.label_erreur.pack(anchor="w", pady=(6, 2))

        ctk.CTkButton(
            contenu, text="Se connecter", width=280, height=38,
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS_CONTROL, font=(theme.FONT_FAMILY, 13, "bold"),
            command=self._tenter_connexion,
        ).pack(anchor="w", pady=(14, 0))

        ctk.CTkLabel(
            contenu, text="Accès réservé aux agents habilités de la DRE",
            font=(theme.FONT_FAMILY, 10), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(16, 0))

    def _basculer_affichage_mdp(self):
        self.afficher_mdp = not self.afficher_mdp
        self.champ_mdp.configure(show="" if self.afficher_mdp else "•")
        self.bouton_afficher.configure(text="Masquer" if self.afficher_mdp else "Afficher")

    def _tenter_connexion(self):
        login = self.champ_login.get().strip()
        mot_de_passe = self.champ_mdp.get()

        if not login or not mot_de_passe:
            self.label_erreur.configure(text="Veuillez renseigner l'identifiant et le mot de passe.")
            return

        ok, resultat = auth_service.se_connecter(login, mot_de_passe)
        if not ok:
            self.label_erreur.configure(text=resultat)
            self.champ_mdp.delete(0, "end")
            return

        self.label_erreur.configure(text="")
        self.on_success(resultat)