import discord
from discord.ext import commands
import sqlite3

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🗄️ base de données
conn = sqlite3.connect("books.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS books (
    user_id TEXT PRIMARY KEY,
    count INTEGER
)
""")
conn.commit()

# ➕ ajouter un livre
@bot.command()
async def books(ctx):
    user_id = str(ctx.author.id)

    c.execute("SELECT count FROM books WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if result:
        new_count = result[0] + 1
        c.execute("UPDATE books SET count = ? WHERE user_id = ?", (new_count, user_id))
    else:
        new_count = 1
        c.execute("INSERT INTO books (user_id, count) VALUES (?, ?)", (user_id, new_count))

    conn.commit()

    await ctx.send(f"📚 {ctx.author.name}, tu as {new_count} livres lus !")

# 📊 total utilisateur
@bot.command()
async def library(ctx):
    user_id = str(ctx.author.id)

    c.execute("SELECT count FROM books WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    count = result[0] if result else 0

    await ctx.send(f"📊 {ctx.author.name}, total : {count} livres lus.")

import os
bot.run(os.getenv("TOKEN"))
