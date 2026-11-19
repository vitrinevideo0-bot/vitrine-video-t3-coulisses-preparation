# RESTAURATION-T3 — Livraison GitHub du candidat silencieux lisible v0.3

**Dépôt public :** https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation
**Commit de rendu :** `cfbc1f82de20a3faf48fbad09efa831d323ce470`
**CI :** https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44551107670
**Rendu GitHub Actions :** https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44551121356
**Pré-Release :** https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.3.0-silent-candidate-3

## Vidéo v0.3 à valider

**Téléchargement direct :**
https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.3.0-silent-candidate-3/VIDEO_T3_SILENCIEUSE_MOTION_TEXT_LISIBLE_V0_3_A_VALIDER.mp4

- SHA-256 : `757ba579bb6d1168fedd5e74c098c228d631d316449309eecc23ff21c6c1543b` ;
- taille : 10 616 560 octets ;
- 30,000 s ;
- 720 × 1280 ;
- 30 i/s ;
- 900 images ;
- H.264 / yuv420p ;
- zéro piste audio.

## Correction typographique ancrée dans le JSON

La source de vérité est `config/T3_TEXT_MOTION_V0_3_0.json` :

- nom du commerçant : Montserrat 700, minimum 30 px ;
- quartier : Plus Jakarta Sans 650, minimum 28 px ;
- CTA : Montserrat 750, minimum 28 px ;
- WhatsApp : Plus Jakarta Sans 700, minimum 30 px ;
- prix : Plus Jakarta Sans 700, minimum 44 px ;
- taille effective minimale à 40 % : 11,2 px ;
- contraste mesuré minimal : 13,06:1 pour un contrat fixé à 7:1 ;
- ombre noire opacité 230 et contour sombre de 2 px ;
- dégradé final renforcé, sans carte dure.

Les poids sont réellement appliqués à l’axe `Weight` des polices variables. Un test compare l’encre du poids 700 à celle du poids 100 afin d’empêcher un retour silencieux à la graisse Thin.

## Contrôles

- CI du commit : PASS ;
- tests du moteur : 14/14 PASS ;
- rendu GitHub Actions : PASS ;
- validation serveur : 27/27 PASS ;
- Release téléchargée puis revalidée indépendamment : 27/27 PASS ;
- manifeste SHA-256 des 13 assets de la Release : PASS ;
- contrôle visuel des images 86, 551 et 899 à 40 % : PASS ;
- 17/17 événements de transition appliqués ;
- 4/4 blocs commerçant appliqués ;
- aucun libellé technique et aucune piste audio.

## Statut humain

La v0.3 est le **nouveau candidat silencieux à valider par le propriétaire**. Les transitions appréciées sont conservées. Cette pré-Release n’est pas encore une approbation créative; musique et voix off restent bloquées.

## Historique rejeté

- v0.2 : logique commerçant correcte, mais petits textes illisibles à cause du poids Montserrat par défaut 100 (Thin) ;
- v0.1 : informations de production visibles dans la publicité.

Ces versions restent uniquement des preuves d’audit et ne doivent pas être utilisées.
