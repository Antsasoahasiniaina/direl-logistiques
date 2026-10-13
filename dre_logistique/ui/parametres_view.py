"""Écran 'Paramètres' — adapté de la maquette DRE Logistics fournie, avec les
notions propres au projet : services, grades, statuts de matériel, comptes
utilisateurs (3 rôles) et sauvegarde locale (mode hors ligne).

TODO intégration réelle :
- les listes SAMPLE_* viennent des DAO (service_dao, grade_dao, utilisateur_dao)
- le bouton "Lancer une sauvegarde" appelle un service d'export pg_dump
"""

import customtkinter as ctk

from config import theme
from ui.widgets import StatusBadge, card

SAMPLE_SERVICES = [
    ("Éducation fondamentale", 96, "success"),
    ("Enseignement secondaire", 74, "success"),
    ("Administration", 41, "success"),
    ("Maintenance", 12, "warning"),
]

SAMPLE_GRADES = [
    ("Grade A", 58),
    ("Grade B", 121),
    ("Grade C", 133),
]

SAMPLE_UTILISATEURS = [
    ("Rakoto H.", "rakoto.h@dre-hautematsiatra.mg", "Admin DRE"),
    ("Rasoa M.", "rasoa.m@dre-hautematsiatra.mg", "Chef de service"),
]


class ParametresView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self._build()

    def _build(self):
        # -- En-tête ---------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 4))
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", anchor="w")
        ctk.CTkLabel(
            left, text="Paramètres", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text="Configuration générale du logiciel DRE Haute Matsiatra",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")
        ctk.CTkButton(
            header, text="Sauvegarder les modifications", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
        ).pack(side="right")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        self._section_services(body)
        self._section_grades(body)
        self._section_utilisateurs(body)
        self._section_sauvegarde(body)

    # ------------------------------------------------------------------
    def _section_header(self, master, title, subtitle, with_toggle=True):
        c = card(master)
        c.pack(fill="x", pady=(0, 14))
        top = ctk.CTkFrame(c, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 4))
        text_col = ctk.CTkFrame(top, fg_color="transparent")
        text_col.pack(side="left", anchor="w")
        ctk.CTkLabel(text_col, text=title, font=(theme.FONT_FAMILY, 15, "bold"),
                     text_color=theme.COLOR_TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(text_col, text=subtitle, font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        if with_toggle:
            ctk.CTkSwitch(top, text="", progress_color=theme.COLOR_ACCENT).pack(side="right")
        return c

    def _section_services(self, master):
        c = self._section_header(master, "Gestion des services",
                                  "Services rattachés à la DRE Haute Matsiatra")
        for nom, nb_materiel, variant in SAMPLE_SERVICES:
            row = ctk.CTkFrame(c, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text=nom, font=(theme.FONT_FAMILY, 12),
                         text_color=theme.COLOR_TEXT_PRIMARY, anchor="w", width=220).pack(side="left")
            ctk.CTkLabel(row, text=f"{nb_materiel} matériels", font=(theme.FONT_FAMILY, 12),
                         text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left", padx=(0, 12))
            StatusBadge(row, "Actif", variant=variant).pack(side="left")
        ctk.CTkButton(c, text="+ Ajouter un service", fg_color="transparent", border_width=1,
                      border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
                      hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
                      height=30).pack(anchor="w", padx=18, pady=(6, 16))

    def _section_grades(self, master):
        c = self._section_header(master, "Grades et statuts",
                                  "Niveaux de grade utilisés pour classer le matériel",
                                  with_toggle=False)
        for nom, nb in SAMPLE_GRADES:
            row = ctk.CTkFrame(c, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text=nom, font=(theme.FONT_FAMILY, 12),
                         text_color=theme.COLOR_TEXT_PRIMARY, anchor="w", width=220).pack(side="left")
            ctk.CTkLabel(row, text=f"{nb} matériels", font=(theme.FONT_FAMILY, 12),
                         text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
            ctk.CTkButton(row, text="Modifier", fg_color="transparent", text_color=theme.COLOR_ACCENT,
                          hover_color=theme.COLOR_BG, width=70, height=24).pack(side="right")
        ctk.CTkFrame(c, height=10, fg_color="transparent").pack()

    def _section_utilisateurs(self, master):
        c = self._section_header(master, "Comptes utilisateurs",
                                  "Comptes Admin DRE et Chef de service", with_toggle=False)
        for nom, email, role in SAMPLE_UTILISATEURS:
            row = ctk.CTkFrame(c, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=6)
            avatar = ctk.CTkLabel(
                row, text=nom[0], width=32, height=32, corner_radius=16,
                fg_color=theme.COLOR_ACCENT, text_color="white", font=(theme.FONT_FAMILY, 13, "bold"),
            )
            avatar.pack(side="left", padx=(0, 10))
            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left")
            ctk.CTkLabel(text_col, text=nom, font=(theme.FONT_FAMILY, 12, "bold"),
                         text_color=theme.COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(text_col, text=email, font=(theme.FONT_FAMILY, 11),
                         text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(anchor="w")
            StatusBadge(row, role, variant="info").pack(side="right")
        ctk.CTkButton(c, text="+ Ajouter un utilisateur", fg_color="transparent", border_width=1,
                      border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
                      hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
                      height=30).pack(anchor="w", padx=18, pady=(6, 16))

    def _section_sauvegarde(self, master):
        c = self._section_header(master, "Sauvegarde locale",
                                  "Le logiciel fonctionne hors ligne : pensez à exporter régulièrement",
                                  with_toggle=False)
        info = ctk.CTkFrame(c, fg_color="transparent")
        info.pack(fill="x", padx=18, pady=(0, 6))
        ctk.CTkLabel(info, text="Dernière sauvegarde : 22/09/2026 à 09:14",
                     font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        btn_row = ctk.CTkFrame(c, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(6, 16))
        ctk.CTkButton(btn_row, text="Lancer une sauvegarde maintenant", fg_color=theme.COLOR_ACCENT,
                      hover_color=theme.COLOR_ACCENT_HOVER,
                      corner_radius=theme.CORNER_RADIUS_CONTROL).pack(side="left")
        ctk.CTkButton(btn_row, text="Restaurer une sauvegarde", fg_color="transparent", border_width=1,
                      border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
                      hover_color=theme.COLOR_BG,
                      corner_radius=theme.CORNER_RADIUS_CONTROL).pack(side="left", padx=(10, 0))
