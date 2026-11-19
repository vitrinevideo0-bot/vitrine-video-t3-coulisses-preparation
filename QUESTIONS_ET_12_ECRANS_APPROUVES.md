# RESTAURATION-T3 — Questions commerçant et 12 écrans approuvés

**Direction approuvée par le propriétaire :** références CapCut 2 + 4 combinées  
**Durée :** 30 secondes  
**Répartition proposée :** 6 s + 8 s + 7 s + 9 s  
**Statut :** approuvé par le propriétaire le 18 novembre 2026 — aucun moteur ni rendu MP4 développé

## 1. Les six questions posées au commerçant

| # | Clé JSON | Question visible | Obligatoire | Exemple |
|---:|---|---|:---:|---|
| 1 | `nom` | Comment s'appelle ton restaurant, ton maquis ou ton activité ? | oui | Chez Afi |
| 2 | `produit` | Quel plat ou quelle préparation allons-nous montrer en coulisses ? | oui | Poulet braisé et alloco |
| 3 | `prix` | Quel est le prix de ce plat ou de cette portion ? | oui | 2500 |
| 4 | `whatsapp` | Quel numéro WhatsApp les clients doivent-ils utiliser ? | oui | +229 01 97 00 00 00 |
| 5 | `quartier` | Dans quel quartier peut-on te trouver ? | oui | Kandi, près du marché central |
| 6 | `accroche` | Qu'est-ce qui rend cette préparation spéciale ? | non | Préparé à la commande avec nos épices maison |

Le prix est saisi sans `FCFA`; le moteur l'ajoutera une seule fois. L'accroche vide est simplement omise : aucun texte n'est inventé.

### Langue pendant le tournage

Ce n'est pas une septième question obligatoire. Chaque écran GUIDE affiche en bas :

> Tu peux parler pendant que tu filmes, en français, en fon ou en anglais.  
> Tu peux aussi ne pas parler si tu préfères.

La voix captée est conservée à vitesse normale. Aucun sous-titre automatique n'est ajouté.

## 2. Les quatre prises

| Scène | Durée | Titre | Fonction |
|---|---:|---|---|
| S1 | 6 s | LES INGRÉDIENTS | fraîcheur et preuve |
| S2 | 8 s | LE GESTE SIGNATURE | savoir-faire réel |
| S3 | 7 s | LE DRESSAGE | précision et finition |
| S4 | 9 s | PRÊT À SERVIR | désir, plat final et CTA |

## 3. Liste exacte des douze écrans

### Écrans 1 à 3 — Scène 1 : LES INGRÉDIENTS · 6 s

1. **`T3_CAPTURE_S1_A_GUIDE`**  
   Explique de filmer les vrais ingrédients sur un plan de travail propre, puis de se rapprocher lentement de l'ingrédient principal. Affiche `À FILMER`, `À ÉVITER`, la langue facultative et `COMMENCER À FILMER`.
2. **`T3_CAPTURE_S1_B_RECORDING`**  
   Caméra plein écran, microphone actif, `SCÈNE 1/4`, `REC`, chrono `0:00 → 0:06`, barre de progression et arrêt automatique.
3. **`T3_CAPTURE_S1_C_REVIEW`**  
   Relecture avec son. Question : `VOIT-ON BIEN LES INGRÉDIENTS ET LE PLAN DE TRAVAIL ?` Actions : `REFAIRE` / `SCÈNE SUIVANTE`.

### Écrans 4 à 6 — Scène 2 : LE GESTE SIGNATURE · 8 s

4. **`T3_CAPTURE_S2_A_GUIDE`**  
   Demande un seul geste complet : verser, mélanger, retourner, découper, pétrir ou griller. Le téléphone reste stable et loin du feu ou de l'huile.
5. **`T3_CAPTURE_S2_B_RECORDING`**  
   Caméra plein écran, microphone actif, `SCÈNE 2/4`, `REC`, chrono `0:00 → 0:08`, progression et arrêt automatique.
6. **`T3_CAPTURE_S2_C_REVIEW`**  
   Relecture avec son. Question : `VOIT-ON LE GESTE DU DÉBUT JUSQU'À LA FIN ?` Actions : `REFAIRE` / `SCÈNE SUIVANTE`.

### Écrans 7 à 9 — Scène 3 : LE DRESSAGE · 7 s

7. **`T3_CAPTURE_S3_A_GUIDE`**  
   Explique de filmer la sauce, la garniture ou la touche finale, puis de retirer la main et garder le résultat immobile deux secondes.
8. **`T3_CAPTURE_S3_B_RECORDING`**  
   Caméra plein écran, microphone actif, `SCÈNE 3/4`, `REC`, chrono `0:00 → 0:07`, progression et arrêt automatique.
9. **`T3_CAPTURE_S3_C_REVIEW`**  
   Relecture avec son. Question : `VOIT-ON LE DRESSAGE ET LA TOUCHE FINALE ?` Actions : `REFAIRE` / `SCÈNE SUIVANTE`.

### Écrans 10 à 12 — Scène 4 : PRÊT À SERVIR · 9 s

10. **`T3_CAPTURE_S4_A_GUIDE`**  
    Demande d'avancer ou poser doucement le plat fini, retirer la main, choisir le meilleur angle et tenir le plan stable pendant les trois dernières secondes.
11. **`T3_CAPTURE_S4_B_RECORDING`**  
    Caméra plein écran, microphone actif, `SCÈNE 4/4`, `REC`, chrono `0:00 → 0:09`, progression et arrêt automatique.
12. **`T3_CAPTURE_S4_C_REVIEW`**  
    Relecture avec son. Question : `LE PLAT RESTE-T-IL NET ET VISIBLE À LA FIN ?` Actions : `REFAIRE` / `VOIR MON MONTAGE`.

## 4. Règles communes du parcours

- Le décompte `3 · 2 · 1` se place entre A et B; il ne compte pas comme un treizième écran.
- La fiche de consigne disparaît entièrement pendant l'enregistrement.
- Le micro reste actif, même si parler est facultatif.
- Chaque prise s'arrête automatiquement à sa durée contractuelle.
- `REFAIRE` supprime seulement la prise courante et revient au GUIDE de la même scène.
- Les prises déjà acceptées restent conservées.
- Après S4C, `VOIR MON MONTAGE` ouvre l'étape de montage.

## 5. Verrou des transitions 2 + 4

Le fichier `reverse-engineering/T3_TRANSITIONS_30S_PROPOSITION.json` contient toutes les familles de transitions des deux références avec `required: true`, leur origine, leurs variantes observées et leur emplacement prévu sur les 900 images.

Le commerçant ne doit pas reproduire ces effets pendant le tournage. Le moteur les fabriquera ensuite à partir des quatre prises seulement.

## 6. Décision enregistrée

Le propriétaire a choisi **Tout valider** le 18 novembre 2026. Sont verrouillés :

1. les six questions ;
2. les titres et consignes des quatre scènes ;
3. la répartition 6/8/7/9 secondes ;
4. les douze écrans et leurs actions ;
5. la mention `français · fon · anglais` et le caractère facultatif de la parole.

L'approbation machine se trouve dans `approvals/APPROBATION_QUESTIONS_CAPTURE_12_ECRANS_2026-11-18.json`. Le moteur et le rendu MP4 ne sont pas encore développés.
