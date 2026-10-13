"""Écran 'Scan QR' — caméra réelle (OpenCV + pyzbar) pour identifier un
matériel, avec les 4 types de mouvement (UC7 à UC11) réellement câblés sur
la couche métier, et un historique des mouvements récents basé sur de
vraies données.

Repli : si aucune caméra n'est détectée (ou si le matériel ne dispose pas
de webcam), un champ de saisie manuelle du code permet de continuer à
travailler — c'est le scénario alternatif prévu dans le diagramme de cas
d'utilisation (UC7).
"""

import cv2
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

from config import theme
from ui.widgets import MetricCard, StatusBadge, card
from services import materiel_service, mouvement_service, qr_service
from database.dao import reference_dao

TYPE_VERS_VARIANT = {"affectation": "info", "transfert": "success",
                     "remplacement": "warning", "rebut": "danger"}

INTERVALLE_FRAME_MS = 200  # ~5 images/seconde : largement suffisant pour un QR immobile


class ScanView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self.camera = None
        self.after_id = None
        self.materiel_detecte = None
        self.dernier_code_lu = None

        self.bind("<Destroy>", self._nettoyer, add="+")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._build_scan_section(body)
        self._build_mouvements_section(body)
        self._demarrer_camera()

    # ------------------------------------------------------------------
    # Section scan
    # ------------------------------------------------------------------
    def _build_scan_section(self, master):
        ctk.CTkLabel(
            master, text="Scan QR code", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(24, 12))

        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=24)
        row.grid_columnconfigure((0, 1), weight=1, uniform="scan")

        # -- Caméra ------------------------------------------------------
        cam_card = card(row)
        cam_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.camera_label = ctk.CTkLabel(
            cam_card, text="Connexion à la caméra...", height=260,
            fg_color=theme.COLOR_BG, text_color=theme.COLOR_TEXT_SECONDARY,
            corner_radius=theme.CORNER_RADIUS_CONTROL,
        )
        self.camera_label.pack(fill="both", expand=True, padx=16, pady=16)
        self.label_statut_camera = ctk.CTkLabel(
            cam_card, text="Présentez le QR code du matériel à la caméra",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self.label_statut_camera.pack(anchor="w", padx=16, pady=(0, 10))

        ligne_manuelle = ctk.CTkFrame(cam_card, fg_color="transparent")
        ligne_manuelle.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(
            ligne_manuelle, text="Pas de caméra ? Saisissez le code :",
            font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")
        sous_ligne = ctk.CTkFrame(ligne_manuelle, fg_color="transparent")
        sous_ligne.pack(fill="x", pady=(4, 0))
        self.champ_code_manuel = ctk.CTkEntry(sous_ligne, placeholder_text="ex. MAT-LAP-0001", height=32)
        self.champ_code_manuel.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.champ_code_manuel.bind("<Return>", lambda e: self._rechercher_code_manuel())
        ctk.CTkButton(
            sous_ligne, text="Rechercher", height=32, width=100, fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=self._rechercher_code_manuel,
        ).pack(side="left")

        # -- Fiche matériel détecté ------------------------------------------
        self.detail_card = card(row)
        self.detail_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._afficher_aucun_materiel()

    def _afficher_aucun_materiel(self):
        for enfant in self.detail_card.winfo_children():
            enfant.destroy()
        ctk.CTkLabel(
            self.detail_card, text="En attente d'un QR code...",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(expand=True, pady=60)

    def _afficher_materiel(self, m):
        self.materiel_detecte = m
        for enfant in self.detail_card.winfo_children():
            enfant.destroy()

        ctk.CTkLabel(
            self.detail_card, text="✓ Matériel détecté", font=(theme.FONT_FAMILY, 12, "bold"),
            text_color=theme.COLOR_SUCCESS,
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            self.detail_card, text=m["code"], font=(theme.FONT_FAMILY, 16, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16)
        ctk.CTkLabel(
            self.detail_card, text=m["designation"], font=(theme.FONT_FAMILY, 12),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        for label, valeur in [("Service", m.get("service_nom") or "Aucun"),
                               ("Grade", m.get("grade_libelle") or "—"),
                               ("Statut", (m.get("statut_libelle") or "").replace("_", " ").capitalize())]:
            ligne = ctk.CTkFrame(self.detail_card, fg_color="transparent")
            ligne.pack(fill="x", padx=16)
            ctk.CTkLabel(ligne, text=label, font=(theme.FONT_FAMILY, 12),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
            ctk.CTkLabel(ligne, text=valeur, font=(theme.FONT_FAMILY, 12),
                        text_color=theme.COLOR_TEXT_PRIMARY).pack(side="right")

        if m.get("statut_libelle") == "archive":
            ctk.CTkLabel(
                self.detail_card, text="Ce matériel est archivé — restaurez-le\ndepuis l'écran Matériel avant de le mouvoir.",
                font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_WARNING, justify="left",
            ).pack(anchor="w", padx=16, pady=(10, 16))
            return

        ctk.CTkLabel(
            self.detail_card, text="Type de mouvement", font=(theme.FONT_FAMILY, 12),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(14, 6))

        btn_grid = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=16, pady=(0, 16))
        btn_grid.grid_columnconfigure((0, 1), weight=1)
        boutons = [
            ("Affectation", lambda: self._ouvrir_modal("affectation")),
            ("Transfert", lambda: self._ouvrir_modal("transfert")),
            ("Remplacement", lambda: self._ouvrir_modal("remplacement")),
            ("Rebut", lambda: self._ouvrir_modal("rebut")),
        ]
        for i, (label, cmd) in enumerate(boutons):
            ctk.CTkButton(
                btn_grid, text=label, height=34, fg_color="transparent",
                text_color=theme.COLOR_TEXT_PRIMARY, border_width=1, border_color=theme.COLOR_BORDER,
                hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
                command=cmd,
            ).grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4)

    def _ouvrir_modal(self, type_mouvement):
        ModalMouvement(self, self.materiel_detecte, type_mouvement, on_succes=self._apres_mouvement)

    def _apres_mouvement(self):
        self._afficher_aucun_materiel()
        self.materiel_detecte = None
        self.dernier_code_lu = None
        self._rafraichir_mouvements()

    # ------------------------------------------------------------------
    # Caméra
    # ------------------------------------------------------------------
    def _demarrer_camera(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.camera = None
            self.camera_label.configure(text="Aucune caméra détectée.\nUtilisez la saisie manuelle ci-dessous.")
            return
        self._boucle_camera()

    def _boucle_camera(self):
        if self.camera is None:
            return
        ok, frame = self.camera.read()
        if ok:
            # Affichage du flux
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(frame_rgb)
            image_pil.thumbnail((480, 360))
            ctk_image = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=image_pil.size)
            self.camera_label.configure(image=ctk_image, text="")
            self._image_camera_courante = ctk_image  # évite le garbage-collect

            # Décodage du QR sur l'image en niveaux de gris
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            codes = qr_service.decoder_image(gris)
            if codes and codes[0] != self.dernier_code_lu:
                self.dernier_code_lu = codes[0]
                self._traiter_code(codes[0])

        self.after_id = self.after(INTERVALLE_FRAME_MS, self._boucle_camera)

    def _nettoyer(self, event=None):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    # ------------------------------------------------------------------
    # Recherche (caméra ou saisie manuelle)
    # ------------------------------------------------------------------
    def _rechercher_code_manuel(self):
        code = self.champ_code_manuel.get().strip()
        if code:
            self._traiter_code(code)

    def _traiter_code(self, code):
        m = materiel_service.rechercher_par_qr(code)
        if m is None:
            self.label_statut_camera.configure(
                text=f"Aucun matériel trouvé pour le code « {code} ».",
                text_color=theme.COLOR_DANGER,
            )
            return
        self.label_statut_camera.configure(
            text="Présentez le QR code du matériel à la caméra",
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self._afficher_materiel(m)

    # ------------------------------------------------------------------
    # Section mouvements récents
    # ------------------------------------------------------------------
    def _build_mouvements_section(self, master):
        ctk.CTkLabel(
            master, text="Mouvements récents", font=(theme.FONT_FAMILY, 18, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(28, 12))

        self.stats_row = ctk.CTkFrame(master, fg_color="transparent")
        self.stats_row.pack(fill="x", padx=24)

        self.table_card = card(master)
        self.table_card.pack(fill="x", padx=24, pady=16)

        self._rafraichir_mouvements()

    def _rafraichir_mouvements(self):
        for enfant in self.stats_row.winfo_children():
            enfant.destroy()
        self.stats_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="stats")

        MetricCard(self.stats_row, "Aujourd'hui", str(mouvement_service.compter_aujourdhui())).grid(
            row=0, column=0, sticky="ew", padx=(0, 8))
        MetricCard(self.stats_row, "Cette semaine", str(mouvement_service.compter_cette_semaine())).grid(
            row=0, column=1, sticky="ew", padx=8)
        MetricCard(self.stats_row, "Ce mois", str(mouvement_service.compter_ce_mois())).grid(
            row=0, column=2, sticky="ew", padx=(8, 0))

        for enfant in self.table_card.winfo_children():
            enfant.destroy()

        mouvements = mouvement_service.mouvements_recents(limite=15)
        header_row = ctk.CTkFrame(self.table_card, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(14, 6))
        for text, w in [("Matériel", 200), ("Type", 100), ("De service", 140),
                        ("Vers service", 140), ("Agent", 120), ("Date", 110)]:
            ctk.CTkLabel(header_row, text=text, width=w, anchor="w",
                        font=(theme.FONT_FAMILY, 11, "bold"),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")

        if not mouvements:
            ctk.CTkLabel(
                self.table_card, text="Aucun mouvement enregistré pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(0, 16))
            return

        for mv in mouvements:
            row = ctk.CTkFrame(self.table_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            mat_col = ctk.CTkFrame(row, fg_color="transparent", width=200)
            mat_col.pack(side="left")
            mat_col.pack_propagate(False)
            ctk.CTkLabel(mat_col, text=mv["code"], font=(theme.FONT_FAMILY, 12, "bold"),
                        text_color=theme.COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(mat_col, text=mv["designation"], font=(theme.FONT_FAMILY, 11),
                        text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(anchor="w")

            variant = TYPE_VERS_VARIANT.get(mv["type_mouvement"], "info")
            badge_col = ctk.CTkFrame(row, width=100, fg_color="transparent")
            badge_col.pack(side="left")
            StatusBadge(badge_col, mv["type_mouvement"].capitalize(), variant=variant).pack(anchor="w")

            ctk.CTkLabel(row, text=mv["service_source_nom"] or "—", width=140, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(row, text=mv["service_dest_nom"] or "—", width=140, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(row, text=f"{mv['agent_prenom']} {mv['agent_nom']}", width=120, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
            ctk.CTkLabel(row, text=mv["date_mouvement"].strftime("%d/%m/%Y %H:%M"), width=110, anchor="w",
                        font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
        ctk.CTkFrame(self.table_card, height=8, fg_color="transparent").pack()


class ModalMouvement(ctk.CTkToplevel):
    """Fenêtre modale demandant les informations nécessaires selon le type
    de mouvement, puis exécute l'action via mouvement_service."""

    TITRES = {
        "affectation": "Affecter le matériel à un service",
        "transfert": "Transférer le matériel",
        "remplacement": "Remplacer le matériel",
        "rebut": "Mettre le matériel au rebut",
    }

    def __init__(self, master, materiel, type_mouvement, on_succes):
        super().__init__(master)
        self.materiel = materiel
        self.type_mouvement = type_mouvement
        self.on_succes = on_succes

        self.title(self.TITRES[type_mouvement])
        self.geometry("420x400")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._build()

    def _build(self):
        conteneur = ctk.CTkFrame(self, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            conteneur, text=self.TITRES[self.type_mouvement], font=(theme.FONT_FAMILY, 15, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY, wraplength=360,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            conteneur, text=f"{self.materiel['code']} — {self.materiel['designation']}",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 6))

        # Service actuel affiché dans tous les cas (affectation, transfert,
        # remplacement, rebut) : le contexte aide l'agent à vérifier qu'il
        # manipule le bon matériel avant de valider.
        ligne_service_actuel = ctk.CTkFrame(conteneur, fg_color="transparent")
        ligne_service_actuel.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(ligne_service_actuel, text="Service actuel", font=(theme.FONT_FAMILY, 12),
                    text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(ligne_service_actuel, text=self.materiel.get("service_nom") or "Aucun",
                    font=(theme.FONT_FAMILY, 12, "bold"), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="right")

        self.menu_service_dest = None
        self.menu_materiel_remplacant = None

        if self.type_mouvement in ("affectation", "transfert"):
            services = reference_dao.lister_services()
            if self.type_mouvement == "transfert":
                # On ne propose pas le service actuel comme destination :
                # un transfert change forcément de service.
                services = [s for s in services if s["nom"] != self.materiel.get("service_nom")]
            self._services = services
            noms = [s["nom"] for s in services] or ["Aucun autre service disponible"]
            ctk.CTkLabel(conteneur, text="Service destination", font=(theme.FONT_FAMILY, 12),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
            self.menu_service_dest = ctk.CTkOptionMenu(conteneur, values=noms, height=34)
            self.menu_service_dest.pack(fill="x", pady=(3, 12))

        if self.type_mouvement == "remplacement":
            candidats = [m for m in materiel_service.lister_materiels()
                        if m["id_materiel"] != self.materiel["id_materiel"]
                        and m["statut_libelle"] == "en_service"]
            self._candidats = candidats
            noms = [f"{m['code']} — {m['designation']}" for m in candidats] or ["Aucun matériel disponible"]
            ctk.CTkLabel(conteneur, text="Matériel remplaçant", font=(theme.FONT_FAMILY, 12),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
            self.menu_materiel_remplacant = ctk.CTkOptionMenu(conteneur, values=noms, height=34)
            self.menu_materiel_remplacant.pack(fill="x", pady=(3, 12))

        ctk.CTkLabel(conteneur, text="Commentaire (optionnel)", font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.champ_commentaire = ctk.CTkEntry(conteneur, height=34)
        self.champ_commentaire.pack(fill="x", pady=(3, 12))

        self.label_erreur = ctk.CTkLabel(
            conteneur, text="", font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_DANGER,
            wraplength=360, justify="left",
        )
        self.label_erreur.pack(anchor="w", pady=(4, 10))

        boutons = ctk.CTkFrame(conteneur, fg_color="transparent")
        boutons.pack(fill="x", side="bottom", pady=(6, 0))
        ctk.CTkButton(
            boutons, text="Annuler", fg_color="transparent", border_width=1,
            border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            boutons, text="Confirmer", fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS_CONTROL, command=self._confirmer,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _confirmer(self):
        commentaire = self.champ_commentaire.get().strip()
        try:
            if self.type_mouvement == "affectation":
                id_service = self._id_service_choisi()
                mouvement_service.affecter(self.materiel["id_materiel"], id_service, commentaire)

            elif self.type_mouvement == "transfert":
                id_service_dest = self._id_service_choisi()
                mouvement_service.transferer(
                    self.materiel["id_materiel"], self.materiel.get("id_service"),
                    id_service_dest, commentaire,
                )

            elif self.type_mouvement == "remplacement":
                if not getattr(self, "_candidats", None):
                    self.label_erreur.configure(text="Aucun matériel disponible pour le remplacement.")
                    return
                index = self.menu_materiel_remplacant.cget("values").index(self.menu_materiel_remplacant.get())
                id_nouveau = self._candidats[index]["id_materiel"]
                mouvement_service.remplacer(self.materiel["id_materiel"], id_nouveau, commentaire)

            elif self.type_mouvement == "rebut":
                confirme = messagebox.askyesno(
                    "Confirmer la mise au rebut",
                    f"Mettre {self.materiel['code']} au rebut ? Cette action change son statut "
                    "définitivement (il restera consultable dans l'historique).",
                )
                if not confirme:
                    return
                mouvement_service.mettre_au_rebut(self.materiel["id_materiel"], commentaire)

        except Exception as erreur:
            self.label_erreur.configure(text=f"Erreur : {erreur}")
            return

        self.on_succes()
        self.destroy()

    def _id_service_choisi(self):
        nom = self.menu_service_dest.get()
        return next(s["id_service"] for s in self._services if s["nom"] == nom)