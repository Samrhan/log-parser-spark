# log-parser-spark# Analyseur de Logs Apache avec Spark (Projet Éducatif)

Ce projet est une application éducative conçue pour démontrer comment utiliser Apache Spark, via PySpark, pour analyser des fichiers de logs web au format Apache Combined Log Format. Il comprend un générateur de logs et un script d'analyse qui extrait diverses métriques à partir des données de logs. L'ensemble est orchestré à l'aide de Docker Compose pour faciliter la mise en place de l'environnement Spark.

## Objectifs Pédagogiques

* Comprendre les bases du traitement de données distribué avec Apache Spark.
* Apprendre à lire et parser des fichiers texte (logs) avec PySpark.
* Utiliser les expressions régulières (regex) pour extraire des informations structurées de données non structurées.
* Effectuer des opérations courantes d'analyse de données avec Spark SQL (comptages, agrégations, tris).
* Se familiariser avec la mise en place d'un environnement Spark simple à l'aide de Docker Compose.
* Découvrir la manipulation de DataFrames Spark.

## Fonctionnalités

* **Génération de Logs** : Un script Python (`logs_generator.py`) pour créer des fichiers de logs réalistes au format Apache Combined Log.
* **Parsing de Logs** : Utilisation d'expressions régulières pour parser chaque ligne de log.
* **Analyse Détaillée** : Le script `log_analyzer.py` effectue les analyses suivantes :
    * Nombre total de requêtes.
    * Répartition des codes de statut HTTP (2xx, 3xx, 4xx, 5xx).
    * Identification des 10 hôtes (adresses IP) les plus fréquents.
    * Identification des 10 endpoints (URLs) les plus demandés.
    * Comptage du nombre d'hôtes uniques.
    * Identification des 10 endpoints générant le plus d'erreurs 404.
    * Calcul du nombre de requêtes par hôte.
    * Calcul du volume total de données transférées (en bytes).
* **Environnement Conteneurisé** : Utilisation de Docker Compose pour déployer un cluster Spark (1 master, 1 worker) prêt à l'emploi.

## Technologies Utilisées

* [Apache Spark](https://spark.apache.org/) : Moteur de traitement de données distribué.
* [PySpark](https://spark.apache.org/docs/latest/api/python/) : API Python pour Apache Spark.
* [Python](https://www.python.org/) : Langage de programmation principal pour les scripts.
* [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) : Pour la conteneurisation et l'orchestration de l'environnement Spark.
* [Faker](https://faker.readthedocs.io/en/master/) : Bibliothèque Python pour générer des données fictives (utilisée dans `logs_generator.py`).

## Prérequis

* [Docker](https://docs.docker.com/get-docker/) installé sur votre machine.
* [Docker Compose](https://docs.docker.com/compose/install/) (souvent inclus avec Docker Desktop).
* [Python 3](https://www.python.org/downloads/) (principalement pour exécuter le générateur de logs si nécessaire, bien que l'analyse se fasse dans le conteneur Spark).
* Bibliothèque Python `Faker` (si vous souhaitez exécuter `logs_generator.py` localement) :
    ```bash
    pip install Faker
    ```

## Installation et Configuration

1.  **Clonez le dépôt :**
    ```bash
    git clone <URL_DU_DEPOT> # Remplacez par l'URL de votre dépôt si applicable
    cd log-parser-spark-main
    ```

2.  **Construisez et démarrez les conteneurs Docker :**
    Cette commande va télécharger les images Spark nécessaires (si elles ne sont pas déjà présentes) et démarrer le master et le worker Spark. Le répertoire courant sera monté dans les conteneurs, rendant les scripts et les données accessibles.
    ```bash
    docker-compose up -d
    ```
    Vous pouvez vérifier que les conteneurs tournent avec `docker ps`. Vous devriez voir un conteneur pour le master Spark et un pour le worker.

## Utilisation

### 1. Générer des Données de Logs (Optionnel)

Le projet inclut un fichier `data/access.log` pré-généré. Si vous souhaitez générer un nouveau fichier de logs ou un fichier plus volumineux :

* **Option A : Exécuter localement (si Python et Faker sont installés)**
    ```bash
    python logs_generator.py --num-lines 10000 --output-file data/access_new.log
    ```
    * `--num-lines`: Nombre de lignes de log à générer (par défaut: 1000).
    * `--output-file`: Chemin du fichier de sortie (par défaut: `data/access.log`, écrasant l'ancien).

* **Option B : Exécuter dans un conteneur Docker (si Python n'est pas installé localement)**
    Vous pouvez utiliser une image Python temporaire pour exécuter le script :
    ```bash
    # Assurez-vous que le dossier 'data' existe
    mkdir -p data
    # Exécute le générateur dans un conteneur Python éphémère
    docker run --rm -v "$(pwd):/app" -w /app python:3.9-slim python logs_generator.py --num-lines 5000 --output-file data/access.log
    ```
    *Note :* Assurez-vous d'utiliser le fichier de log généré (`data/access.log` par défaut) dans l'étape suivante.

### 2. Lancer l'Analyse Spark

Pour exécuter le script d'analyse `log_analyzer.py` sur le cluster Spark démarré via Docker Compose :

```bash
docker-compose exec spark-master spark-submit /app/log_analyzer.py /app/data/access.log
```

* `docker-compose exec spark-master`: Exécute une commande dans le conteneur `spark-master`.
* `spark-submit`: Commande standard pour soumettre une application Spark.
* `/app/log_analyzer.py`: Chemin vers le script d'analyse *à l'intérieur* du conteneur (le répertoire local est monté sur `/app`).
* `/app/data/access.log`: Chemin vers le fichier de log *à l'intérieur* du conteneur. Modifiez si vous utilisez un autre fichier.

Les résultats de l'analyse seront affichés dans la console de votre terminal.

## Format des Logs Attendus

Le script est conçu pour analyser des logs au format Apache Combined Log Format, qui ressemble à ceci :

```
<HOST> - - [<TIMESTAMP>] "<METHOD> <ENDPOINT> <PROTOCOL>" <STATUS_CODE> <CONTENT_SIZE> "<REFERER>" "<USER_AGENT>"
```

Exemple :
`192.168.1.1 - - [10/Mar/2024:13:55:36 +0100] "GET /index.html HTTP/1.1" 200 1234 "http://example.com/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"`

Le script `log_analyzer.py` utilise une expression régulière pour extraire les champs pertinents de chaque ligne.

## Nettoyage

Pour arrêter et supprimer les conteneurs Spark :

```bash
docker-compose down
```

Cela arrêtera les conteneurs, mais ne supprimera pas les fichiers locaux (scripts, données).