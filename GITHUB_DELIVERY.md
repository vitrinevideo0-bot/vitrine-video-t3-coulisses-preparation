# RESTAURATION-T3 — Livraison GitHub du candidat silencieux v0.4

## Vidéo active à valider

La v0.4 conserve le montage, les mouvements de panneaux et la lisibilité de la v0.3, mais retire complètement les deux traits bleus horizontaux et les deux traits bleus verticaux de `R4_MULTI_PANEL_MATCH_CUT`.

**Téléchargement direct :**
https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.4.0-silent-candidate-4/VIDEO_T3_SILENCIEUSE_SANS_TRAITS_BLEUS_V0_4_A_VALIDER.mp4

- commit de rendu : `f87d1ef913fe331b12cf10275f6c2e0392f16007` ;
- run GitHub Actions : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44555498879 ;
- pré-Release : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.4.0-silent-candidate-4 ;
- SHA-256 : `cd61d3cf793874a8b7d2eb8fe694861048368ba64b01216395c6bba0eb879774` ;
- taille : 10 601 443 octets ;
- 30,000 s · 720 × 1280 · 30 i/s · 900 images ;
- H.264 / yuv420p ;
- zéro piste audio.

## Contrôles réalisés

- 16/16 tests du moteur et des contrats PASS ;
- 32/32 contrôles sur le runner GitHub PASS ;
- 32/32 contrôles indépendants après téléchargement PASS ;
- 15/15 assets téléchargés ;
- 14/14 empreintes du manifeste de livraison valides ;
- artefact Actions et pré-Release identiques octet par octet ;
- aucun rush brut publié ;
- images serveur 771 et 778 inspectées à 40 % : aucun trait cyan horizontal ou vertical ;
- audit pixel des images 769, 771, 774, 775, 778, 780 et 781 : zéro pixel dans l’enveloppe de couleur de l’ancien séparateur.

Les preuves sont archivées dans `proofs/`, notamment :

- `T3_GITHUB_RELEASE_AUDIT_RUN_44555498879.json` ;
- `T3_GITHUB_SERVER_VALIDATION_RUN_44555498879.json` ;
- `T3_DOWNLOADED_RELEASE_VALIDATION_RUN_44555498879.json` ;
- `separators-v0.4-server/` ;
- `SHA256SUMS_RELEASE_RUN_44555498879.txt`.

## Ancrage anti-régression

Sources de vérité :

- `reverse-engineering/T3_TRANSITIONS_30S.json` impose `gap_px: 0`, `border_px: 0`, `separator_lines: false`, `separator_color: null` et `separator_policy: forbidden_by_owner` ;
- `engine/render_silent.py` applique ce profil et bloque les guides visibles interdits ;
- `config/T3_TEXT_MOTION_V0_4_0.json` conserve le contrat typographique lisible ;
- `docs/T3_TRANSITION_VISIBILITY_CONTRACT.md` documente la cause et la correction ;
- les tests couvrent les phases en rangées et en colonnes sur une image uniforme.

## Statut humain

La v0.4 est le **nouveau candidat silencieux à valider par le propriétaire**. Le contrôle objectif est terminé avec succès, mais cette pré-Release n’est pas encore une approbation créative. La musique et la voix off restent bloquées.

## Candidats rejetés — ne pas utiliser

- **v0.3** : lisibilité corrigée, mais séparateurs cyan visibles pendant la transition multi-panneaux ;
- **v0.2** : textes trop fins à cause du poids Montserrat par défaut 100 ;
- **v0.1** : informations de production visibles dans la publicité.

Ils restent uniquement des preuves d’audit.
