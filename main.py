import discord
from config import *

client = discord.Client()

@client.event
async def on_ready():
    print("mungjar Bot v0.1")
    game = discord.Game("mungjar")
    stream = discord.Streaming(name="mungjar", url="https://twitch.tv/mungjar", twitch_name="mungjar")
    await client.change_presence(activity=stream)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    # if message.content == "Hello":
    #     await client.send_message(message.channel, "World")


client.run(settings.discord['token'])
