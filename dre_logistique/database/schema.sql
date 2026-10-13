-- Schéma PostgreSQL du logiciel DRE Logistique
-- Correspond au MCD/MLD validé pour le PFE (DRE Haute Matsiatra)

CREATE TABLE IF NOT EXISTS role (
    id_role      SERIAL PRIMARY KEY,
    libelle      VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS service (
    id_service   SERIAL PRIMARY KEY,
    nom          VARCHAR(100) NOT NULL,
    description  TEXT
);

CREATE TABLE IF NOT EXISTS grade (
    id_grade     SERIAL PRIMARY KEY,
    libelle      VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS statut (
    id_statut    SERIAL PRIMARY KEY,
    libelle      VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur  SERIAL PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    login           VARCHAR(50) NOT NULL UNIQUE,
    mot_de_passe    VARCHAR(255) NOT NULL,
    id_role         INT NOT NULL REFERENCES role(id_role),
    actif           BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS materiel (
    id_materiel             SERIAL PRIMARY KEY,
    code                    VARCHAR(30) NOT NULL UNIQUE,
    designation             VARCHAR(150) NOT NULL,
    qr_code                 VARCHAR(255) NOT NULL UNIQUE,
    photo_path              VARCHAR(255),
    date_acquisition        DATE NOT NULL,
    id_service              INT REFERENCES service(id_service),
    id_grade                INT REFERENCES grade(id_grade),
    id_statut               INT NOT NULL REFERENCES statut(id_statut),
    id_materiel_remplacant  INT REFERENCES materiel(id_materiel)
);

CREATE TABLE IF NOT EXISTS mouvement (
    id_mouvement       SERIAL PRIMARY KEY,
    type_mouvement     VARCHAR(20) NOT NULL
        CHECK (type_mouvement IN ('affectation','transfert','remplacement','rebut')),
    date_mouvement     TIMESTAMP NOT NULL DEFAULT now(),
    commentaire        TEXT,
    id_materiel        INT NOT NULL REFERENCES materiel(id_materiel),
    id_utilisateur     INT NOT NULL REFERENCES utilisateur(id_utilisateur),
    id_service_source  INT REFERENCES service(id_service),
    id_service_dest    INT REFERENCES service(id_service)
);

CREATE TABLE IF NOT EXISTS log_action (
    id_log          SERIAL PRIMARY KEY,
    action          VARCHAR(255) NOT NULL,
    cible           VARCHAR(150),
    date_action     TIMESTAMP NOT NULL DEFAULT now(),
    id_utilisateur  INT NOT NULL REFERENCES utilisateur(id_utilisateur)
);

CREATE TABLE IF NOT EXISTS alerte (
    id_alerte         SERIAL PRIMARY KEY,
    type_alerte       VARCHAR(30) NOT NULL
        CHECK (type_alerte IN ('anciennete','frequence_panne','rupture_stock','sur_consommation')),
    message           TEXT NOT NULL,
    niveau_risque     VARCHAR(15) NOT NULL
        CHECK (niveau_risque IN ('faible','moyen','eleve')),
    date_generation   TIMESTAMP NOT NULL DEFAULT now(),
    id_materiel       INT REFERENCES materiel(id_materiel)
);

CREATE INDEX IF NOT EXISTS idx_mouvement_materiel ON mouvement(id_materiel);
CREATE INDEX IF NOT EXISTS idx_mouvement_date ON mouvement(date_mouvement);
CREATE INDEX IF NOT EXISTS idx_alerte_materiel ON alerte(id_materiel);

-- Migration automatique : ajoute la colonne photo_path si elle n'existe pas
-- déjà (pour les bases créées avant l'introduction de cette fonctionnalité).
-- Ce script étant rejoué à chaque démarrage (voir connexion.initialiser_base),
-- IF NOT EXISTS le rend sans danger à ré-exécuter.
ALTER TABLE materiel ADD COLUMN IF NOT EXISTS photo_path VARCHAR(255);

-- Migration automatique : corrige un bug où service.nom n'avait pas de
-- contrainte d'unicité, ce qui faisait que seed.sql recréait les 4 services
-- de référence à CHAQUE démarrage de l'application. Ce bloc dédoublonne les
-- services existants (en réattribuant d'abord le matériel et les mouvements
-- au doublon le plus ancien, pour ne rien perdre) puis verrouille l'unicité
-- pour empêcher que le problème ne se reproduise. Idempotent : sans danger
-- à ré-exécuter à chaque démarrage.
DO $$
DECLARE
    r RECORD;
    id_a_garder INT;
BEGIN
    FOR r IN SELECT nom FROM service GROUP BY nom HAVING COUNT(*) > 1 LOOP
        SELECT MIN(id_service) INTO id_a_garder FROM service WHERE nom = r.nom;

        UPDATE materiel SET id_service = id_a_garder
            WHERE id_service IN (
                SELECT id_service FROM service WHERE nom = r.nom AND id_service <> id_a_garder
            );
        UPDATE mouvement SET id_service_source = id_a_garder
            WHERE id_service_source IN (
                SELECT id_service FROM service WHERE nom = r.nom AND id_service <> id_a_garder
            );
        UPDATE mouvement SET id_service_dest = id_a_garder
            WHERE id_service_dest IN (
                SELECT id_service FROM service WHERE nom = r.nom AND id_service <> id_a_garder
            );

        DELETE FROM service WHERE nom = r.nom AND id_service <> id_a_garder;
    END LOOP;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'service_nom_unique'
    ) THEN
        ALTER TABLE service ADD CONSTRAINT service_nom_unique UNIQUE (nom);
    END IF;
END $$;