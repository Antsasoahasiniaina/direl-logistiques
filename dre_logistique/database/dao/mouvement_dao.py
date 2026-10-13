from database.connexion import executer


def creer(type_mouvement, id_materiel, id_utilisateur, id_service_source=None,
          id_service_dest=None, commentaire=""):
    return executer(
        """INSERT INTO mouvement (type_mouvement, id_materiel, id_utilisateur,
                                    id_service_source, id_service_dest, commentaire)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_mouvement""",
        (type_mouvement, id_materiel, id_utilisateur, id_service_source,
         id_service_dest, commentaire),
        fetch="one",
    )


def historique_materiel(id_materiel):
    return executer(
        """SELECT mv.*, u.nom AS agent_nom, u.prenom AS agent_prenom,
                  ss.nom AS service_source_nom, sd.nom AS service_dest_nom
           FROM mouvement mv
           JOIN utilisateur u ON u.id_utilisateur = mv.id_utilisateur
           LEFT JOIN service ss ON ss.id_service = mv.id_service_source
           LEFT JOIN service sd ON sd.id_service = mv.id_service_dest
           WHERE mv.id_materiel = %s
           ORDER BY mv.date_mouvement DESC""",
        (id_materiel,), fetch="all",
    )


def lister_recents(limite=20):
    return executer(
        """SELECT mv.*, m.code, m.designation,
                  u.nom AS agent_nom, u.prenom AS agent_prenom,
                  ss.nom AS service_source_nom, sd.nom AS service_dest_nom
           FROM mouvement mv
           JOIN materiel m ON m.id_materiel = mv.id_materiel
           JOIN utilisateur u ON u.id_utilisateur = mv.id_utilisateur
           LEFT JOIN service ss ON ss.id_service = mv.id_service_source
           LEFT JOIN service sd ON sd.id_service = mv.id_service_dest
           ORDER BY mv.date_mouvement DESC LIMIT %s""",
        (limite,), fetch="all",
    )


def compter_ce_mois():
    return executer(
        """SELECT COUNT(*) AS n FROM mouvement
           WHERE date_trunc('month', date_mouvement) = date_trunc('month', now())""",
        fetch="one",
    )["n"]


def compter_aujourdhui():
    return executer(
        """SELECT COUNT(*) AS n FROM mouvement
           WHERE date_trunc('day', date_mouvement) = date_trunc('day', now())""",
        fetch="one",
    )["n"]


def compter_cette_semaine():
    return executer(
        """SELECT COUNT(*) AS n FROM mouvement
           WHERE date_trunc('week', date_mouvement) = date_trunc('week', now())""",
        fetch="one",
    )["n"]


def compter_mois_precedent():
    return executer(
        """SELECT COUNT(*) AS n FROM mouvement
           WHERE date_trunc('month', date_mouvement)
                 = date_trunc('month', now() - interval '1 month')""",
        fetch="one",
    )["n"]


def compter_entre(debut, fin):
    return executer(
        """SELECT COUNT(*) AS n FROM mouvement
           WHERE date_mouvement >= %s AND date_mouvement < %s""",
        (debut, fin), fetch="one",
    )["n"]


def lister_entre(debut, fin, limite=2000):
    return executer(
        """SELECT mv.*, m.code, m.designation,
                  u.nom AS agent_nom, u.prenom AS agent_prenom,
                  ss.nom AS service_source_nom, sd.nom AS service_dest_nom
           FROM mouvement mv
           JOIN materiel m ON m.id_materiel = mv.id_materiel
           JOIN utilisateur u ON u.id_utilisateur = mv.id_utilisateur
           LEFT JOIN service ss ON ss.id_service = mv.id_service_source
           LEFT JOIN service sd ON sd.id_service = mv.id_service_dest
           WHERE mv.date_mouvement >= %s AND mv.date_mouvement < %s
           ORDER BY mv.date_mouvement DESC
           LIMIT %s""",
        (debut, fin, limite), fetch="all",
    )


def par_semaine(nb_semaines=5):
    """Affectations (entrées) vs transferts/rebuts (sorties) sur N semaines."""
    return executer(
        """SELECT date_trunc('week', date_mouvement)::date AS semaine,
                  COUNT(*) FILTER (WHERE type_mouvement = 'affectation') AS entrees,
                  COUNT(*) FILTER (WHERE type_mouvement IN ('rebut', 'transfert')) AS sorties
           FROM mouvement
           WHERE date_mouvement >= date_trunc('week', now())
                                 - (%s - 1) * interval '1 week'
           GROUP BY 1
           ORDER BY 1""",
        (nb_semaines,), fetch="all",
    )


def repartition_par_service():
    return executer(
        """SELECT s.nom, COUNT(m.id_materiel) AS total
           FROM service s LEFT JOIN materiel m ON m.id_service = s.id_service
           GROUP BY s.nom ORDER BY total DESC""",
        fetch="all",
    )
