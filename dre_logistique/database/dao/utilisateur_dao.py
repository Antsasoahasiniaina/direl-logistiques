from database.connexion import executer


def trouver_par_login(login):
    return executer(
        """SELECT u.*, r.libelle AS role_libelle
           FROM utilisateur u JOIN role r ON r.id_role = u.id_role
           WHERE u.login = %s AND u.actif = TRUE""",
        (login,), fetch="one",
    )


def lister():
    return executer(
        """SELECT u.*, r.libelle AS role_libelle
           FROM utilisateur u JOIN role r ON r.id_role = u.id_role
           ORDER BY u.nom""",
        fetch="all",
    )


def creer(nom, prenom, login, mot_de_passe_hache, id_role):
    return executer(
        """INSERT INTO utilisateur (nom, prenom, login, mot_de_passe, id_role)
           VALUES (%s, %s, %s, %s, %s) RETURNING id_utilisateur""",
        (nom, prenom, login, mot_de_passe_hache, id_role), fetch="one",
    )
