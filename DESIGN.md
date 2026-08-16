# DESIGN.md — Direction artistique — Vitrine Digitale

## 1. Positionnement visuel

Vitrine Digitale est un outil destiné à de petits commerçants qui veulent simplement présenter leurs produits en ligne et recevoir des commandes/contact via WhatsApp.

Le design doit communiquer :

- simplicité
- confiance
- proximité
- modernité
- rapidité
- sérieux
- accessibilité

Le produit ne doit jamais donner l'impression d'être un logiciel complexe destiné à des développeurs ou à de grandes entreprises.

### Principe directeur

> "Un commerçant doit comprendre l'interface sans avoir besoin d'une formation."

Le produit doit être visuellement moderne mais fonctionnellement simple.

---

# 2. Architecture visuelle globale

Le projet possède deux univers visuels distincts :

1. **La vitrine publique**
2. **Le dashboard commerçant**

Ils partagent le même système de design mais n'ont pas la même densité.

### Vitrine

Priorité :

1. Produit
2. Prix
3. Catégorie
4. WhatsApp
5. Informations du commerce

### Dashboard

Priorité :

1. Produits
2. Actions rapides
3. Catégories
4. Informations du commerce
5. Paramètres

---

# 3. Principes fondamentaux

## Mobile-first

Le design doit être conçu d'abord pour :

- 360px
- 375px
- 390px

Puis adapté aux écrans plus larges.

Ne jamais concevoir d'abord pour desktop puis simplement réduire.

---

## Simplicité

Chaque écran doit répondre à une question simple.

Exemples :

Dashboard :

> "Qu'est-ce que je peux faire maintenant ?"

Catalogue :

> "Quels produits sont disponibles ?"

Produit :

> "Combien ça coûte et comment contacter le vendeur ?"

---

## Hiérarchie visuelle

Chaque page doit avoir :

- 1 titre principal
- 1 action principale
- des informations secondaires discrètes

Ne jamais avoir plusieurs boutons visuellement concurrents.

---

# 4. CTA principal

WhatsApp est le CTA principal de la vitrine.

Il doit être immédiatement identifiable.

### Règles

Sur mobile :

- bouton suffisamment grand pour être facilement touché
- hauteur minimale recommandée : 44px
- texte explicite
- icône WhatsApp possible
- contraste élevé

Exemple :

> Contacter sur WhatsApp

Éviter :

> Envoyer

> Contact

> Cliquez ici

Le CTA doit expliquer l'action.

---

# 5. Navigation

## Vitrine

Navigation extrêmement simple.

Structure recommandée :

```text
Logo / Nom du commerce

Accueil
Catalogue
Contact