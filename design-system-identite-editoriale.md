# 🎨 Design System — Nouvelle Identité "Éditorial Chaleureux"

> À donner à l'agent de développement pour remplacer l'identité actuelle (bleu-gris ardoise / typo condensée bold) sur l'ensemble de la plateforme (site public + dashboard).

---

## 1. Tokens couleur

```css
:root {
  /* Fonds */
  --color-bg-primary: #F5F1EA;      /* fond principal crème chaud */
  --color-bg-alt: #EDE7DC;          /* sections alternées */
  --color-bg-card: #FFFFFF;         /* cartes produit — fait ressortir les photos */
  --color-bg-dark: #1A1A1A;         /* footer, sections contraste fort */

  /* Texte */
  --color-text-primary: #1A1A1A;    /* noir profond, jamais de bleu-gris */
  --color-text-secondary: #6B6458;  /* gris chaud pour le texte secondaire */
  --color-text-inverse: #F5F1EA;    /* texte sur fond sombre */

  /* Accent */
  --color-accent: #B8A88A;          /* taupe/beige doré — bordures, badges, séparateurs */
  --color-accent-dark: #8B7355;     /* variante plus soutenue si besoin de contraste */
  --color-border: #E5DFD3;          /* bordures fines sur cartes/inputs */

  /* Sémantique (ne pas changer — lisibilité avant tout) */
  --color-success: #4A7C59;
  --color-error: #B3452C;
  --color-whatsapp: #25D366;        /* CTA WhatsApp reste vert — reconnaissance de marque */
}
```

### Config Tailwind (`tailwind.config.js`)
```js
theme: {
  extend: {
    colors: {
      cream: '#F5F1EA',
      'cream-alt': '#EDE7DC',
      ink: '#1A1A1A',
      taupe: '#B8A88A',
      'taupe-dark': '#8B7355',
      'border-light': '#E5DFD3',
      whatsapp: '#25D366',
    },
  },
}
```

---

## 2. Typographie

- **Famille unique** : une sans-serif géométrique fine — `Neue Montreal`, `General Sans`, ou à défaut `Inter` (poids 400/500, jamais 700+ sauf exception ci-dessous)
- **Fallback système** : `-apple-system, 'Segoe UI', sans-serif`

```css
:root {
  --font-primary: 'General Sans', -apple-system, 'Segoe UI', sans-serif;
}

.text-logo {
  font-size: 1.25rem;
  letter-spacing: 0.15em;
  font-weight: 500;
  text-transform: uppercase;
}

.text-nav {
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  font-weight: 400;
  text-transform: uppercase;
}

.text-hero {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 500;              /* jamais bold agressif */
  line-height: 1.1;
  letter-spacing: -0.01em;
}

.text-section-label {
  font-size: 0.75rem;
  letter-spacing: 0.12em;
  font-weight: 500;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.text-body {
  font-size: 1rem;
  line-height: 1.5;
  font-weight: 400;
  color: var(--color-text-primary);
}
```

⚠️ **Règle stricte** : supprimer toute police display condensée bold sur les libellés de navigation et le dashboard. Réserver le poids 500 max au H1 hero uniquement.

---

## 3. Espacement

Échelle 8px, cohérente entre public et dashboard :
```
4, 8, 16, 24, 32, 48, 64, 96px
```
- Padding interne cartes : 24px
- Gap entre cartes produit (grille) : 24px
- Marge verticale entre sections : 64-96px desktop, 48px mobile

---

## 4. Composants

### Boutons
```css
.btn-primary {
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
  padding: 14px 32px;
  border-radius: 2px;             /* pas d'arrondi prononcé */
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: opacity 220ms ease;
}
.btn-primary:hover { opacity: 0.85; }

.btn-secondary {
  background: transparent;
  border: 1px solid var(--color-text-primary);
  color: var(--color-text-primary);
  padding: 13px 32px;
  border-radius: 2px;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.btn-whatsapp {
  background: var(--color-whatsapp);
  color: #FFFFFF;
  border-radius: 4px;             /* seule exception — reste proche du bouton WhatsApp natif */
  padding: 14px 24px;
  font-weight: 500;
}
```

### Cartes produit
```css
.product-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 2px;
  /* pas d'ombre lourde — la sobriété fait le rendu premium */
}

.product-card__image-wrapper {
  aspect-ratio: 1 / 1;
  background: var(--color-bg-alt);   /* fond de secours si pas de photo */
  overflow: hidden;
}

.product-card__fallback-icon {
  /* icône silhouette produit neutre, PAS de lettre géante */
  color: var(--color-accent);
  opacity: 0.5;
}
```

### Badges / labels
```css
.badge {
  border: 1px solid var(--color-accent);
  color: var(--color-text-primary);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 2px;
  background: transparent;
}
```

---

## 5. Layout — adaptation multi-tenant (point critique)

### Hero flexible (remplace le hero "mannequin pleine hauteur")
Le hero de référence suppose une photo éditoriale professionnelle. Prévoir 3 variantes selon ce que le commerçant a réellement :

```
Variante A — Photo produit disponible
[ Texte + CTA à gauche ] [ Photo produit en aspect-ratio contrôlé à droite ]

Variante B — Pas de photo
[ Texte + CTA centré ] sur fond --color-bg-alt uni, pas de zone vide à droite

Variante C — Plusieurs produits phares
[ Texte + CTA à gauche ] [ Grille 2x2 de mini-photos à droite plutôt qu'une seule image ]
```
→ Le composant hero doit détecter automatiquement le nombre de produits/photos disponibles et choisir la variante, pas rester figé sur une seule mise en page.

### Tuiles catégories (remplace Women/Men/Bags/Shoes en dur)
- Génère dynamiquement une tuile par catégorie réellement créée par le commerçant (1 à N, pas 4 fixes)
- Si la catégorie n'a pas de photo : fond `--color-bg-alt` + nom de catégorie centré, même traitement typographique que les tuiles avec photo (cohérence visuelle même en absence d'image)

### Bandeau de réassurance
Garder ce bloc (livraison/retours/paiement/support) — pertinent pour rassurer un client qui achète via WhatsApp sans passage par un vrai panier e-commerce. Adapter les 4 items au contexte réel (ex: "Réponse rapide WhatsApp" plutôt que "24/7 Support" si pas de vrai support dédié).

---

## 6. Migration — ce qui change concrètement

| Élément actuel | Nouveau |
|---|---|
| Fond bleu-gris ardoise + texture grille | Fond crème `--color-bg-primary`, uni |
| Police condensée bold partout | Sans-serif fine, poids 400/500, réservée au hero pour le bold |
| Motif "coin coupé" (parallélogramme) | Bordures fines rectangulaires, angles droits ou très légèrement arrondis |
| Placeholder produit = lettre géante | Icône silhouette neutre sur fond `--color-bg-alt` |
| Boutons Modifier/Désactiver encadrés + Supprimer en texte seul | Tous en `.btn-secondary` avec la même forme, rouge réservé à Supprimer via couleur uniquement |
| Deux identités distinctes public/dashboard | Un seul système de tokens partagé, décliné en densité différente (dashboard = plus dense, public = plus aéré) |

---

## 7. Ce qui NE change PAS
- CTA WhatsApp reste vert (`--color-whatsapp`) — ne pas l'intégrer à la palette crème/noir, c'est un repère de reconnaissance pour l'utilisateur final
- Structure de navigation et fonctionnalités existantes — c'est un changement de peau visuelle, pas de refonte fonctionnelle
