# T3 — Contrat de lisibilité typographique v0.3

Ce contrat typographique reste actif dans la v0.4. Le candidat vidéo v0.3 a été rejeté pour des traits de transition sans rapport avec les polices; la lisibilité corrigée est conservée.

## Défaut constaté sur la v0.2

Le propriétaire a validé la fluidité des transitions mais a rejeté la lisibilité de plusieurs petits textes. Les captures de preuve sont conservées dans :

- `proofs/owner-feedback/T3_V0_2_POLICE_ILLISIBLE_FINAL.png` ;
- `proofs/owner-feedback/T3_V0_2_POLICE_ILLISIBLE_IDENTITE.png`.

La cause est déterministe : `Montserrat-Variable.ttf` possède un axe `Weight` de 100 à 900 et sa valeur par défaut est **100 (Thin)**. La v0.2 chargeait cette police sans fixer l’axe. Le nom, le quartier et le CTA étaient en outre rendus entre 17 et 25 px, puis encore réduits dans le lecteur.

## Source de vérité JSON

La correction est verrouillée dans `config/T3_TEXT_MOTION_V0_3_0.json`. Le moteur ne choisit plus silencieusement les graisses ou tailles : il lit les rôles du bloc `legibility.roles`.

| Rôle | Famille | Poids | Taille minimale 720 px | Taille minimale à 40 % |
|---|---|---:|---:|---:|
| nom du commerçant | Montserrat | 700 | 30 px | 12,0 px |
| prix | Plus Jakarta Sans | 700 | 44 px | 17,6 px |
| quartier | Plus Jakarta Sans | 650 | 28 px | 11,2 px |
| CTA | Montserrat | 750 | 28 px | 11,2 px |
| WhatsApp | Plus Jakarta Sans | 700 | 30 px | 12,0 px |

Le produit et l’accroche restent en DM Serif Display, avec un minimum respectif de 48/42 px.

## Contraste et protection

- couleurs claires : contraste contractuel minimal **7:1** sur le fond protégé ;
- résultat mesuré : 13,06:1 pour l’accent et 17,97:1 pour l’ivoire ;
- ombre noire opacité 230 ;
- contour sombre de 2 px ;
- dégradé final : force 0,66 en haut et 0,80 en bas ;
- aucune carte dure et aucune modification des transitions.

## Contrôles bloquants

Le moteur refuse la configuration si :

- un poids variable est absent ou hors de l’axe de la police ;
- un petit texte descend sous 11 px à l’échelle de contrôle de 40 % ;
- un petit texte utilise un poids inférieur à 600 ;
- le contraste calculé descend sous 7:1 ;
- le dégradé final ou l’ombre ne protège plus suffisamment les textes.

Le test `test_montserrat_weight_axis_is_actually_applied` compare aussi l’encre rendue en poids 700 à celle du poids 100. Il empêche une régression où la valeur JSON serait présente sans être appliquée par Pillow.

## Preuve serveur

Le run GitHub Actions `44551121356` passe 27/27 contrôles. Le MP4 de la pré-Release a été téléchargé puis revalidé 27/27. Les images 86, 551 et 899 du MP4 serveur ont été réduites à 40 % et sont conservées dans `proofs/typography-v0.3-server/`; le nom, l’accroche, le quartier, le CTA et WhatsApp y restent lisibles.

## Données commerçant

La correction ne change pas le contrat éditorial : seuls `nom`, `produit`, `prix`, `whatsapp`, `quartier` et `accroche` viennent du RenderJob. Le seul texte fixe reste `COMMANDER MAINTENANT`.
