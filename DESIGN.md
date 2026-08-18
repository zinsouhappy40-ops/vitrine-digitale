# DESIGN.md - Identite editoriale chaleureuse

## Direction

Vitrine Digitale utilise une identite editoriale sobre et chaleureuse, commune a la vitrine publique et au dashboard. La vitrine est aeree et orientee produit. Le dashboard reprend les memes tokens avec une densite plus forte.

La reference visuelle sert uniquement de niveau de finition. Les categories, images et compositions restent dynamiques et multi-tenant.

## Couleurs

- Fond principal : `#F5F1EA`
- Fond alternatif : `#EDE7DC`
- Cartes : `#FFFFFF`
- Texte principal et surfaces sombres : `#1A1A1A`
- Texte secondaire : `#6B6458`
- Accent taupe : `#B8A88A`
- Accent taupe soutenu : `#8B7355`
- Bordures : `#E5DFD3`
- WhatsApp : `#25D366`
- Succes : `#4A7C59`
- Erreur : `#B3452C`

## Typographie

Une seule famille sans-serif geometrique : `General Sans`, avec repli systeme. Les poids usuels sont 400 et 500. Les titres restent legers, sans police condensee ni graisse agressive.

- Logo : capitales, espacement `0.15em`, poids 500
- Navigation : capitales, `0.8rem`, espacement `0.08em`
- Hero : `clamp(2rem, 5vw, 3.5rem)`, poids 500
- Libelles : `0.75rem`, capitales, espacement `0.12em`
- Corps : `1rem`, interligne 1.5

## Composants

- Boutons rectangulaires, rayon maximal de 4px
- Action principale noire, texte creme
- Action secondaire transparente, bordure noire
- WhatsApp vert avec texte blanc
- Cartes blanches, bordure fine, sans ombre lourde
- Images produit dans un cadre carre sur fond creme alternatif
- Placeholder neutre en forme de sac, jamais une initiale geante
- Champs blancs avec bordure fine et focus visible

## Mise En Page

L'espacement suit une echelle de 8px. Les sections publiques utilisent 48px sur mobile et 64 a 96px sur desktop. Le dashboard utilise le meme systeme avec des espacements plus compacts.

Le hero choisit automatiquement sa composition :

- aucune photo : texte centre sans zone vide
- une photo : texte et produit en deux colonnes
- plusieurs photos : texte et grille de produits

Les categories sont generees depuis les donnees du commerce. Une image de produit de la categorie sert de couverture lorsqu'elle existe ; sinon la tuile utilise un fond creme uni.

## Accessibilite

- Contraste WCAG AA pour les textes et controles
- Focus clavier sombre sur fond clair, blanc sur fond sombre
- Cibles tactiles de 44px minimum
- Libelles explicites et semantiques conservees
- Reduction des animations limitee au mouvement, sans supprimer les changements d'etat
