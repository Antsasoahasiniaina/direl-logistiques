"""Écran 'Matériel' — liste du parc actif, avec ajout / modification /
archivage et photo justificative, plus un écran Archives pour consulter et
restaurer les matériels archivés (soft-delete, jamais de suppression réelle).
"""

import datetime
import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from config import theme
from ui.widgets import card, StatusBadge
from ui.icons import icone_boite, icone_rotation
from services import materiel_service, qr_service
from database.dao import reference_dao

STATUT_VERS_VARIANT = {"en_service": "success", "hors_service": "warning",
                        "rebut": "danger", "archive": "info"}


class MaterielView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG, **kwargs)
        self._miniatures = []  # garde les CTkImage en vie (sinon le GC les vide)
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 4))

        gauche = ctk.CTkFrame(header, fg_color="transparent")
        gauche.pack(side="left", anchor="w")
        ctk.CTkLabel(
            gauche, text="Matériel", font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            gauche, text="Parc matériel enregistré dans le système",
            font=(theme.FONT_FAMILY, 13), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        droite = ctk.CTkFrame(header, fg_color="transparent")
        droite.pack(side="right")
        ctk.CTkButton(
            droite, text="Archives", fg_color="transparent", border_width=1,
            border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            height=36, command=self._ouvrir_archives,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            droite, text="+ Ajouter un matériel", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            height=36, command=self._ouvrir_formulaire_creation,
        ).pack(side="right")

        self._liste_card = card(self)
        self._liste_card.pack(fill="both", expand=True, padx=24, pady=(16, 24))
        self._construire_liste()

    def _miniature(self, photo_path):
        """Petite vignette 32x32 si une photo existe, sinon une icône neutre."""
        taille = 32
        if photo_path and os.path.exists(photo_path):
            image_pil = Image.open(photo_path).convert("RGB").resize((taille, taille))
            ctk_img = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(taille, taille))
        else:
            ctk_img = icone_boite(theme.COLOR_TEXT_SECONDARY, taille=taille)
        self._miniatures.append(ctk_img)
        return ctk_img

    def _construire_liste(self):
        for enfant in self._liste_card.winfo_children():
            enfant.destroy()
        self._miniatures.clear()

        materiels = materiel_service.lister_materiels()

        entete = ctk.CTkFrame(self._liste_card, fg_color="transparent")
        entete.pack(fill="x", padx=16, pady=(14, 6))
        for texte, largeur in [("", 40), ("Code", 100), ("Désignation", 160), ("Service", 130),
                                ("Statut", 90), ("Acquisition", 90), ("", 270)]:
            ctk.CTkLabel(entete, text=texte, width=largeur, anchor="w",
                        font=(theme.FONT_FAMILY, 11, "bold"),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")

        if not materiels:
            ctk.CTkLabel(
                self._liste_card, text="Aucun matériel enregistré pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=16, pady=(4, 16))
            return

        zone = ctk.CTkScrollableFrame(self._liste_card, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for m in materiels:
            ligne = ctk.CTkFrame(zone, fg_color="transparent")
            ligne.pack(fill="x", pady=4)

            ctk.CTkLabel(ligne, image=self._miniature(m.get("photo_path")), text="",
                        width=40).pack(side="left")
            ctk.CTkLabel(ligne, text=m["code"], width=100, anchor="w",
                        font=(theme.FONT_FAMILY, 12, "bold"),
                        text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(ligne, text=m["designation"], width=160, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_PRIMARY).pack(side="left")
            ctk.CTkLabel(ligne, text=m["service_nom"] or "—", width=130, anchor="w",
                        font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")
            variant = STATUT_VERS_VARIANT.get(m["statut_libelle"], "info")
            StatusBadge(ligne, m["statut_libelle"].replace("_", " ").capitalize(),
                       variant=variant, width=90, anchor="w").pack(side="left")
            date_str = m["date_acquisition"].strftime("%d/%m/%Y") if m.get("date_acquisition") else "—"
            ctk.CTkLabel(ligne, text=date_str, width=90, anchor="w", font=(theme.FONT_FAMILY, 12),
                        text_color=theme.COLOR_TEXT_SECONDARY).pack(side="left")

            actions = ctk.CTkFrame(ligne, fg_color="transparent", width=270)
            actions.pack(side="left")
            ctk.CTkButton(
                actions, text="Modifier", width=80, height=28,
                fg_color="transparent", border_width=1, border_color=theme.COLOR_BORDER,
                text_color=theme.COLOR_TEXT_PRIMARY, hover_color=theme.COLOR_BG,
                corner_radius=theme.CORNER_RADIUS_CONTROL, font=(theme.FONT_FAMILY, 11),
                command=lambda mat=m: self._ouvrir_formulaire_edition(mat),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                actions, text="Imprimer", width=80, height=28,
                fg_color="transparent", border_width=1, border_color=theme.COLOR_ACCENT,
                text_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_BG,
                corner_radius=theme.CORNER_RADIUS_CONTROL, font=(theme.FONT_FAMILY, 11),
                command=lambda mat=m: self._imprimer(mat),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                actions, text="Archiver", width=80, height=28,
                fg_color="transparent", border_width=1, border_color=theme.COLOR_DANGER,
                text_color=theme.COLOR_DANGER, hover_color=theme.COLOR_DANGER_BG,
                corner_radius=theme.CORNER_RADIUS_CONTROL, font=(theme.FONT_FAMILY, 11),
                command=lambda mat=m: self._archiver(mat),
            ).pack(side="left")

    # ------------------------------------------------------------------
    def _ouvrir_formulaire_creation(self):
        FormulaireMateriel(self, on_valide=self._construire_liste)

    def _ouvrir_formulaire_edition(self, materiel):
        FormulaireMateriel(self, on_valide=self._construire_liste, materiel_existant=materiel)

    def _imprimer(self, materiel):
        try:
            qr_service.imprimer_etiquette(materiel["code"], materiel["designation"])
        except Exception as erreur:
            messagebox.showwarning(
                "Impression impossible",
                f"Impossible d'imprimer ou d'ouvrir l'étiquette : {erreur}\n\n"
                f"Vous pouvez l'ouvrir manuellement depuis :\n{qr_service.chemin_etiquette(materiel['code'])}",
            )

    def _archiver(self, materiel):
        confirme = messagebox.askyesno(
            "Archiver le matériel",
            f"Archiver {materiel['code']} — {materiel['designation']} ?\n\n"
            "Il sera masqué de la liste principale mais restera consultable "
            "et restaurable depuis les Archives. Aucune donnée n'est perdue.",
        )
        if not confirme:
            return
        materiel_service.archiver_materiel(materiel["id_materiel"])
        self._construire_liste()

    def _ouvrir_archives(self):
        FenetreArchives(self, on_restaure=self._construire_liste)


class FenetreArchives(ctk.CTkToplevel):
    """Fenêtre modale listant les matériels archivés, avec un bouton
    Restaurer pour chacun."""

    def __init__(self, master, on_restaure):
        super().__init__(master)
        self.on_restaure = on_restaure
        self.title("Matériels archivés")
        self.geometry("620x480")
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._miniatures = []
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="Matériels archivés", font=(theme.FONT_FAMILY, 17, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(
            self, text="Rien n'est jamais supprimé — restaurez un matériel à tout moment.",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._zone = ctk.CTkScrollableFrame(self, fg_color=theme.COLOR_CARD,
                                             corner_radius=theme.CORNER_RADIUS_CARD)
        self._zone.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._rafraichir()

    def _rafraichir(self):
        for enfant in self._zone.winfo_children():
            enfant.destroy()
        self._miniatures.clear()

        archives = materiel_service.lister_archives()
        if not archives:
            ctk.CTkLabel(
                self._zone, text="Aucun matériel archivé pour le moment.",
                font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w", padx=12, pady=12)
            return

        for m in archives:
            ligne = ctk.CTkFrame(self._zone, fg_color="transparent")
            ligne.pack(fill="x", padx=8, pady=6)

            bloc_texte = ctk.CTkFrame(ligne, fg_color="transparent")
            bloc_texte.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(bloc_texte, text=f"{m['code']} — {m['designation']}",
                        font=(theme.FONT_FAMILY, 12, "bold"),
                        text_color=theme.COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(bloc_texte, text=m["service_nom"] or "Aucun service",
                        font=(theme.FONT_FAMILY, 11),
                        text_color=theme.COLOR_TEXT_SECONDARY, anchor="w").pack(anchor="w")

            ctk.CTkButton(
                ligne, text="  Restaurer", image=icone_rotation(theme.COLOR_ACCENT, taille=14),
                compound="left", fg_color="transparent", border_width=1,
                border_color=theme.COLOR_ACCENT, text_color=theme.COLOR_ACCENT,
                hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
                height=30, command=lambda mat=m: self._restaurer(mat),
            ).pack(side="right")

    def _restaurer(self, materiel):
        materiel_service.restaurer_materiel(materiel["id_materiel"])
        self.on_restaure()
        self._rafraichir()


class FormulaireMateriel(ctk.CTkToplevel):
    """Fenêtre modale de création OU modification d'un matériel (édition si
    `materiel_existant` est fourni)."""

    def __init__(self, master, on_valide, materiel_existant=None):
        super().__init__(master)
        self.on_valide = on_valide
        self.materiel_existant = materiel_existant
        self.chemin_photo_source = None

        est_edition = materiel_existant is not None
        self.title("Modifier le matériel" if est_edition else "Ajouter un matériel")
        self.geometry("420x560")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)

        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._services = reference_dao.lister_services()
        self._grades = reference_dao.lister_grades()
        self._statuts = reference_dao.lister_statuts()
        self._id_statut_en_service = next(
            s["id_statut"] for s in self._statuts if s["libelle"] == "en_service"
        )

        self._build()

    def _build(self):
        conteneur = ctk.CTkFrame(self, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=20, pady=20)

        est_edition = self.materiel_existant is not None
        ctk.CTkLabel(
            conteneur, text="Modifier le matériel" if est_edition else "Nouveau matériel",
            font=(theme.FONT_FAMILY, 17, "bold"), text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkLabel(conteneur, text="Désignation", font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        self.champ_designation = ctk.CTkEntry(
            conteneur, placeholder_text="ex. Laptop Dell Latitude 5420", height=34)
        self.champ_designation.pack(fill="x", pady=(3, 12))

        ctk.CTkLabel(conteneur, text="Service", font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        noms_services = [s["nom"] for s in self._services] or ["Aucun service — créez-en un d'abord"]
        self.menu_service = ctk.CTkOptionMenu(conteneur, values=noms_services, height=34)
        self.menu_service.pack(fill="x", pady=(3, 12))

        ctk.CTkLabel(conteneur, text="Grade", font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        noms_grades = [g["libelle"] for g in self._grades] or ["—"]
        self.menu_grade = ctk.CTkOptionMenu(conteneur, values=noms_grades, height=34)
        self.menu_grade.pack(fill="x", pady=(3, 12))

        if not est_edition:
            ctk.CTkLabel(conteneur, text="Date d'acquisition (JJ/MM/AAAA)", font=(theme.FONT_FAMILY, 12),
                         text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
            self.champ_date = ctk.CTkEntry(conteneur, height=34)
            self.champ_date.insert(0, datetime.date.today().strftime("%d/%m/%Y"))
            self.champ_date.pack(fill="x", pady=(3, 12))

        ctk.CTkLabel(conteneur, text="Photo (optionnel)", font=(theme.FONT_FAMILY, 12),
                     text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")
        ligne_photo = ctk.CTkFrame(conteneur, fg_color="transparent")
        ligne_photo.pack(fill="x", pady=(3, 12))
        ctk.CTkButton(
            ligne_photo, text="Choisir une photo...", height=32, fg_color="transparent",
            border_width=1, border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=self._choisir_photo,
        ).pack(side="left")
        self.label_photo = ctk.CTkLabel(
            ligne_photo, text="Aucune photo sélectionnée", font=(theme.FONT_FAMILY, 11),
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self.label_photo.pack(side="left", padx=(10, 0))

        if est_edition:
            self.champ_designation.insert(0, self.materiel_existant["designation"])
            service_actuel = self.materiel_existant.get("service_nom")
            if service_actuel:
                self.menu_service.set(service_actuel)
            grade_actuel = self.materiel_existant.get("grade_libelle")
            if grade_actuel:
                self.menu_grade.set(grade_actuel)
            if self.materiel_existant.get("photo_path"):
                self.label_photo.configure(text="Photo actuelle conservée (sauf si vous en choisissez une autre)")

        self.label_erreur = ctk.CTkLabel(
            conteneur, text="", font=(theme.FONT_FAMILY, 11), text_color=theme.COLOR_DANGER,
            wraplength=360, justify="left",
        )
        self.label_erreur.pack(anchor="w", pady=(4, 10))

        boutons = ctk.CTkFrame(conteneur, fg_color="transparent")
        boutons.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(
            boutons, text="Annuler", fg_color="transparent", border_width=1,
            border_color=theme.COLOR_BORDER, text_color=theme.COLOR_TEXT_PRIMARY,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            boutons, text="Enregistrer" if est_edition else "Créer",
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
            corner_radius=theme.CORNER_RADIUS_CONTROL, command=self._valider,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _choisir_photo(self):
        chemin = filedialog.askopenfilename(
            title="Choisir une photo du matériel",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")],
        )
        if chemin:
            self.chemin_photo_source = chemin
            self.label_photo.configure(text=os.path.basename(chemin))

    def _valider(self):
        designation = self.champ_designation.get().strip()
        if not designation:
            self.label_erreur.configure(text="La désignation est obligatoire.")
            return
        if not self._services:
            self.label_erreur.configure(text="Aucun service n'existe — créez-en un dans Paramètres.")
            return

        service_choisi = self.menu_service.get()
        id_service = next((s["id_service"] for s in self._services if s["nom"] == service_choisi), None)
        grade_choisi = self.menu_grade.get()
        id_grade = next((g["id_grade"] for g in self._grades if g["libelle"] == grade_choisi), None)

        if self.materiel_existant is not None:
            try:
                materiel_service.modifier_materiel(
                    self.materiel_existant["id_materiel"], designation, id_service, id_grade,
                    chemin_photo_source=self.chemin_photo_source,
                )
            except Exception as erreur:
                self.label_erreur.configure(text=f"Erreur lors de l'enregistrement : {erreur}")
                return
            self.on_valide()
            self.destroy()
            return

        try:
            date_acquisition = datetime.datetime.strptime(
                self.champ_date.get().strip(), "%d/%m/%Y").date()
        except ValueError:
            self.label_erreur.configure(text="Date invalide — format attendu : JJ/MM/AAAA.")
            return

        try:
            resultat = materiel_service.creer_materiel(
                designation, id_service, id_grade, self._id_statut_en_service,
                date_acquisition=date_acquisition, chemin_photo_source=self.chemin_photo_source,
            )
        except Exception as erreur:
            self.label_erreur.configure(text=f"Erreur lors de la création : {erreur}")
            return

        self.on_valide()
        self._afficher_succes(resultat)

    def _afficher_succes(self, resultat):
        for enfant in self.winfo_children():
            enfant.destroy()

        conteneur = ctk.CTkFrame(self, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            conteneur, text="✓ Matériel créé", font=(theme.FONT_FAMILY, 17, "bold"),
            text_color=theme.COLOR_SUCCESS,
        ).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(
            conteneur, text=f"Code généré : {resultat['code']}",
            font=(theme.FONT_FAMILY, 14, "bold"), text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            conteneur, text=f"Étiquette QR enregistrée dans :\n{resultat['etiquette']}",
            font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=360, justify="left",
        ).pack(anchor="w", pady=(8, 8))

        if self.chemin_photo_source:
            if resultat.get("photo"):
                ctk.CTkLabel(
                    conteneur, text=f"✓ Photo enregistrée dans :\n{resultat['photo']}",
                    font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_SUCCESS,
                    wraplength=360, justify="left",
                ).pack(anchor="w", pady=(0, 12))
            else:
                ctk.CTkLabel(
                    conteneur, text="⚠ Une photo avait été choisie mais n'a pas été enregistrée.",
                    font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_WARNING,
                    wraplength=360, justify="left",
                ).pack(anchor="w", pady=(0, 12))

        boutons = ctk.CTkFrame(conteneur, fg_color="transparent")
        boutons.pack(fill="x")
        ctk.CTkButton(
            boutons, text="Imprimer l'étiquette", fg_color="transparent", border_width=1,
            border_color=theme.COLOR_ACCENT, text_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_BG, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=lambda: self._imprimer_depuis_succes(resultat["code"], resultat["designation"]),
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            boutons, text="Fermer", fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, corner_radius=theme.CORNER_RADIUS_CONTROL,
            command=self.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _imprimer_depuis_succes(self, code, designation):
        try:
            qr_service.imprimer_etiquette(code, designation)
        except Exception as erreur:
            messagebox.showwarning(
                "Impression impossible",
                f"Impossible d'imprimer ou d'ouvrir l'étiquette : {erreur}\n\n"
                f"Vous pouvez l'ouvrir manuellement depuis :\n{qr_service.chemin_etiquette(code)}",
            )