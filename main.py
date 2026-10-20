"""
Discord News Bot - FIXED TIJD + ZONDER DUBBELE TIJD
- Goede Nederlandse tijd (Europe/Amsterdam)
- Geen "vandaag om 11:31" meer eronder
"""
import discord
from discord.ext import commands
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is online! ✅"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

TOKEN = os.getenv("DISCORD_TOKEN")
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID", "0"))
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

class NewsModal(discord.ui.Modal, title="Nieuw News Artikel"):
    titel = discord.ui.TextInput(label="Titel", placeholder="Bijv: Politie achtervolgt BMW i8", max_length=256, required=True)
    artikel = discord.ui.TextInput(label="Artikel tekst", placeholder="Schrijf hier het hele artikel...", style=discord.TextStyle.paragraph, max_length=3000, required=True)
    afbeelding_url = discord.ui.TextInput(label="Afbeelding URL (optioneel)", placeholder="https://...", required=False)
    bron = discord.ui.TextInput(label="Bron", placeholder="Bijv: NOS.NL", default="NOS.NL", required=False, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        news_channel = bot.get_channel(NEWS_CHANNEL_ID)
        if not news_channel:
            try:
                news_channel = await bot.fetch_channel(NEWS_CHANNEL_ID)
            except Exception as e:
                await interaction.followup.send(f"❌ News kanaal niet gevonden: {e}", ephemeral=True)
                return

        # GOEDE NEDERLANDSE TIJD
        amsterdam_tz = ZoneInfo("Europe/Amsterdam")
        now = datetime.now(amsterdam_tz)
        datum_str = now.strftime("%d-%m-%Y - %H:%M")

        bron_text = self.bron.value if self.bron.value else "NOS.NL"
        
        # GEEN timestamp meer = geen "vandaag om 11:31" erbij
        embed = discord.Embed(title=self.titel.value, description=self.artikel.value, color=0x2B2D31)
        embed.set_author(name=f"{bron_text} - {datum_str}")
        if self.afbeelding_url.value:
            embed.set_image(url=self.afbeelding_url.value)
        embed.set_footer(text=f"{bron_text} - {datum_str}")

        try:
            await news_channel.send(embed=embed)
            await interaction.followup.send(f"✅ **{self.titel.value}** is gepost in {news_channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Fout: {e}", ephemeral=True)

class NewsButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
    @discord.ui.button(label="Nieuw artikel maken", style=discord.ButtonStyle.primary, emoji="📰")
    async def create_news(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NewsModal())

@bot.command(name="news")
async def news_prefix(ctx):
    if PRIVATE_CHANNEL_ID != 0 and ctx.channel.id != PRIVATE_CHANNEL_ID:
        try:
            await ctx.message.delete()
        except:
            pass
        return
    try:
        await ctx.message.delete()
    except:
        pass
    view = NewsButtonView()
    await ctx.channel.send(f"{ctx.author.mention} Klik hier om je news artikel te maken 👇", view=view, delete_after=300)

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
