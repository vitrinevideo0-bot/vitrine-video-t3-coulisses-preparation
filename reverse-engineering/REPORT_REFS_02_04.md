# RESTAURATION-T3 — Reverse engineering des références 2 et 4

**Date :** 18 novembre 2026  
**Statut :** proposition préparée à la demande du propriétaire, en attente de validation des questions et des 12 écrans  
**Références retenues ensemble :** `R3-B03-REF-02` et `R3-B03-REF-04`  
**Durée imposée par le propriétaire :** 30 secondes  
**Captations commerçant :** exactement quatre

## 1. Décision du propriétaire

Le propriétaire a retenu simultanément :

1. **Food edit burger — SoftFilmClubᵐ³**  
   https://www.capcut.com/template-detail/Food-edit-burger/7601636981705133365
2. **Comida • restaurante — avi capuchina**  
   https://www.capcut.com/template-detail/protemplatetrends-pro-food-creadorestrella/7532579586337508669

Il exige que toutes les familles de transitions visibles dans ces deux templates apparaissent dans le contrat JSON de T3. Cette exigence est maintenant un invariant du projet. Les effets seront reconstruits de manière originale; aucun logo, texte, plat, personne ou média des créateurs ne sera copié.

## 2. OBSERVÉ — Référence 2 : Food edit burger

Aperçu inspecté : 720 × 1280, 30 i/s, 373 images, environ 12,43 s.  
SHA-256 de la copie temporaire d'analyse non committée : `f034551598842101a1345ab7b77ff31de2a8f17034af60b124de69b6555faaf7`.

### Familles réellement visibles

- fond répétitif en X et masque géométrique d'ouverture ;
- ruban diagonal qui révèle et agrandit le plan entrant ;
- impulsions de zoom radial centrées sur le produit ;
- coupe franche au sommet d'un geste ;
- désaturation du plan puis retour sélectif de la couleur dans un panneau orange oblique ;
- mosaïque de plusieurs panneaux et images dans l'image ;
- éclairs lumineux et flash blanc ;
- stroboscope rouge/bleu de type film burn ;
- fermeture finale par bandes diagonales rotatives.

### Point fort

La référence ne se contente pas d'enchaîner des beaux plans. Le produit change de statut visuel à chaque section : apparition, zoom, transformation couleur, multiplication, flash et fermeture graphique.

## 3. OBSERVÉ — Référence 4 : Comida • restaurante

Aperçu inspecté : 720 × 1280, 30 i/s, 695 images, environ 23,17 s.  
SHA-256 de la copie temporaire d'analyse non committée : `bbfe585968d83bda49133cd52df8b9dc9af636df6a902f72d9bd11891cbf2410`.

### Familles réellement visibles

- introduction en grille de vignettes répétées ;
- flash orange avec pic blanc et voile de lumière ;
- fusion douce de deux plans ;
- mosaïque verticale en miroir, proche d'un kaléidoscope ;
- masque circulaire/assiette en rotation ;
- flou radial et flou tournant ;
- whip-zoom avec atterrissage net ;
- répétition du plan en rangées horizontales ;
- séparation en colonnes verticales et raccord entre panneaux ;
- assombrissement final vers le noir.

### Point fort

Cette référence apporte une architecture plus ample : les panneaux permettent de montrer plusieurs détails d'une même préparation et le mouvement traverse toute la composition.

## 4. ADAPTÉ — Structure T3 en quatre prises

La durée totale est verrouillée à 30 secondes. Pour préserver le parcours déjà éprouvé par T1 et T2, la proposition conserve la répartition 6/8/7/9 secondes :

| Scène | Durée | Fonction | Ce que filme le commerçant |
|---|---:|---|---|
| S1 — Les ingrédients | 6 s | fraîcheur et preuve | ingrédients réels, plan de travail, approche lente |
| S2 — Le geste signature | 8 s | savoir-faire | un geste complet : verser, mélanger, retourner, découper, pétrir ou griller |
| S3 — Le dressage | 7 s | soin et finition | sauce, garniture ou touche finale, puis résultat stable |
| S4 — Prêt à servir | 9 s | désir et conversion | plat fini avancé vers la caméra, meilleur angle, maintien final |

Les transitions logicielles ne sont pas demandées au commerçant. Elles sont dérivées par recadrage, panneaux et masques à partir des quatre prises. Aucune cinquième captation n'est cachée dans le plan.

## 5. DÉCISION MOTEUR — Couverture obligatoire

Le contrat `T3_TRANSITIONS_30S_PROPOSITION.json` enregistre toutes les familles suivantes comme `required: true` :

### Référence 2

1. `R2_GEOMETRIC_ARROW_MASK`
2. `R2_RADIAL_ZOOM`
3. `R2_SELECTIVE_COLOR_REVEAL`
4. `R2_MULTI_PANEL_SPLIT`
5. `R2_FLASH_TRANSITION`
6. `R2_DIAGONAL_ROTATING_WIPE`
7. événement complémentaire `R2_HARD_ACTION_MATCH_CUT`

### Référence 4

1. `R4_TILED_GRID_INTRO`
2. `R4_ORANGE_FLASH`
3. `R4_KALEIDOSCOPE_MOSAIC`
4. `R4_RADIAL_BLUR`
5. `R4_ROTATING_MASK`
6. `R4_WHIP_ZOOM`
7. `R4_MULTI_PANEL_MATCH_CUT`
8. `R4_BACKGROUND_FADE_TO_BLACK`
9. événement complémentaire `R4_SOFT_OVERLAY_BLEND`

Le JSON distingue les familles principales et leurs variantes observées : ruban diagonal, X répétés, flash électrique, stroboscope rouge/bleu, rangées horizontales, colonnes verticales et masque d'assiette.

## 6. Timeline proposée

- **0–6 s / ingrédients :** grille répétée, masque géométrique, ruban diagonal et zoom radial ; burn orange vers S2.
- **6–14 s / geste :** coupe sur l'action, reveal noir-et-blanc vers couleur, flash électrique, fusion douce, strobe film burn ; mosaïque kaléidoscopique vers S3.
- **14–21 s / dressage :** panneaux multiples, masque d'assiette rotatif ; flou radial vers S4.
- **21–30 s / plat prêt :** whip-zoom, rangées et colonnes, wipe diagonal rotatif, hero shot et fond qui s'assombrit sans masquer le CTA.

La dernière image ne devient pas noire. Seul l'arrière-plan s'assombrit; le nom, le produit, le prix, le quartier, WhatsApp et l'action restent lisibles à 100 %.

## 7. Questions commerçant

T3 conserve les six clés canoniques de T1/T2 :

- `nom` — obligatoire ;
- `produit` — obligatoire ;
- `prix` — obligatoire ;
- `whatsapp` — obligatoire ;
- `quartier` — obligatoire ;
- `accroche` — facultative.

La formulation exacte et les contraintes se trouvent dans `form/questions_T3_PROPOSITION.json`. La langue parlée n'est pas transformée en septième champ commercial : une aide commune indique que le commerçant peut parler en français, en fon ou en anglais, ou ne pas parler.

## 8. Les douze écrans

Chaque scène possède les trois états éprouvés par T1/T2 :

- **A — Guide :** titre, durée, consigne, à filmer, à éviter, action simple, aide linguistique et exemple facultatif ;
- **B — Enregistrement :** caméra, micro, chrono, progression et arrêt automatique ;
- **C — Vérification :** relecture avec son, question de contrôle, `REFAIRE`, puis `SCÈNE SUIVANTE` ou `VOIR MON MONTAGE`.

Le décompte `3 · 2 · 1` reste transitoire et ne constitue pas un treizième écran.

## 9. État réel

- références 2 et 4 sélectionnées par le propriétaire ;
- reverse engineering documentaire effectué ;
- questions et douze écrans proposés ;
- aucune transition encore codée ;
- aucun moteur, rendu MP4, musique, voix, OTA ou déploiement commencé.

La prochaine porte est la validation humaine des six questions, des quatre consignes et de la planche des douze écrans.
