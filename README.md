# Folie

Folie génère une page HTML autonome présentant le contenu détaillé d'un
répertoire. Aucun serveur web ni accès à Internet n'est nécessaire pour consulter
le résultat.

La page propose :

- une arborescence de dossiers repliables ;
- des icônes adaptées aux principaux formats (Word, Excel, PowerPoint, PDF,
  images, archives, code, audio et vidéo) ;
- la taille, la date de dernière modification et le chemin absolu de chaque
  fichier ;
- l'ouverture du fichier en cliquant sur sa ligne ;
- la copie du chemin absolu d'un dossier via l'icône ⧉, avec les espaces et
  caractères d'origine (sans encodage URL tel que `%20`) ;
- une recherche instantanée et des commandes pour tout déplier ou replier ;
- une liste repliable des dossiers exclus, avec leurs chemins relatifs ;
- un indicateur de progression pendant le parcours et l'écriture ;
- un thème clair ou sombre suivant les préférences du système.

## Utilisation

Avec [uv](https://docs.astral.sh/uv/) et Python 3.11 ou plus récent :

```bash
uv run folie "/chemin/du/dossier" -o inventaire.html
```

Après installation du projet (`pip install .`), la commande courte est également
disponible :

```bash
folie "/chemin/du/dossier" -o inventaire.html
```

Pour exclure des sous-répertoires, répéter `--exclude` (ou `-x`) :

```bash
folie ./documents -o inventaire.html \
  --exclude .git \
  --exclude node_modules \
  --exclude "archives/20*"
```

Un motif sans `/` s'applique au nom d'un dossier, où qu'il soit dans l'arbre.
Un motif contenant `/` s'applique au chemin relatif depuis le répertoire de
départ. Les jokers `*` et `?` sont acceptés.

Pour ignorer tous les sous-répertoires cachés :

```bash
folie ./documents --exclude-hidden
```

La progression affiche le nombre de fichiers et de dossiers déjà rencontrés,
ainsi que le chemin courant. Elle peut être masquée pour une utilisation dans un
script :

```bash
folie ./documents --no-progress
```

Pour privilégier la vitesse maximale sur un dossier contenant plusieurs centaines
de milliers d'entrées, le tri alphabétique peut également être désactivé :

```bash
folie ./documents --no-sort
```

Options disponibles :

```bash
folie --help
```

> Selon les réglages de sécurité du navigateur, un fichier local peut être ouvert
> directement, téléchargé, ou transmis à son application associée. Les liens
> générés utilisent des URI `file://` standard.

## Développement

```bash
uv run pytest
```

## Interface graphique WinFolie

Installez la dépendance graphique optionnelle, puis lancez WinFolie :

```bash
uv sync --extra gui
uv run --extra gui winfolie
```

Avec pip : `pip install ".[gui]"`, puis `winfolie`.
La CLI reste utilisable sans wxPython. Sous Linux, l'installation de wxPython
peut nécessiter les bibliothèques de développement GTK et une compilation locale.

La fenêtre permet de choisir le répertoire source et le fichier HTML de sortie,
le titre, les motifs d'exclusion (un par ligne), l'exclusion des dossiers cachés,
le tri et l'affichage de la progression. La génération s'effectue en arrière-plan.
Le bouton « Ouvrir l’inventaire » affiche ensuite le résultat dans le navigateur.

Les commandes `python -m folie` et `python -m folie.gui` lancent respectivement
la CLI et la GUI dans un environnement où le projet est installé.

## Organisation du code

```text
src/folie/
├── __main__.py          # Entrée CLI
├── version.py           # Version commune, utilisable sans Git
├── core/generator.py    # Parcours et génération HTML partagés
├── cli/main.py          # Interface Typer / Rich
└── gui/
    ├── __main__.py      # Entrée GUI
    ├── app.py           # Application wxPython
    ├── main_window.py   # Fenêtre principale
    └── worker.py        # Génération en arrière-plan

tools/                  # Scripts de version et de construction
packaging/              # Configurations PyInstaller
tests/                 # Tests du moteur, de la CLI et du worker
```

Le moteur ne dépend d'aucune interface. L'API Python reste disponible via
`from folie import generate_html`. Son module est désormais
`folie.core.generator`.

## Construction des exécutables

Sur la plateforme cible (Windows, Linux ou OSX) :

```bash
uv sync --group dev --extra gui
uv run --extra gui python tools/createapp.py Windows
```

Les deux programmes sont produits dans `dist/folie/` et `dist/winfolie/`.
Utilisez `--target folie` ou `--target winfolie` pour construire un seul programme.
La construction de la CLI seule ne nécessite pas l'extra `gui`.
Les configurations se trouvent dans `packaging/folie.spec` et
`packaging/winfolie.spec` ; WinFolie est construit sans console sous Windows.

Le script de construction génère automatiquement `src/folie/_build_version.py`
avec les informations Git communes. Pour les actualiser séparément :

```bash
uv run python tools/createversion.py
```

Ce fichier est ignoré par Git. Sans lui, `version.py` fournit la version de base.
