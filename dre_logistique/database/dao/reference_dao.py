from database.connexion import executer


def lister_services():
    return executer("SELECT * FROM service ORDER BY nom", fetch="all")


def creer_service(nom, description=""):
    return executer(
        "INSERT INTO service (nom, description) VALUES (%s, %s) RETURNING id_service",
        (nom, description), fetch="one",
    )


def lister_grades():
    return executer("SELECT * FROM grade ORDER BY libelle", fetch="all")


def lister_statuts():
    return executer("SELECT * FROM statut ORDER BY id_statut", fetch="all")


def lister_roles():
    return executer("SELECT * FROM role ORDER BY id_role", fetch="all")
