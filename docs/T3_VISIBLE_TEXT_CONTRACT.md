# T3 — Contrat des textes visibles dans la publicité

## Correction imposée par le propriétaire

Le premier candidat silencieux a été rejeté parce qu’il affichait des informations de fabrication : titres de scènes, durées et provenance des rushes. Ces éléments appartiennent au parcours de capture ou aux preuves techniques; ils ne doivent jamais apparaître dans la publicité livrée.

## Source unique

Le moteur lit `merchant_payload` dans le RenderJob. Les seules clés commerciales admises sont :

- `nom` ;
- `produit` ;
- `prix` ;
- `whatsapp` ;
- `quartier` ;
- `accroche`, facultative.

Le seul texte fixe autorisé dans le montage est `COMMANDER MAINTENANT`. `FCFA` est une normalisation d’affichage du prix et n’est ajouté qu’une fois.

## Liaisons

| Bloc | Fenêtre | Données visibles |
|---|---:|---|
| `T3_G01_IDENTITY` | images 18–155 | nom + produit |
| `T3_G02_OFFER` | images 210–377 | produit + prix |
| `T3_G03_HOOK` | images 450–605 | accroche + nom; si accroche vide, nom seulement |
| `T3_G04_FINAL` | images 660–899 | nom + produit + prix + quartier + WhatsApp + CTA fixe |

Les textes sont composités **après** les transitions afin de rester nets. Les fonds n’emploient que des dégradés doux; aucun encart technique, badge, carte dure ou bordure de guide de capture n’est autorisé.

## Chaînes explicitement interdites à l’image

`SCÈNE`, les durées `6 S / 7 S / 8 S / 9 S`, `DÉMO`, `RUSHS`, `PEXELS`, `T3`, ainsi que les titres de captation `LES INGRÉDIENTS`, `LE GESTE SIGNATURE`, `LE DRESSAGE` et `PRÊT À SERVIR`.

La provenance Pexels reste dans `docs/LICENCES_RUSHS.md` et les manifestes, jamais dans les pixels de la publicité.
