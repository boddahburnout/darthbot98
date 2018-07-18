import discord
from discord.ext import commands
import random
import traceback
import asyncio
import random
import time
import math
import urllib.parse
import datetime
import json
import os
import re
import sys
from collections import defaultdict
import psutil
import aiohttp

#from Tournament.tournament import *
from cleverwrap import CleverWrap

#from Util.Question import *
from Util.API_Caller import *

VERSION = "0.15.1.3"
description = '''Darth bot, a bot for the fam, Version {}
(Created by Wertfuzzy77 & Darth Kota98)'''.format(VERSION)
bot = commands.Bot(command_prefix=';', description=description, pm_help = True)

LOG = open("Logs/" + "log" + str(time.time()) + ".txt",'w')

CLEVERBOT = {}

voice = None
player = None

startTime = time.time()
afks = {}
inTrivia = False

class poll:
    def __init__(self):
        self.topic = ''
        self.vote1 = ''
        self.vote2 = ''
        self.vote3 = ''

def isStaff(ctx):
    for role in ctx.message.author.roles:
        if role.name == "Staff":
            return True
    return False

messageNum = 0
EXTENTIONS = ['Modules.StaffCmds', 'Modules.Interaction', 'Modules.Music', 'Modules.Games']

def hasAdmin(ctx):
    if ctx.message.author.server_permissions.administrator or ctx.message.author.id == '292484423658766346' or ctx.message.author.server.owner == ctx.message.author:
        return True
    return False

@bot.event
async def on_ready():
    #Log = open("./Logs./" +Fev "log" + str(time.time()) + ".txt",'w')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    for extension in EXTENTIONS:
        try:
            print("Loading {}".format(extension))
            bot.load_extension(extension)
            print("Loaded {}".format(extension))
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
            EXTENTIONS.append(extension)

    await bot.change_presence(game=discord.Game(name='with code.'))
    await bot.loop.create_task(changeIcons())

    await bot.send_message([x for x in bot.get_all_members() if x.name == "Darth kota98"], "Bot has restarted!")

async def changeIcons():
    await bot.wait_until_ready()
    while not bot.is_closed:
        with open("Icons/" + random.choice(os.listdir("Icons")), 'rb') as fp:
            await bot.edit_profile(avatar = fp.read())
        await asyncio.sleep(600)

@bot.command()
async def Icon():
        with open("Icons/" + random.choice(os.listdir("Icons")), 'rb') as f:
            await bot.edit_profile(avatar = f.read())

@bot.command(pass_context = True)
async def status(ctx):
    'Returns the Status of the Bot, along with Additional Information'
    channel = ctx.message.channel
    member = ctx.message.author
    Embed = discord.Embed(title="Darthbot Status", colour=0x800080)
    Embed.set_author(name=member.name, icon_url=member.avatar_url)
    total_uptime = str(datetime.timedelta(seconds = int(time.time() - startTime)))
    Embed.add_field(name ="Uptime", value =total_uptime)
    Embed.add_field(name ="Total Commands", value =messageNum)
    Embed.add_field(name ="Joined Servers", value =len(bot.servers))
    Embed.add_field(name ="CPU usage", value ="{}%".format(str(psutil.cpu_percent(interval=2))))
    Embed.add_field(name ="Memory usage", value ="{}%".format(str(psutil.virtual_memory().percent)))

    if ctx.message.channel != None and ctx.message.server != None:
        with open("Resc/Toggled_Commands.json", 'r') as f:
            Toggle = json.load(f)
        Server = Toggle.get(ctx.message.server.id, [])
        Channel = Toggle.get(ctx.message.channel.id, [])

        if len(Server) != 0:
            Embed.add_field(name = "Server Toggled Commands", value = ", ".join(Server))
        if len(Channel) != 0:
            Embed.add_field(name = "Channel Toggled Commands", value = ", ".join(Channel))

    return await bot.send_message(channel, embed=Embed)

@bot.command()
async def source():
    'Returns a link to the source code for this bot'
    await bot.say("https://github.com/77Wertfuzzy77/Botfuzzy77")

@bot.command(pass_context = True, hidden = True)
async def relog(ctx):
    '''Relogs The Bot'''
    if ctx.message.author.id not in ["292484423658766346","226164707738910720","184407051001266178"]:
        await bot.say("INVALID")
        return
    else:
        await bot.say("Relogging...")
        LOG.close()
        #os.startfile("Botfuzzy77.bat")
        await bot.logout()

@bot.command()
async def invite():
    'Returns a Link to the Invite URL for this bot'
    await bot.say("https://discordapp.com/oauth2/authorize?client_id=187608834381053952&scope=bot&permissions=00000008")

@bot.event
async def on_member_join(member):
    server = member.server
    result = ("Welcome {0.mention} to {1.name}!")
    await bot.send_message(server, result.format(member, server))

@bot.event
async def on_member_update(before, after):
    return
    message = None
    #print(CONFIG[before.server.name]["Online"])
    try:
        if before.server.name in ["The Pleb Privateers"] or before.server.id in ["126122560596213760"]:
            return
        if str(before.status) == "offline" or str(before.status) == "idle" and str(after.status) == "online":
            message = await bot.send_message(before.server, "**{}**({}) is now Online!".format(before.name, before.top_role if before.top_role.name != "@everyone" else "No Role"))
            await asyncio.sleep(20)
            await bot.delete_message(message)
        if str(before.status) == "online" and str(after.status) == "offline":
            message = await bot.send_message(before.server, "**{}**({}) is now Offline!".format(before.name, before.top_role if before.top_role.name != "@everyone" else "No Role"))
            await asyncio.sleep(5)
            await bot.delete_message(message)
    except Exception as e:
        print(type(e).__name__, e)
 
@bot.event
async def on_message(message):
    #Logging
    global messageNum
    try:
        LOG.write("{1} : {0.server}, {0.channel}, {0.author}, {0.clean_content}\n".format(message, time.strftime("%d %b %Y %H:%M:%S", time.gmtime())))
    except Exception as e:
        print("Someting wong\n", type(e).__name__, e)

    with open("Resc/Toggled_Commands.json", 'r') as f:
        Toggle = json.load(f)

    if message.channel != None and message.server != None:
        #print("Testing")
        Server = Toggle.get(message.server.id, [])
        Channel = Toggle.get(message.channel.id, [])
    else:
        Server, Channel = [], []

    # Dont DO anything if message author is Bot
    if(message.author.id == bot.user.id):
        return
	
    if 'fight club' in message.content:
        await bot.send_message(message.channel, 'Rule number 1!')
        await bot.delete_message(message)
    with open("Resc/AFKS.json", 'r') as f:
        AFK = json.load(f)

    for member in message.mentions:
        #print(member.name, afks)
        if member.id in AFK:
            Embed = discord.Embed(title="{} is AFK".format(member.name), colour=0x800080)
            Embed.add_field(name = 'Reason', value = AFK[member.id]['reason'])
            Embed.add_field(name = 'AFK time', value = str(datetime.timedelta(seconds = int(time.time() - AFK[member.id]['time']))))

            await bot.send_message(message.channel, embed=Embed)

    if message.content[0] == ';':
        messageNum += 1

    #print(message.content + "\n" + message.content.upper())
    if(len(message.content) > 20 and message.content.upper() == message.content and message.content.replace(" ", "").isalpha()):
        await bot.delete_message(message)
        #print("removing caps message")
        return

    # if Parsable as Limitless URL
    if("limitlessmc.net/f/" in message.content):
        await bot.send_message(message.channel, ForumPost(message.content))

    Ids = [x.id for x in message.mentions]
    if(bot.user.id in Ids) and "clever" not in Server and "clever" not in Channel and "all" not in Server and "all" not in Channel:
        try:
            if message.author in CLEVERBOT.keys():
                response =  CLEVERBOT[message.author].say(message.content.replace("<@!{}>".format(bot.user.id), "").replace("<@{}>".format(bot.user.id), ""))
            else:
                CLEVERBOT[message.author] = CleverWrap('CCC74MqKOsCr6I6q9bJez0CVXeg')
                response = CLEVERBOT[message.author].say(message.content.replace("<@!{}>".format(bot.user.id), "").replace("<@{}>".format(bot.user.id), ""))
            await bot.send_message(message.channel, response)
        except:
            await bot.send_message(message.channel, "I'm sorry, I didn't quite get that, ask again please!")
            CLEVERBOT[message.author] = CleverWrap('CCC74MqKOsCr6I6q9bJez0CVXeg')
        return


    MutedServer = ['148202028244402176']
    # # Easter Egg, returns "From the other side" if someone types Hello
    if(message.content == "Hello" or message.content == "hello"and message.channel.id not in MutedServer):
        await bot.send_message(message.channel, random.choice(["*From The Other Side*", "*Its me*"]))
        return

    # if(message.content == "Ayy" or message.content == "ayy" and message.channel.id not in MutedServer):
    #     await bot.send_message(message.channel, "Lmao")
    #     return

    # if(message.content == "^" and message.channel.id not in MutedServer):
    #     await bot.send_message(message.channel, "^")
    #     return

    if "anime" not in Server and "anime" not in Channel and "all" not in Server and "all" not in Channel:
        animes = [x[0] for x in re.findall("\<(http://(www\.)?myanimelist.net/anime/\d+/?[A-Za-z\_\-(%20)]*)\>", message.content)]
        end = []
        for anime in animes[0:3]:
          end.append('\n'.join(MAL_anime_info(anime)))
        if end:
          await bot.send_message(message.channel, '\n\n'.join(end))

        search_error = "There was an issue searching **{}**. It\'s likely that the title contains characters not supported by Discord/Python\'s basic text engine"
        # Link anime details by search query #
        anime_search = re.findall('\<([\w\s^(http|www)]*)\>', message.content)
        end = [] # resetting old array
        for ani_s in anime_search[0:3]:
          print(ani_s)
          try:
            result = MAL_anime_search(ani_s)
            end.append('\n'.join(MAL_anime_info(result.get('href'))))
          except Exception as e:
            print(e)
            await bot.send_message(message.channel, search_error.format(ani_s))
            continue
        if end:
          await bot.send_message(message.channel, '\n'.join(end))

    try:
        if message.content == ";help":
            await bot.send_message(message.channel, "I've PM'ed you a list of my commands")
        # If Not Command
        if ";" not in message.content:
            await bot.process_commands(message)
        # If (Not Server toggled) and (not Channel Toggled) and (not all toggled or command is ctoggle)
        elif message.content.split(";")[1] not in Server and message.content.split(";")[1] not in Channel and ("all" not in Channel or "ctoggle" == message.content.split(";")[1].split(" ")[0]):
            await bot.process_commands(message)
        else:
            print(message.content)
    except Exception as e:
        print(e)
        return

@bot.command(pass_context =True)
async def cleverbot(ctx):
    if ctx.message.author in CLEVERBOT.keys():
        clever = CLEVERBOT[ctx.message.author]
    else:
         await bot.say("You have not started a conversation with me! Mention me to begin a conversation.")
         return
    convLength = clever.count
    if convLength > 10:
        convLength = 10
    toReturn = "Your Conversation with me so far:\n\n"
    for interaction in range(convLength, 0, -1):
        toReturn += "{}: {}\n".format(ctx.message.author.name, clever.history['interaction_{}'.format(interaction)])
        toReturn += "Cleverbot: *{}*\n".format(clever.history['interaction_{}_other'.format(interaction)])
    await bot.say(toReturn)

@bot.command(pass_context = True)
async def broadcast(ctx, * message : str):
    IDs = ["292484423658766346"]
    if(ctx.message.author.id not in IDs):
        return
    message = " ".join(message)
    for server in bot.servers:
        try:
            await bot.send_message(server, message)
        except:
            print("Could not send to {}".format(server.name))

@bot.command(pass_context=True)
async def distribute(ctx, * message : str):
    IDs = ["292484423658766346"]
    if(ctx.message.author.id not in IDs):
        return
    message = " ".join(message)
    for server in bot.servers:
        try:
            #print(server.owner.name)
            await bot.send_message(server.owner, message)
        except:
            print("Could not send to {}".format(server.owner.name))

@bot.command(pass_context = True, name='reload', hidden=True)
async def _reload(ctx, module_input = None):
    """Reloads all of the modules."""
    IDs = ["292484423658766346"]
    if(ctx.message.author.id not in IDs):
        return
    try:
        if module_input == None:
            for module in EXTENTIONS:
                bot.unload_extension(module)
                bot.load_extension(module)
        else:
            bot.unload_extension(module_input)
            bot.load_extension(module_input)
        await bot.say('Reloaded')
    except Exception as e:
        await bot.say('Something went wrong :(')
        await bot.say('{}: {}'.format(type(e).__name__, e))

@bot.command(pass_context=True, hidden=True)
async def debug(ctx, *, code : str):
    IDs = ["292484423658766346"]
    if(ctx.message.author.id not in IDs):
        return
    """Evaluates code.""" 
    code = code.strip('` ')
    python = '```py\n{}\n```'
    result = None

    try:
        result = eval(code)
    except Exception as e:
        await bot.say(python.format(type(e).__name__ + ': ' + str(e)))
        return

    if asyncio.iscoroutine(result):
        result = await result

    await bot.say(python.format(result))

@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    raw_date = member.joined_at
    await bot.say('{0.name} joined at {1}'.format(member, raw_date))

@bot.command()
async def presence( * playing : str):
    playing = " ".join(playing)
    await bot.change_presence(game=discord.Game(name='{}'.format(str(playing))))
    await bot.say('I am now playing {}'.format(playing))

@bot.command()
async def topic( * topic : str):
    poll.topic = ' '.join(topic)
    await bot.say('set!')

@bot.command()
async def poll1( * poll1 : str):
    poll.vote1 = ' '.join(poll1)
    await bot.say('set!')

@bot.command()
async def poll2( * poll2 : str):
    poll.vote2 = ' '.join(poll2)
    await bot.say('set!')

@bot.command()
async def poll3( * poll3 : str):
    poll.vote3 = ' '.join(poll3)
    await bot.say('set!')

@bot.command(pass_context = True)
async def startpoll(ctx):
    topic = poll.topic
    vote1 = poll.vote1
    vote2 = poll.vote2
    vote3 = poll.vote3
    channel = ctx.message.channel
    member = ctx.message.author
    Embed = discord.Embed(title="{}".format(topic), colour=0x800080)
    Embed.set_author(name="Darthbot", icon_url='http://www.freeiconspng.com/uploads/discord-blue-icon-8.png')
    Embed.add_field(name =":one:", value =vote1)
    Embed.add_field(name =":two:", value =vote2)
    Embed.add_field(name =":three:", value =vote3)
    await bot.send_message(channel, embed=Embed)

if __name__ == '__main__':
    bot.run('MzE1NDczMzkzNDAxMjAwNjUx.DjAmBw.x063UUSqYklv12tj7r4ctOXCDzQ')
