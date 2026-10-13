from database.connexion import executer


def creer(type_alerte, message, niveau_risque, id_materiel=None):
    return executer(
        """INSERT INTO alerte (type_alerte, message, niveau_risque, id_materiel)
           VALUES (%s, %s, %s, %s) RETURNING id_alerte""",
        (type_alerte, message, niveau_risque, id_materiel), fetch="one",
    )


def lister_actives(limite=50):
    return executer(
        """SELECT a.*, m.code, m.designation
           FROM alerte a LEFT JOIN materiel m ON m.id_materiel = a.id_materiel
           ORDER BY
               CASE a.niveau_risque WHEN 'eleve' THEN 0 WHEN 'moyen' THEN 1 ELSE 2 END,
               a.date_generation DESC
           LIMIT %s""",
        (limite,), fetch="all",
    )


def vider():
    """Supprime les anciennes alertes avant de recalculer (le module de
    prédiction régénère l'ensemble à chaque exécution plutôt que de les
    mettre à jour une à une)."""
    executer("DELETE FROM alerte")
