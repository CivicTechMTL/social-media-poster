# Civic Tech Montréal Social Media Poster

[English](README.md) | **Français**

Un ensemble d'outils pour générer des visuels promotionnels bilingues (FR/EN) de 1080×1080 pour les
meetups de [Civic Tech Montréal](https://mtl.civictech.ca/), sur un arrière-plan en dégradé de taches
de couleur qui suit les saisons montréalaises, et pour les publier sur les médias sociaux.

Vous pouvez générer les visuels, les prévisualiser dans un navigateur et les publier sur Bluesky avec
leur texte alternatif (y compris des publications antidatées pour les événements passés). Les
légendes et textes alternatifs Instagram se trouvent au même endroit, pour une publication manuelle.

## Installation

Python 3.10 ou plus récent est requis. Depuis le dossier du projet, chargez (dot-source) le script
d'installation correspondant à votre terminal :

```powershell
. .\setup.ps1        # PowerShell
```

```sh
source setup.sh      # bash/zsh (macOS, Linux, Git Bash)
```

Il crée `.venv` au besoin, l'active dans votre terminal, installe les paquets Python et le Chromium de
Playwright, puis copie `.env.example` vers `.env` s'il n'existe pas encore. Relancez-le en tout temps
pour installer de nouvelles dépendances ou pour réactiver l'environnement virtuel dans un nouveau
terminal. Si PowerShell bloque le script, lancez d'abord `Set-ExecutionPolicy -Scope Process Bypass`.

## Tâches

Les commandes courantes sont des tâches [Poe the Poet](https://poethepoet.natn.io/), définies dans
`pyproject.toml`. Lancez `poe` sans argument pour les lister. Les arguments supplémentaires sont
transmis au script.

```sh
poe render data/100             # les deux mises en page
poe render-all                  # les deux mises en page pour chaque événement de data/
poe serve                       # aperçu en direct à http://localhost:8000
poe bsky-check data/100         # vérifie, sans rien publier
poe bsky-post data/100          # publie (demande d'abord)
poe bg-demo                     # une année d'arrière-plans dans out/bg-demo/
poe logo                        # régénère assets/logo-white.png
```

Toutes les options des scripts fonctionnent avec leur tâche, p. ex. `poe render data/100 --reroll 2`.
Lancez `poe render --help` (ou n'importe quelle tâche avec `--help`) pour voir les options.

## Créer un visuel

### 1. Ajouter les données de l'événement

Créez `data/<numéro>/data.json` et déposez la ou les photos des conférenciers à côté. Les noms de
dossier sont complétés par des zéros sur trois chiffres pour qu'ils se trient correctement
(`data/007`, `data/010.5`), mais les commandes acceptent les deux formes : `poe render data/7` trouve
`data/007`.

```json
{
  "number": 100,
  "date": "2031-02-06",
  "time": "18:30",
  "format": "hybrid",
  "speakers": [
    { "name": "Bonhomme de Neige", "photo": "bonhomme.jpg" }
  ],
  "talk": {
    "fr": "Zéro nid-de-poule : une ville réparée par ses citoyens",
    "en": "Pothole Zero: A City Fixed by Its Citizens"
  }
}
```

- `format` : `hybrid` | `in-person` | `online`
- `speakers` : aucun (hacknight), un ou deux. L'option `"photo_position": "50% 30%"` ajuste le
  recadrage circulaire.
- Le texte avant un `:` dans le titre de la présentation est mis en gras.
- L'option `"series": "Hacknight"` remplace « Meetup #N » dans l'en-tête.
- L'option `"hide_photos": true` retire les cercles de photos, mais garde les noms des conférenciers.

> **À FAIRE :** prendre en charge 3 conférenciers ou plus

### 2. Générer

```sh
poe render data/100                 # -> data/100/img-card.jpg + img-open.jpg
poe render data/100 --layout card   # -> data/100/img-card.jpg seulement
poe render data/100 --layout open   # -> data/100/img-open.jpg seulement
poe render data/100 --reroll 2      # nouvel agencement des taches (remplace bg.jpg)

poe render-all                     # chaque mise en page pour chaque événement de data/
```

L'arrière-plan est enregistré dans le dossier de l'événement sous le nom `bg.jpg` : il est généré au
premier rendu, puis réutilisé, de sorte que toutes les mises en page et tous les nouveaux rendus le
partagent. `--reroll` le remplace.

Tout `bg.jpg` déjà présent dans le dossier est utilisé tel quel : vous pouvez donc y déposer votre
propre arrière-plan (idéalement 1080×1080; les autres tailles sont mises à l'échelle et recadrées au
centre). Il n'est pas remplacé, sauf si vous passez `--reroll`.

Pour utiliser plutôt un visuel déjà fait (comme pour le meetup 9), enregistrez-le dans le dossier sous
`img-card.jpg` / `img-open.jpg` et ajoutez `"premade": true` à `data.json`; le rendu saute alors cet
événement (et `render-all` l'ignore).

Mises en page : `card` (panneau givré) ou `open` (texte directement sur l'arrière-plan). Le texte de
la présentation s'ajuste pour remplir son espace. Le français et l'anglais ont le même style; le
français est aligné à gauche, l'anglais à droite.

## Prévisualiser les visuels

```sh
poe serve            # http://localhost:8000
```

Liste chaque événement de `data/`, avec un lien par mise en page. Les pages sont exactement le HTML
qui est capturé, vous pouvez donc utiliser les outils de développement du navigateur pour inspecter
et ajuster le CSS. Les gabarits sont relus à chaque actualisation; redémarrez le serveur après avoir
modifié le code Python. Les pages utilisent le `bg.jpg` de l'événement s'il existe. Ajoutez
`?reroll=x` pour essayer un autre arrière-plan; les aperçus n'écrivent jamais `bg.jpg`.

## Publier

### Bluesky

1. Copiez `.env.example` vers `.env` et remplissez l'identifiant et un
   [mot de passe d'application](https://bsky.app/settings/app-passwords) (pas le mot de passe du
   compte).
2. Ajoutez `post-bsky.txt` (texte de la publication, 300 caractères au maximum, les URL deviennent des
   liens) à côté du `data.json` de l'événement. Le texte alternatif du visuel vient du fichier partagé
   `alt.txt` (voir plus bas).
3. Générez le visuel, vérifiez, puis publiez :

   ```sh
   poe render data/100
   poe bsky-check data/100   # affiche le texte, les longueurs et la taille du visuel; ne publie rien
   poe bsky-post data/100    # demande avant de publier
   ```

Le visuel est converti en JPEG pour respecter la limite de 1 Mo de Bluesky. Après la publication,
`data/<n>/bluesky.json` enregistre l'URL de la publication, et `poe bsky-post` ne republiera pas cet
événement, sauf si vous passez `--force`.

**Rattraper des événements passés :** ajoutez `"bsky-backfill-date": "2025-12-15"` à `data.json` et
la publication est antidatée à midi, heure de Montréal, ce jour-là (ou indiquez une heure précise, p.
ex. `"2025-12-15T09:30"`). `bsky-check` affiche la date qui sera utilisée. Bluesky marque les
publications antidatées comme archivées et les classe selon cette date : elles n'apparaîtront donc
pas en haut du fil des abonnés.

### Instagram

Instagram se publie à la main. À côté du `data.json` de chaque événement, `post-insta.txt` contient la
légende (anglais, puis français, 2 200 caractères au maximum) et `alt.txt` contient le texte
alternatif du visuel (anglais, puis français), partagé avec Bluesky. Utilisez le visuel `card`.

## Autres outils

- `poe bg-demo` - génère une année d'arrière-plans aux deux semaines dans `out/bg-demo/`, avec une
  planche contact.
- `poe logo` - régénère `assets/logo-white.png` à partir du logo sarcelle, `assets/logo-teal.png`.
- `tools/luma-set-cover.js` - à coller dans la console des outils de développement sur luma.com pour
  définir l'image de couverture des événements à partir de `data/<n>/img-open.jpg` (choisissez le
  dossier `data`, cochez les événements). Voir les commentaires en haut du fichier.

## Structure

```
src/            Le code; les scripts derrière les tâches poe sont au premier niveau
  shared/       Utilisé des deux côtés : chemins et chargement de data.json
  images/       Génération des visuels : arrière-plans saisonniers et rendu HTML → JPEG
  posting/      Publication sur les médias sociaux (Bluesky)
templates/      Gabarits HTML Jinja pour chaque mise en page
assets/         Polices et logos, plus les bios des comptes (_refs/ est local seulement, hors git)
data/           Un dossier par événement (avec zéros : 002, 010.5) : data.json, textes, visuels
tools/          Outils ponctuels (générateur de logo, téléversement des couvertures Luma)
```

Les scripts sont lancés comme modules depuis la racine du projet (p. ex.
`python -m src.make_image`), ce que font les tâches `poe`.
