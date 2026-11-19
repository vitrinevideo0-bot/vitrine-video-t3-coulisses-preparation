# Audit architectural croisé — RESTAURATION‑T1, T2 et T3

**Date locale : 18 novembre 2026**

**Référentiel : `INSTRUCTION_UNIVERSELLE_VITRINE_VIDEO_V1.md`**

## Verdict honnête après remédiation T3

**T1 et T2 ne sont pas strictement conformes à 100 % au protocole universel actuel. T3 est désormais conforme à l’architecture de gabarit de référence et son unique écart de preuve vocale est remédié dans l’état courant.**

Le style de montage propre à T2 ou T3 n’est pas un écart : T1 fournit une méthode et des contrats, pas une identité graphique à copier. La chronologie rétrospective de la correction T3 reste déclarée au lieu d’être réécrite. La clôture exige encore les workflows GitHub exacts de rendu et de paquet avant fusion.

| Gabarit | Tests réexécutés | Master/rendu | Architecture universelle stricte | Cloudflare production |
|---|---:|---|---|---|
| T1 | **104/104 PASS** après rematérialisation du golden depuis sa Release | Release complète existante | **Non** — héritage ancien, voix candidates non archivées, workflow Release destructif, branches fragmentées | **Non déployé** |
| T2 | **59/59 PASS** + dry-build et intégration Worker/R2/GitHub PASS | v0.7 approuvé en artefact privé | **Non** — rotation 4 pistes absente, quatre voix candidates absentes, paquet OTA/ZIP absent, Release v0.7 non autorisée | **Plan testé, non déployé** |
| T3 | **43/43 PASS** local après remédiation; master historique 45/45 serveur et 45/45 après téléchargement | Release complète D existante; rejeu GitHub de remédiation requis avant fusion | **Oui pour le paquet de gabarit courant** — quatre voix comparables archivées, VOIX-A / voice-02 choisie, zéro écart connu restant | **Non déployé, frontière documentée** |

## T1

### Confirmé

- commit d’ingénierie audité : `c656510ab81d31d413dc4dfd74b42671532cd978`;
- golden master téléchargé depuis `t1-special-menu-reference-v3-preview`;
- SHA-256 attendu `784bd775…50c7` vérifié;
- suite complète : **104 PASS, 0 FAIL**;
- paquet canonique, schémas RenderJob/Result/Error, pack musical quatre pistes, rotation locale et préparation OTA hors réseau présents;
- Release complète voix existante.

### Écarts

- T1 précède la règle des quatre démonstrations vocales candidates archivées;
- preuve humaine vocale documentaire ambiguë;
- le workflow historique peut supprimer/recréer un tag de Release, pratique désormais interdite;
- travail final réparti entre branche d’ingénierie, branche par défaut et Releases;
- aucun Worker Cloudflare réel, aucun OTA opérationnel.

## T2

### Confirmé

- commit : `4fad4f0983b6a2fa223b4874bd40ff62f8a7c9fd`;
- suite exacte du workflow : **59 PASS, 0 FAIL**;
- trois RenderJobs reconstruits sans dérive;
- schémas, fixtures et verrou visuel valides;
- TypeScript validé sous Node 24;
- `wrangler deploy --dry-run` : **PASS**;
- intégration locale formulaire → 12 écrans → R2 → dispatch GitHub → callback : **PASS**;
- run v0.7 : `44515210635`, succès.

### Écarts

- le runtime courant verrouille D/Afrofire, sans pack de quatre pistes en rotation anti-répétition;
- pas de quatre démonstrations vocales candidates archivées;
- pas de Release publique v0.7, conformément à l’interdiction de publier sans ordre distinct;
- pas de ZIP intégrateur/OTA hors ligne;
- statut canonique historique et runtime v0.7 à consolider.

## T3 — consolidation effectuée pendant cet audit

Le master n’a pas été modifié. Ont été ajoutés :

- identité canonique `RESTAURATION-T3` v1.0.0 et `audio_profile: afrobeat_amapiano`;
- contrat exécutable des douze écrans et simulation navigateur;
- schémas stricts RenderJob, RenderResult et RenderError;
- fixtures complètes;
- adaptateur hors ligne;
- rotation déterministe des quatre pistes excluant le dernier rendu réussi;
- rejet d’un choix explicite identique au précédent;
- stress test de 10 000 rendus : zéro répétition adjacente;
- golden conformance lock;
- constructeur ZIP déterministe et validation après extraction propre;
- frontière Cloudflare/intégrateur explicite;
- publication de Release désormais désactivée par défaut.

Préflight local du paquet après correction vocale :

- **43/43 tests PASS**;
- **32/32 contrôles du ZIP PASS**;
- deux constructions locales byte-identiques;
- 111 fichiers dans le payload contrôlé;
- quatre démonstrations vocales sources et quatre WAV normalisés, même texte français, sans retiming;
- choix propriétaire enregistré : **VOIX-A**, identifiant interne `voice-02`;
- golden master complet inclus et verrouillé;
- aucun original Pixabay complet;
- aucun secret, endpoint de production ou Worker Cloudflare embarqué;
- `ota_implemented=false` et `cloudflare_deployed=false` explicites.

### Remédiation de l’écart vocal

L’audit initial avait correctement signalé l’absence de quatre fichiers comparables. La porte a été rouverte avant T4 : quatre candidats distincts `VOIX-A` à `VOIX-D` ont été synthétisés avec le même texte tiré des scripts approuvés, normalisés à 48 kHz sans modifier leur débit, hashés, schématisés et testés. Le propriétaire a choisi `VOIX-A`, qui correspond à `voice-02` déjà utilisée par les quatre clips de scène et le master approuvé.

La correction est explicitement qualifiée de **rétrospective** : elle ne prétend pas que ces quatre fichiers existaient avant le premier master. À l’état courant, `known_protocol_deviations` est vide et le validateur de paquet indique `strict_universal_protocol_100_percent=true`. Cette conclusion ne couvre ni Android, ni OTA opérationnel, ni Cloudflare de production, qui restent une mission d’intégration séparée.

## Cloudflare : réponse précise

### Ce qui existe

- **T1 :** aucune implémentation Worker; seulement préparation hors ligne.
- **T2 :** plan de contrôle Worker/R2 typé, testé et dry-buildé.
- **T3 :** contrat de frontière et de passation vers le futur plan commun; aucun Worker dupliqué dans le gabarit.

### Ce qui n’existe pas

- aucun secret GitHub Cloudflare dans T2 ou T3;
- aucune variable publique Worker;
- aucun environnement de production GitHub;
- aucun enregistrement de déploiement;
- le dépôt commun proposé `vitrinevideo0-bot/vitrine-video-gabarits` n’existe pas;
- aucun Cloudflare/OTA de production n’est actif.

### Pourquoi il n’a pas été déployé

L’instruction interdit explicitement tout déploiement Cloudflare, création de bucket ou installation de secret sans ordre séparé du propriétaire. Elle impose également que la configuration soit **commune au catalogue**, et non copiée dans chaque JSON de gabarit. Ne pas déployer T3 était donc correct. Ce qui manquait était la passation et les contrats; ils ont maintenant été ajoutés.

## Règles verrouillées pour T4 et T5

1. quatre références puis approbation;
2. douze écrans exécutables;
3. quatre musiques approuvées **et rotation testée**;
4. quatre démonstrations vocales candidates archivées avant la voix retenue;
5. RenderJob/Result/Error dès le départ;
6. master de validation uniquement sur GitHub;
7. publication désactivée par défaut;
8. métadonnées OTA et ZIP intégrateur après validation finale;
9. Cloudflare commun, sans secret dans Git et sans déploiement implicite;
10. aucune affirmation « 100 % » si une preuve manque.
