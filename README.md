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

Les questions, les quatre prises et les 12 écrans ont été approuvés par le propriétaire le 18 novembre 2026. Trois candidats sont conservés uniquement pour l’audit :

- **v0.1 rejetée** : titres de scènes, durées et provenance visibles dans la publicité ;
- **v0.2 rejetée** : nom, quartier et CTA trop fins dans le lecteur ;
- **v0.3 rejetée** : lisibilité corrigée, mais deux traits bleus horizontaux puis deux traits bleus verticaux étaient visibles pendant la transition multi-panneaux.

La v0.4 conserve la fluidité, le montage et la lisibilité de la v0.3, mais supprime complètement ces traits :

- le profil JSON impose `gap_px: 0`, `border_px: 0`, `separator_lines: false` et `separator_color: null` ;
- la contrainte globale interdit tout guide de transition visible ;
- le moteur lit ce profil au lieu de dessiner des lignes de 4 px en dur ;
- les rangées et colonnes continuent de bouger, sans bordure colorée ;
- les images 771 et 778 sont réservées au contrôle des phases horizontale et verticale ;
- les textes restent liés aux six champs `merchant_payload`, avec le contrat typographique v0.3 conservé.

Le préflight local v0.4 passe **32/32 contrôles** et les phases horizontale/verticale ont été inspectées à 40 %. Le master autoritatif doit encore être produit puis revalidé sur GitHub Actions avant présentation. Musique, voix off, OTA et intégration mobile restent hors de ce jalon.

Historique v0.3 rejeté : [run](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44551121356) · [pré-Release](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.3.0-silent-candidate-3).

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
- `config/T3_TEXT_MOTION_V0_4_0.json` — quatre blocs graphiques, lisibilité et interdiction des guides visibles ;
- `demo/render_job_silent_demo_v0_4.json` — fixture du même contrat `merchant_payload` que le runtime ;
- `docs/T3_VISIBLE_TEXT_CONTRACT.md` — chaînes autorisées et interdites ;
- `docs/T3_TYPOGRAPHY_LEGIBILITY_CONTRACT.md` — poids, tailles, contraste et contrôles bloquants ;
- `docs/T3_TRANSITION_VISIBILITY_CONTRACT.md` — interdiction des traits séparateurs et logique JSON/moteur ;
- `proofs/typography-v0.3-server/` — preuves historiques de lisibilité ;
- `docs/LICENCES_POLICES.md` — familles et empreintes du motion design ;
- `rushes/manifest.json` — sources Pexels verrouillées ;
- `engine/render_silent.py` — moteur reproductible ;
- `tools/validate_silent.py` — validation indépendante ;
- `docs/LICENCES_RUSHS.md` — provenance et limites de licence.

## Références créatives

Les pages CapCut 2 et 4 servent uniquement à observer une grammaire de mouvement. Aucun média, logo, texte ou création des auteurs n’est inclus dans ce dépôt. Les effets sont reconstruits de manière originale à partir des quatre rushes Pexels.
