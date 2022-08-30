# Movie Pipeline

Ensemble d'outils automatisant une grande partie du processus d'extraction de 
contenus pertinents des vidéos.

## Utilisation

```
$ python app.py --help
usage: app.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] {legacy_move,process_movie,scaffold_dir} ...

positional arguments:
  {legacy_move,process_movie,scaffold_dir}
                        Available commands:
    legacy_move         Move converted movies or series to their folder
    process_movie       Cut and merge movies to keep only relevant parts
    scaffold_dir        Scaffold movie processed data files from movies

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
```

## Pipeline

Ouvrir un terminal et changer le répertoire courant

```
cd D:\Documents\Autres\movie-pipeline
```

### 1. Génération des modèles et remplissage des fichiers d'instructions

Si le répertoire contenant les vidéos est `V:\PVR`, lancer la commande suivante :

```
python app.py scaffold_dir "V:\PVR"
```

A la fin de l'exécution de ce module, vous devriez trouver pour chaque film
un fichier portant le même nom se finissant par `.yml.txt`.

Ce sont les modèles à remplir.

Ouvrir le film ayant le même nom que le fichier `.yml.txt` dans un programme
de recherche de parties indésirables comme `Videpub` et lancer l'analyse.

A la fin de l'analyse, vérifier les parties à garder, c'est-à-dire :
- Supprimer les parties indésirables en sélectionnant le segment, puis cliquer
  sur l'icône moins ;

- Joindre les segments séparés en sélectionnant les segments à joindre, puis en
  cliquant sur `-><-` ;

- Corriger le début et la fin de chaque segments restants. Les parties des segments
  revus seront désormais en vert ;

- Si le fichier en question est une **série**, rechercher le nom de l'épisode
  (qui est souvent donné après le générique ou après la fin des crédits de début) 
  et en déduire le numéro de _saison_ et d'_épisode_.

  Par exemple pour l'épisode _Mariage à la mexicaine_ de la série _Drop Dead Diva_,
  entrer dans le champ `filename` du modèle `Drop Dead Diva S05E08.mp4`.

  Des sites comme [The movie Db](themoviedb.org) ou [IMDb](imdb.com) permet de trouver
  facilement ces informations à partir du nom de la série.

  Pour éviter cette fastidieuse phase de recherche, vous pouvez rechercher dans la liste
  des enregistrements terminés dans l'interface d'administration de `TVHeadend` l'entrée
  correspondante et faire une recherche sur internet. Des sites comme `L'internaute`
  vous donneront toutes les informations nécessaires au remplissage du nom de fichier.

- Enfin, sélectionner tous les segments restants, puis cliquer sur le bouton copier.
  Remplacer `INSERT_SEGMENTS_HERE` par le résultat copier, puis ajouter une virgule
  à la fin.

  Ainsi, `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560`
  devient `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560,`

### 2. Conversion en lot des films

Ce programme prend en charge toute la partie fastidieuse du traitement des films,
de la conversion au déplacement dans le bon sous-dossier tout en journalisant
chaque action.

Pour ce faire, "activer" chaque fichier d'instructions en retirant changeant l'extension
`.yml.txt` en `.yml`.

Lancer la commande suivante :

```
python app.py process_movie "V:\PVR"
```

et attendez la fin du traitement qui peut prendre plusieurs dizaines de minutes.

Vérifier s'il n'y a pas eu d'erreur à l'exécution et que les films convertis
sont bien lisibles.

S'il n'y a pas de problèmes, videz les poubelles.

> NB: Des marges de 30 min avant et après les films sont ajoutées lors de leurs 
> enregistrements.
