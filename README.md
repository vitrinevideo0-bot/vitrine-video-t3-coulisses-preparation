# RESTAURATION-T3 — Coulisses de préparation

Gabarit vertical Vitrine Vidéo pour montrer les coulisses d’un plat : ingrédients, geste signature, dressage et plat prêt à servir.

## Contrat silencieux courant

- 720 × 1280, portrait 9:16 ;
- 30 images/s ;
- 900 images, exactement 30 secondes ;
- quatre scènes : 6 s / 8 s / 7 s / 9 s ;
- zéro piste audio ;
- exactement 12 écrans de capture approuvés ;
- toutes les familles de transitions des références CapCut 2 et 4 sont représentées par 16 profils et 17 événements originaux ;
- quatre rushes réels Pexels téléchargés à la volée, vérifiés par SHA-256 et jamais publiés bruts.

## État réel

Les questions, les quatre prises et les 12 écrans ont été approuvés par le propriétaire le 18 novembre 2026. Le workflow `Rendu silencieux T3 sur GitHub` construit un **candidat silencieux à valider**, pas un master créatif déjà approuvé. Musique, voix off, OTA et intégration mobile restent hors de ce jalon.

## Reproduire localement

```bash
python -m pip install -r requirements.txt
python tools/fetch_rushes.py
python engine/render_silent.py
python tools/validate_silent.py
```

FFmpeg et FFprobe doivent être installés.

## Rendu GitHub Actions

Lancer manuellement **Rendu silencieux T3 sur GitHub**. Le runner :

1. compile et teste les contrats ;
2. télécharge les quatre rushes Pexels ;
3. vérifie taille et SHA-256 ;
4. produit le MP4 H.264 sans son ;
5. contrôle 720 × 1280, 30 i/s, 900 images, 30 s et zéro piste audio ;
6. publie uniquement le rendu composite, les preuves et les rapports ;
7. peut créer une pré-Release immuable si l’entrée `publish_prerelease` vaut `true`.

## Fichiers clés

- `form/questions_T3.json` — six questions approuvées ;
- `capture-guide/consignes_T3.json` — quatre prises et machine A/B/C ;
- `ui-screens/approved/` — 12 écrans approuvés ;
- `reverse-engineering/T3_TRANSITIONS_30S.json` — 17 événements ;
- `rushes/manifest.json` — sources Pexels verrouillées ;
- `engine/render_silent.py` — moteur reproductible ;
- `tools/validate_silent.py` — validation indépendante ;
- `docs/LICENCES_RUSHS.md` — provenance et limites de licence.

## Références créatives

Les pages CapCut 2 et 4 servent uniquement à observer une grammaire de mouvement. Aucun média, logo, texte ou création des auteurs n’est inclus dans ce dépôt. Les effets sont reconstruits de manière originale à partir des quatre rushes Pexels.
