# SPEC.md — Vitrine Digitale
### Spécification d'implémentation destinée à un agent de développement IA (Kilo Code)

Ce document est autosuffisant : il ne nécessite pas de relire le PRD d'origine. Toute ambiguïté du PRD a été tranchée ci-dessous, avec justification.

**Changement de socle technique par rapport à la version précédente de ce document** : le framework retenu est **Django**, et non Flask. Justification : ce projet est structurellement un CRUD multi-entités avec back-office d'administration (gestion des commerces par le super_admin), et Django fournit nativement l'admin, l'ORM, les migrations, l'authentification et les protections de sécurité de base — ce qui réduit fortement le volume de code à écrire et à maintenir par rapport à un assemblage manuel d'extensions Flask, pour un résultat plus robuste par défaut. Le scope fonctionnel, le modèle de données, les règles métier, la sécurité et les phases restent identiques à la version précédente — seule la couche framework change.

**Contradictions détectées dans le PRD et arbitrage retenu :**
- Le PRD évoquait une réinitialisation de mot de passe "par email" sans jamais prévoir d'infrastructure d'envoi d'email ailleurs dans le document. **Décision : réinitialisation manuelle par le super_admin depuis Django Admin, pas d'email automatisé au MVP.**
- Le PRD proposait SQLite en dev et PostgreSQL en prod. **Décision : PostgreSQL partout (y compris en développement, via Docker Compose)**, pour éviter toute divergence de comportement entre deux dialectes SQL.

---

## 1. Vision et objectifs

Permettre à un petit commerçant d'Afrique francophone d'obtenir, en 48h, une vitrine en ligne (catalogue + contact + bouton WhatsApp) accessible via un lien unique, gérable en autonomie via un dashboard simple, sur une plateforme multi-tenant unique et peu coûteuse à exploiter.

Objectif technique du MVP : livrer un produit fonctionnel, sûr sur l'isolation des données entre commerces, déployable en un seul conteneur, en s'appuyant au maximum sur ce que Django fournit nativement plutôt que de réécrire des briques déjà résolues.

---

## 2. Scope exact du MVP

Identique à la version précédente — le changement de framework ne change pas le périmètre fonctionnel :

- Authentification (connexion/déconnexion) pour `business_owner` et `super_admin`.
- CRUD Produit (nom, prix, catégorie, description, image, statut actif/inactif).
- CRUD Catégorie (nom, réassignation par défaut).
- Édition des informations du commerce (nom, logo, description, contact, numéro WhatsApp, adresse, horaires).
- Vitrine publique par slug : accueil, catalogue filtrable par catégorie, fiche produit, page contact.
- Bouton WhatsApp avec message pré-rempli.
- Génération de QR code pour le lien de la vitrine.
- Balises Open Graph correctes sur la vitrine publique.
- Création de commerce et de compte `business_owner` par le `super_admin`, désormais **directement via Django Admin** plutôt qu'un blueprint sur-mesure (cf. section 10).
- Upload et traitement automatique (compression/redimensionnement) d'une image par produit et d'un logo par commerce.

---

## 3. Fonctionnalités hors scope (à ne pas développer dans ce MVP)

Inchangé :
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
- Réinitialisation de mot de passe par email automatisé

---

## 4. Rôles et permissions

Deux rôles, portés par le modèle `User` (extension du modèle utilisateur Django) :

| Rôle | Accès |
|---|---|
| `super_admin` | Utilisateur Django `is_staff=True` avec accès à **Django Admin** pour créer/modifier/suspendre tout commerce et tout compte `business_owner`. N'a pas besoin d'un accès aux vues dashboard des commerces. |
| `business_owner` | `is_staff=False`, accès exclusif à l'app `dashboard` pour son propre `business_id`. Aucun accès à Django Admin. |

Pas de permissions granulaires au MVP — Django dispose d'un système de permissions fin (`django.contrib.auth.permissions`), volontairement non utilisé ici pour rester simple : la distinction se fait uniquement sur le champ `role` et sur `is_staff`.

---

## 5. User flows

**Flow A — Création d'un commerce (par super_admin)** : connexion à `/admin/` (Django Admin) → `Business` → "Ajouter" → saisie nom (slug généré automatiquement) → création simultanée du `User` propriétaire via un inline admin ou une action admin dédiée → super_admin ajoute les premiers produits pour le compte du client si nécessaire.

**Flow B — Connexion commerçant** : `/connexion` → email + mot de passe → redirection vers `/dashboard/`.

**Flow C — Gestion produit** : `/dashboard/produits/` → "Ajouter un produit" → formulaire Django → validation serveur → sauvegarde → retour à la liste avec message de confirmation (`django.contrib.messages`).

**Flow D — Consultation vitrine** : visiteur ouvre `/<slug>/` → parcourt catégories → clique un produit → voit fiche produit → clique "Contacter sur WhatsApp".

**Flow E — Réinitialisation de mot de passe** : le commerçant contacte le super_admin hors application → le super_admin réinitialise le mot de passe depuis Django Admin (action admin "Réinitialiser le mot de passe" qui génère un mot de passe temporaire affiché une seule fois) → transmission manuelle au commerçant.

---

## 6. Architecture applicative

Projet Django monolithique, rendu serveur (templates Django, syntaxe proche de Jinja2), un seul conteneur applicatif, une base PostgreSQL, un stockage objet S3-compatible pour les images via `django-storages`. Pas d'API REST — non justifié pour ce MVP.

Découpage en apps Django, chacune avec une responsabilité claire :

- **`accounts`** : modèle `User` personnalisé (rôle, lien vers `Business`), vues de connexion/déconnexion.
- **`businesses`** : modèle `Business`, configuration Django Admin pour le super_admin, logique de génération de slug.
- **`catalog`** : modèles `Category` et `Product`, vues dashboard pour le `business_owner`.
- **`storefront`** : vues publiques (accueil, catalogue, fiche produit, contact), aucune écriture en base, lecture seule.
- **`core`** : utilitaires partagés (isolation tenant, décorateurs de rôle, génération WhatsApp/QR code, traitement d'image).

Couches à l'intérieur de chaque app : **vues** (reçoivent la requête, appellent les services) → **services** (`core/services/` ou `<app>/services.py`, logique métier réutilisable, ne connaissent pas HTTP) → **modèles** (ORM Django). Les templates ne contiennent pas de logique métier au-delà de conditions d'affichage simples.

---

## 7. Architecture multi-tenant

Multi-tenant à base de données partagée, isolation logique par `business_id`, identique dans le principe à la version Flask.

- Sur les routes publiques (`storefront`) : le `slug` dans l'URL détermine le `Business` courant, résolu une fois via un middleware ou une fonction utilitaire au début de la vue, jamais recalculé implicitement plus loin.
- Sur les routes dashboard : le `business_id` vient exclusivement de `request.user.business` (le `business_owner` connecté), jamais d'un paramètre d'URL ou de formulaire.

Règle absolue : tout `QuerySet` sur `Product` ou `Category` dans l'app `catalog` (dashboard) doit être filtré par `business_id`, sans exception — y compris sur les vues de modification/suppression où l'ID de l'objet est fourni par le client (cf. section 14). Le manager par défaut de Django (`Model.objects`) n'effectue **aucun filtrage tenant automatique** — c'est un manager custom (`TenantScopedManager`, cf. section 12) qui porte cette responsabilité, pour éviter qu'une requête l'oublie par erreur.

---

## 8. Modèle de données détaillé

**User** (modèle personnalisé étendant `AbstractUser`, `AUTH_USER_MODEL` défini dans `settings.py`)
- `email` (unique, obligatoire — utilisé comme identifiant de connexion à la place du `username`)
- `role` (`CharField` avec choix : `super_admin`, `business_owner`)
- `business` (`ForeignKey` vers `Business`, `null=True, blank=True` — null uniquement si `role = super_admin`)
- Champs Django standards conservés (`is_staff`, `is_active`, `date_joined`, etc.) — `is_staff=True` réservé aux `super_admin` pour l'accès à Django Admin.

**Business**
- `name` (`CharField`, obligatoire)
- `slug` (`SlugField`, unique, généré automatiquement à la création, non modifiable ensuite via le dashboard commerçant)
- `logo` (`ImageField`, stockage S3 via `django-storages`, nullable)
- `description` (`TextField`, nullable)
- `whatsapp_number` (`CharField`, nullable, format international validé)
- `phone` (`CharField`, nullable)
- `address` (`CharField`, nullable)
- `opening_hours` (`CharField`, texte libre, nullable)
- `currency` (`CharField`, défaut `"FCFA"`)
- `status` (`CharField`, choix : `active`, `suspended`, défaut `active`)
- `created_at` (`DateTimeField(auto_now_add=True)`)

**Category**
- `business` (`ForeignKey` vers `Business`, obligatoire)
- `name` (`CharField`, obligatoire)
- `display_order` (`PositiveIntegerField`, défaut 0)
- `Meta.unique_together = ("business", "name")`

**Product**
- `business` (`ForeignKey` vers `Business`, obligatoire)
- `category` (`ForeignKey` vers `Category`, obligatoire)
- `name` (`CharField`, obligatoire)
- `price` (`DecimalField(max_digits=10, decimal_places=2)`, contrainte `>= 0` via `CheckConstraint`)
- `description` (`CharField`, max 200 caractères, nullable)
- `image` (`ImageField`, stockage S3, nullable — image par défaut gérée côté template si absente)
- `status` (`CharField`, choix : `active`, `inactive`, défaut `active`)
- `display_order` (`PositiveIntegerField`, défaut 0)
- `created_at` (`DateTimeField(auto_now_add=True)`)
- `updated_at` (`DateTimeField(auto_now=True)`)

Pas de modèle `Image`, `Contact`, `Order`, `Lead` — confirmé sans changement.

---

## 9. Schéma des relations

```
Business (1) ────< (N) Category
Business (1) ────< (N) Product
Category (1) ────< (N) Product
Business (1) ────< (N) User   [uniquement business_owner ; super_admin a business = NULL]
```

Contrainte applicative critique : `Product.category` doit référencer une `Category` dont `business` est identique à `Product.business`. Vérifiée dans `ProductForm.clean()` et dans le service `catalog.services.create_or_update_product`, pas seulement supposée par la contrainte FK.

---

## 10. Vues et URLs Django

**App `accounts`** (préfixe aucun)
- `GET/POST /connexion/` → `LoginView` custom (redirige vers `/dashboard/` après connexion)
- `POST /deconnexion/` → `LogoutView`

**App `catalog`** (préfixe `/dashboard/`, protégé, décorateur `@business_owner_required`)
- `GET /dashboard/` — vue d'ensemble
- `GET /dashboard/produits/` — liste des produits
- `GET/POST /dashboard/produits/nouveau/`
- `GET/POST /dashboard/produits/<int:pk>/modifier/`
- `POST /dashboard/produits/<int:pk>/supprimer/`
- `POST /dashboard/produits/<int:pk>/statut/` — bascule actif/inactif
- `GET /dashboard/categories/`
- `POST /dashboard/categories/nouveau/`
- `POST /dashboard/categories/<int:pk>/renommer/`
- `POST /dashboard/categories/<int:pk>/supprimer/`

**App `businesses`** (préfixe `/dashboard/commerce/`, protégé, `@business_owner_required`)
- `GET/POST /dashboard/commerce/` — édition des infos du commerce
- `GET/POST /dashboard/mot-de-passe/` — changement de mot de passe (utilisateur déjà connecté)

**Django Admin** (préfixe `/admin/`, réservé `is_staff` / `super_admin`)
- Géré nativement, pas d'URL custom à écrire : `ModelAdmin` pour `Business` (avec inline `User` pour créer le compte propriétaire en même temps), action admin "Réinitialiser le mot de passe", action admin "Suspendre"/"Réactiver".

**App `storefront`** (préfixe aucun, accès libre)
- `GET /<slug>/` — accueil vitrine
- `GET /<slug>/catalogue/` — catalogue, paramètre optionnel `?categorie=<id>`
- `GET /<slug>/produit/<int:pk>/` — fiche produit
- `GET /<slug>/contact/` — page contact
- `GET /<slug>/qr/` — image QR code de la vitrine

---

## 11. Structure des apps

Chaque app suit la structure Django standard (`models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py` le cas échéant) **plus** un fichier `services.py` qui porte toute la logique métier. Règle non négociable identique à la version précédente : **aucun `QuerySet` construit directement dans `views.py`** en dehors d'un appel à un service ou à un manager custom — garantit que le filtrage tenant (section 7, 14) reste centralisé et auditable en un seul endroit par type d'opération.

---

## 12. Services et responsabilités

- **`core.tenant`** : résout le `Business` courant à partir du slug (vues `storefront`) ou de `request.user.business` (vues `catalog`/`businesses`) ; fournit `TenantScopedManager`, un manager Django custom appliqué sur `Product` et `Category`, qui expose `.for_business(business)` comme unique point d'entrée pour toute lecture/écriture filtrée.
- **`catalog.services`** : création/édition/suppression/bascule de statut d'un produit (vérifie que `category.business == product.business`), création/renommage/suppression de catégorie avec réassignation vers "Divers".
- **`businesses.services`** : génération de slug à la création, création du `User` propriétaire associé, suspension/réactivation, réinitialisation de mot de passe (appelée depuis une action Django Admin).
- **`core.images`** : validation du fichier (type MIME réel via Pillow, taille max), redimensionnement/compression, délégué au champ `ImageField` + `django-storages` pour l'upload, suppression de l'ancien fichier lors d'un remplacement.
- **`core.whatsapp`** : construit l'URL `wa.me` avec message pré-rempli encodé.
- **`core.qrcode`** : génère un QR code (image PNG) à partir de l'URL complète de la vitrine.

---

## 13. Authentification et autorisation

- Authentification via `django.contrib.auth`, backend custom si nécessaire pour permettre la connexion par email plutôt que par `username` (`EmailBackend` simple, ou `USERNAME_FIELD = "email"` sur le modèle `User` personnalisé — approche recommandée, plus simple).
- Mot de passe hashé via le hasher par défaut de Django (`PBKDF2` ou `Argon2` si `django[argon2]` installé — Argon2 recommandé, léger à activer via `PASSWORD_HASHERS` dans `settings.py`).
- Autorisation par rôle : décorateur custom `@business_owner_required` (vérifie `request.user.is_authenticated and request.user.role == "business_owner"`) appliqué sur toutes les vues `catalog`/`businesses`. Accès à Django Admin déjà géré nativement par `is_staff`/`is_superuser`, pas de décorateur à écrire pour cette partie.
- Réinitialisation de mot de passe : réservée au super_admin via une action Django Admin custom sur `User`, génère un mot de passe temporaire aléatoire affiché une seule fois — pas d'envoi automatisé.
- Limitation des tentatives de connexion : `django-axes` ou `django-ratelimit` sur la vue de connexion, 5 tentatives par email/IP par tranche de 10 minutes, message générique identique en cas d'email inexistant ou de mot de passe erroné.

---

## 14. Règles d'isolation tenant

- Aucune vue `catalog`/`businesses` ne doit accepter un `business_id` en paramètre d'URL ou de formulaire pour déterminer le tenant — il vient **exclusivement** de `request.user.business`.
- Toute vue qui reçoit un identifiant d'objet (`pk` de produit/catégorie) en paramètre d'URL doit passer par `TenantScopedManager.for_business(request.user.business).get(pk=pk)` (renvoie `Http404` via `get_object_or_404` si absent du queryset filtré) — jamais `Product.objects.get(pk=pk)` sans filtrage.
- En cas de non-correspondance (objet appartenant à un autre tenant) : réponse 404, jamais 403, pour ne pas révéler l'existence de l'objet chez un autre commerce.
- **Critère d'acceptation testable** : un test Django (`TestCase` avec `self.client`) doit démontrer qu'un `business_owner` du commerce A, authentifié, qui tente d'accéder à `/dashboard/produits/<id>/modifier/` où `<id>` appartient au commerce B, reçoit un statut 404 et qu'aucune donnée du commerce B n'apparaît dans le contenu de la réponse.

---

## 15. Gestion des images

- Une image par produit, une image (logo) par commerce — pas de galerie, `ImageField` simple sur chaque modèle.
- Formats acceptés : JPEG, PNG, WebP, validés par ouverture réelle du fichier via Pillow dans un `clean_image()` du formulaire, pas seulement par extension.
- Taille maximale acceptée à l'upload : 5 Mo (`FileSizeValidator` custom ou vérification manuelle dans le formulaire).
- Traitement automatique post-upload : redimensionnement à une largeur maximale de 1200px (conservation du ratio), compression, conversion en JPEG sauf logo avec transparence (conservé en PNG) — implémenté via un signal `post_save` ou directement dans `core.images` appelé depuis le service concerné.
- Stockage S3-compatible (Cloudflare R2) configuré via `django-storages` (`STORAGES["default"]` dans `settings.py`), jamais le disque du conteneur applicatif.
- Nom de fichier : Django génère par défaut un nom sûr, mais on force un renommage explicite en UUID pour éviter toute fuite d'information via le nom original.
- Si aucune image n'est fournie pour un produit : image par défaut générique servie en asset statique, gérée au niveau du template (`{% if product.image %}...{% else %}...{% endif %}`).
- **Critère d'acceptation testable** : un upload d'un fichier `.exe` renommé en `.jpg` est rejeté avec une erreur de formulaire explicite ; un upload de 8 Mo est rejeté avant tout traitement.

---

## 16. Gestion des catégories

- Une `Category` appartient à un seul `Business`, nom unique au sein de ce commerce (`unique_together`).
- Une catégorie "Divers" est créée automatiquement à la création du `Business` (signal `post_save` sur `Business`, ou directement dans `businesses.services.create_business`), non supprimable (vérification explicite dans la vue de suppression).
- Suppression d'une catégorie non vide : confirmation côté interface, puis réassignation automatique de tous ses produits vers "Divers" dans une transaction atomique (`transaction.atomic()`).
- **Critère d'acceptation testable** : la suppression d'une catégorie contenant 3 produits aboutit à 3 produits recatégorisés en "Divers", zéro produit orphelin.

---

## 17. Gestion des produits

- Champs obligatoires à la création : nom, prix, catégorie. Description et image optionnelles.
- `price` validé `>= 0` à la fois par `CheckConstraint` en base et par validation de formulaire (`MinValueValidator(0)`).
- Statut `active`/`inactive` : un produit `inactive` est exclu du `QuerySet` des vues `storefront` mais reste visible/modifiable côté dashboard.
- **Critère d'acceptation testable** : un produit créé sans image affiche l'image par défaut sur la vitrine publique sans erreur ; un produit avec un prix négatif est rejeté par la validation serveur, indépendamment de toute validation HTML côté client.

---

## 18. Vitrine publique

- Page d'accueil (`/<slug>/`) : logo/nom, description courte, aperçu des catégories, bouton WhatsApp visible sans scroll.
- Catalogue (`/<slug>/catalogue/`) : produits actifs groupés par catégorie (`TenantScopedManager.for_business(business).filter(status="active")`), filtre par catégorie via paramètre de requête `?categorie=`, pas de pagination nécessaire à l'échelle de 10-60 produits.
- Fiche produit (`/<slug>/produit/<pk>/`) : photo, nom, prix, description, bouton WhatsApp avec message pré-rempli mentionnant le produit.
- Contact (`/<slug>/contact/`) : adresse, téléphone, horaires, bouton WhatsApp.
- Slug inexistant ou `Business.status = suspended` → `Http404` générique via `get_object_or_404`, sans distinguer les deux cas dans le message.

---

## 19. Génération des liens WhatsApp

- Format : `https://wa.me/<numero_international_sans_plus>?text=<message_encode_urllib>`.
- Message par défaut sur accueil/contact : `"Bonjour, je suis intéressé(e) par vos produits."`
- Message sur une fiche produit : `"Bonjour, je suis intéressé(e) par : <nom_du_produit>."`
- Si `whatsapp_number` est vide ou mal formé (validation à la saisie côté formulaire dashboard, format E.164 sans le `+`), le bouton WhatsApp n'est pas rendu (condition dans le template), pas de lien cassé.

---

## 20. Règles UX/UI

Inchangé par rapport à la version précédente :
- Un seul call-to-action principal par page (bouton WhatsApp), visible en haut ET en bas des pages longues.
- Palette et composants Tailwind homogènes imposés par le template, pas de personnalisation par le commerçant au MVP.
- Vocabulaire du dashboard en français simple, aucun jargon technique visible.
- Messages d'erreur et de confirmation via `django.contrib.messages`, affichés en haut de page, courts et explicites.

---

## 21. Responsive / mobile-first

- Conception et test prioritaires sur viewport ~360-390px de large.
- Grille catalogue : 1 colonne sur mobile, 2-3 colonnes au-delà de 768px (Tailwind `sm:`/`md:` standards).
- Images servies en résolution unique compressée à 1200px de large — pas de génération de plusieurs tailles au MVP.
- JavaScript minimal (aucun framework front), limité à des interactions ponctuelles si nécessaire (ex. filtre catégorie sans rechargement).

---

## 22. Sécurité

- CSRF activé par défaut sur tous les formulaires (middleware Django natif, `{% csrf_token %}` dans chaque `<form>`).
- Cookies de session : `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True` (en production), `SESSION_COOKIE_SAMESITE = "Lax"` — configuration explicite dans `settings.py`, ne pas se reposer sur les seuls défauts.
- Protections XSS/clickjacking activées par défaut (`SecurityMiddleware`, `X-Frame-Options`), à vérifier explicitement en configuration de production (`SECURE_*` settings, `DEBUG = False`).
- Rate limiting sur `/connexion/` (section 13).
- Toutes les requêtes passent par l'ORM Django (requêtes paramétrées), aucun SQL brut.
- Auto-échappement des templates Django conservé partout — ne jamais utiliser `|safe` sur du contenu saisi par un commerçant.
- Secrets (`SECRET_KEY`, identifiants base de données, clés du stockage objet) exclusivement en variables d'environnement (`django-environ` ou équivalent), jamais commités.
- Pas de 2FA, pas de chiffrement applicatif additionnel au MVP.

---

## 23. Validation des données

- Toute validation existe côté serveur (Django `Form`/`ModelForm`), indépendamment de toute validation HTML/JS côté client.
- Validateurs explicites par champ : `MinValueValidator(0)` sur le prix, `MaxLengthValidator` sur nom/description, validateur custom de format international sur `whatsapp_number`.
- Nettoyage (`.strip()`) des champs texte dans les méthodes `clean_<field>()` du formulaire.

---

## 24. Gestion des erreurs

- 404 personnalisée (template `404.html` cohérent avec le reste du site) pour : slug inexistant, produit/catégorie appartenant à un autre tenant, produit inexistant.
- 403 (template `403.html`) réservée aux cas où l'utilisateur est authentifié mais n'a pas le rôle requis pour la vue — jamais utilisée pour un problème d'appartenance tenant (cf. section 14, qui utilise 404).
- 500 (template `500.html`) générique sans détail technique exposé, `DEBUG = False` en production, erreurs journalisées côté serveur.
- Erreurs de validation de formulaire affichées au champ concerné via le rendu standard des formulaires Django, jamais par redirection vers une page d'erreur générique.

---

## 25. Tests unitaires

Couverture minimale exigée, via `django.test.TestCase` :
- `catalog.services` : création avec catégorie d'un autre tenant rejetée ; prix négatif rejeté ; statut basculé correctement.
- `catalog.services` (catégories) : suppression avec réassignation vers "Divers" ; nom dupliqué dans le même commerce rejeté ; nom dupliqué entre deux commerces différents accepté.
- `core.images` : rejet d'un fichier non-image ; rejet d'un fichier trop lourd ; redimensionnement produit une image ≤ 1200px de large.
- `core.whatsapp` : URL générée valide et correctement encodée avec et sans nom de produit ; absence de numéro → pas d'URL générée.
- `businesses.services` : slug généré unique même en cas de collision de nom ; création d'un `User` propriétaire correctement lié au `Business`.

---

## 26. Tests d'intégration

Via `django.test.Client` :
- Flow complet de connexion `business_owner` → accès `/dashboard/` → déconnexion.
- Flow complet de création d'un produit via le formulaire dashboard → apparition immédiate sur la vitrine publique.
- Flow de désactivation d'un produit → disparition de la vitrine publique, persistance dans le dashboard.
- Accès à `/admin/` par un utilisateur `business_owner` (`is_staff=False`) → redirection Django Admin standard vers la page de connexion admin, jamais d'accès aux données.
- Accès à `/<slug>/` avec un slug inexistant → 404.
- Accès à `/<slug>/` avec un `Business.status = suspended` → 404.

---

## 27. Tests multi-tenant

- Deux commerces A et B créés en base de test avec chacun un produit et une catégorie du même nom.
- Un `business_owner` de A connecté ne voit, sur `/dashboard/produits/`, que les produits de A (vérifié via le contenu du `QuerySet` passé au contexte de la vue, pas seulement via le HTML rendu).
- Tentative de A d'éditer/supprimer un produit de B via manipulation d'URL → 404, aucune donnée de B exposée dans la réponse.
- Les vitrines publiques `/A/` et `/B/` n'affichent chacune que leurs propres produits actifs, y compris quand les deux commerces ont des catégories de même nom.

---

## 28. Configuration environnementale

Variables d'environnement requises (via `django-environ`, aucune valeur par défaut en dur pour les secrets) :

- `DJANGO_ENV` (`development` / `production`)
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`False` en production, jamais laissé implicite)
- `DATABASE_URL` (format `postgresql://...`)
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`
- `ALLOWED_HOSTS`

Un fichier `.env.example` doit lister ces variables sans valeurs réelles.

---

## 29. Docker

- Un `Dockerfile` unique pour l'application Django (image Python slim, dépendances via `requirements.txt`, serveur applicatif de production — Gunicorn — jamais `runserver` en production).
- Un `docker-compose.yml` pour le développement local, avec deux services : `app` et `db` (PostgreSQL), volume persistant pour la base en local.
- `collectstatic` exécuté à la construction de l'image ou au démarrage du conteneur pour les fichiers statiques (CSS Tailwind compilé) — pas de stockage objet nécessaire pour les statiques, seulement pour les médias uploadés (images produits/logos).

---

## 30. Base de données

- PostgreSQL en développement et en production, hébergée en managé en production.
- Encodage UTF-8, fuseau horaire UTC (`USE_TZ = True` dans `settings.py`, comportement par défaut de Django).
- Pas de réplication ni de partitionnement au MVP.

---

## 31. Migrations

- Migrations Django natives (`makemigrations` / `migrate`), générées automatiquement à partir des modèles.
- Une migration par changement de schéma, jamais de modification manuelle du schéma en production.
- Chaque migration testée sur une copie de la base de développement avant application en production.

---

## 32. Déploiement

- Plateforme d'hébergement à faible coût (Railway, Render, ou VPS équivalent) exécutant l'image Docker applicative (Gunicorn).
- Base de données PostgreSQL managée par la même plateforme ou un service dédié.
- HTTPS automatique via la plateforme (Let's Encrypt géré).
- Sauvegardes automatiques quotidiennes de la base de données, vérifiées explicitement à la configuration.
- Domaine unique pour toute la plateforme, commerces différenciés par chemin (`/<slug>/`), pas de sous-domaine ni domaine personnalisé au MVP.

---

## 33. Structure exacte du repository

```
vitrine-digitale/
├── config/                       # projet Django (anciennement "projet racine")
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                   # inclut les urls.py de chaque app
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   │   ├── models.py              # modèle User personnalisé
│   │   ├── views.py                # LoginView/LogoutView custom
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── backends.py             # backend auth par email si nécessaire
│   ├── businesses/
│   │   ├── models.py                # Business
│   │   ├── admin.py                  # ModelAdmin Business + inline User
│   │   ├── services.py
│   │   ├── views.py                   # édition commerce, mot de passe (dashboard)
│   │   ├── forms.py
│   │   └── urls.py
│   ├── catalog/
│   │   ├── models.py                  # Category, Product
│   │   ├── managers.py                 # TenantScopedManager
│   │   ├── services.py
│   │   ├── views.py                     # CRUD dashboard produits/catégories
│   │   ├── forms.py
│   │   └── urls.py
│   ├── storefront/
│   │   ├── views.py                      # accueil, catalogue, fiche produit, contact
│   │   └── urls.py
│   └── core/
│       ├── tenant.py                      # résolution du business courant
│       ├── decorators.py                   # business_owner_required
│       ├── images.py                        # validation/traitement image
│       ├── whatsapp.py
│       └── qrcode.py
├── templates/
│   ├── storefront/
│   ├── dashboard/
│   ├── accounts/
│   └── shared/                                # layout de base, composants communs
├── static/                                     # sources Tailwind avant compilation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── multi_tenant/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 34. Conventions de code

- Python : PEP 8, `snake_case` pour fonctions/variables/fichiers, `PascalCase` pour les classes (modèles, formulaires, vues class-based si utilisées).
- Un service = un fichier `services.py` par app, pas de fonction de service de plus de ~40 lignes sans découpage.
- Aucun `QuerySet` construit directement dans `views.py` en dehors d'un appel à `TenantScopedManager` ou à un service.
- Noms de routes et de templates en français (cohérence avec les URLs déjà françaises), noms de variables/fonctions/modèles en anglais (convention Django standard).
- Un `forms.py` par app, un `ModelForm` par modèle principal.

---

## 35. Definition of Done

Une fonctionnalité est terminée seulement si :
- Le code respecte la structure d'apps/services (section 11, 33).
- Les critères d'acceptation listés dans la section correspondante sont vérifiés par au moins un test automatisé (`django.test.TestCase`).
- Aucune requête sur `Product`/`Category` ne contourne `TenantScopedManager`.
- L'affichage a été vérifié sur un viewport mobile (~375px).
- Aucune régression sur les tests multi-tenant existants (section 27).
- Les variables sensibles sont lues depuis la configuration d'environnement, jamais codées en dur.
- `DEBUG = False` et `ALLOWED_HOSTS` correctement configurés avant tout déploiement.

---

## 36. Découpage du développement en phases

**Phase A — Socle applicatif**
Projet Django créé, apps `accounts`/`businesses`/`catalog`/`storefront`/`core` scaffoldées, configuration PostgreSQL, Docker/Docker Compose fonctionnels, première migration.

**Phase B — Authentification et rôles**
Modèle `User` personnalisé, connexion par email, `business_owner_required`, création d'un `super_admin` initial via `createsuperuser`, configuration Django Admin pour `Business` (avec inline `User`).

**Phase C — Isolation tenant et CRUD dashboard**
`TenantScopedManager`, CRUD produits/catégories dans `catalog`, édition des infos commerce dans `businesses`, tests multi-tenant.

**Phase D — Vitrine publique**
App `storefront` complète (accueil, catalogue, fiche produit, contact), template public homogène, responsive mobile-first.

**Phase E — Images, WhatsApp, QR code, Open Graph**
`core.images` (upload, validation, compression, stockage S3), `core.whatsapp`, `core.qrcode`, balises Open Graph sur les templates publics.

**Phase F — Sécurité et durcissement**
Configuration `SECURE_*`, rate limiting sur la connexion, revue de toutes les vues contre la checklist section 14 et 22, suite de tests complète.

**Phase G — Déploiement**
Dockerfile de production (Gunicorn), `collectstatic`, déploiement sur la plateforme choisie, configuration du stockage objet de production, vérification des sauvegardes.

---

## 37. Critères d'acceptation de chaque phase

**Phase A** : l'application démarre via `docker-compose up`, se connecte à PostgreSQL, `python manage.py migrate` s'applique sans erreur.

**Phase B** : un `super_admin` peut se connecter à `/admin/`, créer un `Business` avec son `User` propriétaire inline, et ce dernier peut se connecter via `/connexion/` et accéder à un `/dashboard/` vide.

**Phase C** : tous les tests de la section 27 passent ; un `business_owner` peut créer/modifier/supprimer un produit et une catégorie exclusivement dans son propre commerce.

**Phase D** : la vitrine publique d'un commerce affiche exactement ses produits actifs, groupés par catégorie, sur un viewport mobile sans défaut d'affichage visible.

**Phase E** : un upload d'image invalide est rejeté avec message clair ; le bouton WhatsApp ouvre une conversation pré-remplie correcte ; le lien partagé sur WhatsApp affiche un aperçu (image + titre) correct ; le QR code généré redirige bien vers la vitrine.

**Phase F** : aucun formulaire ne peut être soumis sans jeton CSRF valide ; 6 tentatives de connexion successives avec mauvais mot de passe déclenchent un blocage temporaire ; l'ensemble des tests unitaires, d'intégration et multi-tenant passe.

**Phase G** : l'application est accessible en HTTPS sur l'environnement de production, une vitrine de test créée en production reste accessible après redéploiement du conteneur.

---

## IMPLEMENTATION ORDER

1. Structure du repository (section 33), projet Django initialisé, configuration (section 28, 29).
2. Modèle `User` personnalisé (`AUTH_USER_MODEL`) — **doit être fait avant la première migration**, car changer de modèle User après coup est coûteux en Django.
3. Modèles `Business`, `Category`, `Product` (section 8) et migrations (section 31).
4. `TenantScopedManager` (section 7, 12) — construit avant tout CRUD, car tout le reste en dépend.
5. Backend d'authentification par email + vues `accounts` (connexion/déconnexion) + décorateur `business_owner_required` (section 13).
6. Configuration Django Admin pour `Business` (inline `User`, actions "réinitialiser mot de passe", "suspendre"/"réactiver") — remplace un blueprint super_admin entier.
7. Création manuelle d'un `super_admin` initial (`python manage.py createsuperuser`).
8. `catalog.services` + vues dashboard catégories (section 16).
9. `catalog.services` + vues dashboard produits (section 17).
10. `core.images` intégré aux formulaires produit/commerce (section 15).
11. App `storefront` : accueil, catalogue, fiche produit, contact (section 18).
12. `core.whatsapp` intégré aux templates publics (section 19).
13. `core.qrcode` + vue `/<slug>/qr/` (section 10).
14. Balises Open Graph sur les templates publics (section 18).
15. Durcissement sécurité : `SECURE_*` settings, rate limiting, cookies (section 22).
16. Suite de tests complète : unitaires (25) → intégration (26) → multi-tenant (27).
17. Dockerfile de production + `collectstatic` + déploiement (section 32).

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
- Modèles `Order`, `Lead`, ou `Image` en tant que table séparée
- Un blueprint/app "super_admin" custom qui réimplémente ce que Django Admin fait déjà nativement
- Toute forme d'API REST/JSON publique non demandée explicitement (pas de Django REST Framework)
- Tout framework JavaScript front (React, Vue, etc.)
- Toute infrastructure d'envoi d'email
- Utilisation du système de permissions granulaires Django (`django.contrib.auth.permissions`) — la distinction de rôle via le champ `role` suffit au MVP

---

## 38. Règles d'implémentation pour l'agent IA

Cette spécification constitue la source de vérité principale pour l'implémentation.

L'agent de développement IA doit respecter les règles suivantes :

### 38.1 Ne pas élargir le scope

L'agent ne doit pas implémenter de fonctionnalité absente du scope du MVP.

Si une idée semble utile mais n'est pas explicitement demandée :

1. ne pas l'implémenter ;
2. la signaler dans le compte-rendu ;
3. poursuivre avec le scope existant.

Exemples de fonctionnalités à ne pas ajouter spontanément :

* recherche ;
* pagination ;
* notifications ;
* API REST ;
* analytics ;
* système de commande ;
* système de paiement ;
* personnalisation avancée ;
* architecture frontend SPA.

### 38.2 Ne pas remplacer une décision architecturale

Les choix suivants sont considérés comme verrouillés :

* Django ;
* PostgreSQL ;
* Docker Compose en développement ;
* Django Admin pour le `super_admin` ;
* templates Django côté serveur ;
* Tailwind CSS ;
* stockage S3-compatible pour les médias ;
* architecture multi-tenant à base de `business_id` ;
* pas de Django REST Framework ;
* pas de framework JavaScript frontend.

L'agent ne doit pas remplacer ces choix sans demande explicite.

### 38.3 Modifier progressivement

L'agent doit travailler par petites étapes.

Après chaque étape importante :

1. modifier les fichiers nécessaires ;
2. lancer les tests concernés ;
3. corriger les erreurs ;
4. vérifier que les tests précédents passent ;
5. seulement ensuite passer à l'étape suivante.

Il est interdit de générer l'intégralité de l'application en une seule opération sans validation intermédiaire.

### 38.4 Ne jamais masquer une erreur

L'agent ne doit jamais :

* désactiver un test pour le faire passer ;
* supprimer une assertion ;
* utiliser `# noqa` ou équivalent pour contourner un problème architectural ;
* désactiver CSRF ;
* désactiver les validations ;
* utiliser `|safe` pour contourner l'échappement Django ;
* supprimer une contrainte de sécurité pour simplifier l'implémentation ;
* remplacer PostgreSQL par SQLite uniquement pour faire fonctionner les tests.

Toute erreur doit être comprise puis corrigée.

---

## 39. Workflow de travail obligatoire de l'agent

Pour chaque phase, utiliser le cycle suivant :

```text
ANALYSER
   ↓
PLANIFIER
   ↓
IMPLÉMENTER
   ↓
TESTER
   ↓
CORRIGER
   ↓
VÉRIFIER
   ↓
CHECKPOINT
```

Avant de modifier plusieurs fichiers simultanément, l'agent doit identifier :

* les fichiers concernés ;
* les dépendances ;
* les modèles impactés ;
* les migrations nécessaires ;
* les tests à ajouter ou modifier.

---

## 40. Checkpoints obligatoires

### Checkpoint A — Socle

Conditions :

* projet Django lancé ;
* PostgreSQL accessible ;
* Docker Compose fonctionnel ;
* variables d'environnement chargées ;
* `manage.py check` sans erreur ;
* migrations appliquées ;
* serveur Django accessible.

Commandes minimales :

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

Aucun développement fonctionnel ne doit commencer si le socle n'est pas stable.

---

### Checkpoint B — Authentification

Conditions :

* `AUTH_USER_MODEL` configuré ;
* connexion par email fonctionnelle ;
* déconnexion fonctionnelle ;
* `super_admin` fonctionnel ;
* `business_owner` fonctionnel ;
* protection du dashboard fonctionnelle ;
* business owner incapable d'accéder à Django Admin.

Tests obligatoires :

```bash
python manage.py test apps.accounts
```

---

### Checkpoint C — Multi-tenant

Avant de construire toute l'interface CRUD, vérifier :

```text
Business A
 ├── Category A
 └── Product A

Business B
 ├── Category B
 └── Product B
```

Un utilisateur de A :

* voit A ;
* ne voit jamais B ;
* ne peut pas modifier B ;
* ne peut pas supprimer B ;
* reçoit 404 lorsqu'il tente d'accéder directement à un objet de B.

Ce checkpoint est critique.

**L'interface ne doit pas être considérée comme fonctionnelle tant que l'isolation tenant n'est pas démontrée par les tests.**

---

## 41. Stratégie de développement du multi-tenant

Le filtrage tenant doit être centralisé autant que possible.

Exemple conceptuel :

```python
products = Product.objects.for_business(request.user.business)
```

et non :

```python
products = Product.objects.all()
```

puis filtrage ultérieur.

Pour une opération sur un objet :

```python
product = get_object_or_404(
    Product.objects.for_business(request.user.business),
    pk=pk,
)
```

Il est interdit de récupérer un objet avec :

```python
Product.objects.get(pk=pk)
```

dans une vue dashboard.

Même règle pour `Category`.

---

## 42. Services métier

Les services doivent rester indépendants de HTTP autant que possible.

Un service ne doit pas dépendre directement de :

* `request`;
* `HttpResponse`;
* `redirect`;
* messages Django ;
* templates.

Exemple :

```python
create_product(
    business=business,
    name=name,
    price=price,
    category=category,
)
```

La vue est responsable de :

* récupérer les données du formulaire ;
* appeler le service ;
* afficher le résultat ;
* rediriger.

Le service est responsable de :

* vérifier les règles métier ;
* effectuer les opérations ;
* garantir les invariants ;
* utiliser les transactions lorsque nécessaire.

---

## 43. Transactions

Utiliser `transaction.atomic()` lorsqu'une opération comporte plusieurs modifications dépendantes.

Cas obligatoires :

### Suppression d'une catégorie

```text
Suppression catégorie
        ↓
Recherche catégorie Divers
        ↓
Réassignation produits
        ↓
Suppression catégorie
```

Ces opérations doivent être atomiques.

### Création d'un commerce

```text
Business
   +
User propriétaire
   +
Category Divers
```

Si une étape échoue, l'opération complète doit être annulée.

---

## 44. Gestion du compte propriétaire

Lorsqu'un `Business` est créé depuis Django Admin :

1. le nom du commerce est validé ;
2. le slug est généré ;
3. le `Business` est créé ;
4. la catégorie `Divers` est créée ;
5. le compte `business_owner` est créé ;
6. le compte est associé au commerce ;
7. le mot de passe initial est généré de manière sécurisée ;
8. le mot de passe temporaire est affiché une seule fois à l'administrateur.

Le mot de passe temporaire ne doit jamais :

* être écrit dans les logs ;
* être enregistré en clair en base ;
* apparaître dans une réponse publique ;
* être inclus dans une exception.

---

## 45. Règle concernant les mots de passe temporaires

Le mot de passe temporaire doit être généré avec une source aléatoire cryptographiquement sûre.

Le compte doit être marqué comme nécessitant idéalement un changement de mot de passe lors de la première connexion si cette fonctionnalité est implémentée simplement.

Si cette fonctionnalité ajoute une complexité disproportionnée au MVP, elle peut être remplacée par une procédure manuelle documentée dans le README.

Le mot de passe ne doit être affiché qu'à l'administrateur qui vient d'effectuer l'action.

---

## 46. Images — pipeline obligatoire

Le traitement d'une image suit cette chaîne :

```text
Upload
  ↓
Taille maximale
  ↓
Ouverture Pillow
  ↓
Vérification image réelle
  ↓
Validation format
  ↓
Redimensionnement
  ↓
Compression
  ↓
Conversion éventuelle
  ↓
Nom UUID
  ↓
Stockage S3/R2
```

Le fichier original ne doit pas être considéré comme fiable simplement parce que son extension est `.jpg`, `.png` ou `.webp`.

Un fichier contenant du contenu non-image et renommé `.jpg` doit être rejeté.

---

## 47. Stockage des fichiers

L'application ne doit pas dépendre du système de fichiers local du conteneur pour les médias persistants en production.

Les médias doivent utiliser le backend S3-compatible.

En développement, si les credentials S3 ne sont pas disponibles, une configuration locale peut être utilisée temporairement uniquement pour faciliter le développement, mais elle ne doit pas modifier le comportement métier.

Le README doit expliquer clairement les deux modes.

---

## 48. Templates

Structure minimale :

```text
templates/
├── base.html
├── 404.html
├── 403.html
├── 500.html
├── accounts/
│   └── login.html
├── dashboard/
│   ├── base.html
│   ├── index.html
│   ├── produits/
│   │   ├── list.html
│   │   └── form.html
│   ├── categories/
│   │   └── list.html
│   ├── commerce/
│   │   └── form.html
│   └── password/
│       └── form.html
├── storefront/
│   ├── home.html
│   ├── catalogue.html
│   ├── produit.html
│   └── contact.html
└── shared/
    ├── messages.html
    └── components/
```

Les templates doivent :

* rester simples ;
* ne pas contenir de logique métier ;
* utiliser les URLs Django nommées ;
* utiliser les messages Django ;
* respecter l'échappement automatique ;
* être utilisables sur mobile.

---

## 49. URLs nommées

Toutes les URLs doivent être nommées.

Exemples :

```text
accounts:login
accounts:logout

catalog:dashboard
catalog:product_list
catalog:product_create
catalog:product_update
catalog:product_delete

businesses:settings
businesses:password_change

storefront:home
storefront:catalogue
storefront:product_detail
storefront:contact
storefront:qr
```

Les templates ne doivent pas hardcoder les chemins URL.

Utiliser :

```django
{% url 'storefront:home' business.slug %}
```

plutôt que :

```django
href="/{{ business.slug }}/"
```

---

## 50. Dashboard

Le dashboard doit rester volontairement simple.

### Page d'accueil

Afficher uniquement :

* nom du commerce ;
* nombre de produits ;
* nombre de produits actifs ;
* nombre de catégories ;
* lien vers la vitrine ;
* actions principales.

Pas de statistiques avancées.

### Produits

La liste doit permettre :

* voir ;
* ajouter ;
* modifier ;
* supprimer ;
* activer/désactiver.

### Catégories

La liste doit permettre :

* voir ;
* créer ;
* renommer ;
* supprimer.

### Commerce

Le commerçant peut modifier :

* nom ;
* logo ;
* description ;
* WhatsApp ;
* téléphone ;
* adresse ;
* horaires.

Le slug ne doit pas être modifiable.

---

## 51. Storefront

La vitrine publique doit être conçue comme un produit destiné principalement au mobile.

Ordre visuel recommandé sur la page d'accueil :

```text
Logo
Nom du commerce
Description
CTA WhatsApp
Catégories
Produits populaires / aperçu
Informations pratiques
CTA WhatsApp
```

Le bouton WhatsApp doit être facilement identifiable.

La vitrine ne doit jamais exposer :

* IDs internes inutiles ;
* informations utilisateur ;
* informations administratives ;
* données d'un autre commerce ;
* produits inactifs.

---

## 52. SEO et Open Graph

Chaque page publique doit disposer au minimum de :

```html
<title>
<meta name="description">
<meta property="og:title">
<meta property="og:description">
<meta property="og:image">
<meta property="og:url">
```

La fiche produit doit générer des métadonnées spécifiques au produit.

La page d'accueil doit utiliser les informations du commerce.

Si aucun logo/image n'est disponible, utiliser une image par défaut.

---

## 53. QR Code

Le QR code doit pointer vers :

```text
https://<domaine>/<business-slug>/
```

Il ne doit jamais pointer vers une URL interne de dashboard.

Le QR code doit être généré dynamiquement.

Le contenu doit rester valide même après redéploiement de l'application.

---

## 54. WhatsApp

La génération des liens WhatsApp doit être centralisée dans :

```text
apps/core/whatsapp.py
```

Aucun template ne doit construire manuellement une URL `wa.me`.

Le service doit :

1. nettoyer le numéro ;
2. vérifier le format ;
3. construire le message ;
4. encoder le message ;
5. retourner l'URL.

Si aucune URL valide ne peut être générée :

```python
None
```

doit être retourné.

Le template décide alors de ne pas afficher le bouton.

---

## 55. Configuration Django

Le fichier `settings.py` doit être organisé par sections :

```text
BASE
INSTALLED_APPS
MIDDLEWARE
URLS
TEMPLATES
DATABASE
AUTHENTICATION
PASSWORDS
STATIC
MEDIA
STORAGE
SECURITY
LOCALIZATION
LOGGING
```

Les valeurs sensibles ne doivent jamais être présentes directement dans le code.

Les valeurs de développement peuvent être documentées dans `.env.example`, mais aucune vraie clé ne doit y figurer.

---

## 56. Gestion de DEBUG

La valeur par défaut ne doit pas être dangereuse.

Production :

```text
DEBUG=False
```

Les erreurs détaillées Django ne doivent jamais être exposées publiquement en production.

Avant déploiement :

```bash
python manage.py check --deploy
```

doit être exécuté.

Toute alerte de sécurité pertinente doit être traitée ou explicitement documentée.

---

## 57. Logging

Le système doit journaliser les événements utiles :

* erreurs serveur ;
* erreurs d'upload ;
* erreurs de stockage ;
* événements importants de sécurité.

Ne jamais journaliser :

* mots de passe ;
* tokens ;
* clés API ;
* secrets ;
* contenu sensible inutile.

Les logs doivent permettre de diagnostiquer une erreur sans exposer de credentials.

---

## 58. Tests — règle de non-régression

Avant chaque checkpoint :

```bash
python manage.py test
```

doit être exécuté.

Après une correction de bug :

1. reproduire le bug avec un test ;
2. corriger le code ;
3. vérifier que le test échoue avant correction si possible ;
4. vérifier qu'il passe après correction ;
5. exécuter toute la suite.

Un bug corrigé sans test de non-régression n'est pas considéré comme définitivement traité lorsqu'un test automatisé est raisonnablement possible.

---

## 59. Tests prioritaires

L'ordre de priorité des tests est :

### Priorité 1 — Sécurité

* isolation tenant ;
* authentification ;
* permissions ;
* CSRF ;
* accès admin.

### Priorité 2 — Métier

* produits ;
* catégories ;
* prix ;
* statut ;
* réassignation `Divers`.

### Priorité 3 — Médias

* validation ;
* taille ;
* traitement ;
* stockage.

### Priorité 4 — Présentation

* URLs ;
* vitrine ;
* WhatsApp ;
* QR code ;
* Open Graph.

---

## 60. Vérification manuelle finale

Avant de déclarer le MVP terminé, effectuer manuellement :

### Commerce A

Créer :

```text
Commerce : Boutique A
Catégorie : Vêtements
Produit : Chemise
Prix : 5000 FCFA
```

### Commerce B

Créer :

```text
Commerce : Boutique B
Catégorie : Vêtements
Produit : Pantalon
Prix : 7500 FCFA
```

Vérifier :

* A ne voit jamais B ;
* B ne voit jamais A ;
* `/boutique-a/` affiche uniquement A ;
* `/boutique-b/` affiche uniquement B ;
* les catégories identiques ne provoquent aucune collision ;
* un produit inactif disparaît de la vitrine ;
* la suppression d'une catégorie réassigne les produits vers `Divers`.

---

## 61. Scénario de test complet

Le scénario suivant doit fonctionner sans intervention manuelle dans la base :

```text
1. Créer le super_admin
2. Se connecter à /admin/
3. Créer Business A
4. Créer son business_owner
5. Se connecter comme business_owner
6. Créer une catégorie
7. Créer un produit
8. Modifier le produit
9. Désactiver le produit
10. Vérifier sa disparition de la vitrine
11. Réactiver le produit
12. Vérifier sa présence
13. Modifier les informations du commerce
14. Vérifier la vitrine
15. Générer le QR code
16. Tester WhatsApp
17. Se déconnecter
18. Vérifier qu'un autre business_owner ne peut pas accéder au dashboard
```

---

## 62. Git

Le développement doit utiliser Git dès le début.

Commits recommandés :

```text
chore: initialize django project
feat: add custom user model
feat: add business catalog models
feat: add tenant scoped manager
feat: add email authentication
feat: add django admin business management
feat: add category management
feat: add product management
feat: add storefront
feat: add image processing
feat: add whatsapp links
feat: add qr code generation
test: add tenant isolation tests
test: add catalog integration tests
security: harden production settings
chore: add docker production setup
docs: add deployment instructions
```

Éviter les commits vagues :

```text
update
fix stuff
changes
test
final
```

---

## 63. README obligatoire

Le README doit expliquer :

### Installation

```text
Prérequis
Variables d'environnement
Installation
Docker Compose
Migrations
Création du super_admin
Lancement
```

### Développement

```text
Lancer l'application
Lancer les tests
Créer une migration
Appliquer une migration
Compiler Tailwind
```

### Architecture

Expliquer brièvement :

```text
accounts
businesses
catalog
storefront
core
```

### Multi-tenant

Expliquer la règle d'isolation.

### Production

Expliquer :

* Docker ;
* Gunicorn ;
* PostgreSQL ;
* stockage S3/R2 ;
* variables d'environnement ;
* HTTPS ;
* sauvegardes.

---

## 64. Gestion des dépendances

Les dépendances doivent être minimales.

Dépendances attendues à titre indicatif :

```text
Django
psycopg
django-environ
Pillow
django-storages
boto3
qrcode
gunicorn
```

Pour le rate limiting, choisir **une seule** solution :

```text
django-ratelimit
```

ou :

```text
django-axes
```

Ne pas installer les deux.

Les versions doivent être verrouillées dans l'environnement de production.

L'agent doit vérifier les versions actuellement compatibles au moment de l'installation plutôt que d'inventer des numéros de version.

---

## 65. Tailwind

Le frontend doit rester léger.

Utiliser Tailwind uniquement pour :

* layout ;
* responsive ;
* composants ;
* couleurs ;
* spacing ;
* états interactifs simples.

Ne pas introduire :

* React ;
* Vue ;
* Alpine.js ;
* jQuery ;
* framework frontend supplémentaire.

Le JavaScript éventuel doit être limité aux interactions qui apportent une réelle valeur.

---

## 66. Principe de simplicité

Lorsque Django fournit nativement une solution fiable, elle doit être préférée.

Exemples :

```text
Django Admin       → administration
Django ORM         → accès base
Django Forms       → validation
Django Auth        → authentification
Django Messages    → notifications
Django CSRF        → protection CSRF
Django Sessions    → sessions
Django Migrations  → migrations
```

Ne pas réimplémenter ces mécanismes inutilement.

---

## 67. Gestion des ambiguïtés

Si une ambiguïté mineure apparaît pendant l'implémentation :

1. chercher d'abord la décision correspondante dans ce document ;
2. privilégier la solution Django native ;
3. choisir la solution la plus simple compatible avec le MVP ;
4. documenter la décision dans le rapport final.

Si l'ambiguïté concerne une décision architecturale majeure, **arrêter l'implémentation concernée** et demander confirmation avant de modifier l'architecture.

---

## 68. Rapport de progression de l'agent

À la fin de chaque phase, l'agent doit produire un court rapport :

```text
PHASE :
Statut : DONE / BLOCKED

Implémenté :
- ...

Tests :
- ...

Fichiers principaux modifiés :
- ...

Problèmes rencontrés :
- ...

Décisions prises :
- ...

Prochaine étape :
- ...
```

Le rapport doit rester factuel.

Ne pas déclarer une phase terminée si ses critères d'acceptation ne sont pas satisfaits.

---

## 69. Conditions de blocage

L'agent doit s'arrêter et signaler `BLOCKED` lorsqu'il rencontre :

* une dépendance externe indisponible ;
* des credentials manquants ;
* une décision architecturale non couverte par cette spécification ;
* une migration destructive nécessitant une décision ;
* une incompatibilité majeure entre dépendances ;
* un problème empêchant de vérifier un critère d'acceptation.

Il ne doit pas contourner silencieusement le problème.

---

## 70. Definition of Done — MVP complet

Le MVP est considéré comme livré uniquement lorsque toutes les conditions suivantes sont satisfaites :

### Fonctionnel

* [ ] super_admin fonctionnel ;
* [ ] business_owner fonctionnel ;
* [ ] création d'un commerce ;
* [ ] création d'un propriétaire ;
* [ ] gestion des catégories ;
* [ ] gestion des produits ;
* [ ] édition du commerce ;
* [ ] vitrine publique ;
* [ ] catalogue ;
* [ ] fiche produit ;
* [ ] contact ;
* [ ] WhatsApp ;
* [ ] QR code ;
* [ ] Open Graph.

### Multi-tenant

* [ ] isolation Business A / Business B ;
* [ ] aucun accès croisé ;
* [ ] tests 404 sur objets étrangers ;
* [ ] vitrines isolées.

### Sécurité

* [ ] CSRF ;
* [ ] authentification ;
* [ ] autorisation ;
* [ ] rate limiting ;
* [ ] cookies sécurisés en production ;
* [ ] DEBUG désactivé en production ;
* [ ] secrets externalisés ;
* [ ] aucun SQL brut ;
* [ ] aucun secret dans les logs.

### Images

* [ ] validation MIME réelle ;
* [ ] limite 5 Mo ;
* [ ] compression ;
* [ ] redimensionnement ;
* [ ] UUID ;
* [ ] stockage S3/R2.

### Tests

* [ ] tests unitaires ;
* [ ] tests intégration ;
* [ ] tests multi-tenant ;
* [ ] tests images ;
* [ ] tests WhatsApp ;
* [ ] tests catégories ;
* [ ] tests produits ;
* [ ] suite complète verte.

### Infrastructure

* [ ] Docker Compose développement ;
* [ ] PostgreSQL ;
* [ ] Dockerfile production ;
* [ ] Gunicorn ;
* [ ] collectstatic ;
* [ ] variables d'environnement ;
* [ ] README ;
* [ ] procédure de déploiement.

---

## 71. Instruction finale à Kilo Code

Tu es l'agent d'implémentation de ce projet.

Tu dois :

1. lire l'intégralité de `SPEC.md` avant de modifier le projet ;
2. respecter strictement le scope ;
3. suivre `IMPLEMENTATION ORDER` ;
4. travailler par checkpoints ;
5. écrire les tests avant ou en même temps que les fonctionnalités critiques ;
6. vérifier l'isolation multi-tenant avant de poursuivre le CRUD ;
7. utiliser les mécanismes natifs Django lorsque ceux-ci répondent au besoin ;
8. ne jamais contourner une règle de sécurité pour simplifier l'implémentation ;
9. ne jamais inventer une fonctionnalité ;
10. signaler explicitement tout blocage ;
11. exécuter les tests après chaque étape significative ;
12. ne déclarer une phase terminée que lorsque ses critères d'acceptation sont satisfaits.

### Priorité absolue

En cas de conflit entre rapidité d'implémentation et sécurité/isolation des données :

**sécurité et isolation des données gagnent toujours.**

En cas de conflit entre sophistication et simplicité :

**simplicité gagne toujours**, tant qu'elle respecte le périmètre et les critères d'acceptation.

### Objectif final

Livrer une première version réellement utilisable d'une plateforme de vitrines digitales multi-tenant permettant à un petit commerçant de :

```text
se connecter
     ↓
gérer ses catégories
     ↓
gérer ses produits
     ↓
mettre à jour son commerce
     ↓
obtenir sa vitrine publique
     ↓
recevoir des contacts WhatsApp
```

Le système doit être suffisamment propre et sécurisé pour servir de base aux futures évolutions, mais **aucune fonctionnalité future ne doit être construite au détriment du MVP actuel.**

**FIN DE LA SPECIFICATION**