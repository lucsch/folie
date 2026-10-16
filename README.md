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
