"""Écran 'Tableau de bord' — vue d'ensemble à l'ouverture de l'application :
KPI globaux, répartition du matériel par service, alertes prioritaires et
derniers mouvements. Toutes les données viennent des vrais services/DAO
(pas de données d'exemple ici, contrairement aux premières maquettes)."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import theme
from ui.widgets import StatusBadge, card, IconMetricCard
from ui.icons import icone_boite, icone_alerte, icone_mouvement, icone_rotation
from services import materiel_service, mouvement_service, prediction_service
from database.dao import mouvement_dao

NIVEAU_VERS_VARIANT = {"eleve": "danger", "moyen": "warning", "faible": "info"}


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._build(body)

    def _build(self, master):
        # -- En-tête -----------------------------------------------------
        ctk.CTkLabel(
            master, text="Tableau de bord", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(24, 2))
        ctk.CTkLabel(
            master, text="Vue d'ensemble du parc matériel de la DRE Haute Matsiatra",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # -- KPI -----------------------------------------------------------
        total_actif = materiel_service.compter_actifs()
        alertes = prediction_service.lister_alertes_actives()
        nb_alertes_elevees = sum(1 for a in alertes if a["niveau_risque"] == "eleve")
        mouvements_recents = mouvement_service.mouvements_recents(limite=100)
        mouvements_ce_mois = mouvement_dao.compter_ce_mois()
        taux_rotation = round((mouvements_ce_mois / total_actif) * 100, 1) if total_actif else 0

        kpi_row = ctk.CTkFrame(master, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24)
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        IconMetricCard(kpi_row, icone_boite, "Matériel actif", str(total_actif),
                       couleur_fond=theme.COLOR_INFO_BG, couleur_badge=theme.COLOR_INFO).grid(
            row=0, column=0, sticky="ew", padx=(0, 8))
        IconMetricCard(kpi_row, icone_alerte, "Alertes actives", str(len(alertes)),
                       f"{nb_alertes_elevees} à risque élevé" if nb_alertes_elevees else "Aucun risque élevé",
                       delta_positive=(nb_alertes_elevees == 0),
                       couleur_fond=theme.COLOR_PURPLE_BG, couleur_badge=theme.COLOR_PURPLE).grid(
            row=0, column=1, sticky="ew", padx=8)
        IconMetricCard(kpi_row, icone_mouvement, "Mouvements ce mois", str(mouvements_ce_mois),
                       couleur_fond=theme.COLOR_SUCCESS_BG, couleur_badge=theme.COLOR_SUCCESS).grid(
            row=0, column=2, sticky="ew", padx=8)
        IconMetricCard(kpi_row, icone_rotation, "Taux de rotation", f"{taux_rotation}%",
                       couleur_fond=theme.COLOR_WARNING_BG, couleur_badge=theme.COLOR_WARNING).grid(
            row=0, column=3, sticky="ew", padx=(8, 0))

        # -- Fizarazarany service + alertes prioritaires -------------------
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=24, pady=16)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        repartition_card = card(row)
        repartition_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            repartition_card, text="Répartition du matériel par service",
            font=(theme.FONT_FAMILY, 14, "bold"), text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 4))
        self._build_chart_repartition(repartition_card)

        alertes_card = card(row)
        alertes_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(
            alertes_card, text="Alertes prioritaires", font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 8))

        if not alertes:
            ctk.CTkLabel(
                alertes_card, text="Aucune alerte active pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        for a in alertes[:5]:
            ligne = ctk.CTkFrame(alertes_card, fg_color="transparent")
            ligne.pack(fill="x", padx=16, pady=5)
            StatusBadge(ligne, a["niveau_risque"].capitalize(),
                       variant=NIVEAU_VERS_VARIANT.get(a["niveau_risque"], "info")).pack(anchor="w")
            ctk.CTkLabel(
                ligne, text=a["message"], font=(theme.FONT_FAMILY, 11),
                text_color=theme.COLOR_TEXT_PRIMARY, wraplength=260, justify="left", anchor="w",
            ).pack(anchor="w", pady=(3, 0))
        ctk.CTkFrame(alertes_card, height=8, fg_color="transparent").pack()

        # -- Mouvements natao farany------------------------------------------------
        mouv_card = card(master)
        mouv_card.pack(fill="x", padx=24, pady=(0, 24))
        ctk.CTkLabel(
            mouv_card, text="Derniers mouvements", font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 6))

        if not mouvements_recents:
            ctk.CTkLabel(
                mouv_card, text="Aucun mouvement enregistré pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        for m in mouvements_recents[:6]:
            ligne = ctk.CTkFrame(mouv_card, fg_color="transparent")
            ligne.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(ligne, text=m["code"], width=110, anchor="w",
                        font=(theme.FONT_FAMILY, 12, "bold"),
                        text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(ligne, text=m["type_mouvement"].capitalize(), width=110, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
            destination = m["service_dest_nom"] or m["service_source_nom"] or "-"
            ctk.CTkLabel(ligne, text=destination, width=180, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(ligne, text=m["date_mouvement"].strftime("%d/%m/%Y"), anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
        ctk.CTkFrame(mouv_card, height=8, fg_color="transparent").pack()

    def _build_chart_repartition(self, master):
        donnees = mouvement_dao.repartition_par_service()
        fig = Figure(figsize=(4.6, 2.6), dpi=100)
        fig.patch.set_facecolor(theme.COLOR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme.COLOR_CARD)

        if donnees:
            noms = [d["nom"] for d in donnees]
            valeurs = [d["total"] for d in donnees]
            ax.barh(noms, valeurs, color=theme.COLOR_ACCENT)
            ax.tick_params(axis="both", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
        else:
            ax.text(0.5, 0.5, "Aucune donnée pour le moment", ha="center", va="center", fontsize=9)
            ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 12))