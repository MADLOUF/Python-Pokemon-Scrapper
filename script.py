import time
import requests
from bs4 import BeautifulSoup
import asyncio
import sqlite3
import threading
import discord
from discord.ext import commands

# Configuration des en-têtes pour la requête
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Connexion à la base de données SQLite
db_path = r"C:\Users\33662\Desktop\Scrapping Pokemon\Stock_status.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fonction pour vérifier la disponibilité sur Amazon
def check_availability_Amazon(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        # Rechercher l'information de disponibilité
        availability = soup.find("span", {"class": "a-size-medium a-color-success"})
        if availability and "en stock" in availability.text.lower():
            return 1  # Disponible
        return 0  # Indisponible
    except Exception as e:
        print(f"Erreur lors de la vérification de {url} : {e}")
        return 0  # Considérer comme indisponible en cas d'erreur

# Configuration du bot Discord
TOKEN = ""  # Remplacez par le token de votre bot
CHANNEL_ID = 1328022576118894716  # Remplacez par l'ID de votre channel

# Initialisation du bot Discord
intents = discord.Intents.default()
intents.messages = True  # Activer l'intent pour les messages
intents.message_content = True  # Activer l'intent de contenu des messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction pour envoyer une notification Discord
async def send_notification(product_url):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"@everyone Le produit est maintenant disponible ! 🚨\n{product_url}")
    else:
        print("Impossible de trouver le channel.")

# Fonction pour démarrer le bot Discord dans un thread séparé
def start_bot():
    bot.run(TOKEN)

# Démarrer le bot dans un thread séparé
threading.Thread(target=start_bot, daemon=True).start()

# Boucle principale pour vérifier chaque lien dans la base de données
while True:
    try:
        # Récupérer tous les liens et leur disponibilité actuelle
        cursor.execute("SELECT Link, Availibility FROM Stock_status")
        rows = cursor.fetchall()

        for row in rows:
            url, previous_availability = row
            current_availability = check_availability_Amazon(url)

            # Vérifier si la disponibilité est passée de 0 à 1
            if current_availability == 1 : # and previous_availability == 0:
                print(f"Produit disponible : {url}")
                # Envoyer une notification Discord
                asyncio.run(send_notification(url))
            
            # Mettre à jour la disponibilité dans la base de données
            cursor.execute("""
                UPDATE Stock_status
                SET Availibility = ?
                WHERE Link = ?
            """, (current_availability, url))

        # Valider les modifications
        conn.commit()

    except Exception as e:
        print(f"Erreur : {e}")

    # Attendre 5 minutes avant la prochaine vérification
    time.sleep(300)
