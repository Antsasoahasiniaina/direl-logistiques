"""Écran 'Rapports' — KPI, graphiques et export PDF / Excel branchés sur
reporting_service (données réelles de la DRE Haute Matsiatra).
"""

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import theme
from ui.widgets import MetricCard, HorizontalBar, StatusBadge, card
from services import reporting_service


class RapportView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self._canvas = None
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 4))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", anchor="w")
        ctk.CTkLabel(
            left, text="Rapports", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Générez et consultez les rapports d'inventaire de la DRE",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        ctk.CTkButton(
            right, text="Exporter Excel", fg_color="transparent",
            border_width=1, border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=lambda: self._exporter("xlsx"),
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            right, text="Exporter PDF", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=lambda: self._exporter("pdf"),
        ).pack(side="right")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        gen_card = card(body)
        gen_card.pack(fill="x", padx=24, pady=16)

        ctk.CTkLabel(
            gen_card, text="Génération de rapport", font=(theme.FONT_FAMILY, 15, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(16, 10))

        row = ctk.CTkFrame(gen_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 20))

        self._menu_type = self._labeled_field(
            row, "Type de rapport", list(reporting_service.TYPES_RAPPORT.keys()))
        self._menu_periode = self._labeled_field(
            row, "Période", list(reporting_service.PERIODES.keys()))
        self._menu_format = self._labeled_field(
            row, "Format", ["Détaillé", "Résumé"])
        self._menu_periode.configure(command=lambda _v: self._rafraichir_indicateurs())

        ctk.CTkButton(
            row, text="Générer le rapport", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            height=36, width=170, command=lambda: self._exporter("pdf"),
        ).pack(side="left", padx=(12, 0), pady=(18, 0))

        self._kpi_row = ctk.CTkFrame(body, fg_color="transparent")
        self._kpi_row.pack(fill="x", padx=24)
        self._kpi_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="kpi")

        charts_row = ctk.CTkFrame(body, fg_color="transparent")
        charts_row.pack(fill="x", padx=24, pady=16)
        charts_row.grid_columnconfigure(0, weight=3)
        charts_row.grid_columnconfigure(1, weight=2)

        stats_card = card(charts_row)
        stats_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            stats_card, text="Mouvements par semaine", font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 4))
        self._build_chart(stats_card)

        service_card = card(charts_row)
        service_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(
            service_card, text="Analyse par service", font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 10))
        services = reporting_service.analyse_par_service()
        if not services:
            ctk.CTkLabel(
                service_card, text="Aucun matériel réparti par service pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        for nom, pct, color, _total in services:
            HorizontalBar(service_card, nom, pct, color=color).pack(fill="x", padx=16)
        ctk.CTkFrame(service_card, height=10, fg_color="transparent").pack()

        self._hist_card = card(body)
        self._hist_card.pack(fill="x", padx=24, pady=(0, 24))

        self._rafraichir_indicateurs()
        self._construire_historique()

    def _labeled_field(self, master, label, options):
        col = ctk.CTkFrame(master, fg_color="transparent")
        col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(
            col, text=label, font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 4))
        menu = ctk.CTkOptionMenu(
            col, values=options, width=190, fg_color=theme.COLOR_BG,
            button_color=theme.COLOR_ACCENT, button_hover_color=theme.COLOR_ACCENT_HOVER,
            text_color=theme.COLOR_TEXT_PRIMARY,
        )
        menu.pack(anchor="w")
        return menu

    def _params(self):
        type_rapport = reporting_service.TYPES_RAPPORT[self._menu_type.get()]
        periode = reporting_service.PERIODES[self._menu_periode.get()]
        detaille = self._menu_format.get() == "Détaillé"
        return type_rapport, periode, detaille

    def _rafraichir_indicateurs(self):
        for enfant in self._kpi_row.winfo_children():
            enfant.destroy()
        _, periode, _ = self._params()
        kpi = reporting_service.indicateurs(periode)
        delta = kpi["delta_mouvements"]
        signe = "+" if delta >= 0 else ""
        MetricCard(
            self._kpi_row, "Matériel actif", str(kpi["materiel_actif"]),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        MetricCard(
            self._kpi_row, "Stock faible", str(kpi["stock_faible"]),
            "Désignations sous le seuil", delta_positive=kpi["stock_faible"] == 0,
        ).grid(row=0, column=1, sticky="ew", padx=8)
        MetricCard(
            self._kpi_row, "Mouvements (période)", str(kpi["mouvements_periode"]),
            f"{signe}{delta} vs mois précédent",
            delta_positive=delta >= 0,
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0))

    def _construire_historique(self):
        for enfant in self._hist_card.winfo_children():
            enfant.destroy()
        ctk.CTkLabel(
            self._hist_card, text="Derniers rapports générés", font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 6))

        historique = reporting_service.lister_historique()
        if not historique:
            ctk.CTkLabel(
                self._hist_card, text="Aucun rapport généré pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(0, 16))
            return

        for item in historique[:8]:
            row = ctk.CTkFrame(self._hist_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(
                row, text=item["nom"], font=(theme.FONT_FAMILY, 12),
                text_color=theme.COLOR_TEXT_PRIMARY, width=280, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=item["date"], font=(theme.FONT_FAMILY, 12),
                text_color=theme.COLOR_TEXT_SECONDARY, width=130, anchor="w",
            ).pack(side="left")
            StatusBadge(row, item["format"], variant="success").pack(side="left", padx=(0, 12))
            ctk.CTkButton(
                row, text="Ouvrir", width=70, height=24, fg_color="transparent",
                border_width=1, border_color=theme.COLOR_BORDER,
                text_color=theme.COLOR_TEXT_PRIMARY, hover_color=theme.COLOR_BG,
                corner_radius=theme.CORNER_RADIUS_CONTROL,
                command=lambda chemin=item["chemin"]: self._ouvrir_fichier(chemin),
            ).pack(side="right")
        ctk.CTkFrame(self._hist_card, height=8, fg_color="transparent").pack()

    def _ouvrir_fichier(self, chemin):
        if not os.path.exists(chemin):
            messagebox.showwarning("Rapport introuvable", "Le fichier n'existe plus sur le disque.")
            return
        os.startfile(chemin)

    def _exporter(self, extension):
        type_rapport, periode, detaille = self._params()
        os.makedirs(reporting_service.DOSSIER_RAPPORTS, exist_ok=True)
        nom_defaut = f"rapport_{type_rapport}_{periode}.{extension}"
        if extension == "pdf":
            chemin = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialdir=reporting_service.DOSSIER_RAPPORTS,
                initialfile=nom_defaut,
            )
            if not chemin:
                return
            try:
                reporting_service.generer_rapport_pdf(chemin, type_rapport, periode, detaille)
            except Exception as exc:
                messagebox.showerror("Export PDF", str(exc))
                return
        else:
            chemin = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialdir=reporting_service.DOSSIER_RAPPORTS,
                initialfile=nom_defaut,
            )
            if not chemin:
                return
            try:
                reporting_service.generer_rapport_excel(chemin, type_rapport, periode, detaille)
            except Exception as exc:
                messagebox.showerror("Export Excel", str(exc))
                return

        self._construire_historique()
        messagebox.showinfo("Rapport généré", f"Fichier enregistré :\n{chemin}")

    def _build_chart(self, master):
        labels, entrees, sorties = reporting_service.mouvements_hebdo()
        fig = Figure(figsize=(4.6, 2.6), dpi=100)
        fig.patch.set_facecolor(theme.COLOR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme.COLOR_CARD)

        x = range(len(labels))
        width = 0.35
        ax.bar([i - width / 2 for i in x], entrees, width, label="Affectations", color=theme.COLOR_ACCENT)
        ax.bar([i + width / 2 for i in x], sorties, width, label="Transferts / rebuts", color=theme.COLOR_INFO)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(fontsize=8, frameon=False)
        fig.tight_layout()

        self._canvas = FigureCanvasTkAgg(fig, master=master)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 12))
