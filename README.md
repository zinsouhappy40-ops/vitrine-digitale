# Vitrine Digitale

Plateforme Django multi-tenant permettant à de petits commerçants de gérer un catalogue et de publier une vitrine orientée WhatsApp.

## Prérequis

- Docker avec Docker Compose
- Ou Python 3.13+ et PostgreSQL pour un lancement hors conteneur

## Installation

1. Copier `.env.example` vers `.env`.
2. Renseigner `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` et les autres variables requises.
3. Lancer les services : `docker compose up --build`.
4. Créer le super-admin : `docker compose exec app python manage.py createsuperuser`.

L'application est ensuite accessible sur `http://localhost:8000`.

## Développement

- Vérifier la configuration : `python manage.py check`
- Créer les migrations : `python manage.py makemigrations`
- Appliquer les migrations : `python manage.py migrate`
- Lancer les tests : `python manage.py test`
- Lancer Django localement : `python manage.py runserver`
- Installer Tailwind : `npm install`
- Compiler le CSS : `npm run build:css`
- Recompiler le CSS en continu : `npm run watch:css`

Le fichier compilé `static/css/app.css` est versionné afin que l'image de production ne nécessite pas Node.js.

## Architecture

- `accounts` : utilisateurs, rôles et authentification par e-mail
- `businesses` : commerces et administration
- `catalog` : catégories, produits et dashboard commerçant
- `storefront` : vitrine publique en lecture seule
- `core` : isolation tenant et utilitaires partagés

## Isolation multi-tenant

Le commerce courant du dashboard vient exclusivement de `request.user.business`. Toute lecture ou modification de `Product` et `Category` doit passer par `TenantScopedManager.for_business()`; un identifiant appartenant à un autre commerce retourne une réponse 404.

## Médias

Le stockage local est autorisé uniquement en développement. La production utilisera un stockage S3-compatible configuré par variables d'environnement; les médias persistants ne doivent jamais dépendre du disque du conteneur.

## Production

Le conteneur exécute `collectstatic`, les migrations Django, puis Gunicorn sur la variable `$PORT`. WhiteNoise sert les fichiers statiques compilés; les médias restent exclusivement sur S3/R2.

Variables obligatoires :

- `DJANGO_ENV=production`
- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `S3_ENDPOINT_URL`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET_NAME`

Procédure de déploiement :

1. Créer une base PostgreSQL managée avec sauvegardes quotidiennes activées.
2. Créer un bucket S3/R2 privé dédié aux médias de production.
3. Déployer le `Dockerfile` sur Railway, Render ou une plateforme Docker équivalente.
4. Configurer les variables ci-dessus et exposer le port fourni par `$PORT`.
5. Activer HTTPS et vérifier `python manage.py check --deploy`.
6. Créer le super-admin avec `python manage.py createsuperuser`.
7. Vérifier une restauration de sauvegarde PostgreSQL avant ouverture commerciale.

Après chaque redéploiement, contrôler qu'une image déjà envoyée reste accessible afin de confirmer que les médias ne dépendent pas du disque du conteneur.
