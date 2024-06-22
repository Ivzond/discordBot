from collections import deque
import discord
from discord.ext import commands
import asyncio
import yt_dlp

config = {
    'token': 'MTI1MzQ1MTc3NDAxOTUwMjA5MA.GflywC.YtlCbzYJxKEos_aCs2O3R0Hk_cpvH16mIewzu8',
    'prefix': '!',
}

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'noplaylist': True,
    'quiet': True,
    'ignoreerrors': True,
}

intents = discord.Intents.default()
intents.voice_states = True
intents.messages = True
intents.message_content = True  # Важно для чтения содержимого сообщения
bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

song_queue = deque()
current_song = None

@bot.event
async def on_ready():
    print(f'Бот {bot.user} подключен и готов к работе!')

@bot.event
async def on_command(ctx):
    print(f'Команда {ctx.command} была вызвана пользователем {ctx.author}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        await ctx.send(f"Произошла ошибка: {error}")
    else:
        raise error

@bot.command()
async def play(ctx, *, url):
    if ctx.author.voice is None:
        await ctx.send("Вы должны быть в голосовом канале, чтобы воспроизводить музыку.")
        return

    voice_channel = ctx.author.voice.channel
    song_queue.append(url)
    await ctx.send(f"Трек добавлен в очередь: {url}")

    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await voice_channel.connect()

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    global current_song
    if len(song_queue) == 0:
        current_song = None
        return

    url = song_queue.popleft()
    current_song = url
    voice_client = ctx.voice_client
    ydl_opts = {
        'format': 'bestaudio/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        URL = info['url']
        voice_client.play(discord.FFmpegPCMAudio(URL), after=lambda e: bot.loop.create_task(play_next(ctx)))

@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Пропускаю текущий трек.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        song_queue.clear()
        await ctx.send("Остановил воспроизведение музыки и очистил очередь.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Поставил музыку на паузу.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Возобновил воспроизведение музыки.")

@bot.command()
async def join(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Эта команда должна быть выполнена в текстовом канале сервера.")
        return

    print('Команда join вызвана')
    if ctx.author.voice is None:
        await ctx.send("Вы не подключены к голосовому каналу.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client is not None:
        await voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"Подключился к каналу: {channel}")

@bot.command()
async def leave(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Эта команда должна быть выполнена в текстовом канале сервера.")
        return

    print('Команда leave вызвана')
    voice_client = ctx.voice_client
    if voice_client is not None:
        await voice_client.disconnect()
        await ctx.send("Отключился от голосового канала.")
    else:
        await ctx.send("Я не подключен к голосовому каналу.")

@bot.command()
async def check_permissions(ctx):
    permissions = ctx.channel.permissions_for(ctx.guild.me)
    permissions_dict = {
        'manage_channels': permissions.manage_channels,
        'manage_guild': permissions.manage_guild,
        'view_channel': permissions.view_channel,
        'send_messages': permissions.send_messages,
        'manage_messages': permissions.manage_messages,
    }

    missing_permissions = [perm for perm, has_perm in permissions_dict.items() if not has_perm]

    if missing_permissions:
        await ctx.send(f"Отсутствуют следующие разрешения: {', '.join(missing_permissions)}")
    else:
        await ctx.send("У меня есть все необходимые разрешения!")

    # Вывод всех разрешений для отладки
    print("Разрешения бота в канале:")
    for perm, has_perm in permissions_dict.items():
        print(f"{perm}: {has_perm}")

bot.run(config['token'])
