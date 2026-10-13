-- Données de référence (à exécuter une seule fois après schema.sql)

INSERT INTO role (libelle) VALUES ('admin'), ('chef_service'), ('agent')
    ON CONFLICT (libelle) DO NOTHING;

INSERT INTO grade (libelle) VALUES ('A'), ('B'), ('C')
    ON CONFLICT (libelle) DO NOTHING;

INSERT INTO statut (libelle) VALUES ('en_service'), ('hors_service'), ('rebut'), ('archive')
    ON CONFLICT (libelle) DO NOTHING;
    
INSERT INTO service (nom, description) VALUES
    ('Éducation fondamentale', 'Écoles primaires rattachées à la DRE'),
    ('Enseignement secondaire', 'Collèges et lycées rattachés à la DRE'),
    ('Administration', 'Services administratifs du siège'),
    ('Maintenance', 'Équipe technique et logistique')
    ON CONFLICT DO NOTHING;

-- Mot de passe par défaut : "admin123" (haché avec bcrypt, voir auth_service.py)
-- Le hash ci-dessous est généré au premier lancement si la table est vide
-- (voir database/connexion.py -> initialiser_admin_par_defaut)
