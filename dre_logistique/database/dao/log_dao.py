from database.connexion import executer


def journaliser(id_utilisateur, action, cible=""):
    executer(
        "INSERT INTO log_action (id_utilisateur, action, cible) VALUES (%s, %s, %s)",
        (id_utilisateur, action, cible),
    )


def lister_journal(limite=100):
    return executer(
        """SELECT l.*, u.nom, u.prenom, r.libelle AS role_libelle
           FROM log_action l
           JOIN utilisateur u ON u.id_utilisateur = l.id_utilisateur
           JOIN role r ON r.id_role = u.id_role
           ORDER BY l.date_action DESC LIMIT %s""",
        (limite,), fetch="all",
    )
