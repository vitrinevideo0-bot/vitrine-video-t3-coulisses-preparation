# Simulation du parcours T3

Cette simulation consomme directement `config/T3_CAPTURE_FLOW_V1_0_0.json` et parcourt les douze écrans stables dans l’ordre S1A…S4C.

Depuis la racine du dépôt :

```bash
python -m http.server 8000
```

Puis ouvrir `http://localhost:8000/simulation/`.

Elle sert de preuve contractuelle navigateur; elle n’est pas une application caméra Android et ne prétend pas enregistrer de vrais médias.
