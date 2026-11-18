# T3 — audit final de la rotation musicale stricte

**Date : 18 novembre 2026**
**Statut local : PASS**

## 1. Cycle de production

T3 impose désormais l’ordre fermé suivant :

1. `t3_music_481806` — LASER
2. `t3_music_360659` — Omalicha Nwa
3. `t3_music_485507` — Safe
4. `t3_music_245452` — Dlozi Lam

L’état initial choisit exclusivement la piste 1. Chaque nouveau succès choisit et valide le successeur exact `481806→360659→485507→245452→481806`. Une sélection explicite de production ne peut que confirmer ce successeur; une répétition ou un saut est rejeté. Un échec ne modifie jamais l’état.

Le registre persistant `successful_render_jobs` conserve chaque association réussie `render_job_id → music_id`. Le rejeu de tout ancien succès est donc idempotent même après un tour complet, et un même job ne peut jamais changer de musique. Les écritures locales restent atomiques et sérialisées sous verrou interprocessus; une concurrence hors séquence est rejetée sans mutation.

Le rendu historique D reste un exemplaire canonique approuvé, explicitement séparé du sélecteur runtime. Il ne constitue pas une dérogation permettant de commencer la rotation de production par la piste 4.

## 2. Contrats mis à niveau

- `adapter/t3_adapter.py` : ordre verrouillé, successeur explicite exact, registre durable et validation fail-closed du contrat.
- `config/T3_MUSIC_PACK_V1_0_0.json` : politique `exact_successor_only` et clé `successful_render_jobs`.
- `schemas/T3_music_pack.schema.json` : ordre, algorithme et politique stricts.
- `schemas/T3_music_selection_state.schema.json` : registre durable des succès.
- `tests/test_integrator_architecture.py` : saut explicite, rejeu ancien après tour complet, concurrence par threads et par processus, échec sans mutation.
- `tools/validate_t3_integrator_package.py` : validation du schéma d’état, cycle exact sur 10 000 sélections et rejeu ancien.
- `README.md` et passation intégrateur : sémantique stricte documentée.

## 3. Validation locale

| Contrôle | Résultat |
|---|---:|
| Suite du dépôt | **49 PASS + 19 sous-tests PASS** |
| Stress du cycle | **10 000 sélections exactes, 2 500 par piste** |
| Rejeu ancien après un tour complet | **PASS, état inchangé à 4 succès** |
| Concurrence locale | **PASS, hors séquence rejetée** |
| Sommes du pack musical | **PASS** |
| Sommes voix finale | **PASS** |
| Sommes des quatre voix candidates | **PASS** |
| JSON suivis | **83/83 parsés** |
| YAML suivis | **4/4 parsés** |
| Schémas JSON suivis | **8/8 valides** |
| Compilation Python | **PASS** |
| `git diff --check` | **PASS** |

## 4. Paquet intégrateur reproductible

Deux constructions locales indépendantes du paquet ont produit exactement les mêmes octets :

- fichier : `restauration-t3-coulisses-v1.0.0.zip`
- taille : **29 501 392 octets**
- SHA-256 : `ba051aeaa9f904cac6616c14362f80ff44dd33ab5cf24f26dc9ec30aaf1c0a30`
- payload : **128 fichiers**, 36 337 944 octets avant compression
- golden inclus : 11 363 724 octets, SHA-256 `4208d58f52804b2440845c9ce5b249695e9072d8b707ae134386d4bc494740de`
- validation après extraction propre : **37/37 PASS**
- suite embarquée après extraction : **49/49 PASS**
- aucun original Pixabay complet, secret ou Worker Cloudflare embarqué

Le paquet est un résultat local de préflight; aucune nouvelle Release n’a été publiée.

## 5. Publication et déploiement

Au moment de cet audit, les changements de cette migration sont uniquement locaux : **aucun commit, push, tag, déploiement Cloudflare ou publication de Release n’a été effectué**. T3 conserve explicitement `cloudflare_deployed=false`; le rendu vidéo reste du ressort de GitHub Actions.
