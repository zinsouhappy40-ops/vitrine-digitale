# SPEC.md — Vitrine Digitale
### Spécification d'implémentation destinée à un agent de développement IA (Kilo Code)

Ce document est autosuffisant : il ne nécessite pas de relire le PRD d'origine. Toute ambiguïté du PRD a été tranchée ci-dessous, avec justification.

**Contradictions détectées dans le PRD et arbitrage retenu :**
- Le PRD évoquait une réinitialisation de mot de passe "par email" (section 6) sans jamais prévoir d'infrastructure d'envoi d'email ailleurs dans le document. Ajouter un service d'envoi d'email pour un seul flux secondaire est disproportionné pour le MVP. **Décision : la réinitialisation de mot de passe se fait manuellement par le super_admin (toi) au MVP, pas d'email automatisé.** Cf. section 13.
- Le PRD proposait SQLite en dev et PostgreSQL en prod (section 9), mais la présente spécification impose PostgreSQL comme socle de travail. **Décision : PostgreSQL partout, y compris en développement, via Docker Compose**, pour éliminer tout risque de divergence de comportement entre SQLite et PostgreSQL (types de données, contraintes, comportement des migrations). C'est plus simple à maintenir qu'à faire cohabiter deux dialectes SQL.

---

## 1. Vision et objectifs

Permettre à un petit commerçant d'Afrique francophone d'obtenir, en 48h, une vitrine en ligne (catalogue + contact + bouton WhatsApp) accessible via un lien unique, gérable en autonomie via un dashboard simple, sur une plateforme multi-tenant unique et peu coûteuse à exploiter.

Objectif technique du MVP : livrer un produit fonctionnel, sûr sur l'isolation des données entre commerces, déployable en un seul conteneur, sans dépendance à un service tiers coûteux ou complexe.

---

## 2. Scope exact du MVP

Fonctionnalités à construire, et uniquement celles-ci :

- Authentification (connexion/déconnexion) pour `business_owner` et `super_admin`.
- CRUD Produit (nom, prix, catégorie, description, image, statut actif/inactif).
- CRUD Catégorie (nom, réassignation par défaut).
- Édition des informations du commerce (nom, logo, description, contact, numéro WhatsApp, adresse, horaires).
- Vitrine publique par slug : accueil, catalogue filtrable par catégorie, fiche produit, page contact.
- Bouton WhatsApp avec message pré-rempli.
- Génération de QR code pour le lien de la vitrine.
- Balises Open Graph correctes sur la vitrine publique.
- Création de commerce et de compte `business_owner` par le `super_admin` (pas de self-service d'inscription).
- Upload et traitement automatique (compression/redimensionnement) d'une image par produit et d'un logo par commerce.

Tout le reste est hors scope (section 3) ou en section "DO NOT BUILD".

---

## 3. Fonctionnalités hors scope (à ne pas développer dans ce MVP)

- Recherche texte dans le catalogue
- Panier / commande / checkout
- Comptes utilisateurs pour les visiteurs
- Chat en ligne / chatbot
- Personnalisation avancée du design (page builder)
- Notifications automatisées (email, push, SMS)
- Statistiques de visite/clic
- Galerie multi-images par produit
- Multi-langue
- Multi-utilisateur par commerce
- Domaine personnalisé par commerce
- Sous-domaine par commerce
- Paiement en ligne intégré
- Réinitialisation de mot de passe par email automatisé (cf. arbitrage en préambule)

---

## 4. Rôles et permissions

Deux rôles uniquement, stockés sur `User.role` :

| Rôle | Accès |
|---|---|
| `super_admin` | Création/modification/suspension de tout commerce et de tout compte `business_owner`. Aucun accès aux routes `dashboard` d'un commerce (pas nécessaire, évite la confusion de contexte). |
| `business_owner` | Accès exclusif aux routes `dashboard` de son propre `business_id`. Aucun accès aux autres commerces, ni aux routes `super_admin`. |

Pas de permissions granulaires (pas de sous-rôles, pas de droits à la fonctionnalité) au MVP — un `business_owner` a tous les droits sur son propre commerce, sans distinction.

---

## 5. User flows

**Flow A — Création d'un commerce (par super_admin)** : connexion super_admin → formulaire "nouveau commerce" (nom, génère un slug proposé, email/mot de passe temporaire du propriétaire) → création de `Business` + `User` (role `business_owner`) en une seule transaction → super_admin ajoute les premiers produits pour le compte du client si nécessaire (assistance au setup).

**Flow B — Connexion commerçant** : `/login` → email + mot de passe → redirection vers `/dashboard`.

**Flow C — Gestion produit** : `/dashboard/produits` → "Ajouter un produit" → formulaire → validation serveur → sauvegarde → retour à la liste avec message de confirmation.

**Flow D — Consultation vitrine** : visiteur ouvre `/<slug>` → parcourt catégories → clique un produit → voit fiche produit → clique "Contacter sur WhatsApp".

**Flow E — Réinitialisation de mot de passe** : le commerçant contacte le super_admin (hors application, via WhatsApp/téléphone) → le super_admin réinitialise le mot de passe depuis `/admin/commerces/<id>/reinitialiser-mot-de-passe` → un mot de passe temporaire est généré et communiqué manuellement par le super_admin.

---

## 6. Architecture applicative

Application Flask monolithique, rendu serveur (Jinja2), un seul conteneur applicatif, une base PostgreSQL, un stockage objet S3-compatible pour les images. Pas de séparation front/back en API — pas de justification à cette complexité pour un MVP sans app mobile ni SPA prévue.

Couches :
- **Routes (blueprints)** : reçoivent la requête HTTP, appellent les services, retournent une vue.
- **Services** : logique métier réutilisable, ne connaissent pas HTTP.
- **Modèles (SQLAlchemy)** : structure des données et contraintes.
- **Templates (Jinja2 + Tailwind)** : présentation uniquement, pas de logique métier dans les templates au-delà de conditions d'affichage simples.

---

## 7. Architecture multi-tenant

Multi-tenant à base de données partagée, isolation logique par `business_id`. Identification du tenant :
- Sur les routes publiques : le `slug` dans l'URL détermine le `Business` courant, chargé une fois en début de requête et stocké dans le contexte de requête (`g.current_business`).
- Sur les routes dashboard : le `business_id` de l'utilisateur connecté (`current_user.business_id`) détermine le tenant courant — **jamais** un identifiant transmis par l'URL ou le formulaire pour déterminer le tenant.

Règle absolue : toute requête SQL sur `Product` ou `Category` doit être filtrée par `business_id`, sans exception, y compris sur les routes de modification/suppression où l'ID de l'objet est fourni par le client (cf. section 14).

---

## 8. Modèle de données détaillé

**User**
- `id` (PK, integer, auto-increment)
- `email` (string, unique, obligatoire)
- `password_hash` (string, obligatoire)
- `role` (enum : `super_admin`, `business_owner`, obligatoire)
- `business_id` (FK vers `Business.id`, nullable — null uniquement si `role = super_admin`)
- `created_at` (datetime, auto)

**Business**
- `id` (PK)
- `name` (string, obligatoire)
- `slug` (string, unique, obligatoire, généré à la création, non modifiable par le `business_owner`)
- `logo_path` (string, nullable — URL du stockage objet)
- `description` (text, nullable)
- `whatsapp_number` (string, nullable — format international)
- `phone` (string, nullable)
- `address` (string, nullable)
- `opening_hours` (string, nullable — texte libre, pas de structure horaire complexe au MVP)
- `currency` (string, défaut `FCFA`)
- `status` (enum : `active`, `suspended`, défaut `active`)
- `created_at` (datetime, auto)

**Category**
- `id` (PK)
- `business_id` (FK, obligatoire)
- `name` (string, obligatoire)
- `display_order` (integer, défaut 0)
- Contrainte unique composite : (`business_id`, `name`)

**Product**
- `id` (PK)
- `business_id` (FK, obligatoire)
- `category_id` (FK vers `Category.id`, obligatoire)
- `name` (string, obligatoire)
- `price` (numeric(10,2), obligatoire, contrainte `>= 0`)
- `description` (string, max 200 caractères, nullable)
- `image_path` (string, nullable — URL du stockage objet, image par défaut si absent)
- `status` (enum : `active`, `inactive`, défaut `active`)
- `display_order` (integer, défaut 0)
- `created_at` (datetime, auto)
- `updated_at` (datetime, auto-update)

Pas d'entité `Image`, `Contact`, `Order`, `Lead` — cf. PRD section 8, confirmé sans changement.

---

## 9. Schéma des relations

```
Business (1) ────< (N) Category
Business (1) ────< (N) Product
Category (1) ────< (N) Product
Business (1) ────< (N) User   [uniquement business_owner ; super_admin a business_id = NULL]
```

Contrainte applicative critique : `Product.category_id` doit référencer une `Category` dont `business_id` est identique à `Product.business_id`. Cette cohérence est vérifiée au niveau service (section 12), pas uniquement en base.

---

## 10. Routes Flask

**Blueprint `auth`** (préfixe aucun)
- `GET/POST /login`
- `POST /logout`

**Blueprint `dashboard`** (préfixe `/dashboard`, protégé, rôle `business_owner`)
- `GET /dashboard` — vue d'ensemble
- `GET /dashboard/produits` — liste des produits
- `GET/POST /dashboard/produits/nouveau`
- `GET/POST /dashboard/produits/<int:product_id>/modifier`
- `POST /dashboard/produits/<int:product_id>/supprimer`
- `POST /dashboard/produits/<int:product_id>/statut` — bascule actif/inactif
- `GET /dashboard/categories` — liste
- `POST /dashboard/categories/nouveau`
- `POST /dashboard/categories/<int:category_id>/renommer`
- `POST /dashboard/categories/<int:category_id>/supprimer`
- `GET/POST /dashboard/commerce` — édition des infos du commerce
- `GET/POST /dashboard/mot-de-passe` — changement de mot de passe (utilisateur déjà connecté, connaît son ancien mot de passe)

**Blueprint `super_admin`** (préfixe `/admin`, protégé, rôle `super_admin`)
- `GET /admin/commerces` — liste
- `GET/POST /admin/commerces/nouveau` — création commerce + compte propriétaire
- `GET/POST /admin/commerces/<int:business_id>/modifier`
- `POST /admin/commerces/<int:business_id>/suspendre`
- `POST /admin/commerces/<int:business_id>/reactiver`
- `POST /admin/commerces/<int:business_id>/reinitialiser-mot-de-passe`

**Blueprint `public`** (préfixe aucun, accès libre)
- `GET /<slug>` — accueil vitrine
- `GET /<slug>/catalogue` — catalogue, paramètre optionnel `?categorie=<id>`
- `GET /<slug>/produit/<int:product_id>` — fiche produit
- `GET /<slug>/contact` — page contact
- `GET /<slug>/qr` — image QR code de la vitrine (générée à la volée ou mise en cache)

---

## 11. Structure des blueprints

Chaque blueprint est un sous-package avec `routes.py` (définition des routes, appel des services), `forms.py` (formulaires WTForms), et éventuellement `__init__.py` déclarant le blueprint. Les blueprints ne contiennent **aucune requête SQL directe** — toute interaction avec les modèles passe par la couche `services`. Cette règle est non négociable : elle garantit que le filtrage `business_id` est appliqué à un seul endroit, testable indépendamment.

---

## 12. Services et responsabilités

- **`tenant_service`** : résout le `Business` courant à partir du slug (routes publiques) ou du `current_user` (routes dashboard) ; expose une fonction unique de filtrage (`scoped_query(model, business_id)`) utilisée par tous les autres services pour toute lecture/écriture sur `Product`/`Category`.
- **`product_service`** : création/édition/suppression/bascule de statut d'un produit, vérifie systématiquement que `category_id` appartient au même `business_id`.
- **`category_service`** : création/renommage/suppression avec réassignation automatique vers une catégorie "Divers" (créée par défaut à la création du `Business`).
- **`business_service`** : création de commerce (génère le slug, crée le `User` propriétaire associé), édition des infos, suspension/réactivation.
- **`auth_service`** : vérification des identifiants, hashage/vérification de mot de passe, réinitialisation par le super_admin.
- **`image_service`** : validation du fichier (type MIME réel, taille max), redimensionnement/compression, upload vers le stockage objet, suppression de l'ancienne image lors d'un remplacement.
- **`whatsapp_service`** : construit l'URL `wa.me` avec message pré-rempli encodé, à partir du numéro du commerce et, si disponible, du nom du produit consulté.
- **`qrcode_service`** : génère un QR code (image PNG) à partir de l'URL complète de la vitrine.

---

## 13. Authentification et autorisation

- Gestion de session via Flask-Login.
- Mot de passe hashé avec `werkzeug.security.generate_password_hash` (algorithme par défaut de la librairie, pas de choix custom).
- Décorateurs d'accès : `@login_required` (Flask-Login) combiné à un décorateur maison `@role_required("business_owner")` ou `@role_required("super_admin")` appliqué sur chaque route protégée.
- Réinitialisation de mot de passe : réservée au `super_admin`, génère un mot de passe temporaire aléatoire, l'affiche une seule fois à l'écran au super_admin pour transmission manuelle — pas d'envoi automatisé (cf. arbitrage en préambule).
- Limitation des tentatives de connexion : Flask-Limiter, 5 tentatives par email par tranche de 10 minutes, réponse identique en cas d'email inexistant ou de mot de passe erroné.

---

## 14. Règles d'isolation tenant

- Aucune route dashboard ne doit accepter un `business_id` en paramètre d'URL ou de formulaire pour déterminer le tenant — il vient **exclusivement** de `current_user.business_id`.
- Toute route qui reçoit un identifiant d'objet (`product_id`, `category_id`) en paramètre d'URL doit vérifier, via le service correspondant, que cet objet appartient bien au `business_id` du `current_user` **avant** toute lecture ou modification. En cas de non-correspondance : réponse 404 (pas 403, pour ne pas révéler l'existence de l'objet chez un autre tenant).
- Cette vérification est centralisée dans `tenant_service.scoped_query` — aucun service métier ne doit reconstruire manuellement un filtre `business_id` en dehors de cette fonction.
- **Critère d'acceptation testable** : un test d'intégration doit démontrer qu'un `business_owner` du commerce A, authentifié, qui tente d'accéder à `/dashboard/produits/<id>/modifier` où `<id>` appartient au commerce B, reçoit une réponse 404 et qu'aucune donnée du commerce B n'est retournée dans la réponse.

---

## 15. Gestion des images

- Une image par produit, une image (logo) par commerce — pas de galerie.
- Formats acceptés : JPEG, PNG, WebP. Validation par lecture réelle du fichier (ouverture via Pillow), pas seulement par extension.
- Taille maximale acceptée à l'upload : 5 Mo.
- Traitement automatique : redimensionnement à une largeur maximale de 1200px (conservation du ratio), compression, conversion en JPEG pour homogénéité, sauf logo qui peut rester PNG si transparence détectée.
- Nom de fichier généré (UUID), jamais le nom original du fichier utilisateur, pour éviter les collisions et les informations sensibles dans le nom de fichier.
- Stockage sur un service objet compatible S3 (Cloudflare R2 recommandé), jamais sur le disque du conteneur applicatif.
- Si aucune image n'est fournie pour un produit : image par défaut générique servie par l'application (asset statique).
- **Critère d'acceptation testable** : un upload d'un fichier `.exe` renommé en `.jpg` est rejeté avec un message d'erreur explicite ; un upload de 8 Mo est rejeté avant tout traitement.

---

## 16. Gestion des catégories

- Une catégorie appartient à un seul `Business`, nom unique au sein de ce commerce.
- Une catégorie "Divers" est créée automatiquement à la création du `Business`, non supprimable.
- Suppression d'une catégorie non vide : demande de confirmation côté interface, puis réassignation automatique de tous ses produits vers "Divers".
- **Critère d'acceptation testable** : la suppression d'une catégorie contenant 3 produits aboutit à 3 produits recatégorisés en "Divers", zéro produit orphelin (sans `category_id`).

---

## 17. Gestion des produits

- Champs obligatoires à la création : nom, prix, catégorie. Description et image optionnelles (image par défaut si absente).
- Le prix est stocké en unité entière de la devise (ex. FCFA, pas de sous-unité décimale utile ici, mais le champ reste `numeric(10,2)` pour flexibilité future sans migration).
- Statut `active`/`inactive` : un produit `inactive` est exclu de toute requête publique mais reste visible/modifiable côté dashboard.
- **Critère d'acceptation testable** : un produit créé sans image affiche l'image par défaut sur la vitrine publique sans erreur ; un produit avec un prix négatif est rejeté à la validation serveur (pas seulement côté formulaire client).

---

## 18. Vitrine publique

- Page d'accueil (`/<slug>`) : logo/nom, description courte, aperçu des catégories, bouton WhatsApp visible sans scroll.
- Catalogue (`/<slug>/catalogue`) : liste des produits actifs groupés par catégorie, filtre par catégorie via paramètre de requête, pas de pagination nécessaire à l'échelle de 10-60 produits.
- Fiche produit (`/<slug>/produit/<id>`) : photo, nom, prix, description, bouton WhatsApp avec message pré-rempli mentionnant le produit.
- Contact (`/<slug>/contact`) : adresse, téléphone, horaires, bouton WhatsApp.
- Slug inexistant ou `Business.status = suspended` → page 404 générique (ne pas distinguer "n'existe pas" de "suspendu", pour ne pas exposer d'information de facturation).

---

## 19. Génération des liens WhatsApp

- Format : `https://wa.me/<numero_international_sans_plus>?text=<message_encode>`.
- Message par défaut sur la page d'accueil/contact : `"Bonjour, je suis intéressé(e) par vos produits."`
- Message sur une fiche produit : `"Bonjour, je suis intéressé(e) par : <nom_du_produit>."`
- Si `whatsapp_number` est vide ou mal formé (validation à la saisie côté dashboard, format international obligatoire E.164 sans le `+`), le bouton WhatsApp n'est simplement pas rendu sur la vitrine — pas de lien cassé.

---

## 20. Règles UX/UI

- Un seul call-to-action principal par page (bouton WhatsApp), toujours visible en haut ET en bas des pages longues.
- Palette et composants Tailwind homogènes imposés par le template, pas de personnalisation par le commerçant au MVP.
- Vocabulaire du dashboard en français simple, aucun jargon technique visible ("catégorie", "produit", "photo" — pas "slug", "SEO", "cache").
- Messages d'erreur et de confirmation explicites et courts, affichés en haut de page (flash messages).

---

## 21. Responsive / mobile-first

- Conception et test prioritaires sur viewport ~360-390px de large.
- Grille catalogue : 1 colonne sur mobile, 2-3 colonnes au-delà de 768px (Tailwind `sm:`/`md:` breakpoints standards, pas de breakpoints custom).
- Images servies en résolution adaptée (la version compressée à 1200px de large suffit à tous les viewports, pas de génération de plusieurs tailles au MVP — complexité non justifiée à ce volume de trafic).
- Aucune dépendance JavaScript lourde ; JS limité à des interactions ponctuelles (ex. bascule d'un filtre catégorie sans rechargement si jugé utile), jamais un framework front complet.

---

## 22. Sécurité

- CSRF activé sur tous les formulaires via Flask-WTF.
- Cookies de session : `HttpOnly`, `Secure` (en production), `SameSite=Lax`.
- Rate limiting sur `/login` (cf. section 13).
- Toutes les requêtes SQL passent par SQLAlchemy (requêtes paramétrées), aucun SQL brut concaténé.
- Échappement automatique Jinja2 conservé partout — ne jamais utiliser `|safe` sur du contenu saisi par un commerçant.
- Secrets (`SECRET_KEY`, identifiants base de données, clés du stockage objet) exclusivement en variables d'environnement, jamais commités.
- Pas de 2FA, pas de chiffrement applicatif additionnel au MVP (cf. PRD section 13 — disproportionné pour la sensibilité réelle des données).

---

## 23. Validation des données

- Toute validation existe côté serveur, indépendamment de toute validation HTML/JS côté client (qui reste une commodité UX, jamais une garantie).
- Formulaires construits avec WTForms, validateurs explicites par champ (obligatoire, longueur max, type numérique, format téléphone international pour `whatsapp_number`).
- Le nom de commerce/produit est nettoyé (`strip()`) avant sauvegarde, longueur maximale imposée pour éviter les débordements d'affichage (ex. 80 caractères pour un nom).

---

## 24. Gestion des erreurs

- 404 personnalisée (template cohérent avec le reste du site) pour : slug inexistant, produit/catégorie appartenant à un autre tenant, produit inexistant.
- 403 réservée aux cas où l'utilisateur est authentifié mais n'a pas le rôle requis pour la route (ex. `business_owner` qui tente d'accéder à `/admin`) — jamais utilisée pour un problème d'appartenance tenant (cf. section 14, qui utilise 404).
- 500 : page générique sans détail technique exposé, erreur journalisée côté serveur.
- Les erreurs de validation de formulaire s'affichent au champ concerné, jamais en redirigeant vers une page d'erreur générique.

---

## 25. Tests unitaires

Couverture minimale exigée, par service :
- `product_service` : création avec catégorie invalide (autre tenant) rejetée ; prix négatif rejeté ; statut basculé correctement.
- `category_service` : suppression avec réassignation vers "Divers" ; nom dupliqué dans le même commerce rejeté ; nom dupliqué entre deux commerces différents accepté.
- `image_service` : rejet d'un fichier non-image ; rejet d'un fichier trop lourd ; redimensionnement produit une image ≤ 1200px de large.
- `whatsapp_service` : URL générée valide et correctement encodée avec et sans nom de produit ; absence de numéro → pas d'URL générée.
- `auth_service` : hash de mot de passe jamais égal au mot de passe en clair ; vérification correcte d'un mot de passe valide/invalide.

---

## 26. Tests d'intégration

- Flow complet de connexion `business_owner` → accès dashboard → déconnexion.
- Flow complet de création d'un produit via le formulaire dashboard → apparition immédiate sur la vitrine publique.
- Flow de désactivation d'un produit → disparition de la vitrine publique, persistance dans le dashboard.
- Accès à une route `/admin/*` par un utilisateur `business_owner` → 403.
- Accès à `/<slug>` avec un slug inexistant → 404.
- Accès à `/<slug>` avec un `Business.status = suspended` → 404.

---

## 27. Tests multi-tenant

- Deux commerces A et B créés en base de test avec chacun un produit et une catégorie du même nom.
- Un `business_owner` de A connecté ne voit, sur `/dashboard/produits`, que les produits de A.
- Tentative de A d'éditer/supprimer un produit de B via manipulation d'URL (`/dashboard/produits/<id_de_B>/modifier`) → 404, aucune donnée de B exposée dans la réponse.
- Les vitrines publiques `/A` et `/B` n'affichent chacune que leurs propres produits actifs, y compris quand les deux commerces ont des catégories de même nom.

---

## 28. Configuration environnementale

Variables d'environnement requises (aucune valeur par défaut en dur dans le code pour les secrets) :

- `FLASK_ENV` (`development` / `production`)
- `SECRET_KEY`
- `DATABASE_URL` (format `postgresql://...`)
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`
- `WTF_CSRF_SECRET_KEY` (peut être dérivé de `SECRET_KEY` si absent)

Un fichier `.env.example` doit lister ces variables sans valeurs réelles.

---

## 29. Docker

- Un `Dockerfile` unique pour l'application Flask (image Python slim, dépendances via `requirements.txt`, serveur applicatif de production — Gunicorn — pas le serveur de développement Flask).
- Un `docker-compose.yml` pour le développement local uniquement, avec deux services : `app` et `db` (PostgreSQL), volumes persistants pour la base en local.
- Pas de conteneur séparé pour le stockage objet en local — utiliser directement le service S3-compatible distant (compte de développement séparé du compte de production).

---

## 30. Base de données

- PostgreSQL en développement et en production (cf. arbitrage en préambule), hébergée en managé en production.
- Encodage UTF-8, fuseau horaire UTC pour tous les `datetime`.
- Pas de réplication ni de partitionnement au MVP — hors de proportion pour le volume attendu.

---

## 31. Migrations

- Flask-Migrate (Alembic) dès la première ligne de modèle.
- Une migration par changement de schéma, jamais de modification manuelle du schéma en production.
- Chaque migration doit être testée sur une copie de la base de développement avant application en production.

---

## 32. Déploiement

- Plateforme d'hébergement à faible coût (Railway, Render, ou VPS équivalent) exécutant l'image Docker applicative.
- Base de données PostgreSQL managée par la même plateforme ou un service dédié.
- HTTPS automatique via la plateforme (Let's Encrypt géré).
- Sauvegardes automatiques quotidiennes de la base de données, vérifiées explicitement à la configuration (pas supposées incluses).
- Domaine unique pour toute la plateforme, commerces différenciés par chemin (`/<slug>`), pas de sous-domaine ni domaine personnalisé au MVP.

---

## 33. Structure exacte du repository

```
vitrine-digitale/
├── app/
│   ├── __init__.py
│   ├── extensions.py            # instanciation Flask-Login, Flask-Migrate, Flask-Limiter, CSRFProtect
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── business.py
│   │   ├── category.py
│   │   └── product.py
│   ├── blueprints/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   ├── dashboard/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   ├── super_admin/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   └── public/
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── services/
│   │   ├── tenant_service.py
│   │   ├── product_service.py
│   │   ├── category_service.py
│   │   ├── business_service.py
│   │   ├── auth_service.py
│   │   ├── image_service.py
│   │   ├── whatsapp_service.py
│   │   └── qrcode_service.py
│   ├── templates/
│   │   ├── public/
│   │   ├── dashboard/
│   │   ├── super_admin/
│   │   ├── auth/
│   │   └── shared/               # layout de base, composants Jinja communs
│   ├── static/
│   │   └── (CSS Tailwind compilé, image par défaut produit)
│   └── utils/
│       ├── decorators.py         # role_required, etc.
│       └── validators.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── multi_tenant/
├── config.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 34. Conventions de code

- Python : PEP 8, `snake_case` pour fonctions/variables/fichiers, `PascalCase` pour les classes.
- Un service = un fichier, une responsabilité (cf. section 12), pas de fonction de service de plus de ~40 lignes sans découpage.
- Aucune requête SQLAlchemy directe dans les fichiers `routes.py` — toujours passer par un service.
- Noms de routes et de templates en français (cohérence avec les URLs déjà françaises du PRD), noms de variables/fonctions en anglais (convention Python standard).
- Chaque formulaire WTForms dans un fichier `forms.py` dédié à son blueprint.

---

## 35. Definition of Done

Une fonctionnalité est considérée terminée seulement si :
- Le code respecte la structure de blueprints/services (section 11, 33).
- Les critères d'acceptation listés dans la section correspondante sont vérifiés par au moins un test automatisé.
- Aucune requête sur `Product`/`Category` ne contourne `tenant_service.scoped_query`.
- L'affichage a été vérifié sur un viewport mobile (~375px).
- Aucune régression sur les tests multi-tenant existants (section 27).
- Les variables sensibles utilisées sont lues depuis la configuration d'environnement, jamais codées en dur.

---

## 36. Découpage du développement en phases

**Phase A — Socle applicatif**
Structure du projet, configuration, connexion PostgreSQL, modèles, migrations initiales, Docker/Docker Compose fonctionnels.

**Phase B — Authentification et rôles**
Blueprint `auth`, `role_required`, création manuelle d'un `super_admin` initial (script ou commande CLI), blueprint `super_admin` minimal (création de commerce + compte propriétaire).

**Phase C — Isolation tenant et CRUD dashboard**
`tenant_service`, blueprint `dashboard` complet (produits, catégories, infos commerce), tests multi-tenant.

**Phase D — Vitrine publique**
Blueprint `public` (accueil, catalogue, fiche produit, contact), template public homogène, responsive mobile-first.

**Phase E — Images, WhatsApp, QR code, Open Graph**
`image_service` (upload, validation, compression, stockage objet), `whatsapp_service`, `qrcode_service`, balises Open Graph sur les pages publiques.

**Phase F — Sécurité et durcissement**
CSRF, rate limiting, revue de toutes les routes contre la checklist section 14 et 22, tests d'intégration complets.

**Phase G — Déploiement**
Dockerfile de production (Gunicorn), déploiement sur la plateforme choisie, configuration du stockage objet de production, vérification des sauvegardes.

---

## 37. Critères d'acceptation de chaque phase

**Phase A** : l'application démarre via `docker-compose up`, se connecte à PostgreSQL, une migration initiale s'applique sans erreur.

**Phase B** : un `super_admin` peut se connecter, créer un commerce, et le compte `business_owner` généré peut se connecter et accéder à un dashboard vide.

**Phase C** : tous les tests de la section 27 passent ; un `business_owner` peut créer/modifier/supprimer un produit et une catégorie exclusivement dans son propre commerce.

**Phase D** : la vitrine publique d'un commerce affiche exactement ses produits actifs, groupés par catégorie, sur un viewport mobile sans défaut d'affichage visible.

**Phase E** : un upload d'image invalide est rejeté avec message clair ; le bouton WhatsApp ouvre une conversation pré-remplie correcte ; le lien partagé sur WhatsApp affiche un aperçu (image + titre) correct ; le QR code généré redirige bien vers la vitrine.

**Phase F** : aucun formulaire ne peut être soumis sans jeton CSRF valide ; 6 tentatives de connexion successives avec mauvais mot de passe déclenchent un blocage temporaire ; l'ensemble des tests unitaires, d'intégration et multi-tenant passe en intégration continue locale.

**Phase G** : l'application est accessible en HTTPS sur l'environnement de production, une vitrine de test créée en production reste accessible après redéploiement du conteneur (preuve que les images ne dépendent pas du disque local).

---

## IMPLEMENTATION ORDER

1. Structure du repository (section 33) et configuration (section 28, 29).
2. Modèles SQLAlchemy (section 8) et première migration (section 31).
3. `tenant_service` (section 12) — construit avant tout CRUD, car tout le reste en dépend.
4. `auth_service` + blueprint `auth` + décorateur `role_required` (section 13).
5. Commande de création d'un `super_admin` initial (hors interface web, script/CLI).
6. Blueprint `super_admin` : création de commerce + compte `business_owner` (section 10).
7. `category_service` + routes dashboard catégories (section 16).
8. `product_service` + routes dashboard produits (section 17).
9. `image_service` intégré aux routes produit/commerce (section 15).
10. Blueprint `public` : accueil, catalogue, fiche produit, contact (section 18).
11. `whatsapp_service` intégré aux templates publics (section 19).
12. `qrcode_service` + route `/​<slug>/qr` (section 10).
13. Balises Open Graph sur les templates publics (section 18).
14. Durcissement sécurité : CSRF, rate limiting, cookies (section 22).
15. Suite de tests complète : unitaires (25) → intégration (26) → multi-tenant (27).
16. Dockerfile de production + déploiement (section 32).

---

## DO NOT BUILD

- Recherche texte dans le catalogue
- Panier, commande, checkout, paiement en ligne
- Comptes utilisateurs pour les visiteurs de la vitrine
- Chat en ligne, chatbot, ou toute messagerie interne à l'application
- Page builder ou personnalisation avancée du design par le commerçant
- Notifications automatisées (email, SMS, push)
- Tableau de statistiques de visite/clic
- Galerie multi-images par produit
- Support multi-langue
- Comptes multi-utilisateurs pour un même commerce
- Domaine personnalisé ou sous-domaine par commerce
- Réinitialisation de mot de passe automatisée par email
- Entités `Order`, `Lead`, ou `Image` en tant que table séparée
- Toute forme d'API REST/JSON publique non demandée explicitement
- Tout framework JavaScript front (React, Vue, etc.)
- Toute infrastructure d'envoi d'email
