"""Barre de navigation latérale commune à toutes les pages de l'application."""

import customtkinter as ctk

from config import theme
from ui import icons


class Sidebar(ctk.CTkFrame):
    NAV_ITEMS = [
        ("dashboard", "Tableau de bord", icons.icone_tableau_bord),
        ("materiel", "Matériel", icons.icone_boite),
        ("scan", "Scan QR", icons.icone_scan),
        ("alertes", "Alertes", icons.icone_cloche),
        ("rapports", "Rapports", icons.icone_rapport),
        ("parametres", "Paramètres", icons.icone_parametres),
    ]

    def __init__(self, master, on_navigate, on_logout, active="dashboard",
                 user_name="Admin DRE", **kwargs):
        super().__init__(master, width=210, fg_color=theme.COLOR_SIDEBAR, corner_radius=0, **kwargs)
        self.on_navigate = on_navigate
        self.pack_propagate(False)

        ctk.CTkLabel(
            self, text="DRE Logistique",
            font=(theme.FONT_FAMILY, 17, "bold"), text_color="white",
        ).pack(anchor="w", padx=20, pady=(24, 0))

        ctk.CTkLabel(
            self, text="Gestion du matériel",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_SIDEBAR_TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 24))

        # Conserver une référence aux icônes CTkImage : sans ça, le
        # ramasse-miettes Python les détruit et les boutons deviennent vides.
        self._icones = {}
        self._boutons = {}
        for key, label, icone_fn in self.NAV_ITEMS:
            icone = icone_fn("white", taille=18)
            self._icones[key] = icone
            btn = ctk.CTkButton(
                self, text=f"  {label}", image=icone, compound="left", anchor="w",
                fg_color=theme.COLOR_SIDEBAR_ACTIVE if key == active else "transparent",
                hover_color=theme.COLOR_SIDEBAR_HOVER,
                text_color="white", corner_radius=theme.CORNER_RADIUS_CONTROL, height=38,
                font=(theme.FONT_FAMILY, 13),
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._boutons[key] = btn

        # -- Pied de sidebar : déconnexion + infos utilisateur -----------------
        pied = ctk.CTkFrame(self, fg_color="transparent")
        pied.pack(side="bottom", fill="x", padx=12, pady=16)

        self._icone_deconnexion = icons.icone_deconnexion(theme.COLOR_DANGER, taille=16)
        ctk.CTkButton(
            pied, text="  Déconnexion", image=self._icone_deconnexion, compound="left", anchor="w",
            fg_color="transparent", hover_color=theme.COLOR_SIDEBAR_HOVER,
            text_color="#f87171", corner_radius=theme.CORNER_RADIUS_CONTROL, height=36,
            font=(theme.FONT_FAMILY, 13), command=on_logout,
        ).pack(fill="x", pady=(0, 12))

        separateur = ctk.CTkFrame(pied, height=1, fg_color=theme.COLOR_SIDEBAR_HOVER)
        separateur.pack(fill="x", pady=(0, 12))

        bloc_user = ctk.CTkFrame(pied, fg_color="transparent")
        bloc_user.pack(fill="x", padx=8)
        ctk.CTkLabel(
            bloc_user, text=user_name, font=(theme.FONT_FAMILY, 13, "bold"), text_color="white",
        ).pack(anchor="w")
        ctk.CTkLabel(
            bloc_user, text="Administrateur", font=(theme.FONT_FAMILY, 11),
            text_color=theme.COLOR_SIDEBAR_TEXT_MUTED,
        ).pack(anchor="w")

    def _navigate(self, key):
        for k, btn in self._boutons.items():
            btn.configure(fg_color=theme.COLOR_SIDEBAR_ACTIVE if k == key else "transparent")
        self.on_navigate(key)

    def set_active(self, key):
        for k, btn in self._boutons.items():
            btn.configure(fg_color=theme.COLOR_SIDEBAR_ACTIVE if k == key else "transparent")