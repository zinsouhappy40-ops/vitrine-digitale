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

La compilation Tailwind sera ajoutée avec les interfaces des phases dashboard et vitrine.

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

Le conteneur exécute Django avec Gunicorn et PostgreSQL. La configuration de production doit utiliser HTTPS, `DJANGO_DEBUG=False`, des hôtes explicitement autorisés, un stockage S3/R2 pour les médias et des sauvegardes quotidiennes vérifiées de la base.
