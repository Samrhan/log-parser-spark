# spark-log-analysis/Dockerfile

# Utilisez une image Bitnami Spark avec une version de Spark et Python compatible
# Vérifiez les tags disponibles sur Docker Hub: https://hub.docker.com/r/bitnami/spark/tags
# Ex: Spark 3.5 avec Python 3.9
FROM bitnami/spark

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le script PySpark dans le répertoire de travail de l'image
# Note: Le fichier de log sera monté via docker-compose, pas copié ici
COPY log_analyzer.py .

# (Optionnel) Si votre script a d'autres dépendances Python:
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# La commande par défaut pour exécuter le script lors du démarrage du conteneur
# spark-submit s'occupe de lancer l'application Spark
CMD ["spark-submit", "log_analyzer.py"]

# Note: L'image bitnami/spark configure déjà SPARK_HOME et autres variables d'environnement.
# Elle inclut également PySpark correspondant à la version de Spark.