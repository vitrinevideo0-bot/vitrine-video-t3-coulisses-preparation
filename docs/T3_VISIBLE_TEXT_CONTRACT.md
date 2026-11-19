# T3 — Contrat des textes visibles dans la publicité

## Corrections imposées par le propriétaire

- v0.1 rejetée : informations de fabrication visibles dans la publicité ;
- v0.2 rejetée : plusieurs petits textes utilisent une graisse Thin et deviennent illisibles dans la prévisualisation ;
- v0.3 : même logique commerciale, avec poids, tailles minimales et contraste verrouillés dans le JSON.

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

Le contrat de lisibilité détaillé est `docs/T3_TYPOGRAPHY_LEGIBILITY_CONTRACT.md`. Les rôles exécutables sont dans `config/T3_TEXT_MOTION_V0_3_0.json`.

## Chaînes explicitement interdites à l’image

`SCÈNE`, les durées `6 S / 7 S / 8 S / 9 S`, `DÉMO`, `RUSHS`, `PEXELS`, `T3`, ainsi que les titres de captation `LES INGRÉDIENTS`, `LE GESTE SIGNATURE`, `LE DRESSAGE` et `PRÊT À SERVIR`.

La provenance Pexels reste dans `docs/LICENCES_RUSHS.md` et les manifestes, jamais dans les pixels de la publicité.
