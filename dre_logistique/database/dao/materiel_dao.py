from database.connexion import executer


def creer(code, designation, qr_code, date_acquisition, id_service, id_grade, id_statut):
    return executer(
        """INSERT INTO materiel (code, designation, qr_code, date_acquisition,
                                  id_service, id_grade, id_statut)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_materiel""",
        (code, designation, qr_code, date_acquisition, id_service, id_grade, id_statut),
        fetch="one",
    )


def trouver_par_qr(qr_code):
    return executer(
        """SELECT m.*, s.nom AS service_nom, g.libelle AS grade_libelle,
                  st.libelle AS statut_libelle
           FROM materiel m
           LEFT JOIN service s ON s.id_service = m.id_service
           LEFT JOIN grade g ON g.id_grade = m.id_grade
           LEFT JOIN statut st ON st.id_statut = m.id_statut
           WHERE m.qr_code = %s""",
        (qr_code,), fetch="one",
    )


def trouver_par_id(id_materiel):
    return executer(
        """SELECT m.*, s.nom AS service_nom, g.libelle AS grade_libelle,
                  st.libelle AS statut_libelle
           FROM materiel m
           LEFT JOIN service s ON s.id_service = m.id_service
           LEFT JOIN grade g ON g.id_grade = m.id_grade
           LEFT JOIN statut st ON st.id_statut = m.id_statut
           WHERE m.id_materiel = %s""",
        (id_materiel,), fetch="one",
    )


def lister(limite=200):
    """Liste le matériel actif (exclut les matériels archivés)."""
    return executer(
        """SELECT m.*, s.nom AS service_nom, st.libelle AS statut_libelle
           FROM materiel m
           LEFT JOIN service s ON s.id_service = m.id_service
           LEFT JOIN statut st ON st.id_statut = m.id_statut
           WHERE st.libelle IS DISTINCT FROM 'archive'
           ORDER BY m.id_materiel DESC LIMIT %s""",
        (limite,), fetch="all",
    )


def lister_archives(limite=200):
    """Liste uniquement les matériels archivés (soft-delete)."""
    return executer(
        """SELECT m.*, s.nom AS service_nom, st.libelle AS statut_libelle
           FROM materiel m
           LEFT JOIN service s ON s.id_service = m.id_service
           LEFT JOIN statut st ON st.id_statut = m.id_statut
           WHERE st.libelle = 'archive'
           ORDER BY m.id_materiel DESC LIMIT %s""",
        (limite,), fetch="all",
    )


def compter_actifs():
    return executer(
        """SELECT COUNT(*) AS n FROM materiel m
           JOIN statut s ON s.id_statut = m.id_statut
           WHERE s.libelle = 'en_service'""",
        fetch="one",
    )["n"]


def mettre_a_jour_service(id_materiel, id_service):
    executer(
        "UPDATE materiel SET id_service = %s WHERE id_materiel = %s",
        (id_service, id_materiel),
    )


def mettre_a_jour_statut(id_materiel, id_statut, id_materiel_remplacant=None):
    executer(
        "UPDATE materiel SET id_statut = %s, id_materiel_remplacant = %s WHERE id_materiel = %s",
        (id_statut, id_materiel_remplacant, id_materiel),
    )


def mettre_a_jour(id_materiel, designation, id_service, id_grade):
    executer(
        "UPDATE materiel SET designation = %s, id_service = %s, id_grade = %s WHERE id_materiel = %s",
        (designation, id_service, id_grade, id_materiel),
    )


def mettre_a_jour_photo(id_materiel, photo_path):
    executer(
        "UPDATE materiel SET photo_path = %s WHERE id_materiel = %s",
        (photo_path, id_materiel),
    )


def compter_mouvements(id_materiel):
    return executer(
        "SELECT COUNT(*) AS n FROM mouvement WHERE id_materiel = %s",
        (id_materiel,), fetch="one",
    )["n"]


def archiver(id_materiel, id_statut_archive):
    """Bascule le matériel vers le statut 'archive' (soft-delete) — ne
    supprime jamais la ligne, préserve la traçabilité et l'historique."""
    executer(
        "UPDATE materiel SET id_statut = %s WHERE id_materiel = %s",
        (id_statut_archive, id_materiel),
    )


def restaurer(id_materiel, id_statut_cible):
    executer(
        "UPDATE materiel SET id_statut = %s WHERE id_materiel = %s",
        (id_statut_cible, id_materiel),
    )


def supprimer(id_materiel):
    """Suppression physique — conservée pour un usage interne éventuel,
    mais n'est plus utilisée depuis l'écran Matériel (remplacée par
    archiver(), qui préserve la traçabilité)."""
    executer("DELETE FROM materiel WHERE id_materiel = %s", (id_materiel,))