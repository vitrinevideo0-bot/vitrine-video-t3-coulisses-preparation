# T3 — Matrice exacte des transitions 2 + 4 sur 30 secondes

**Statut :** candidat contractuel à valider — aucun moteur ni MP4 développé  
**Format :** 720 × 1280 · 30 i/s · 900 images · 30,000 s  
**Captations approuvées :** quatre seulement · 6 s / 8 s / 7 s / 9 s  
**Principe :** toutes les valeurs numériques ci-dessous sont des décisions moteur candidates; les familles et variantes proviennent des aperçus observés.

## Couverture

- Référence 2 : 7 familles/événements obligatoires couverts.
- Référence 4 : 9 familles/événements obligatoires couverts.
- Total : 16 profils paramétrés et 17 événements, car la famille de flash de la référence 2 intervient sous deux variantes.
- Aucune cinquième prise; grilles, répétitions et panneaux réemploient visuellement les quatre captures approuvées.

## Timeline image par image

| # | Images inclusives | Temps exact `[début, fin[` | Source | Transition / variantes | Placement |
|---:|---:|---:|---|---|---|
| 1 | 0–17 | 0.000000–0.600000 s | Réf. 4 | `R4_TILED_GRID_INTRO` · repeated_tile_grid+grid_scale_in | S1 |
| 2 | 18–35 | 0.600000–1.200000 s | Réf. 2 | `R2_GEOMETRIC_ARROW_MASK` · x_grid_background+diagonal_ribbon_reveal+arrow_mask_expand | S1 |
| 3 | 78–86 | 2.600000–2.900000 s | Réf. 2 | `R2_RADIAL_ZOOM` · zoom_pulse+center_push | S1 |
| 4 | 171–179 | 5.700000–6.000000 s | Réf. 4 | `R4_ORANGE_FLASH` · warm_orange_burn+white_bloom_peak | S1_TO_S2 |
| 5 | 224–225 | 7.466667–7.533333 s | Réf. 2 | `R2_HARD_ACTION_MATCH_CUT` · hard_action_match_cut | S2 |
| 6 | 252–263 | 8.400000–8.800000 s | Réf. 2 | `R2_SELECTIVE_COLOR_REVEAL` · desaturate_background+orange_slanted_color_panel | S2 |
| 7 | 303–312 | 10.100000–10.433333 s | Réf. 2 | `R2_FLASH_TRANSITION` · electric_light_streak+white_flash | S2 |
| 8 | 344–353 | 11.466667–11.800000 s | Réf. 4 | `R4_SOFT_OVERLAY_BLEND` · soft_overlay_blend | S2 |
| 9 | 374–383 | 12.466667–12.800000 s | Réf. 2 | `R2_FLASH_TRANSITION` · red_blue_strobe_film_burn | S2 |
| 10 | 408–419 | 13.600000–14.000000 s | Réf. 4 | `R4_KALEIDOSCOPE_MOSAIC` · vertical_mirror_mosaic+folded_tile_repeat | S2_TO_S3 |
| 11 | 453–466 | 15.100000–15.566667 s | Réf. 2 | `R2_MULTI_PANEL_SPLIT` · picture_in_picture_tiles+sliding_mosaic | S3 |
| 12 | 540–551 | 18.000000–18.400000 s | Réf. 4 | `R4_ROTATING_MASK` · rotating_plate_mask+circular_spin_wipe | S3 |
| 13 | 617–629 | 20.566667–21.000000 s | Réf. 4 | `R4_RADIAL_BLUR` · center_radial_blur+spin_blur | S3_TO_S4 |
| 14 | 699–710 | 23.300000–23.700000 s | Réf. 4 | `R4_WHIP_ZOOM` · whip_spin+zoom_blur_landing | S4 |
| 15 | 768–781 | 25.600000–26.066667 s | Réf. 4 | `R4_MULTI_PANEL_MATCH_CUT` · horizontal_repeater_rows+vertical_split_columns+panel_match_cut | S4 |
| 16 | 824–840 | 27.466667–28.033333 s | Réf. 2 | `R2_DIAGONAL_ROTATING_WIPE` · rotating_diagonal_band+strip_collapse | S4 |
| 17 | 885–899 | 29.500000–30.000000 s | Réf. 4 | `R4_BACKGROUND_FADE_TO_BLACK` · background_fade_only | S4 |

## Paramètres candidats par famille

- **`R4_TILED_GRID_INTRO`** — grille 3 × 4, écart 4 px, 12 décalages temporels muets, échelle 1,22 → 1,00, opacité 0,15 → 1,00.
- **`R2_GEOMETRIC_ARROW_MASK`** — fond X 3 × 5, masque flèche/ruban à −28°, plume 2 px, progression 0 → 1,25, entrée 1,14 → 1,02.
- **`R2_RADIAL_ZOOM`** — échelle 1,00 → 1,14 → 1,03, flou radial 0 → 16 → 0 px, ancre sur le produit.
- **`R4_ORANGE_FLASH`** — orange #F06B2D jusqu’à 0,86, bloom blanc jusqu’à 1,00, exposition +1,1 EV au pic.
- **`R2_HARD_ACTION_MATCH_CUT`** — coupe sans fondu au sommet du geste, erreur d’alignement ≤ 12 px, rapport d’échelle ≤ 1,08.
- **`R2_SELECTIVE_COLOR_REVEAL`** — fond désaturé, panneau oblique −16°, teinte orange à 0,38, couleur complète en sortie.
- **`R2_FLASH_TRANSITION`** — profil éclair/blanc puis profil stroboscope rouge–bleu–orange; copies audio muettes.
- **`R4_SOFT_OVERLAY_BLEND`** — deux couches, fondu sinusoïdal, overlay screen max. 0,62, flou 0 → 4 → 0 px.
- **`R4_KALEIDOSCOPE_MOSAIC`** — 5 bandes verticales miroir, rotations −6° à +6°, échelle 1,08, ombre de pli 0,22.
- **`R2_MULTI_PANEL_SPLIT`** — 5 panneaux, décalages −12/−6/0/+6/+12 images, bord 3 px, écart 6 px.
- **`R4_ROTATING_MASK`** — masque assiette circulaire, rayon 0,18 → 0,78, rotation 0° → 110°, plume 2 px.
- **`R4_RADIAL_BLUR`** — 24 échantillons, quantité 0 → 0,055 → 0, spin 0° → 12° → 0°.
- **`R4_WHIP_ZOOM`** — sortie 1,00 → 1,48, entrée 0,72 → 1,00, flou directionnel max. 30 px, atterrissage net 4 images.
- **`R4_MULTI_PANEL_MATCH_CUT`** — 3 rangées puis 3 colonnes, 14 images, ancre plat/verre, décalage d’entrée d’une image.
- **`R2_DIAGONAL_ROTATING_WIPE`** — 6 bandes à −24°, rotation jusqu’à 24°, fermeture puis révélation du hero — pas du noir.
- **`R4_BACKGROUND_FADE_TO_BLACK`** — seul le fond baisse à 0,18 et se floute à 7 px; sujet, CTA et WhatsApp restent à 1,00.

## Contrats non négociables

- La voix captée reste à vitesse **1,0×** et sans changement de hauteur.
- Toutes les copies servant aux panneaux et mosaïques sont **muettes**; seule la piste de base reste audible.
- La dernière image est l’image **899** à 29,966667 s. Le fond peut s’assombrir mais ne devient pas entièrement noir.
- Nom, produit, prix, quartier, WhatsApp et CTA restent lisibles; leur opacité finale vaut **1,00**.
- Aucun effet n’est demandé au commerçant pendant le tournage.

## Décision attendue

Valider ou corriger cette timeline et ses paramètres. Après validation seulement, elle pourra devenir le contrat moteur approuvé. Aucun rendu silencieux n’est encore produit.

**JSON complet :** `reverse-engineering/T3_TRANSITIONS_30S.json`  
**QA structurelle :** `qa/T3_TRANSITIONS_30S_QA.json`
