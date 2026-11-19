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

Le master v0.4 a été produit sur GitHub Actions puis téléchargé et revalidé : **32/32 contrôles PASS** côté serveur et **32/32 PASS** après téléchargement. Les 15 assets de la pré-Release correspondent à l’artefact Actions octet par octet; les images serveur 771 et 778 ne montrent aucun trait cyan à 40 %. **Le propriétaire a approuvé cette v0.4**, qui devient la base visuelle immuable du rendu complet.

## Voix et musique approuvées

Les quatre dérivés Afrobeat/Amapiano A–D ont été approuvés et sont versionnés dans `audio/music/t3-afrobeat-v1/`, sans les sources Pixabay intégrales. La voix française masculine `voice-02`, son débit et le ducking ont également été approuvés.

Le rendu complet est verrouillé sur **D — Dlozi Lam / PremiumMusicOdyssey** :

- placements voix : 1,2 / 6,8 / 14,7 / 21,8 s ;
- musique à −3 dB hors parole et −10 dB sous parole ;
- attaque 120 ms, relâchement 450 ms ;
- master cible −16 LUFS / −2 dBTP ;
- AAC stéréo 48 kHz ;
- flux vidéo v0.4 copié bit pour bit, sans réencodage ;
- un seul MP4 complet produit par GitHub Actions.

Le workflow `.github/workflows/render-complete-voice-music-D.yml` télécharge le silencieux approuvé, vérifie ses deux hashes, construit le mix sur le runner, exécute une validation indépendante et publie l’artefact ainsi qu’une pré-Release immuable.

Le rendu complet a été produit au commit `073888f` par le run GitHub Actions `44564485698` : **22/22 contrôles du constructeur et 45/45 contrôles indépendants PASS**. La pré-Release téléchargée a été revalidée **45/45 PASS**; l’artefact Actions et les 11 assets de la pré-Release sont identiques octet par octet.

- [Run du rendu complet voix + musique D](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44564485698)
- [Pré-Release du rendu complet](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.7.0-complete-D-1)
- [Téléchargement direct du MP4 complet](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.7.0-complete-D-1/VIDEO_T3_COMPLETE_VOIX_MUSIQUE_D_V0_7_A_VALIDER.mp4)

## Architecture d’intégration et préparation OTA

Après l’approbation finale, l’audit croisé T1/T2/T3 a ajouté sans modifier le master :

- le JSON canonique `RESTAURATION-T3` v1.0.0 et son schéma ;
- le contrat exécutable des douze écrans et une simulation navigateur ;
- les schémas RenderJob, RenderResult et RenderError ;
- un adaptateur avec rotation déterministe des quatre musiques, sans répétition du dernier rendu réussi ;
- un stress test de 10 000 sélections sans répétition adjacente ;
- un golden conformance lock ;
- un ZIP intégrateur déterministe, son manifest et sa validation après extraction propre ;
- une passation explicite vers le futur plan de contrôle Cloudflare commun.

`ota_implemented=false`, `android_integration_implemented=false` et `cloudflare_deployed=false` restent explicites. Aucun Worker, secret, compte, bucket ou endpoint de production n’est dupliqué dans le JSON du gabarit. Le workflow du paquet peut publier une Release uniquement sur demande, avec l’option désactivée par défaut.

**Remédiation vocale en cours de clôture :** l’audit avait déclaré l’absence de quatre démonstrations vocales candidates comparables. La branche `fix/t3-four-voice-candidates` archive maintenant `VOIX-A` à `VOIX-D`, toutes sur le même texte français, sans retiming, avec mesures et hashes. Le propriétaire a choisi explicitement **VOIX-A**, qui correspond à `voice-02` déjà utilisée par le master approuvé. Cette remédiation est rétrospective et ne réécrit pas l’histoire. La CI et le rendu/mixage GitHub post-sélection sont validés; le MP4 téléchargé est byte-identique au master approuvé et son visuel reste immuable. Seul le paquet intégrateur GitHub doit encore être reconstruit et validé après extraction.

- [Run de rendu GitHub Actions v0.4](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44555498879)
- [Pré-Release sans traits bleus v0.4](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.4.0-silent-candidate-4)
- [Téléchargement direct du MP4](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/download/t3-coulisses-v0.4.0-silent-candidate-4/VIDEO_T3_SILENCIEUSE_SANS_TRAITS_BLEUS_V0_4_A_VALIDER.mp4)

Historique v0.3 rejeté : [run](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/actions/runs/44551121356) · [pré-Release](https://github.com/vitrinevideo0-bot/vitrine-video-t3-coulisses-preparation/releases/tag/t3-coulisses-v0.3.0-silent-candidate-3).

## Reproduire localement

```bash
python -m pip install -r requirements.txt
python tools/fetch_rushes.py
python engine/render_silent.py
python tools/validate_silent.py
```

FFmpeg et FFprobe doivent être installés.

Un préflight audio local est possible avec `audio/scripts/build_t3_complete_voice.py`, mais **il ne constitue jamais le rendu livré**. Le master complet autoritatif doit provenir du workflow GitHub Actions.

## Rendu GitHub Actions

Pour le master final, lancer manuellement **Rendu complet T3 — voix + musique D**. Ce workflow vérifie les quatre dérivés et la voix, verrouille le silencieux v0.4 par SHA-256, produit uniquement le choix D, exécute `tools/validate_complete.py`, puis publie l’artefact et la pré-Release.

Le workflow historique **Rendu silencieux T3 sur GitHub** :

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
- `proofs/separators-v0.4-server/` — images 771/778 et audit pixel du MP4 GitHub sans traits cyan ;
- `proofs/T3_GITHUB_RELEASE_AUDIT_RUN_44555498879.json` — intégrité de l’artefact, de la pré-Release et du master ;
- `proofs/typography-v0.3-server/` — preuves historiques de lisibilité ;
- `docs/LICENCES_POLICES.md` — familles et empreintes du motion design ;
- `rushes/manifest.json` — sources Pexels verrouillées ;
- `engine/render_silent.py` — moteur reproductible ;
- `tools/validate_silent.py` — validation indépendante du silencieux ;
- `config/T3_MUSIC_PACK_V1_0_0.json` — quatre dérivés approuvés et sélection finale D ;
- `config/T3_VOICE_MIX_V1_0_0.json` — voix `voice-02`, placements, ducking et hashes visuels ;
- `audio/music/t3-afrobeat-v1/` — quatre dérivés de 30 s, preuves et provenance, sans sources intégrales ;
- `audio/voice/t3-voice-v1/` — prises définitives, normalisations et tige voix 30 s ;
- `audio/scripts/build_t3_complete_voice.py` — constructeur reproductible du master complet ;
- `tools/validate_complete.py` — validation indépendante voix, musique, loudness et invariance visuelle ;
- `.github/workflows/render-complete-voice-music-D.yml` — rendu serveur, artefact et pré-Release ;
- `config/T3_COULISSES_TEMPLATE_V1_0_0.json` — identité canonique et métadonnées OTA honnêtes ;
- `config/T3_CAPTURE_FLOW_V1_0_0.json` — machine exécutable des douze écrans ;
- `adapter/t3_adapter.py` — RenderJob et rotation musicale anti-répétition ;
- `schemas/render_job.schema.json`, `render_result.schema.json`, `render_error.schema.json` — frontière runtime stricte ;
- `packages/t3-coulisses-v1/package_spec.json` — source du ZIP intégrateur déterministe ;
- `integration-handoff/` — limites Android, serveur, Cloudflare et OTA ;
- `.github/workflows/build-integrator-package.yml` — build et validation du paquet, publication désactivée par défaut ;
- `proofs/complete-v0.7-server/` — rapports serveur, audit Release et revalidation après téléchargement ;
- `reports/RAPPORT_RENDU_COMPLET_GITHUB_RUN_44564485698.md` — synthèse du master complet ;
- `reports/AUDIT_ARCHITECTURE_T1_T2_T3_2026-11-18.md` — audit comparatif et écarts déclarés ;
- `docs/LICENCES_RUSHS.md` — provenance et limites de licence.

## Références créatives

Les pages CapCut 2 et 4 servent uniquement à observer une grammaire de mouvement. Aucun média, logo, texte ou création des auteurs n’est inclus dans ce dépôt. Les effets sont reconstruits de manière originale à partir des quatre rushes Pexels.
