"""Écran 'Alertes' — aide à la décision (UC12).

Affiche les alertes calculées par prediction_service (ancienneté, fréquence
de panne, rupture de stock, sur-consommation). L'utilisateur peut filtrer
et relancer le calcul sans quitter l'écran.
"""

import customtkinter as ctk

from config import theme
from ui.widgets import StatusBadge, card, IconMetricCard
from ui.icons import icone_alerte, icone_cloche, icone_boite, icone_rotation
from services import prediction_service

NIVEAU_VERS_VARIANT = {"eleve": "danger", "moyen": "warning", "faible": "info"}
NIVEAU_LIBELLE = {"eleve": "Élevé", "moyen": "Moyen", "faible": "Faible"}
TYPE_LIBELLE = {
    "anciennete": "Ancienneté",
    "frequence_panne": "Fréquence de panne",
    "rupture_stock": "Rupture de stock",
    "sur_consommation": "Sur-consommation",
}
FILTRE_TYPES = ["Tous les types"] + list(TYPE_LIBELLE.values())
FILTRE_NIVEAUX = ["Tous les niveaux", "Élevé", "Moyen", "Faible"]
LIBELLE_VERS_TYPE = {v: k for k, v in TYPE_LIBELLE.items()}
LIBELLE_VERS_NIVEAU = {v: k for k, v in NIVEAU_LIBELLE.items()}


class AlerteView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self._filtre_type = "Tous les types"
        self._filtre_niveau = "Tous les niveaux"
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 4))

        gauche = ctk.CTkFrame(header, fg_color="transparent")
        gauche.pack(side="left", anchor="w")
        ctk.CTkLabel(
            gauche, text="Alertes", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            gauche, text="Aide à la décision : ancienneté, pannes, stock et consommation",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="Recalculer les alertes", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            height=36, command=self._recalculer,
        ).pack(side="right")

        self._kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        self._kpi_row.pack(fill="x", padx=24, pady=(16, 0))
        self._kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        filtres = ctk.CTkFrame(self, fg_color="transparent")
        filtres.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(
            filtres, text="Filtrer", font=(theme.FONT_FAMILY, 12),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 10))
        self._menu_type = ctk.CTkOptionMenu(
            filtres, values=FILTRE_TYPES, width=200, command=self._changer_type,
            fg_color=theme.COLOR_CARD, button_color=theme.COLOR_ACCENT,
            button_hover_color=theme.COLOR_ACCENT_HOVER,
            text_color=theme.COLOR_TEXT_PRIMARY,
        )
        self._menu_type.pack(side="left", padx=(0, 8))
        self._menu_niveau = ctk.CTkOptionMenu(
            filtres, values=FILTRE_NIVEAUX, width=170, command=self._changer_niveau,
            fg_color=theme.COLOR_CARD, button_color=theme.COLOR_ACCENT,
            button_hover_color=theme.COLOR_ACCENT_HOVER,
            text_color=theme.COLOR_TEXT_PRIMARY,
        )
        self._menu_niveau.pack(side="left")

        self._liste_card = card(self)
        self._liste_card.pack(fill="both", expand=True, padx=24, pady=(16, 24))

        self._rafraichir()

    def _changer_type(self, valeur):
        self._filtre_type = valeur
        self._rafraichir(recalculer_kpi=False)

    def _changer_niveau(self, valeur):
        self._filtre_niveau = valeur
        self._rafraichir(recalculer_kpi=False)

    def _recalculer(self):
        prediction_service.calculer_toutes_les_alertes()
        self._rafraichir()

    def _alertes_filtrees(self, alertes):
        resultats = list(alertes)
        if self._filtre_type != "Tous les types":
            code = LIBELLE_VERS_TYPE[self._filtre_type]
            resultats = [a for a in resultats if a["type_alerte"] == code]
        if self._filtre_niveau != "Tous les niveaux":
            code = LIBELLE_VERS_NIVEAU[self._filtre_niveau]
            resultats = [a for a in resultats if a["niveau_risque"] == code]
        return resultats

    def _rafraichir(self, recalculer_kpi=True):
        alertes = prediction_service.lister_alertes_actives() or []
        if recalculer_kpi:
            self._construire_kpi(alertes)
        self._construire_liste(self._alertes_filtrees(alertes))

    def _construire_kpi(self, alertes):
        for enfant in self._kpi_row.winfo_children():
            enfant.destroy()

        n_eleve = sum(1 for a in alertes if a["niveau_risque"] == "eleve")
        n_moyen = sum(1 for a in alertes if a["niveau_risque"] == "moyen")
        n_faible = sum(1 for a in alertes if a["niveau_risque"] == "faible")

        IconMetricCard(
            self._kpi_row, icone_cloche, "Alertes actives", str(len(alertes)),
            couleur_fond=theme.COLOR_PURPLE_BG, couleur_badge=theme.COLOR_PURPLE,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        IconMetricCard(
            self._kpi_row, icone_alerte, "Risque élevé", str(n_eleve),
            couleur_fond=theme.COLOR_DANGER_BG, couleur_badge=theme.COLOR_DANGER,
        ).grid(row=0, column=1, sticky="ew", padx=8)
        IconMetricCard(
            self._kpi_row, icone_rotation, "Risque moyen", str(n_moyen),
            couleur_fond=theme.COLOR_WARNING_BG, couleur_badge=theme.COLOR_WARNING,
        ).grid(row=0, column=2, sticky="ew", padx=8)
        IconMetricCard(
            self._kpi_row, icone_boite, "Risque faible", str(n_faible),
            couleur_fond=theme.COLOR_INFO_BG, couleur_badge=theme.COLOR_INFO,
        ).grid(row=0, column=3, sticky="ew", padx=(8, 0))

    def _construire_liste(self, alertes):
        for enfant in self._liste_card.winfo_children():
            enfant.destroy()

        entete = ctk.CTkFrame(self._liste_card, fg_color="transparent")
        entete.pack(fill="x", padx=16, pady=(14, 6))
        for texte, largeur in [
            ("Niveau", 90), ("Type", 150), ("Matériel", 110),
            ("Message", 420), ("Date", 110),
        ]:
            ctk.CTkLabel(
                entete, text=texte, width=largeur, anchor="w",
                font=(theme.FONT_FAMILY, 11, "bold"),
                text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(side="left")

        if not alertes:
            ctk.CTkLabel(
                self._liste_card,
                text="Aucune alerte pour ces filtres. Recalculez ou élargissez le filtre.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(4, 16))
            return

        zone = ctk.CTkScrollableFrame(self._liste_card, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for a in alertes:
            ligne = ctk.CTkFrame(zone, fg_color="transparent")
            ligne.pack(fill="x", pady=5)

            variant = NIVEAU_VERS_VARIANT.get(a["niveau_risque"], "info")
            badge_frame = ctk.CTkFrame(ligne, fg_color="transparent", width=90)
            badge_frame.pack(side="left")
            badge_frame.pack_propagate(False)
            StatusBadge(
                badge_frame, NIVEAU_LIBELLE.get(a["niveau_risque"], a["niveau_risque"]),
                variant=variant,
            ).pack(anchor="w")

            ctk.CTkLabel(
                ligne, text=TYPE_LIBELLE.get(a["type_alerte"], a["type_alerte"]),
                width=150, anchor="w", font=(theme.FONT_FAMILY, 12),
                text_color=theme.COLOR_TEXT_PRIMARY,
            ).pack(side="left")
            ctk.CTkLabel(
                ligne, text=a.get("code") or "—", width=110, anchor="w",
                font=(theme.FONT_FAMILY, 12, "bold"),
                text_color=theme.COLOR_TEXT_PRIMARY,
            ).pack(side="left")
            ctk.CTkLabel(
                ligne, text=a["message"], width=420, anchor="w",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
                wraplength=400, justify="left",
            ).pack(side="left")
            date_str = a["date_generation"].strftime("%d/%m/%Y %H:%M") if a.get("date_generation") else "—"
            ctk.CTkLabel(
                ligne, text=date_str, width=110, anchor="w",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(side="left")
