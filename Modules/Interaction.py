import discord
import random
from discord.ext import commands
import asyncio
import http.client
import urllib.parse
from Util.API_Caller import *
from Util.PokemonJson import *

import time

from mcstatus import MinecraftServer

class FlavorTexts:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, hidden=True)
	async def interactdebug(self, ctx, *, code : str):
	    IDs = ["134441036905840640", "126122455248011265"]
	    if(ctx.message.author.id not in IDs):
	        return
	    """Evaluates code."""
	    code = code.strip('` ')
	    python = '```py\n{}\n```'
	    result = None

	    try:
	        result = eval(code)
	    except Exception as e:
	        await self.bot.say(python.format(type(e).__name__ + ': ' + str(e)))
	        return

	    if asyncio.iscoroutine(result):
	        result = await result

	    await self.bot.say(python.format(result))

	@commands.command(hidden = True)
	async def hep(self):
	    await self.bot.say("Dont Be Lazy, Type ;help")

	@commands.command(hidden = True)
	async def srbr(self):
	    await self.bot.say("Dont Be Lazy, Type ;server")

	@commands.command()
	async def fml(self):
		'Returns a Random Post from fmylife.com'
		await self.bot.say("*{}*".format(fmlText()))

	@commands.command()
	async def conch(self, question : str):
	    'Ask the Magic Conch a Question'
	    conn = http.client.HTTPSConnection("8ball.delegator.com")
	    question = urllib.parse.quote(question)
	    conn.request('GET', '/magic/JSON/' + question)
	    response = conn.getresponse()
	    if response.status == http.client.OK:
	        lines = response.read().decode(encoding='UTF-8').split('\n')
	        await self.bot.say("*" + lines[3][15:-2] + "*")
	        await self.bot.say("The Conch has Spoken!")
	     
	    conn.close()

	@commands.command()
	async def wyr(self):
		result = wouldYouRather()
		while(str(result[0][0]) == "" or str(result[1][0]) == ""):
			result = wouldYouRather()
		await self.bot.say("Would you Rather...\n*" + result[0][1] + "* or *" + result[1][1] + "*")
		await asyncio.sleep(5)
		await self.bot.say("People say...\n*" + str(result[0][0]) + "* and *" + str(result[1][0]) + "*")

	@commands.command()
	async def rps(self, player_input = None):
		"Allows the player to play Rock, Paper, Scissors with the Bot. Simply enter, R, P or S to play!"
		if player_input == None or player_input not in ['R', 'P', 'S']:
			await self.bot.say("You need to put in either (R)ock, (P)aper, or (S)cissors")
			return
		Values = {"R":":right_facing_fist:", "P":":raised_back_of_hand:", "S":":v:"}
		bot_choice = random.choice(["R", "P", "S"])
		await self.bot.say("You throw {}\nI throw {}".format(Values[player_input], Values[bot_choice]))
		if(bot_choice == player_input):
			await self.bot.say("Its a Tie, we both put {}".format(Values[player_input]))
		if bot_choice == "R":
			if player_input == "P":
				await self.bot.say("**You Win!**")
			if player_input == "S":
				await self.bot.say("I Win! :stuck_out_tongue:")
		if bot_choice == "P":
			if player_input == "S":
				await self.bot.say("**You Win!**")
			if player_input == "R":
				await self.bot.say("I Win! :stuck_out_tongue:")
		if bot_choice == "S":
			if player_input == "R":
				await self.bot.say("**You Win!**")	
			if player_input == "P":
				await self.bot.say("I Win! :stuck_out_tongue:")

	
	@commands.command(pass_context = True)
	async def server(self, ctx, IP = None):
		'Returns Information on the Limitless MC server!'
		IP = [IP]
		if IP == [None]:
			ServerIPs = {"535484961357037568" : ["darthcraft.hoptp.org"], "237329306232029184" : ["infinity.protongaming.co.uk", 'skyfactory.protongaming.co.uk'], "333330598871695360" : ["playpokeislands.tk:25650"], "197586442300424193" : ["198.50.156.149:25603"], "230515184265986048" : ["crystalfantasy.cf:29774"]}
			IPs = ServerIPs.get(ctx.message.server.id, IP)
			if IPs == [None]:
				IPs = ["mc.limitlessmc.net"]
		else:
			IPs = IP
		for IP in IPs:
		    m = ""
		    try:
		        server = MinecraftServer.lookup(IP)

		        ping = server.ping()
		        m += "**Server IP**: {}\n".format(IP)
		        m += "**Server Status**\n *Ping*: {} ms".format(ping)

		        status = server.query()
		        m += "\n *Online Players*: {} players out of {}\n *MC Version*: {}\n".format(status.players.online, status.players.max, status.software.version)
		        m +="**Players Online**:\n *{}...*\n".format(", ".join(status.players.names))
		    except Exception as e:
		        print(e)
		        if m == "":
		        	m += "*Server is Down :(*\n"
		    await self.bot.say(m)

	@commands.command(pass_context = True)
	async def rate(self, ctx):
	    "Rates the Player"
	    if ctx.message.author.id == '134441036905840640' or ctx.message.author.id == '183307266475294721':
	    	await self.bot.say("{} is actually the best person to ever exist".format(ctx.message.author.name))
	    	return
	    await self.bot.say("{} is Basically Garbage".format(ctx.message.author.name))

	@commands.command(Hidden = True)
	async def kys(self):
	    await self.bot.say(random.choice([
	    	"Hey Mean!",
	    	"How about... no",
	    	"Sure, just gimme some bleach",
	    	"Im Sorry, That goes against my programming"]))

	@commands.command(hidden = True)
	async def kms(self):
	    await self.bot.say(random.choice([
	    	"Nu, I be sad then ;-;",
	    	"Don't Die",
	    	"Bet",
	    	"Do it, you wont",
	    	"Good :)"]))

	@commands.command(pass_context = True)
	async def highfive(self, ctx, * member):
		await self.bot.say('{} highfived {}'.format(ctx.message.author.name, ''.join(member)))
		await self.bot.delete_message(ctx.message)
			
	@commands.command(pass_context = True)
	async def gif(self, ctx, *toSearch : str):
		"Returns the First Found Image on Google Images for this Input"
		await self.bot.say(getGif("%20".join(toSearch)))

	@commands.command(pass_context = True)
	async def slap(self, ctx, *member):
	    'Adds Emotion'
	    await self.bot.say(":raised_hand: *{} slapped {}* :raised_hand:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def kiss(self, ctx,  *member):
	    'Adds Emotion'
	    await self.bot.say(":kissing_heart: *{} Kissed {}* :kissing_heart:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def loves(self, ctx,  *member):
	    'Adds Emotion'
	    await self.bot.say(":heart: *{} Loves {}* :heart:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def hates(self, ctx,  *member):
	    'Adds Emotion'
	    await self.bot.say(":angry: *{} Hates {}* :angry:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def likes(self, ctx,  *member):
	    'Adds Emotion'
	    await self.bot.say(":thumbsup: *{} Likes {}* :thumbsup:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def kill(self,ctx, *member):
	    'Adds Emotion'
	    await self.bot.say(":skull: *{} Killed {}* :skull:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)

	@commands.command(pass_context = True)
	async def hug(self,ctx, *member):
	    'Adds Emotion'
	    await self.bot.say(":hugging: *{} Hugged {}* :hugging:".format(ctx.message.author.name, " ".join(member)))
	    await self.bot.delete_message(ctx.message)


	@commands.command()
	async def lmgtfy(self, * toGoogle : str):
		'Returns a Link to a "Let me Google That For You" Page'
		await self.bot.say("http://lmgtfy.com/?q={}".format("+".join(toGoogle)))

	@commands.command()
	async def funify(self, * text : str):
		'Funifies a given text input'
		finalOutput = ""
		for x in text:
			for character in x:
				for i in range(0,int(random.random() * 2 + 1),1):
					finalOutput += random.choice([character.lower()] * 10 + [character.upper()] * 10 + [character.lower() + random.choice("1234567890-=[];',./!@#$%^&{(_+)}: ")] + [character.upper() + random.choice("1234567890-=[];',./!@#$%^{&(_+}): ")])
			finalOutput += " "
		await self.bot.say(finalOutput)

	@commands.command()
	async def choose(self, * options : str):
		'Chooses from a set of things'
		await self.bot.say(random.choice(["Hmm, tough choice", "Oh, Thats easy", "Alright, picked one"]))
		await self.bot.say("Chosen Option: " + random.choice(options))

	@commands.command(pass_context = True)
	async def luck(self,ctx):
		'Returns the Player\'s Luck'
		luck = round(random.random() * 100,2)
		if 0 <= luck <= 20:
			text = "Completly Horrible"
		elif 20 <= luck <= 40:
			text = "Pretty Bad"
		elif 40 <= luck <= 60:
			text = "Not Bad"
		elif 60 <= luck <= 80:
			text = "Pretty Good"
		elif 80 <= luck <= 100:
			text = "AMAZING"
		else:
			text = "Literally Impossible"

		await self.bot.say("{0.message.author.name}'s luck is {1} out of 100, which is **{2}**".format(ctx,luck,text))

	@commands.command()
	async def ev(self, *playerInput : str):
	    for inp in playerInput:
	        ret = "**" + inp + "**\n```py\n" + getEVs(inp) + "```"
	        await self.bot.say(ret)

	@commands.command(pass_context = True)
	async def pokemon(self, ctx, name = "charizard"):
	    '''Returns Links to Pokemon pages'''
	    name = name.lower()
	    if name.capitalize() not in ALLPOKEMON:
	        await self.bot.say("Please only use actual pokemon!")
	    with open('TestingImage.gif','wb') as f:
	        f.write(requests.get('https://randompokemon.com/sprites/animated/{}.gif'.format(ALLPOKEMON.index(name.capitalize()) + 1)).content)
	    await self.bot.say("***{}***".format(name.capitalize()))
	    await self.bot.send_file(ctx.message.channel, 'TestingImage.gif')
	    m = ''
	    m += "**Pixelmon Page**: <http://pixelmonmod.com/wiki/index.php?title={}>\n".format(name)
	    m += "**Bulbapedia Page**: <http://bulbapedia.bulbagarden.net/wiki/{}>\n".format(name)
	    m += "**Pokemon DB**: <http://pokemondb.net/pokedex/{}>\n".format(name)
	    m += "**Smogon**: <http://www.smogon.com/dex/bw/pokemon/{}>".format(name)
	    await self.bot.say(m)


	@commands.command(pass_context = True)
	async def afk(self, ctx, * reason : str):
	    '''Sets you as AFK, and the Bot will auto Reply for you with the Given Reason. (Put no Reason to Un-Afk)'''
	    with open("Resc/AFKS.json", 'r') as f:
	        AFK = json.load(f)
	    if(len(reason) == 0):
	        if ctx.message.author.id in AFK.keys():
	            del AFK[ctx.message.author.id]
	            await self.bot.say('''{} is no Longer AFK'''.format(ctx.message.author.name))
	    else:
	        AFK[ctx.message.author.id] = {
	        "reason" : ' '.join(reason),
	        "time" : time.time()
	        }
	        await self.bot.say('''{} is now AFK for reason:\n**{}**'''.format(ctx.message.author.name, ' '.join(reason)))

	    with open("Resc/AFKS.json", 'w') as f:
                json.dump(AFK, f, indent = 4)

def setup(bot):
	bot.add_cog(FlavorTexts(bot))
