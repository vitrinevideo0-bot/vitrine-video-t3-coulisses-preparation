# RESTAURATION‑T3 — passation à l’agent intégrateur

## Ce qui est terminé

- contrat canonique `RESTAURATION-T3` v1.0.0;
- formulaire à six champs et parcours de quatre captures 6/8/7/9 s;
- contrat exécutable des douze écrans A/B/C;
- moteur visuel, transitions et textes dynamiques;
- silencieux v0.4 approuvé et verrouillé par SHA-256 de fichier et de flux;
- quatre dérivés musicaux approuvés avec rotation locale anti-répétition et état JSON persistant;
- voix `voice-02`, quatre clips, tige 30 s et ducking approuvés;
- master complet D produit sur GitHub Actions et revalidé après téléchargement;
- schémas RenderJob, RenderResult et RenderError;
- package hors ligne, manifest, checksums et golden master externe verrouillé.

## Ce qui reste à l’intégrateur

1. consommer `config/T3_CAPTURE_FLOW_V1_0_0.json` dans l’application caméra réelle;
2. stocker les quatre captures et recalculer leurs SHA-256;
3. construire un RenderJob strict avec `build_render_job_from_state` dans `adapter/t3_adapter.py`;
4. appeler `tools/record_t3_music_result.py` après le callback : `success` écrit atomiquement selon `schemas/T3_music_selection_state.schema.json`, `failed` laisse l’état inchangé;
5. déclencher GitHub Actions depuis le plan de contrôle commun;
6. vérifier le callback RenderResult/RenderError;
7. télécharger, vérifier et activer le paquet selon la future politique OTA;
8. assurer rollback, signature, télémétrie autorisée et compatibilité Android.

## Frontière Cloudflare

Aucun Worker Cloudflare n’est inclus ou déployé dans ce dépôt de gabarit. C’est volontaire : la configuration Cloudflare doit être commune au catalogue et non dupliquée dans chaque JSON de gabarit.

Le contrat précis est `integration-handoff/T3_CLOUDFLARE_BOUNDARY_V1.json`. Il ne contient aucune valeur de secret, aucun compte, bucket ou endpoint de production. Cloudflare peut orchestrer, stocker et dispatcher; **il ne rend jamais la vidéo**. FFmpeg/OpenCV restent sur GitHub Actions.

Tout déploiement Cloudflare, création de stockage, installation de secret ou activation OTA exige un ordre explicite du propriétaire et une mission d’intégration distincte.

## Limite historique connue

Le propriétaire a sélectionné `voice-02` via l’audition de la plateforme et a approuvé le débit et le mix final. Le dépôt conserve la voix retenue et ses quatre clips de scène, mais pas quatre fichiers archivés de démonstrations vocales candidates comparables. Cette déviation est déclarée; elle ne doit pas être reproduite pour T4/T5.

## Sources de preuve

- rendu complet : run GitHub `44564485698`;
- commit de rendu : `073888f7498385e576d42eed3a3c0f7dd71bb9d5`;
- validation serveur : 45/45 PASS;
- revalidation après téléchargement : 45/45 PASS;
- MP4 : SHA-256 `4208d58f52804b2440845c9ce5b249695e9072d8b707ae134386d4bc494740de`;
- flux vidéo : SHA-256 `8e415063add70f5807e009b2306c6b1154b0ec19bf35d5b9350012a5f4abe666`.
