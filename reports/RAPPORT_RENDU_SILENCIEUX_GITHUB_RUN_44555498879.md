# T3 — Rapport du rendu silencieux v0.4 sans traits bleus

## Résultat

**PASS objectif.** Le master a été produit par GitHub Actions depuis le commit `f87d1ef913fe331b12cf10275f6c2e0392f16007`, puis téléchargé et revalidé indépendamment.

- run : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44555498879 ;
- pré-Release : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.4.0-silent-candidate-4 ;
- téléchargement direct : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.4.0-silent-candidate-4/VIDEO_T3_SILENCIEUSE_SANS_TRAITS_BLEUS_V0_4_A_VALIDER.mp4 .

## Master GitHub

- fichier : `VIDEO_T3_SILENCIEUSE_SANS_TRAITS_BLEUS_V0_4_A_VALIDER.mp4` ;
- SHA-256 : `cd61d3cf793874a8b7d2eb8fe694861048368ba64b01216395c6bba0eb879774` ;
- taille : 10 601 443 octets ;
- 30,000 s · 720 × 1280 · 30 i/s · 900 images ;
- H.264 / yuv420p ;
- zéro piste audio.

## Contrôles

- tests du moteur et des contrats : **16/16 PASS** ;
- validation sur le runner GitHub : **32/32 PASS** ;
- validation indépendante après téléchargement : **32/32 PASS** ;
- mêmes métadonnées vidéo et mêmes résultats de contrôle côté serveur et après téléchargement ;
- 15/15 assets téléchargés ;
- les 14 empreintes du manifeste `SHA256SUMS.txt` sont valides ;
- l’artefact Actions et les 15 assets de la pré-Release sont identiques octet par octet ;
- aucun rush brut publié.

## Suppression des séparateurs

Le JSON impose `gap_px: 0`, `border_px: 0`, `separator_lines: false` et `separator_color: null`. Le moteur applique désormais ce profil et conserve le déplacement des rangées et des colonnes.

- images serveur 771 et 778 inspectées à 40 % : aucun trait bleu/cyan horizontal ou vertical ;
- audit pixel sur les images 769, 771, 774, 775, 778, 780 et 781 : zéro pixel dans l’enveloppe cyan de l’ancien séparateur ;
- aucune ligne pleine largeur ou pleine hauteur détectée ;
- mouvement multi-panneaux préservé.

## Lisibilité et périmètre

Le contrat typographique v0.3 reste actif : petits textes en graisse 600 minimum, taille effective minimale de 11 px à 40 %, contraste contractuel de 7:1, ombre et contour. Les 17 événements et les quatre blocs commerçant sont présents. Aucun libellé technique n’est rendu.

**Statut humain : candidat silencieux à valider par le propriétaire.** Ce PASS objectif ne vaut pas approbation créative. La musique et la voix off restent bloquées.
