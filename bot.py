import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime


# -----------------------------
# CONFIGURATION DU BOT
# -----------------------------

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# -----------------------------
# BASE DE DONNÉES
# -----------------------------

conn = sqlite3.connect("books.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    username TEXT,
    title TEXT,
    date TEXT
)
""")

conn.commit()


# -----------------------------
# SYNCHRONISATION DES COMMANDES /
# -----------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Connecté en tant que {bot.user}")


# -----------------------------
# AJOUTER UN LIVRE
# -----------------------------

@bot.tree.command(name="lu", description="Ajoute un livre terminé à ta bibliothèque")
@app_commands.describe(titre="Nom du livre terminé")
async def lu(interaction: discord.Interaction, titre: str):

    user_id = str(interaction.user.id)
    username = interaction.user.name
    date = datetime.now().strftime("%d/%m/%Y")

    c.execute(
        """
        INSERT INTO books (user_id, username, title, date)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, username, titre, date)
    )

    conn.commit()


    c.execute(
        "SELECT COUNT(*) FROM books WHERE user_id = ?",
        (user_id,)
    )

    total = c.fetchone()[0]


    embed = discord.Embed(
        title="📖 Nouveau livre terminé !",
        description=(
            f"Bravo {interaction.user.mention} 🎉\n\n"
            f"📚 Livre ajouté : **{titre}**\n"
            f"📊 Total de livres lus : **{total}**"
        )
    )

    await interaction.response.send_message(embed=embed)


# -----------------------------
# PROFIL
# -----------------------------

@bot.tree.command(name="profil", description="Voir ton profil de lecteur")
async def profil(interaction: discord.Interaction):

    user_id = str(interaction.user.id)


    c.execute(
        """
        SELECT COUNT(*) FROM books
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total = c.fetchone()[0]


    c.execute(
        """
        SELECT title FROM books
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    dernier = c.fetchone()

    dernier_livre = dernier[0] if dernier else "Aucun"


    if total < 5:
        niveau = "🌱 Nouveau lecteur"

    elif total < 20:
        niveau = "📖 Lecteur régulier"

    elif total < 50:
        niveau = "🔥 Lecteur passionné"

    else:
        niveau = "🏆 Maître lecteur"


    embed = discord.Embed(
        title=f"📚 Profil lecteur de {interaction.user.name}",
        description=(
            f"📖 Livres lus : **{total}**\n\n"
            f"🏅 Niveau : **{niveau}**\n\n"
            f"📌 Dernière lecture : **{dernier_livre}**"
        )
    )


    await interaction.response.send_message(embed=embed)


# -----------------------------
# BIBLIOTHÈQUE
# -----------------------------

@bot.tree.command(name="bibliotheque", description="Voir tes derniers livres lus")
async def bibliotheque(interaction: discord.Interaction):

    user_id = str(interaction.user.id)


    c.execute(
        """
        SELECT title, date FROM books
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    )

    livres = c.fetchall()


    if not livres:
        texte = "Tu n'as encore enregistré aucun livre 📚"

    else:
        texte = ""

        for i, livre in enumerate(livres, 1):
            texte += f"{i}. 📖 {livre[0]} ({livre[1]})\n"


    embed = discord.Embed(
        title=f"📚 Bibliothèque de {interaction.user.name}",
        description=texte
    )


    await interaction.response.send_message(embed=embed)


# -----------------------------
# CLASSEMENT
# -----------------------------

@bot.tree.command(name="classement", description="Voir le classement des lecteurs")
async def classement(interaction: discord.Interaction):

    c.execute(
        """
        SELECT username, COUNT(*) as total
        FROM books
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """
    )

    classement = c.fetchall()


    texte = ""

    for i, lecteur in enumerate(classement, 1):

        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📚"

        texte += (
            f"{emoji} **{lecteur[0]}** "
            f"- {lecteur[1]} livres\n"
        )


    if texte == "":
        texte = "Aucun lecteur pour le moment."


    embed = discord.Embed(
        title="🏆 Classement des lecteurs",
        description=texte
    )


    await interaction.response.send_message(embed=embed)


# -----------------------------
# LANCEMENT
# -----------------------------

bot.run(os.getenv("TOKEN"))
