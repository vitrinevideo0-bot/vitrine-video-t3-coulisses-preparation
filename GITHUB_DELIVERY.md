# RESTAURATION-T3 — État de livraison

## Candidat actif

La v0.4 conserve les transitions, le montage et la typographie de la v0.3, mais retire complètement les traits bleus horizontaux et verticaux de `R4_MULTI_PANEL_MATCH_CUT`.

Le préflight local passe 32/32 contrôles. Le rendu autoritatif doit encore être produit sur GitHub Actions, téléchargé puis revalidé avant présentation au propriétaire.

Sources de vérité :

- `reverse-engineering/T3_TRANSITIONS_30S.json` ;
- `config/T3_TEXT_MOTION_V0_4_0.json` ;
- `demo/render_job_silent_demo_v0_4.json` ;
- `docs/T3_TRANSITION_VISIBILITY_CONTRACT.md` ;
- `engine/render_silent.py`.

## Candidat v0.3 rejeté — ne pas utiliser

La fluidité et la lisibilité ont été appréciées, mais la v0.3 affichait deux traits bleus horizontaux puis deux traits bleus verticaux pendant la transition multi-panneaux.

- commit de rendu : `cfbc1f82de20a3faf48fbad09efa831d323ce470` ;
- run historique : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44551121356 ;
- pré-Release historique : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.3.0-silent-candidate-3 ;
- preuves du défaut : `proofs/owner-feedback/T3_V0_3_TRAITS_BLEUS_*.png` ;
- verrou historique : `config/T3_SILENT_IMPLEMENTATION_V0_3_0.json`.

Cause : l’ancien moteur ignorait `border_px: 0` du JSON et dessinait des séparateurs cyan de 4 px en dur. La v0.4 impose `gap_px: 0`, `border_px: 0`, `separator_lines: false` et `separator_color: null`, puis fait appliquer ces valeurs par le moteur.

## Versions antérieures rejetées

- v0.2 : textes trop fins à cause du poids Montserrat par défaut 100 ;
- v0.1 : informations de production visibles dans la publicité.

Elles restent uniquement des preuves d’audit.
