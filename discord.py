import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import yt_dlp
import asyncio
import os

# Setup Flask server untuk UptimeRobot
app = Flask('')

@app.route('/')
def home():
    return "Bot Discord sedang berjalan!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Konfigurasi bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Konfigurasi untuk yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Event ketika bot siap
@bot.event
async def on_ready():
    print(f'{bot.user} telah berhasil login!')
    print(f'Bot telah bergabung di {len(bot.guilds)} server')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))

# Command untuk bergabung ke voice channel
@bot.command(name='join', help='Meminta bot bergabung ke voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("Kamu tidak berada di voice channel!")
        return
    
    channel = ctx.message.author.voice.channel
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)
    
    await channel.connect()
    await ctx.send(f"Bergabung ke **{channel}**")

# Command untuk meninggalkan voice channel
@bot.command(name='leave', help='Mengeluarkan bot dari voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Bot telah meninggalkan voice channel")
    else:
        await ctx.send("Bot tidak terhubung ke voice channel")

# Command untuk memutar musik
@bot.command(name='play', help='Memutar musik dari YouTube')
async def play(ctx, *, query):
    # Cek apakah pengguna ada di voice channel
    if not ctx.message.author.voice:
        await ctx.send("Kamu harus berada di voice channel untuk memutar musik!")
        return
    
    # Bergabung ke voice channel jika belum
    if ctx.voice_client is None:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    
    async with ctx.typing():
        try:
            # Mendapatkan URL dari query
            if not query.startswith('http'):
                query = f"ytsearch:{query}"
            
            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            
            # Memutar musik
            ctx.voice_client.play(player, after=lambda e: print(f'Error: {e}') if e else None)
            
            await ctx.send(f'🎵 **Sedang diputar:** {player.title}')
        except Exception as e:
            await ctx.send(f"Terjadi error: {str(e)}")

# Command untuk menjeda musik
@bot.command(name='pause', help='Menjeda musik yang sedang diputar')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸️ Musik dijeda")
    else:
        await ctx.send("Tidak ada musik yang sedang diputar")

# Command untuk melanjutkan musik
@bot.command(name='resume', help='Melanjutkan musik yang dijeda')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶️ Musik dilanjutkan")
    else:
        await ctx.send("Tidak ada musik yang dijeda")

# Command untuk menghentikan musik
@bot.command(name='stop', help='Menghentikan musik yang sedang diputar')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("⏹️ Musik dihentikan")
    else:
        await ctx.send("Tidak ada musik yang sedang diputar")

# Command untuk menampilkan bantuan
@bot.command(name='helpme', help='Menampilkan semua command yang tersedia')
async def helpme(ctx):
    help_embed = discord.Embed(
        title="🎵 Music Bot Commands",
        description="Berikut adalah semua command yang tersedia:",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("!join", "Bergabung ke voice channel"),
        ("!leave", "Meninggalkan voice channel"),
        ("!play [judul/URL]", "Memutar musik dari YouTube"),
        ("!pause", "Menjeda musik"),
        ("!resume", "Melanjutkan musik"),
        ("!stop", "Menghentikan musik"),
        ("!helpme", "Menampilkan bantuan ini")
    ]
    
    for cmd, desc in commands_list:
        help_embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=help_embed)

# Jalankan bot
keep_alive()  # Jalankan Flask server
bot.run(os.environ['MTQwOTUyOTE4MjMzNzI0MTI1Mg.GRJ9zv.6kKo1o9n-NPlBXtUsxHJeOH1LVGs7yVSaV6XRA'])  # Gunakan token dari environment variable
