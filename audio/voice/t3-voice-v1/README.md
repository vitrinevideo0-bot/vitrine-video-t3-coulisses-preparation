# T3 — voix française v1

Voix masculine publicitaire française sélectionnée par audition : **`voice-02`**.

Le propriétaire a approuvé le débit, la prononciation, les respirations et le ducking avant le lancement du rendu GitHub.

## Placements verrouillés

| Scène | Début | Fin | Texte |
|---|---:|---:|---|
| 1 | 1,200 s | 5,542 s | Chez Casa Tacos, découvrez notre tacos maison. |
| 2 | 6,800 s | 10,469 s | Généreusement garni, et préparé à la commande. |
| 3 | 14,700 s | 17,811 s | Chaque geste révèle un tacos chaud et gourmand. |
| 4 | 21,800 s | 26,618 s | À Kandi, votre tacos est à deux mille cinq cents francs. Commandez sur WhatsApp. |

- `source/` : quatre prises définitives issues de l’audition vocale;
- `processed/` : prises normalisées autour de −20 LUFS;
- `t3_voice_stem_30s.wav` : tige mono exacte de 30 secondes avec les quatre placements;
- `manifest.json` : hashes, textes et mesures;
- contrat de mixage : `config/T3_VOICE_MIX_V1_0_0.json`.

## Ducking repris de T1

- musique hors parole : −3 dB;
- musique sous parole : −10 dB;
- profondeur : −7 dB;
- attaque : 120 ms;
- relâchement : 450 ms;
- master : cible −16 LUFS, plafond −2 dBTP;
- livraison : AAC stéréo 48 kHz.
