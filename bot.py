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

c.execute("""
CREATE TABLE IF NOT EXISTS top3 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    username TEXT,
    place INTEGER,
    book TEXT,
    date TEXT
)
""")

conn.commit()


# -----------------------------
# SYNCHRONISATION DES COMMANDES /
# -----------------------------

@bot.event
async def on_ready():
    print("🔄 Bot connecté, synchronisation en cours...")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Connecté en tant que {bot.user}")
        print(f"✅ {len(synced)} commandes synchronisées")

    except Exception as e:
        print(f"❌ Erreur synchronisation : {e}")


# -----------------------------
# AJOUTER UN LIVRE
# -----------------------------

@bot.tree.command(name="read", description="Ajoute un livre terminé à ta bibliothèque")
@app_commands.describe(titre="Nom du livre terminé")
async def read(interaction: discord.Interaction, titre: str):

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
            f"✨ Total de livres lus : **{total}**"
        )
    )

    await interaction.response.send_message(embed=embed)


# -----------------------------
# PROFIL
# -----------------------------

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
        niveau = "🐚 Baby lectrice"

    elif total < 20:
        niveau = "🌊 Dévoreuse de livre"

    elif total < 50:
        niveau = "🪸 Lectrice passionée"

    elif total < 100:
        niveau = "🐙 Bibliothéquaire"

    else:
        niveau = "🌅 Légende littéraire"

    embed = discord.Embed(
        title=f"💌 Profil lecteur de {interaction.user.name}",
        description=(
            f"📚 Livres lus : **{total}**\n\n"
            f"🏅 Niveau : **{niveau}**\n\n"
            f"📌 Dernière lecture : **{dernier_livre}**"
        ),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed)


# -----------------------------
# BIBLIOTHÈQUE
# -----------------------------

@bot.tree.command(name="library", description="Voir tes derniers livres lus")
async def library(interaction: discord.Interaction):

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
# INITIALISER SON HISTORIQUE
# -----------------------------

@bot.tree.command(
    name="update_books",
    description="Met à jour ton nombre de livres déjà lus avant ton arrivée"
)
@app_commands.describe(nombre="Nombre de livres déjà lus")
async def update_books(interaction: discord.Interaction, nombre: int):

    user_id = str(interaction.user.id)
    username = interaction.user.name

    # Vérifie si la personne a déjà ajouté un historique
    c.execute(
        """
        SELECT COUNT(*) FROM books
        WHERE user_id = ?
        """,
        (user_id,)
    )

    existant = c.fetchone()[0]


    if existant > 0:
        await interaction.response.send_message(
            "⚠️ Ton historique de lecture est déjà configuré. "
            "Contacte un administrateur si tu dois le modifier.",
            ephemeral=True
        )
        return


    # Ajoute des livres fictifs pour créer le compteur
    for i in range(nombre):
        c.execute(
            """
            INSERT INTO books (user_id, username, title, date)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                "Livre lu avant l'arrivée",
                "Avant Discord"
            )
        )

    conn.commit()


    embed = discord.Embed(
        title="📚 Historique ajouté !",
        description=(
            f"{interaction.user.mention}, ton ancienne bibliothèque a été prise en compte.\n\n"
            f"📖 Total enregistré : **{nombre} livres lus**\n\n"
            "Bienvenue parmi les lecteurs 📚✨"
        )
    )


    await interaction.response.send_message(embed=embed)

# -----------------------------
# TOP 3 LIVRES
# -----------------------------

@bot.tree.command(
    name="top3",
    description="Créer ton top 3 de livres préférés"
)
@app_commands.describe(
    livre1="Ton livre préféré",
    livre2="Ton deuxième livre préféré",
    livre3="Ton troisième livre préféré"
)
async def top3(
    interaction: discord.Interaction,
    livre1: str,
    livre2: str,
    livre3: str
):

    user_id = str(interaction.user.id)
    username = interaction.user.name
    date = datetime.now().strftime("%d/%m/%Y")


    # Vérifie si un top existe déjà
    c.execute(
        "SELECT COUNT(*) FROM top3 WHERE user_id = ?",
        (user_id,)
    )

    existe = c.fetchone()[0]


    if existe > 0:
        await interaction.response.send_message(
            "⚠️ Tu as déjà enregistré ton Top 3.\n"
            "Une commande de modification pourra être ajoutée plus tard.",
            ephemeral=True
        )
        return

    livres = [
        (1, livre1),
        (2, livre2),
        (3, livre3)
    ]

    for place, livre in livres:
        c.execute(
            """
            INSERT INTO top3
            (user_id, username, place, book, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                place,
                livre,
                date
            )
        )

    conn.commit()

    podium = (
        "```text\n"
        "              🥇\n"
        f"           {livre1}\n\n"
        f"🥈 {livre2}        🥉 {livre3}\n"
        "```"
    )

    embed = discord.Embed(
        title=f"💌 Top 3 de {interaction.user.name}",
        description=(
            f"{podium}\n"
            f"📅 Ajouté le {date}"
        ),
        color=discord.Color.gold()
    )

    TOP3_CHANNEL_ID = 1524038773955100742

    channel = bot.get_channel(TOP3_CHANNEL_ID)

    if channel is not None:
        await channel.send(embed=embed)

    await interaction.response.send_message(
        "💌 Ton Top 3 a été publié dans #top-des-lecteurs !",
        ephemeral=True
    )

# -----------------------------
# MODIFIER SON TOP 3
# -----------------------------

@bot.tree.command(
    name="update_top3",
    description="Modifier ton top 3 de livres préférés"
)
@app_commands.describe(
    livre1="Ton nouveau livre préféré",
    livre2="Ton nouveau deuxième livre préféré",
    livre3="Ton nouveau troisième livre préféré"
)
async def update_top3(
    interaction: discord.Interaction,
    livre1: str,
    livre2: str,
    livre3: str
):

    user_id = str(interaction.user.id)
    username = interaction.user.name
    date = datetime.now().strftime("%d/%m/%Y")

    # Vérifie si un top existe déjà
    c.execute(
        "SELECT COUNT(*) FROM top3 WHERE user_id = ?",
        (user_id,)
    )

    existe = c.fetchone()[0]

    if existe == 0:
        await interaction.response.send_message(
            "⚠️ Tu n'as pas encore créé de Top 3.\n"
            "Utilise d'abord la commande `/top3`.",
            ephemeral=True
        )
        return

    # Supprime l'ancien top
    c.execute(
        "DELETE FROM top3 WHERE user_id = ?",
        (user_id,)
    )

    livres = [
        (1, livre1),
        (2, livre2),
        (3, livre3)
    ]

    # Enregistre le nouveau top
    for place, livre in livres:
        c.execute(
            """
            INSERT INTO top3
            (user_id, username, place, book, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                place,
                livre,
                date
            )
        )

    conn.commit()

    podium = (
        "```text\n"
        "              🥇\n"
        f"           {livre1}\n\n"
        f"🥈 {livre2}        🥉 {livre3}\n"
        "```"
    )

    embed = discord.Embed(
        title=f"💌 Top 3 mis à jour de {interaction.user.name}",
        description=(
            f"{podium}\n"
            f"📅 Mis à jour le {date}"
        ),
        color=discord.Color.gold()
    )

    TOP3_CHANNEL_ID = 1524038773955100742

    channel = bot.get_channel(TOP3_CHANNEL_ID)

    if channel is not None:
        await channel.send(embed=embed)

    await interaction.response.send_message(
        "💌 Ton Top 3 a été mis à jour dans #top-des-lecteurs !",
        ephemeral=True
    )
    
# -----------------------------
# LANCEMENT
# -----------------------------

bot.run(os.getenv("TOKEN"))
