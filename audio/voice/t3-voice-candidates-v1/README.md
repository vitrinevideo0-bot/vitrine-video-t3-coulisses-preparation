# T3 — quatre démonstrations vocales candidates comparables

## Objet

Ce dossier remédie rétrospectivement à l’unique preuve manquante déclarée dans l’audit T3 : quatre démonstrations vocales candidates archivées et directement comparables.

Le master visuel approuvé, les quatre clips de scène existants et le mix final ne sont pas modifiés par la création de ce dossier.

## Comparabilité

Les quatre voix prononcent exactement le même texte, en français :

> Chez Casa Tacos, découvrez notre tacos maison, généreusement garni et préparé à la commande. Chaque geste révèle un tacos chaud et gourmand. À Kandi, votre tacos est à deux mille cinq cents francs. Commandez simplement sur WhatsApp.

Toutes les données proviennent de l’exemple commerçant et des quatre scripts T3 déjà approuvés. Aucun prix, lieu, produit ou avantage nouveau n’a été inventé.

- langue : `fr` ;
- identité demandée : voix masculine publicitaire ;
- quatre fichiers source distincts ;
- quatre fichiers normalisés à 48 kHz mono ;
- cible d’écoute : environ −20 LUFS, plafond −3 dBTP ;
- aucune accélération ni décélération ;
- les différences de durée reflètent le débit naturel de chaque voix.

## Candidats

La planche d’écoute masque volontairement les identifiants internes et affiche seulement `VOIX-A` à `VOIX-D`.

- `VOIX-A` correspond à la voix `voice-02` déjà retenue pour le master approuvé ;
- `VOIX-B`, `VOIX-C` et `VOIX-D` sont des comparaisons nouvelles ;
- le propriétaire a écouté le lot et choisi explicitement **`VOIX-A`** via la porte `t3_voice_selection_remediation` ;
- la décision durable est enregistrée dans `approvals/APPROBATION_VOIX_CANDIDATE_A_2026-11-18.json`.

## Chronologie honnête

Cette porte est rouverte **après** la production historique du master T3. Le dépôt ne prétendra jamais que les quatre candidats avaient été archivés avant le premier choix. Pour corriger l’état courant, le propriétaire choisira maintenant une voix parmi les quatre, puis les étapes voix/mixage/tests/paquet seront rejouées dans l’ordre à partir de cette nouvelle décision.

## Fichiers

- `source/` : sorties synthétiques originales ;
- `normalized/` : fichiers d’écoute comparables ;
- `NORMALIZATION_REPORT.json` : mesures et hashes ;
- `manifest.json` : provenance, texte et état de la porte ;
- `T3_ECOUTE_4_VOIX.html` : planche locale d’écoute ;
- `normalize_candidates.py` : normalisation reproductible sans retiming.
