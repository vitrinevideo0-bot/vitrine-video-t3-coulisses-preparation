# RESTAURATION-T3 — État de livraison

## Candidat actif

La v0.3 corrige la lisibilité typographique à la source. Son préflight local passe 27/27 contrôles, mais elle n’est pas encore une livraison : le rendu autoritatif doit être produit sur GitHub Actions, téléchargé puis revalidé avant présentation au propriétaire.

Source de vérité :

- `config/T3_TEXT_MOTION_V0_3_0.json` ;
- `demo/render_job_silent_demo_v0_3.json` ;
- `docs/T3_TYPOGRAPHY_LEGIBILITY_CONTRACT.md` ;
- `engine/text_motion.py`.

## Candidat v0.2 rejeté — ne pas utiliser

La fluidité des transitions a été appréciée, mais le propriétaire a rejeté la v0.2 parce que plusieurs textes étaient trop fins et trop peu lisibles dans le lecteur.

- commit de rendu : `1cbd7e02560d9d8da32d201f6b97064c53f7ea92` ;
- run historique : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44548349489 ;
- pré-Release historique : https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.2.0-silent-candidate-2 ;
- preuves du défaut : `proofs/owner-feedback/` ;
- verrou historique : `config/T3_SILENT_IMPLEMENTATION_V0_2_0.json`.

Cause : `Montserrat-Variable.ttf` utilisait sa valeur d’axe par défaut 100 (Thin), car la v0.2 ne fixait pas le poids. La v0.3 impose les poids, tailles minimales, contrastes, ombres et dégradés dans le JSON.

## Candidat v0.1 rejeté — ne pas utiliser

La v0.1 exposait des titres de scènes, des durées et des mentions de provenance dans la publicité. Elle reste uniquement une preuve d’audit.
