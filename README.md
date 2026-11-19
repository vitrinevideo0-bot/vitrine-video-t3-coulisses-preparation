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

Les questions, les quatre prises et les 12 écrans ont été approuvés par le propriétaire le 18 novembre 2026. Le premier candidat silencieux v0.1 a ensuite été **rejeté** : il affichait des titres de scènes, des durées et une mention de provenance qui appartiennent aux preuves techniques, pas à la publicité.

La correction v0.2 applique maintenant la logique T1/T2 :

- les textes visibles proviennent de `merchant_payload` dans le RenderJob ;
- les seuls champs sont `nom`, `produit`, `prix`, `whatsapp`, `quartier` et `accroche` ;
- l’accroche vide est omise ;
- `FCFA` est ajouté une seule fois ;
- le seul texte fixe est `COMMANDER MAINTENANT` ;
- aucun titre de scène, durée, mot démo, mot rush ou provenance média n’est composité ;
- les textes sont ajoutés après les transitions afin de rester nets.

La v0.2 a été rendue sur GitHub Actions au commit `1cbd7e02560d9d8da32d201f6b97064c53f7ea92`, puis revalidée après téléchargement : **22/22 contrôles PASS**. Elle reste un **candidat silencieux à valider**, pas un master créatif déjà approuvé. Musique, voix off, OTA et intégration mobile restent hors de ce jalon.

- [Run de rendu GitHub Actions](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44548349489)
- [Pré-Release corrigée v0.2](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.2.0-silent-candidate-2)
- [Téléchargement direct du MP4](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.2.0-silent-candidate-2/VIDEO_T3_SILENCIEUSE_MOTION_TEXT_V0_2_A_VALIDER.mp4)

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
- `config/T3_TEXT_MOTION_V0_2_0.json` — quatre blocs graphiques liés aux champs commerçant ;
- `demo/render_job_silent_demo.json` — fixture du même contrat `merchant_payload` que le runtime ;
- `docs/T3_VISIBLE_TEXT_CONTRACT.md` — chaînes autorisées et interdites ;
- `docs/LICENCES_POLICES.md` — familles et empreintes du motion design ;
- `rushes/manifest.json` — sources Pexels verrouillées ;
- `engine/render_silent.py` — moteur reproductible ;
- `tools/validate_silent.py` — validation indépendante ;
- `docs/LICENCES_RUSHS.md` — provenance et limites de licence.

## Références créatives

Les pages CapCut 2 et 4 servent uniquement à observer une grammaire de mouvement. Aucun média, logo, texte ou création des auteurs n’est inclus dans ce dépôt. Les effets sont reconstruits de manière originale à partir des quatre rushes Pexels.
