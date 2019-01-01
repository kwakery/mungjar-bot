import aiohttp
import asyncio
import discord
import threading
from config import *
from discord.ext import commands

client = commands.Bot(command_prefix = '!')

headers = {"Authorization": "Bearer " + settings.API['token']}
allowed = ['chibi1', 'chibi2', 'traditional', 'commissions', 'panels', 'other']


@client.event
async def on_ready():
    print("mungjar Bot v0.1")
    game = discord.Game("mungjar")
    stream = discord.Streaming(name="mungjar", url="https://twitch.tv/mungjar", twitch_name="mungjar")
    await client.change_presence(activity=stream)
    await checkTasks()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await process_uploads(message)
    await client.process_commands(message)

    # if message.content == "Hello":
    #     await client.send_message(message.channel, "World")

async def process_uploads(message):
    if message.channel.id != settings.discord['upload_cid'] or len(message.attachments) < 1 or not message.content:
        return

    url = settings.API['baseUrl'] + '/pictures'

    if message.content not in allowed:
        return

    for attachment in message.attachments:
        test = await attachment.save("tempFile")
        tempFile = open('tempfile', 'rb')

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', open('tempFile', 'rb'))
            data.add_field('type', message.content)

            await session.post(url, data=data, headers=headers)
        await message.add_reaction("\u2049")

async def checkTasks():
    while True:
        async with aiohttp.ClientSession() as session:
            url = settings.API['baseUrl'] + '/tasks'
            response = await session.get(url, headers=headers)

            tasks = (await response.json())['data']
            for task in tasks:
                commission = task['commission']
                guild = client.get_guild(settings.discord['guild_id'])
                member = guild.get_member(int(commission['discord']))
                print(member)
                category = guild.get_channel(settings.discord['category_id'])

                # Create Role
                newRole = await guild.create_role(name=commission['token'])
                await member.add_roles(newRole)

                # Create discord
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    newRole: discord.PermissionOverwrite(read_messages=True)
                }

                # Create Channel
                newChannel = await guild.create_text_channel('commission-' + commission['token'], overwrites=overwrites, category=category)
                await newChannel.send("Hello "+member.mention+". Please continue discussion about your commission here.\n"
                                    + "Here is the summary about your commission:\n"
                                    + "**Name:** " + commission['name'] + '\n'
                                    + "**Email:** " + commission['email'] + '\n'
                                    + "**Date needed by:** " + commission['duedate'] + '\n'
                                    + "**Type:** " + commission['type'] + '\n'
                                    + "**Commercial Use?** " + str(commission['commercial']) + '\n'
                                    + "**Additional Info** \n```\n" + commission['info'] + '```\n'
                                    + "Your commission link can be found at:\n"
                                    + "https://mungjar.aegyo.pro/commissions/"
                                    + commission['token'])

                # Mark completed
                url = settings.API['baseUrl'] + '/tasks/' + str(task['id'])
                data = aiohttp.FormData()
                data.add_field('status', 1)

                response = await session.patch(url, headers=headers, data=data)

        await asyncio.sleep(20)


@client.command(name='status')
async def setStatus(ctx, token, status):
    async with aiohttp.ClientSession() as session:
        url = settings.API['baseUrl'] + '/commissions/' + token
        data = aiohttp.FormData()
        data.add_field('status', status)

        response = await session.patch(url, headers=headers, data=data)

    await ctx.send('Done!')

@client.command(name='open')
async def setOpened(ctx):
    async with aiohttp.ClientSession() as session:
        url = settings.API['baseUrl'] + '/settings'
        data = aiohttp.FormData()
        data.add_field('key', "COMMISSIONS_OPEN")
        data.add_field('value', 'true')

        response = await session.patch(url, headers=headers, data=data)

    await ctx.send('Done!')

@client.command(name='close')
async def setClosed(ctx, value):
    async with aiohttp.ClientSession() as session:
        url = settings.API['baseUrl'] + '/settings'
        data = aiohttp.FormData()
        data.add_field('key', "COMMISSIONS_OPEN")
        data.add_field('value', 'false')

        response = await session.patch(url, headers=headers, data=data)

    await ctx.send('Done!')

client.run(settings.discord['token'])
