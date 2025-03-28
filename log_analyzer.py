# Importez les bibliothèques nécessaires
import re
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType

# --- Configuration ---
# Adaptez ce chemin vers votre fichier de log
log_file_path = "/data/access.log"

# Expression régulière pour parser le Combined Log Format
# Ex: 192.168.1.10 - - [28/Mar/2025:10:15:30 +0100] "GET /images/logo.png HTTP/1.1" 200 12345 "http://example.com/" "Mozilla/5.0 (...)"
# Groupes : 1:IP, 2:ClientID, 3:UserID, 4:Timestamp, 5:Method, 6:URL, 7:Protocol, 8:Status, 9:Size, 10:Referrer, 11:UserAgent
LOG_PATTERN = r'^(\S+) (\S+) (\S+) \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S*)\s*(\S*)" (\d{3}) (\S+) "([^"]*)" "([^"]+)"$'

# --- Initialisation Spark ---
spark = SparkSession.builder \
    .appName("WebLogAnalysis") \
    .master("local[*]") \
    .getOrCreate() # En environnement cluster, ajustez .master()

print(f"SparkSession initialisée. Version Spark: {spark.version}")
print("-" * 30)

# --- Tâche 1: Chargement et Parsing ---
print("Tâche 1: Chargement et Parsing des logs...")

# Charger les données brutes
raw_logs_df = spark.read.text(log_file_path).withColumnRenamed("value", "raw_log")

# Parser les lignes avec regexp_extract
# Note: regexp_extract renvoie une chaîne vide si le groupe ne correspond pas ou si la regex échoue
parsed_logs_df = raw_logs_df.select(
    F.regexp_extract('raw_log', LOG_PATTERN, 1).alias('ip'),
    F.regexp_extract('raw_log', LOG_PATTERN, 4).alias('timestamp_str'),
    F.regexp_extract('raw_log', LOG_PATTERN, 5).alias('method'),
    F.regexp_extract('raw_log', LOG_PATTERN, 6).alias('url'),
    F.regexp_extract('raw_log', LOG_PATTERN, 7).alias('protocol'),
    F.regexp_extract('raw_log', LOG_PATTERN, 8).alias('status_str'),
    F.regexp_extract('raw_log', LOG_PATTERN, 9).alias('size_str'),
    F.regexp_extract('raw_log', LOG_PATTERN, 10).alias('referrer'),
    F.regexp_extract('raw_log', LOG_PATTERN, 11).alias('user_agent')
)

# Filtrer les lignes qui n'ont pas pu être parsées (basé sur un champ essentiel comme IP ou status)
# On vérifie que l'IP n'est pas une chaîne vide
valid_logs_df = parsed_logs_df.filter(F.col('ip') != '')

# Convertir les types et gérer les valeurs manquantes/spéciales
valid_logs_df = valid_logs_df.withColumn('status', F.col('status_str').cast(IntegerType()))
valid_logs_df = valid_logs_df.withColumn(
    'size',
    F.when(F.col('size_str') == '-', 0) # Si la taille est '-', mettre 0
     .otherwise(F.col('size_str').cast(LongType())) # Sinon, convertir en Long
)
# Optionnel: Convertir le timestamp (peut être coûteux)
# Assurez-vous que le format 'dd/MMM/yyyy:HH:mm:ss Z' correspond EXACTEMENT à vos logs
# valid_logs_df = valid_logs_df.withColumn('timestamp', F.to_timestamp('timestamp_str', 'dd/MMM/yyyy:HH:mm:ss Z'))

# Supprimer les colonnes string intermédiaires si elles ne sont plus nécessaires
final_logs_df = valid_logs_df.drop('status_str', 'size_str') # Ajoutez 'timestamp_str' si 'timestamp' a été créé

# Mise en cache car ce DataFrame sera réutilisé plusieurs fois
final_logs_df.cache()

# Afficher le schéma et quelques exemples
print("Schéma du DataFrame parsé :")
final_logs_df.printSchema()
print("Exemples de lignes parsées :")
final_logs_df.show(5, truncate=False)
print("-" * 30)

# --- Tâche 2: Analyses de Base ---
print("Tâche 2: Analyses de Base...")

total_requests = final_logs_df.count()
print(f"Nombre total de requêtes valides : {total_requests}")

unique_ips = final_logs_df.select('ip').distinct().count()
print(f"Nombre d'adresses IP uniques : {unique_ips}")
print("-" * 30)

# --- Tâche 3: Analyse des Statuts HTTP ---
print("Tâche 3: Analyse des Statuts HTTP...")

status_counts_df = final_logs_df.groupBy('status').count()
print("Nombre de requêtes par code de statut HTTP :")
status_counts_df.show()

print("Top 5 des codes de statut les plus fréquents :")
status_counts_df.orderBy(F.col('count').desc()).show(5)
print("-" * 30)

# --- Tâche 4: Analyse des Requêtes ---
print("Tâche 4: Analyse des Requêtes...")

# Exclure potentiellement les requêtes sans URL (si possible)
url_counts_df = final_logs_df.filter(F.col('url') != '').groupBy('url').count()

print("Top 10 des ressources les plus demandées :")
url_counts_df.orderBy(F.col('count').desc()).show(10, truncate=False)
print("-" * 30)

# --- Tâche 5: Analyse des Erreurs ---
print("Tâche 5: Analyse des Erreurs...")

# Requêtes en erreur (4xx ou 5xx)
error_df = final_logs_df.filter((F.col('status') >= 400) & (F.col('status') < 600))
print(f"Nombre total de requêtes en erreur (4xx, 5xx) : {error_df.count()}")

# Erreurs 404 (Not Found)
not_found_df = final_logs_df.filter(F.col('status') == 404)
not_found_counts_df = not_found_df.groupBy('url').count()

print("Top 10 des ressources générant le plus d'erreurs 404 :")
not_found_counts_df.orderBy(F.col('count').desc()).show(10, truncate=False)
print("-" * 30)

# --- Tâche 6: (Optionnel) Analyse Temporelle ---
# Assurez-vous que la colonne 'timestamp' a été créée et parsée correctement plus haut
# Décommentez cette section si vous avez activé la conversion du timestamp
# print("Tâche 6: (Optionnel) Analyse Temporelle...")
# if 'timestamp' in final_logs_df.columns:
#     hourly_counts_df = final_logs_df.withColumn('hour', F.hour(F.col('timestamp'))) \
#                                     .groupBy('hour') \
#                                     .count() \
#                                     .orderBy('hour')
#     print("Nombre de requêtes par heure :")
#     hourly_counts_df.show(24)
# else:
#     print("Conversion du timestamp désactivée ou échouée, section ignorée.")
# print("-" * 30)

# --- Tâche 7: (Optionnel) Utilisation de Spark SQL ---
print("Tâche 7: (Optionnel) Utilisation de Spark SQL...")

# Créer une vue temporaire
final_logs_df.createOrReplaceTempView("logs_view")

print("Exécution de la Tâche 3 (Top 5 Status) avec Spark SQL:")
top_5_status_sql = spark.sql("""
    SELECT status, COUNT(*) as count
    FROM logs_view
    GROUP BY status
    ORDER BY count DESC
    LIMIT 5
""")
top_5_status_sql.show()

print("Exécution de la Tâche 4 (Top 10 URLs) avec Spark SQL:")
top_10_urls_sql = spark.sql("""
    SELECT url, COUNT(*) as count
    FROM logs_view
    WHERE url != ''
    GROUP BY url
    ORDER BY count DESC
    LIMIT 10
""")
top_10_urls_sql.show(truncate=False)
print("-" * 30)


# --- Nettoyage ---
print("Analyse terminée. Arrêt de la SparkSession.")
spark.stop()