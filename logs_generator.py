#!/usr/bin/env python3
import random
import time
import datetime
import argparse
import sys
import os
from faker import Faker

# Initialiser Faker (utilise en_US par défaut, suffisant pour ce cas)
fake = Faker()

# --- Configuration des choix possibles ---
# Méthodes HTTP et leurs poids relatifs
http_methods = ["GET", "POST", "PUT", "DELETE", "HEAD"]
http_methods_weights = [75, 15, 3, 2, 5]

# Codes de statut HTTP et leurs poids relatifs
# (Plus de 200, quelques 3xx et 404, moins de 5xx/autres 4xx)
status_codes = [200, 301, 304, 404, 500, 403, 401, 201]
status_codes_weights = [70, 5, 10, 7, 2, 3, 1, 2]

# Protocoles HTTP
protocols = ["HTTP/1.1", "HTTP/1.0", "HTTP/2.0"]
protocols_weights = [85, 10, 5]

# Quelques chemins d'URL courants pour plus de réalisme
common_paths = ["/", "/index.html", "/login", "/products", "/images/logo.png", "/favicon.ico", "/api/users"]
common_paths_weights = [20, 10, 5, 15, 8, 7, 10] # Le reste sera généré par faker

def generate_log_line(start_time, current_offset_seconds):
    """Génère une seule ligne de log au format Combined Log Format."""

    # 1. Adresse IP
    ip = fake.ipv4()

    # 2. Client ID (souvent '-')
    client_id = "-"

    # 3. User ID (souvent '-')
    user_id = "-"

    # 4. Timestamp
    # Génère un timestamp en avançant depuis le début + offset
    event_time = start_time + datetime.timedelta(seconds=current_offset_seconds)
    # Format: [DD/Mon/YYYY:HH:MM:SS +ZZZZ]
    # Attention: %b dépend de la locale système. S'assurer qu'elle est de type 'en_US' pour 'Mar', 'Apr', etc.
    # Alternativement, on pourrait forcer la locale ou utiliser un mapping manuel.
    try:
        # Forcer temporairement la locale si nécessaire (peut impacter le multithreading)
        # import locale
        # locale.setlocale(locale.LC_TIME, 'en_US.UTF-8') # ou 'C'
        timestamp = event_time.strftime("[%d/%b/%Y:%H:%M:%S %z]")
    except ValueError: # Gestion de l'erreur possible avec %z avant Python 3.x ou sur certains OS
         timestamp = event_time.strftime("[%d/%b/%Y:%H:%M:%S +0000]") # Fallback UTC

    # 5. Requête HTTP ("METHOD URL PROTOCOL")
    method = random.choices(http_methods, weights=http_methods_weights, k=1)[0]
    protocol = random.choices(protocols, weights=protocols_weights, k=1)[0]

    # Générer l'URL : soit une commune, soit une aléatoire
    if random.randint(1, 100) <= 60: # 60% de chance d'utiliser un chemin commun pondéré
        url = random.choices(common_paths, weights=common_paths_weights, k=1)[0]
        # Ajouter un ID aléatoire pour certains chemins
        if url == "/products":
            url += f"/{random.randint(1, 1000)}"
        elif url == "/api/users" and method != 'POST':
             url += f"/{random.randint(1, 500)}"
    else: # 40% de chance pour une URL générée par faker
        url = fake.uri_path()

    request = f'"{method} {url} {protocol}"'

    # 6. Code de statut HTTP
    # On pourrait lier le statut à l'URL (ex: 404 si URL non commune?) -> Simplifié ici
    status = random.choices(status_codes, weights=status_codes_weights, k=1)[0]

    # 7. Taille de la réponse
    # Lie la taille au statut (plus petit pour erreurs/redirections)
    if status == 304:
        size = "-" # Souvent '-' pour 304 Not Modified
    elif status >= 400:
        size = str(random.randint(50, 500)) # Petite taille pour les erreurs
    elif status >= 300:
        size = str(random.randint(0, 200)) # Taille nulle ou petite pour redirections
    elif method == 'HEAD':
        size = "0" # Pas de corps de réponse pour HEAD
    else: # Statut 2xx (sauf HEAD)
        size = str(random.randint(500, 15000)) # Taille variable pour succès

    # 8. Referrer
    # Soit '-', soit une URL interne, soit une URL externe
    ref_choice = random.randint(1, 100)
    if ref_choice <= 50: # 50% pas de referrer
        referrer = "-"
    elif ref_choice <= 75: # 25% referrer interne (ex: page précédente)
        ref_path = random.choices(common_paths, weights=common_paths_weights, k=1)[0]
        if ref_path == "/": ref_path = "/index.html" # Eviter le referrer '/' seul
        referrer = f"http://{fake.domain_name()}{ref_path}"
    else: # 25% referrer externe
        referrer = fake.uri()
    referrer = f'"{referrer}"'

    # 9. User Agent
    user_agent = f'"{fake.user_agent()}"'

    # Assembler la ligne de log
    log_line = f"{ip} {client_id} {user_id} {timestamp} {request} {status} {size} {referrer} {user_agent}"
    return log_line


def main():
    parser = argparse.ArgumentParser(description="Générateur de fausses logs web au format Combined Log Format.")
    parser.add_argument("-n", "--lines", type=int, default=1000, help="Nombre de lignes de log à générer.")
    parser.add_argument("-o", "--output", type=str, default="access_generated.log", help="Nom du fichier de sortie.")
    parser.add_argument("-s", "--sleep", type=float, default=0.0, help="Pause (en secondes) entre chaque ligne générée (pour simuler un flux).")
    parser.add_argument("--stdout", action="store_true", help="Écrire sur la sortie standard au lieu d'un fichier.")

    args = parser.parse_args()

    num_lines = args.lines
    output_file = args.output
    sleep_time = args.sleep
    write_to_stdout = args.stdout

    if not write_to_stdout:
        print(f"Génération de {num_lines} lignes dans le fichier '{output_file}'...")
        # Créer le répertoire parent si nécessaire
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
    else:
         print(f"Génération de {num_lines} lignes sur la sortie standard...", file=sys.stderr)


    # Définir l'heure de début (peut être ajusté pour une période spécifique)
    # Utilise le fuseau horaire local de la machine
    start_time = datetime.datetime.now(datetime.timezone.utc).astimezone() - datetime.timedelta(minutes=random.randint(60, 120)) # Commence il y a 1 ou 2 heures
    current_offset = 0 # Offset en secondes depuis start_time


    try:
        output_stream = sys.stdout if write_to_stdout else open(output_file, 'w', encoding='utf-8')
        with output_stream:
            for i in range(num_lines):
                # Faire avancer le temps légèrement et aléatoirement
                current_offset += random.uniform(0.01, 1.5) # Avance de 0.01s à 1.5s

                log_line = generate_log_line(start_time, current_offset)
                output_stream.write(log_line + "\n")

                # Afficher la progression toutes les N lignes (sur stderr si stdout est utilisé)
                if (i + 1) % 10000 == 0:
                    print(f"  {i + 1}/{num_lines} lignes générées...", file=sys.stderr)

                if sleep_time > 0:
                    time.sleep(sleep_time)

        if not write_to_stdout:
            print(f"Terminé. Fichier '{output_file}' généré.")
        else:
            print("Génération terminée.", file=sys.stderr)

    except IOError as e:
        print(f"Erreur lors de l'écriture dans '{output_file}': {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nGénération interrompue par l'utilisateur.", file=sys.stderr)

if __name__ == "__main__":
    main()