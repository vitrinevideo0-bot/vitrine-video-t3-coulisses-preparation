# T3 — Contrat de visibilité des transitions v0.4

## Défaut constaté sur la v0.3

Le propriétaire a approuvé la fluidité et la lisibilité, mais a rejeté deux traits bleus horizontaux puis deux traits bleus verticaux pendant `R4_MULTI_PANEL_MATCH_CUT`.

Preuves :

- `proofs/owner-feedback/T3_V0_3_TRAITS_BLEUS_HORIZONTAUX.png` ;
- `proofs/owner-feedback/T3_V0_3_TRAITS_BLEUS_VERTICAUX.png`.

## Cause

Le contrat JSON indiquait déjà `border_px: 0`, mais l’ancienne fonction `panel_match` ignorait cette valeur et dessinait deux lignes BGR `(244, 206, 103)` de 4 px en dur :

- aux limites des trois rangées pendant la première moitié ;
- aux limites des trois colonnes pendant la seconde moitié.

Ces lignes étaient des séparateurs de montage, pas des éléments publicitaires. Elles n’auraient jamais dû être visibles.

## Correction ancrée dans le JSON

Le profil `R4_MULTI_PANEL_MATCH_CUT` de `reverse-engineering/T3_TRANSITIONS_30S.json` impose désormais :

```json
{
  "gap_px": 0,
  "border_px": 0,
  "separator_lines": false,
  "separator_color": null,
  "separator_policy": "forbidden_by_owner"
}
```

La contrainte globale `owner_constraints.visible_transition_guides_allowed` vaut `false`.

## Logique moteur

`engine/render_silent.py` passe le profil JSON à `panel_match`. Une ligne ne peut être dessinée que si `separator_lines` vaut explicitement `true` **et** si `border_px` est supérieur à zéro. Le moteur échoue avant le rendu si le contrat propriétaire interdit les guides mais que le profil tente de les réactiver.

Le mouvement des rangées et colonnes est conservé. Seuls les traits colorés sont supprimés.

## Contrôles bloquants

- test du contrat : écart, bordure et séparateurs à zéro/désactivés ;
- test moteur sur image grise uniforme aux phases horizontale et verticale : la sortie doit rester intégralement grise ;
- rapport de rendu : `visible_transition_guides_rendered: false` ;
- validation indépendante : contrôle du profil et des images de preuve 771 et 778 ;
- planche de contrôle : images 771 et 778 incluses explicitement.
