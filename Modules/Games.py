import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
import time
import random
import operator
import json
import math
import aiohttp
import requests
import unicodedata

from Util.levelHelper import *
from Util.PokemonJson import *

COLORS = {
	'easy' : 0xeb8c00,
	'medium' : 0xe0301e,
	'hard' : 0xa32020,
	'insane' : 0x602320,
	'xp' : 0x8989E5,
	'level' : 0x4A4AD7,
	'train' : 0x2F972F,
	'mine' : 0x996409,
	'ranking' : 0xFFD700,
	'xpLoss': 0x000000,
	'valid' : 0x06cc19,
	'invalid' : 0xed0b0b,
	'information' : 0x800080}

HELDITEMS = {
	"Quick Sash" : "Reduces Cooldowns by 25%",
	"Power Booster" : "Stab moves do 50% more damage",
	"Incense" : "Attracts 25% more pokemon while training",
	"XP Share" : "You gain 50% less XP, and 50% of the lost XP is given to a player of your choosing",
	"Lucky Coin" : "10% higher chance to get a positive result."}

COOLDOWN = 60
TCOOLDOWN = 3600
MCOOLDOWN = 180
NEWPLAYER = {"Name" : "BLANK", "Level": 5, "XP": 0, "largest_damage" : 0, "Takedowns" : 0, "Pokemon" : [" "], "Type" : "Normal", "Prestige" : 0, "Time": time.time()}
TYPES = ['normal', 'water', 'fire', 'grass', 'poison', 'dragon', 'steel', 'electric', 'bug', 'ice']

HelpMessage = """Welcome to the **Pokemon Battle Sim**!
Here you fight together against Pokemon Bosses. There are 4 areas, *Easy*, *Medium*, *Hard* and *Insane*.	
To fight a boss, you use the command `;pokebattle`, a set of moves you will fight the boss with, and a location you want to fight in. (The bot will default to the area best suited for you level if left blank)
An example of this is the following:
`;pokebattle ngfse easy`
which means you will be fighting the easy boss with battle combo of Normal, Grass, Fire, Steel, and Electric.
You can use any combination of the 10 moves which can be found on `;types`"""

def enabled(ctx):
	return ctx.message.server == None or ctx.message.server.id not in ['	']

class Games:
	def __init__(self, bot):
		self.bot = bot
		self.AUTO_RESPAWN = True
		self.Locations = ["easy", "medium", "hard", "insane"]
		self.EASY_MAX = (5, 20)
		self.MEDIUM_MAX = (20, 50)
		self.HARD_MAX = (50, 80)
		self.INSANE_MAX = (80, 99)
		self.loc_to_levels = {"easy" : self.EASY_MAX, "medium" : self.MEDIUM_MAX, "hard" : self.HARD_MAX, "insane" : self.INSANE_MAX}
		self.bosses = {}
		self.init_bosses()

	def init_bosses(self):
		def init_boss(JSON, loc):
			if JSON.get('level') == None:
				return Boss(self.loc_to_levels[loc])	

			boss = Boss(blank = True)
			boss.level = JSON['level']
			boss.Name = JSON['name']
			boss.Moves = JSON['moves']
			boss.Health = JSON['health']
			boss.StartingHealth = JSON['starting_health']
			boss.Damage = {}
			for x in JSON['damage'].keys():
				boss.Damage[self.getMemberFromID(x)] = JSON['damage'][x]
			boss.isDefeated = JSON['is_defeated']
			boss.hasBeenRevealed = JSON['has_been_revealed']
			boss.combination = JSON['combination']
			boss.lastUsedCombo = JSON['last_used_combo']
			boss.summoner = JSON['summoner']
			boss.Image = JSON['image']

			return boss


		with open("Resc/Bosses.json") as f:
			Bosses = json.load(f)
			for loc in self.Locations:
				self.bosses[loc] = init_boss(Bosses[loc], loc)
		

	def write_bosses(self):
		def generate_dict(boss):
			JSON = {}
			JSON['level'] = boss.level
			JSON['name'] = boss.Name 
			JSON['moves'] = boss.Moves
			JSON['health'] = boss.Health
			JSON['starting_health'] = boss.StartingHealth
			damage = {}
			for x in boss.Damage:
				damage[x.id] = boss.Damage[x]
			JSON['damage'] = damage
			JSON['is_defeated'] = boss.isDefeated
			JSON['has_been_revealed'] = boss.hasBeenRevealed
			JSON['combination'] = boss.combination
			JSON['last_used_combo'] = boss.lastUsedCombo
			JSON['summoner'] = boss.summoner
			JSON['image'] = boss.Image

			# print(JSON)

			return JSON

		with open("Resc/Bosses.json") as f:
			Bosses = json.load(f)
			for loc in self.Locations:
				Bosses[loc] = generate_dict(self.bosses[loc])

		with open("Resc/Bosses.json", 'w') as f:
			json.dump(Bosses, f, indent = 4)



	@commands.command(pass_context=True, hidden=True)
	async def gamesdebug(self, ctx, *, code : str):
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

	@commands.command(pass_context = True)
	async def recent(self, ctx):
		Activeplayers = sorted([x for x in json.load(open('Resc/Players.json', 'r')).values() if x.get("Time", 0) + 86400 > time.time()], key = lambda x: x.get("Time", 0), reverse = True)
		Recentplayers = sorted([x for x in json.load(open('Resc/Players.json', 'r')).values() if x.get("Time", 0) + 7200 > time.time()], key = lambda x: x.get("Time", 0), reverse = True)
		ret = "\n".join(["**{}**: *{}* minutes ago".format(x['Name'], int(int(time.time() - x['Time'])/60)) for x in Recentplayers])
		ret += "\nThere have been *{}* players active in the last 24 hours".format(len(Activeplayers))
		await self.send_information_message(ctx, ret)

	@commands.command(pass_context = True, aliases = ['pbt', 'pb'])
	async def pokebattle(self, ctx, moves = "", area = ""):
		'Fights a Pokemon Boss'
		if not enabled(ctx):
			return
		# Checks Location
		# Gets the player JSON Entry
		player = await self.getPlayer(ctx.message.author)

		if area == "":
			area = await self.BestArea(ctx.message.author)

		area = area.lower()
		if area not in self.Locations:
			await self.send_invalid_message(ctx, "The Available Locations are {}".format(", ".join(self.Locations)))
			return

		# Check Valid Area
		if not await self.AvailableToBattle(ctx.message.author, area):
			await self.send_invalid_message(ctx, "You are not a high enough level to be in this area!")
			if area == "easy":
				neededLevel = 0
			elif area == "medium":
				neededLevel = self.MEDIUM_MAX[0]
			elif area == "hard":
				neededLevel = self.HARD_MAX[0]
			else:
				neededLevel = self.INSANE_MAX[0]
			await self.send_invalid_message(ctx, "You need to be atleast Level {}".format(neededLevel))
			return

		# Check cooldown on players
		if player.get('last_battle_time', 0) + COOLDOWN > time.time():
			seconds = (player.get('last_battle_time', 0) + COOLDOWN - time.time())
			m, s = divmod(seconds, 60)
			await self.send_invalid_message(ctx, "Please wait {}m {}s seconds before you can fight the boss again.".format(int(m), int(s)))
			return


		boss = self.bosses[area]
		if moves == "":
			await self.send_invalid_message(ctx, "Please use a Combination of **{}** Types. `;types`".format(boss.Moves))
			return

		moves = moves.upper()
		if len(moves) is not boss.Moves:
			await self.send_invalid_message(ctx, "Please use a Combination of **{}** Types. `;types`".format(boss.Moves))
			return
		for x in moves:
			if x not in ["N","F","W","G","P","D","S","E","B","I"]:
				await self.send_invalid_message(ctx, "Please use a Combination of **{}** Types. `;types`".format(boss.Moves))
				return


		# Respawn boss or say is Dead.
		if boss.isDefeated:
			if area == "easy":
				self.bosses[area] = Boss(self.EASY_MAX)
			elif area == "medium":
				self.bosses[area] = Boss(self.MEDIUM_MAX)
			elif area == "hard":
				self.bosses[area] = Boss(self.HARD_MAX)
			else:
				self.bosses[area] = Boss(self.INSANE_MAX)
			boss = self.bosses[area]

		m = ""
		# Reveal the Boss
		if not boss.hasBeenRevealed:
			m += "A Level {} Boss **{}** has appeared in the {} zone!\nIt has {:,} Health.\n".format(boss.level, boss.Name, area.capitalize(), boss.Health)
			boss.hasBeenRevealed = True
			boss.summoner = ctx.message.author.name
		else:
			m += "Level {} Boss **{}** in {} has {:,} health left.\n".format(boss.level, boss.Name, area.capitalize(), boss.Health)

		# Compute Correct Moves
		correctOnes = [boss.combination[x] == moves[x] for x in range(0, boss.Moves, 1)]
		Pinput = [unicodedata.lookup("REGIONAL INDICATOR SYMBOL LETTER {}".format(value.upper())) for value in moves]
		output = [unicodedata.lookup("WHITE HEAVY CHECK MARK") if value else unicodedata.lookup("CROSS MARK") for value in correctOnes]
		m += unicodedata.lookup("ZERO WIDTH SPACE").join(Pinput) + "\n" +  unicodedata.lookup("ZERO WIDTH SPACE").join(output) + "\n"
		boss.lastUsedCombo = unicodedata.lookup("ZERO WIDTH SPACE").join(Pinput) + "\n" +  unicodedata.lookup("ZERO WIDTH SPACE").join(output) + "\n"

		# Raw Damage just based off of # Correct
		dmg = player['Level'] * (1 + (0.10 * player.get("Prestige", 0)))
		Total_Damage = sum([dmg if value else 0 for value in correctOnes])

		# Combo Effectiveness
		if random.random() < 0.10:
			m += "Its a Critical Strike\n"
			Total_Damage = Total_Damage * 2
		if correctOnes.count(True) == boss.Moves - 1:
			m += "Its **Super Effective**\nThe Boss has switched *1/4* of the Super Effective Moves!\n"
			Total_Damage = Total_Damage * 10
			boss.changeQuarter()
		elif correctOnes.count(True) == boss.Moves:
			m += "Its a **Perfect Combo**\nThe Boss has switched *1/2* of the Super Effective Moves!\n"
			Total_Damage = Total_Damage * 25
			boss.changeHalf()
		elif correctOnes.count(True) > boss.Moves / 2:
			m += "Its Sort-Of Effective\n"
			Total_Damage = Total_Damage * 1.35 * (correctOnes.count(True) + 1) / (boss.Moves / 2)

		# Penalty for Low Level Bosses
		if area == "easy":
			maxLevel = self.EASY_MAX[1]
		elif area == "medium":
			maxLevel = self.MEDIUM_MAX[1]
		elif area == "hard":
			maxLevel = self.HARD_MAX[1]
		else:
			maxLevel = self.INSANE_MAX[1]

		if player['Level'] > maxLevel:
			Total_Damage = Total_Damage * boss.level / player["Level"]
			m += "*Low level boss penalty...*\n"

		# Rival Bonus
		if boss.summoner == ctx.message.author.name:
			m += "Rival Bonus!\n"
			Total_Damage = Total_Damage * 1.25


		# STAB Bonuses
		Type = player['Type'].upper()
		STABcount = 0
		for x in range(0, boss.Moves, 1):	
			if Type[0] == moves[x] and correctOnes[x] == True:
				Total_Damage *= 1.08
				STABcount += 1
		if STABcount >= 1:
			m += "STAB bonus damage for {} type ({}x)\n".format(Type.capitalize(), STABcount)

		# Randomize Boss Damage, and Apply are handicap
		if Total_Damage is not 0:
			Total_Damage = int(Total_Damage * 8 / boss.Moves * random.randrange(75, 125, 5) * 1.15 / 100 + 1)

		# Deal Damage
		await self.dealDamage(ctx.message.author, Total_Damage)
		GivenXP = int(Total_Damage/4 * random.randrange(75, 125, 5) / 100) if int(Total_Damage/4 * random.randrange(75, 125, 5) / 100) > 1 else 1
		m += "Your moves did **{:,}** damage\n".format(Total_Damage)

		# Add Player Damage to Boss Damage Dict
		boss.Health = boss.Health - Total_Damage
		try: 
			boss.Damage[ctx.message.author] = boss.Damage[ctx.message.author] + Total_Damage
		except:
			boss.Damage[ctx.message.author] = Total_Damage
		if boss.Health >= 0:
			m += "Level {} Boss **{}** has {:,} health left.\n".format(boss.level, boss.Name, boss.Health)

		# Send Embedded Message
		channel = ctx.message.channel
		member = ctx.message.author
		await self.bot.send_message(channel, embed=discord.Embed(title='**{} Boss Pokemon**'.format(area.capitalize()), description=m, colour=COLORS[area.lower()]).set_author(name=member.name, icon_url=member.avatar_url).set_thumbnail(url=boss.Image))
		
		# Give XP
		player = await self.giveXP(ctx.message.author, GivenXP, ctx.message.channel)

		# Boss is ded
		if boss.Health <= 0:
			m2 = ""
			await self.takeDown(ctx.message.author)
			m2 += "Level {} Boss **{}** has been defeated!\n".format(boss.level, boss.Name)
			sorted_Damage = sorted(boss.Damage.items(), key=operator.itemgetter(1), reverse=True)
			try:
				m2 += "Most Damage by **{}** with **{:,}** damage\n".format(sorted_Damage[0][0].name, sorted_Damage[0][1])
			except:
				m2 += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[0][1])
			if len(sorted_Damage) >= 2:
				try:
					m2 += "2nd most Damage by *{}* with *{:,}* damage\n".format(sorted_Damage[1][0].name, sorted_Damage[1][1])
				except:
					m2 += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[1][1])
			if len(sorted_Damage) >= 3:
				try:
					m2 += "3rd most Damage by *{}* with *{:,}* damage\n".format(sorted_Damage[2][0].name, sorted_Damage[2][1])
				except:
					m2 += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[2][1])
			if len(sorted_Damage) >= 4:
				m2 += "Assisted by {}\n".format(", ".join([sorted_Damage[x][0].name for x in range(3, len(sorted_Damage), 1)]))
			boss.isDefeated = True
			await self.bot.send_message(channel, embed=discord.Embed(title='**{} Boss Defeated**'.format(area.capitalize()), description=m2, colour=COLORS[area.lower()]).set_author(name=member.name, icon_url=member.avatar_url).set_thumbnail(url=boss.Image))

			# XP
			await self.giveXP(sorted_Damage[0][0], int(boss.StartingHealth* 0.45) + int(boss.Damage[sorted_Damage[0][0]] * 0.70) + 1, ctx.message.channel)
			if len(sorted_Damage) >= 2:
				await self.giveXP(sorted_Damage[1][0], int(boss.StartingHealth* 0.15) + int(boss.Damage[sorted_Damage[1][0]] * 0.45) + 1, ctx.message.channel)
			if len(sorted_Damage) >= 3:
				await self.giveXP(sorted_Damage[2][0], int(boss.StartingHealth* 0.08) + int(boss.Damage[sorted_Damage[2][0]] * 0.35) + 1, ctx.message.channel)
			if len(sorted_Damage) >= 4:
				members = [sorted_Damage[x][0] for x in range(3, len(sorted_Damage), 1)]
				for member in members:
					await self.giveXP(member, boss.Damage[member]/5 + 1, ctx.message.channel)

			for member in boss.Damage.items():
				players = await self.getPlayer(member)
				players ['last_battle_time'] = 0
				await self.setPlayer(ctx.message.author.id, players)
			#await self.bot.send_message(channel, embed=discord.Embed(title='**{} Boss Defeated**'.format(area.capitalize()), description=m2, colour=0x3232FF).set_author(name=member.name, icon_url=member.avatar_url).set_thumbnail(url=boss.Image))


		else:
			player['last_battle_time'] = time.time()

		player['battle_count'] = player.get('battle_count', 0) + 1
		await self.setPlayer(ctx.message.author.id, player)
		self.write_bosses()

	async def dealDamage(self, member, damage):
		player = await self.getPlayer(member)

		if(player.get('largest_damage', 0) < damage):
			player['largest_damage'] = damage
		player['Time'] = time.time()

		await self.setPlayer(member.id, player)

	async def takeDown(self, member):
		player = await self.getPlayer(member)

		player['Takedowns'] += 1

		await self.setPlayer(member.id, player)

	async def AvailableToBattle(self, member, area):
		player = await self.getPlayer(member)

		if area == "easy":
			neededLevel = 0
		elif area == "medium":
			neededLevel = self.MEDIUM_MAX[0]
		elif area == "hard":
			neededLevel = self.HARD_MAX[0]
		else:
			neededLevel = self.INSANE_MAX[0]

		return player['Level'] >= neededLevel

	async def BestArea(self, member):
		player = await self.getPlayer(member)

		if player['Level'] >= self.INSANE_MAX[0]:
			return "insane"
		elif player['Level'] >= self.HARD_MAX[0]:
			return 'hard'
		elif player['Level'] >= self.MEDIUM_MAX[0]:
			return 'medium'
		else:
			return 'easy'

	@commands.command(pass_context = True, aliases = ['pbs'])
	async def pokeboss(self, ctx, area = ""):
		'Displays Boss Info'
		if not enabled(ctx):
			return
		if area == "":
			area = await self.BestArea(ctx.message.author)

		if area not in self.Locations:
			await self.bot.say("wut")
			return
		boss = self.bosses[area]

		if not boss.hasBeenRevealed:
			await self.send_information_message(ctx, "Boss has not been Revealed!\nPlease use ;pokebattle <moves> {} to fight and reveal the boss.".format(area))
			return
		if boss.isDefeated:
			await self.send_information_message(ctx, "Level {} Boss **{}** has been defeated!\nPlease use ;pokebattle <moves> {} to fight and reveal a new boss.".format(boss.level, boss.Name, area))
		member = ctx.message.author
		channel = ctx.message.channel
		toPrint = "*Name*: {0.Name}\n*Health*: {0.Health:,}/{0.StartingHealth:,} ({1}%)\n*Level*: {2}\nLast Combo:\n{3}\n".format(boss, round(100*boss.Health / boss.StartingHealth, 2), boss.level, boss.lastUsedCombo, )
		sorted_Damage = sorted(boss.Damage.items(), key=operator.itemgetter(1), reverse=True)
		try:
			toPrint += "Most Damage by **{}** with **{:,}** damage\n".format(sorted_Damage[0][0].name, sorted_Damage[0][1])
		except:
			toPrint += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[0][1])
		if len(sorted_Damage) >= 2:
			try:
				toPrint += "2nd most Damage by *{}* with *{:,}* damage\n".format(sorted_Damage[1][0].name, sorted_Damage[1][1])
			except:
				toPrint += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[1][1])
		if len(sorted_Damage) >= 3:
			try:
				toPrint += "3rd most Damage by *{}* with *{:,}* damage\n".format(sorted_Damage[2][0].name, sorted_Damage[2][1])
			except:
				toPrint += "Most Damage by *UNKNOWN* with **{:,}** damage\n".format(sorted_Damage[2][1])
		if len(sorted_Damage) >= 4:
			toPrint += "Assisted by {}\n".format(", ".join([sorted_Damage[x][0].name for x in range(3, len(sorted_Damage), 1)]))

		await self.bot.send_message(channel, embed=discord.Embed(title='**{} Boss Pokemon**'.format(area.capitalize()), description=toPrint, colour=COLORS[area.lower()]).set_author(name=member.name, icon_url=member.avatar_url).set_thumbnail(url=boss.Image))
		self.write_bosses()

	@commands.command(pass_context = True, aliases = ['cd'])
	async def cooldown(self, ctx):
		'Shows your Cooldowns'
		if not enabled(ctx):
			return
		member = ctx.message.author
		player = await self.getPlayer(member)
		msg = ""
		msg += "**Battle**\n"
		if player.get('last_battle_time', 0) + COOLDOWN > time.time():
			msg += "You need to wait {} seconds\n".format(round(player['last_battle_time'] + COOLDOWN - time.time()), 0)
		else:
			msg += "You can Battle right now!\n"

		msg += "**Train**\n"
		if player.get('last_train_time', 0) + TCOOLDOWN > time.time():
			msg += "You need to wait {:,} seconds\n".format(round(player['last_train_time'] + TCOOLDOWN - time.time()), 0)
		else:
			msg += "You can Train right now!\n"

		msg += "**Mine**\n"
		if player.get('last_mine_time', 0) + MCOOLDOWN > time.time():
			msg += "You need to wait {} seconds".format(round(player['last_mine_time'] + MCOOLDOWN - time.time()), 0)
		else:
			msg += "You can Mine right now!"

		m = await self.send_information_message(ctx, msg)
		await asyncio.sleep(5)
		await self.bot.delete_messages([m, ctx.message])

	@commands.command(pass_context = True)
	async def prestige(self, ctx, option = ""):
		'Allows you to prestige at the cost of levels'
		if not enabled(ctx):
			return
		member = ctx.message.author
		player = await self.getPlayer(member)
		player['Prestige'] = player.get('Prestige', 0)

		if player["Prestige"] <= 4:
			if player['Level'] >= 50:	
				if option == "confirm":
					player['Prestige'] = player['Prestige'] + 1
					player['XP'] += self.totalXPTo(player['Level']) - self.totalXPTo(50)
					player['Level'] = 5
					await self.send_valid_message(ctx, "You are now Prestige {}".format(player['Prestige']))
				else:
					await self.send_information_message(ctx, "You can Prestige to Prestige {}!\nPlease do ;prestige confirm to prestige up!".format(player["Prestige"] + 1))
			else:
				await self.send_invalid_message(ctx, "You arent a high enough level to Prestige! Level **50** is Required!")
		elif player["Prestige"] < 10:
			if player['Level'] >= 90:
				if option == "confirm":
					player['Prestige'] = player['Prestige'] + 1
					player['XP'] += self.totalXPTo(player['Level']) - self.totalXPTo(90)
					player['Level'] = 5
					await self.send_valid_message(ctx, "You are now Prestige {}".format(player['Prestige']))
				else:
					await self.send_information_message(ctx, "You can Prestige to Prestige {}!\nPlease do ;prestige confirm to prestige up!".format(player["Prestige"] + 1))
			else:
				await self.send_invalid_message(ctx, "You arent a high enough level to Prestige! Level **90** is Required!")

		player['Time'] = time.time()
		# player = await self.setPlayer(ctx.message.author.id, player)
		# player = await self.giveXP(ctx.message.author, 0, ctx.message.channel)
		player = await self.checkLevel(player)
		await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context = True, aliases = ['ph'])
	async def pokehelp(self, ctx):
		'Pokemon Battle Sim Help (Basically useless)'
		if not enabled(ctx):
			return
		await self.send_information_message(ctx, HelpMessage)

	@commands.command(pass_context = True, aliases = ['lv', 'lvl', 'lookup'])
	async def level(self, ctx, membername = None):
		'Displays your Current Information'
		if not enabled(ctx):
			return
		if membername == None:
			member = ctx.message.author
			player = await self.getPlayer(member)

			player['Name'] = member.name
		else:
			member = self.getMember(membername)
			if member == None:
				return
			player = await self.getPlayer(member)

		avatar = member.avatar_url[:-10]
		if avatar[-4:] == "webp":
			avatar = avatar[:-4] + "png"
		tolevel = await self.ToLevel(int(player['Level']) + 1)
		xp = [player['XP'], tolevel]
		if player['Level'] == 100:
			xp = [player['XP'], None]
		if membername != None:
			player = await getLevelCard(player, avatar, xp)
		else:
			await getLevelCard(player, avatar, xp)
		await self.bot.send_file(ctx.message.channel, 'Resc/Output.png')
		if membername == None:
			player['Time'] = time.time()
			await self.setPlayer(ctx.message.author.id, player)
		else:
			pass

	@commands.command(pass_context = True, aliases = ['bg'])
	async def changeBackground(self, ctx, link):
		if not enabled(ctx):
			return
		member = ctx.message.author
		player = await self.getPlayer(member)
		player['image'] = link
		await self.send_valid_message(ctx, "Changed Background sucessfully")
		player['Time'] = time.time()
		await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context = True)
	async def color(self, ctx, option = "some sketchy invalid choice", one  : int = 255, two : int = 255, three : int = 255):
		if not enabled(ctx):
			return
		player = await self.getPlayer(ctx.message.author)
		if one > 255 or one < 0 or two > 255 or two < 0 or three > 255 or three < 0:
			await self.send_invalid_message(ctx, "Invalid RGB code, all 3 numbers need to be between 0-255")
			return
		if option.lower() == 'text':
			player['text_color'] = tuple([one, two, three])
			await self.send_valid_message(ctx, "Text Color sucessfully")
		elif option.lower() == 'box':
			player['box_color'] = tuple([one, two, three])
			await self.send_valid_message(ctx, "Box Color sucessfully")
		elif option.lower() == 'title':
			player['title_color'] = tuple([one, two, three])
			await self.send_valid_message(ctx, "Title Color sucessfully")
		elif option.lower() == 'bar':
			player['bar_color'] = tuple([one, two, three])
			await self.send_valid_message(ctx, "Bar Color sucessfully")
		elif option.lower() == 'reset':
			for x in ['text_color', 'box_color', 'title_color', 'bar_color']:
				player.pop(x, None)
			await self.send_valid_message(ctx, "Custom colors reset!")
		elif option.lower() == 'palette':
			await self.send_valid_message(ctx, "\n".join(["{} : {}".format(x, player[x]) for x in ['text_color', 'box_color', 'title_color', 'bar_color']]))
		else:
			await self.send_invalid_message(ctx, "Options include:\n{}\nEx `;color box 30 30 30`\nUse `palette` to return the current color palette being used\nUse `reset` to reset the custom options back to default.".format(', '.join(['Text', 'Box', 'Title', 'Bar'])))
		player['Time'] = time.time()
		await self.setPlayer(ctx.message.author.id, player)

		# await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context = True)
	async def mine(self, ctx):
		'Allows you to mine for a risk to your XP'
		if not enabled(ctx):
			return

		player = await self.getPlayer(ctx.message.author)

		# If they are on cooldown for Mining
		if player.get('last_mine_time',0) + MCOOLDOWN > time.time():
			await self.send_invalid_message(ctx, "Please wait {} seconds before you can mine again.".format(round(player.get('last_mine_time',0) + MCOOLDOWN - time.time()), 0))
			return

		amount = int(await self.ToLevel(player['Level'] + 1) / 10)

		# If they don't have enough
		if player['XP'] < amount:
			await self.send_invalid_message(ctx, "You don't have enough XP (need {:,})".format(amount))
			return

		await self.takeXP(ctx.message.author, amount, ctx.message.channel, True)

		Options = {
			"Large Rock" : {
				"Count" : (7 * (player['Level'] - 5)) + 100, 
				"Value" : 0.00,
				"Flavor Text" : "A useless rock. Makes a good paper weight!",
				"Note" : ""
			},
			"Common TYPE Gem" : {
				"Count" : 175,
				"Value" : 0.12,
				"Flavor Text" : "A small gem worth a little experience.",
				"Note" : "Doubles XP gain if gem type is the same as yours"
			},
			"Greater TYPE Gem" : {
				"Count" : 85,
				"Value" : 0.20,
				"Flavor Text" : "A medium sized gem that gives you a good amount of experience.",
				"Note" : "Doubles XP gain if gem type is the same as yours"
			},
			"Legendary TYPE Gem" : {
				"Count" : 35,
				"Value" : 0.40,
				"Flavor Text" : "A large gem that is filled with valuable experience.",
				"Note" : "Doubles XP gain if gem type is the same as yours"
			},
			"Rainbow Gem" : {
				"Count" : 15,
				"Value" : 0.50,
				"Flavor Text" : "A rainbowed colored Gem that sparkles in the sunlight.",
				"Note" : ""
			},
			"Energy Crystal" : {
				"Count" : 15,
				"Value" : 0.10, #### Change to 0.4 for drop table testing, and 0.1 for live
				"Flavor Text" : "A rare crystal that fills you with energy.",
				"Note" : "Allows you to train again"
			},
			"Gold Artifact" : {
				"Count" : 5,
				"Value" : 1.1,
				"Flavor Text" : "A powerful and ancient pokemon artifact that pulses with power!",
				"Note" : ""
			},
		}
		Constructed_List = []
		for entry in Options.keys():
			Constructed_List += [entry] * Options[entry]['Count']
		exhausted = False
		Choice = random.choice(Constructed_List)
		found_type = random.choice(TYPES)

		description = "You spend **{:,}** XP to go mining!\n\nYou found a...\n**{}**.\n\n*{}*".format(amount, Choice.replace("TYPE", found_type.capitalize()), Options[Choice]['Flavor Text'].replace("TYPE", found_type.capitalize()))
		if found_type == player['Type'].lower() and "TYPE" in Choice:
			description += "\nYou gain 2X XP for being the same type as the gem!"

		if random.random() < 0.40:
			exhausted = True
			description += "\n\n**You are exhausted from Mining...** "

		embed = discord.Embed(title='**Mining Session**', description=description, colour=COLORS['mine'])
		embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
		embed.set_footer(text = Options[Choice]['Note'])
		embed.set_thumbnail(url = 'https://cdn.bulbagarden.net/upload/thumb/f/f6/Explorer_Kit.png/250px-Explorer_Kit.png')

		await self.bot.send_message(ctx.message.channel, embed=embed)

		xp_gained = int(await self.ToLevel(player['Level'] + 1) * Options[Choice]['Value'])
		if found_type == player['Type']:
			xp_gained *= 2
		player = await self.giveXP(ctx.message.author, xp_gained, ctx.message.channel)

		if exhausted:
			player['last_mine_time'] = time.time()

		if Choice == "Energy Crystal":
			player['last_train_time'] = 0		
		player['mine_count'] = player.get('mine_count', 0) + 1
		await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context = True,  aliases = ['rankings'])
	async def ranking(self, ctx):
		'Shows the Ranking of the top players'
		if not enabled(ctx):
			return

		with open('Resc/Players.json', 'r') as f:
			ALLPLAYERS = json.load(f)
		sorted_players = sorted(ALLPLAYERS.items(), key=self.score, reverse=True)
		#print(sorted_players[:20])

		for x in range(0, len(sorted_players), 1):
			ALLPLAYERS[sorted_players[x][0]]['ranking'] = x + 1
			ALLPLAYERS[sorted_players[x][0]]['score'] = self.score(sorted_players[x])

		
			ret = "Your Score is:\n"

			ret += "**{:,}**\n\n".format(ALLPLAYERS[ctx.message.author.id]['score'])
			ret += "**Global Scoring**\n"
			first = sorted_players[0][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("TROPHY"), first['Name'], first['Level'], first.get('Prestige', 0), first['score'])

			second = sorted_players[1][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), second['Name'], second['Level'], second.get('Prestige', 0), second['score'])

			third = sorted_players[2][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), third['Name'], third['Level'], third.get('Prestige', 0), third['score'])

			for x in range(3, 5, 1):
				ply = sorted_players[x][1]
				ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), ply['Name'], ply['Level'], ply.get('Prestige', 0), ply['score'])

		try:
			ret += "\n"
			local_sorted_players = []
			local_IDs = [x.id for x in list(ctx.message.server.members)]

			for x in range(0, len(sorted_players), 1):
				if sorted_players[x][0] in local_IDs:
					local_sorted_players.append(sorted_players[x])

			ret += "**Local Scoring**\n"
			first = local_sorted_players[0][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("TROPHY"), first['Name'], first['Level'], first.get('Prestige', 0), first['score'])

			second = local_sorted_players[1][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), second['Name'], second['Level'], second.get('Prestige', 0), second['score'])

			third = local_sorted_players[2][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), third['Name'], third['Level'], third.get('Prestige', 0), third['score'])

			third = local_sorted_players[3][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: 	**{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), third['Name'], third['Level'], third.get('Prestige', 0), third['score'])

			third = local_sorted_players[4][1]
			ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("MILITARY MEDAL"), third['Name'], third['Level'], third.get('Prestige', 0), third['score'])

			for x in range(5, min(10, len(local_sorted_players)), 1):
				ply = local_sorted_players[x][1]
				ret += "{} **{:25s}** Lv: **{}** Prestige: **{}** Score: *{:,}*\n".format(unicodedata.lookup("SPORTS MEDAL"), ply['Name'], ply['Level'], ply.get('Prestige', 0), ply['score'])
		except:
			pass


		channel = ctx.message.channel
		member = ctx.message.author
		await self.bot.send_message(channel, embed=discord.Embed(title='**Ranking**', description=ret, colour=COLORS['ranking']).set_author(name=member.name, icon_url=member.avatar_url))
		ALLPLAYERS[ctx.message.author.id]['Time'] = time.time()
		with open('Resc/Players.json', 'w') as f:
			json.dump(ALLPLAYERS, f, indent = 4)

	async def giveXP(self, member , XP : int, channel):
		player = await self.getPlayer(member)

		player['Prestige'] = player.get('Prestige', 0)
		XP_gain = int(XP * (1 + (0.08 * player['Prestige']) ) )
		player["XP"] = int(player["XP"] + XP_gain)

		if player['Level'] < 5:
			player['Level'] = 5

		pre = player['Level']
		player = await self.checkLevel(player)
		toPrint = "You have gained **{:,}** XP (*{:,} + {}%*)".format(XP_gain, XP, player['Prestige'] * 8)
		if XP > 0:
			await self.bot.send_message(channel, embed=discord.Embed(title='{0} XP Gain {0}'.format(unicodedata.lookup("PARTY POPPER")), description=toPrint, colour=COLORS['xp']).set_author(name=member.name, icon_url=member.avatar_url))
		if pre is not player['Level']:
			toPrint2 = "You Have Leveled up from **{}** to **{}**!".format(pre, player['Level'])
			await self.bot.send_message(channel, embed=discord.Embed(title='{0} Level UP! {0}'.format(unicodedata.lookup("GLOWING STAR")), description=toPrint2, colour=COLORS['level']).set_author(name=member.name, icon_url=member.avatar_url))
		
		await self.setPlayer(member.id, player)

		return player

	async def takeXP(self, member , XP : int, channel, quiet = False):
		player = await self.getPlayer(member)
				
		player["XP"] = player["XP"] - XP
		toPrint = "You have lost {:,} XP".format(XP)
		if not quiet:
			await self.bot.send_message(channel, embed=discord.Embed(title='{0} XP Loss {0}'.format(unicodedata.lookup("SKULL AND CROSSBONES")), description=toPrint, colour=COLORS['xpLoss']).set_author(name=member.name, icon_url=member.avatar_url))
		
		await self.setPlayer(member.id, player)

	@commands.command(pass_context = True)
	async def settype(self, ctx, Type = "none"):
		if not enabled(ctx):
			return

		member = ctx.message.author
		if Type.lower() not in TYPES:
			await self.send_invalid_message(ctx, "You must pick a type from ;types")
			return

		player = await self.getPlayer(member)

		if player.get("last_type_set", 0) + 43200 > time.time():
			await self.send_invalid_message(ctx, "You can only set your type every 12 hours! ({:,} seconds reminaing)".format(round(player.get('last_type_set', 0) + 43200 - time.time()), 0))
			return

		player["Type"] = Type
		await self.send_valid_message(ctx, "You are now a(n) {} type".format(Type.capitalize()))

		player['Time'] = time.time()
		player['last_type_set'] = time.time()
		await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context = True, aliases = ['fightstuff'])
	async def train(self, ctx):
		"Fights Pokemon for XP"
		if not enabled(ctx):
			return

		player = await self.getPlayer(ctx.message.author)

		if player.get('last_train_time', 0) + TCOOLDOWN > time.time():
			await self.send_invalid_message(ctx, "Please wait {:,} seconds before you can train again.".format(round(player['last_train_time'] + TCOOLDOWN - time.time()), 0))
			return

		# Fight (LEVEL/4 + 1 to LEVEL Pokemon)
		# Levels from 1 to 2 * LEVEL
		# Percent to win = LEVEL / 2 / level * 100

		Enemies = [Enemy(getRandomName(), random.randrange(int(player['Level']/2), 2*player['Level'])) for x in range(0, 5 + int(random.random() * 10), 1)]
		beatEnemies = []
		toPrint = ""
		XP = 0
		beat = False
		for enemy in Enemies:
			if enemy.level > 100:
				enemy.level = 100
			percent_to_kill = player['Level'] / 2 / enemy.level * 100
			if percent_to_kill > 90 + player.get('Prestige', 0):
				percent_to_kill = 90 + player.get('Prestige', 0)
			if random.random() * 100 < percent_to_kill:
				beatEnemies.append(enemy)
				# kill_xp = int(player['Level'] * (100 - percent_to_kill) * 0.8)
				kill_xp = int(1.25 * math.pow(enemy.level, 2) / 3) + 1
				XP += kill_xp
				toPrint += "You **Beat** a Level {} **{}** for {:,} XP ({}% to beat)\n".format(enemy.level, enemy.name, kill_xp, int(percent_to_kill))
				beat = True
			else:
				toPrint += "You *Lost* to a Level {} **{}** ({}% to beat)\n".format(enemy.level, enemy.name, int(percent_to_kill))

		toPrint += "\n"
		if random.random() <= 0.33:
			toPrint += "You use an **EXP share** to gain more XP! (+ {:,})\n".format(int(XP * 0.5))
			XP = XP * 1.5

		Searching = [.50, .10, .02, .005]

		if random.random() <= 0.33:
			toPrint += 'You use an **Item Finder** for a better chance at Pokeloots! (+50%)\n'
			Searching = [x * 1.50 for x in Searching]

		pokelootText = ""
		pokeloot = 0
		if random.random() <= Searching[0]:
			pokeloot += await self.ToLevel(player['Level'] + 1) * 0.05 + 1
			pokelootText += "You Find a **Pokeloot** worth {:,} XP\n".format(int(await self.ToLevel(player['Level'] + 1) * 0.05 + 1))
		if random.random() <= Searching[1]:
			pokeloot += await self.ToLevel(player['Level'] + 1) * 0.15 + 1
			pokelootText += "You Find a **Ultra Pokeloot** worth {:,} XP\n".format(int(await self.ToLevel(player['Level'] + 1) * 0.15 + 1))
		if random.random() <= Searching[2]:
			pokeloot += await self.ToLevel(player["Level"] + 1) * 0.40 + 1
			pokelootText += "You Find an **Master Pokeloot** worth {:,} XP\n".format(int(await self.ToLevel(player["Level"] + 1) * 0.40 + 1))
		if random.random() <= Searching[3]:
			pokeloot += await self.ToLevel(player["Level"] + 1)
			pokelootText += "You Find an **Rare candy** and you gain a level!\n"
		toPrint += pokelootText
		XP += pokeloot

		await self.addPokedex(ctx.message.author, beatEnemies)
		XP = int(XP)
		await self.bot.send_message(ctx.message.channel, embed=discord.Embed(title='Pokemon Training Session', description=toPrint, colour=COLORS['train']).set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url))
		#await self.bot.say(toPrint)
		player = await self.giveXP(ctx.message.author, XP, ctx.message.channel)
		if beat:
			player['last_train_time'] = time.time()
		else:
			player['last_train_time'] = time.time() - int(TCOOLDOWN * .75)

		player['train_count'] = player.get('train_count', 0) + 1
		await self.setPlayer(ctx.message.author.id, player)

	@commands.command(pass_context=True, aliases = ['dex'])
	async def pokedex(self, ctx, search = ""):
		if not enabled(ctx):
			return
		member = ctx.message.author
		player = await self.getPlayer(member)

		pokemon = player.get('Pokemon', [' '])
		if search == "":
			await self.send_information_message(ctx, "Your Pokedex is {}% complete!".format(round((len(pokemon)-1) / 721 * 100, 2)))
		elif search.lower() == "list":
			await self.bot.send_message(member, "Your Pokedex contains the following pokemon: {}".format(", ".join(pokemon[1:])))
		else:
			if search.capitalize() in pokemon:
				await self.send_valid_message(ctx, "You **have** beat a {}".format(search.capitalize()))
			else:
				await self.send_invalid_message(ctx, "You have not beat a {}".format(search.capitalize()))
		player['Time'] = time.time()
		await self.setPlayer(member.id, player)

	async def addPokedex(self, member, enemies):
		player = await self.getPlayer(member)
		names = []
		for enemy in enemies:
			names.append(enemy.name)

		try:
			defeated = player["Pokemon"]
		except:
			player["Pokemon"] = [" "]
			defeated = player["Pokemon"]

		pokemon = player["Pokemon"]
		for name in names:
			if name not in defeated:
				pokemon.append(name)

		player["Pokemon"] = pokemon
		player['Time'] = time.time()
		await self.setPlayer(member.id, player)

	async def getPlayer(self, member):
		with open('Resc/Players.json', 'r') as f:
			ALLPLAYERS = json.load(f)
		try:
			player = await self.checkLevel(ALLPLAYERS[member.id])
		except:
			print("NEW PLAYER: {}".format(member.name))
			NEWPLAYER['Name'] = member.name
			ALLPLAYERS[member.id] = NEWPLAYER
			player = ALLPLAYERS[member.id]

		ALLPLAYERS[member.id]['Time'] = time.time()
		with open('Resc/Players.json', 'w') as f:
			if ALLPLAYERS != None:
				json.dump(ALLPLAYERS, f, indent = 4)
		return player

	async def setPlayer(self, player_id, player):
		with open('Resc/Players.json', 'r') as f:
			ALLPLAYERS = json.load(f)
		ALLPLAYERS[player_id] = player
		with open('Resc/Players.json', 'w') as f:
			json.dump(ALLPLAYERS, f, indent = 4)

	def getMember(self, name):
		try:
			return [x for x in list(self.bot.get_all_members()) if x.name == name][0]
		except Exception:
			return None

	def getMemberFromID(self, ID):
		try:
			return [x for x in list(self.bot.get_all_members()) if x.id == ID][0]
		except Exception:
			# print("Didn't find, feelsbad")
			return None	

	@commands.command(pass_context = True)
	async def types(self, ctx):
		if not enabled(ctx):
			return
		val = """ -= **Possible Types ** =-\n:regional_indicator_n: ormal\n:regional_indicator_f: ire\n:regional_indicator_w: ater\n:regional_indicator_g: rass\n:regional_indicator_p: oison\n:regional_indicator_d: ragon\n:regional_indicator_s: teel\n:regional_indicator_e: lectric\n:regional_indicator_b: ug\n:regional_indicator_i: ce"""
		await self.bot.say(val)

	async def ToLevel(self, level):
		return int(math.pow(level, 3))

	async def checkLevel(self, player):
		while player['XP'] >= await self.ToLevel(int(player['Level']) + 1) and player['Level'] is not 100:
			player['XP'] -= await self.ToLevel(int(player['Level']) + 1)
			player['Level'] += 1
		while player['XP'] < 0:
			player['XP'] += await self.ToLevel(int(player['Level']))
			player['Level'] -= 1
		return player

	def score(self, dict):
		player = dict[1]
		# Base Score is total XP
		score = self.totalXPTo(player['Level'], player['XP'])
		# Add-on Prestige XP
		if player.get('Prestige', 0) > 0:
			if player['Prestige'] <= 5:
				score += self.totalXPTo(50) * player['Prestige'] * 2
			else:
				score += self.totalXPTo(50) * 5 * 2
				score += self.totalXPTo(90) * (player['Prestige'] - 5) * 2
		# Additional Score for Large Damage
		score += player.get('largest_damage', 0) * 5

		# Multiplier for Pokedex Completeness
		Pokedex = (len(player.get("Pokemon", [" "]))-1) / 721
		Pokedex = Pokedex + 0.3
		score *= math.pow(Pokedex, 0.5)
		if Pokedex == 1.3:
			score *= 1.2

		# Takedown additions
		score *= (math.log(player['Takedowns'] + 1, 3.4) + 1)

		return int(score/100)

	def totalXPTo(self, level = 100, currentXP = 0):
		if level <= 5:
			return currentXP
		else:
			return self.totalXPTo(level-1, currentXP + int(math.pow(level, 3)))

	async def send_invalid_message(self, ctx, message):
		channel = ctx.message.channel
		member = ctx.message.author
		Embed = discord.Embed(description=message, colour=COLORS['invalid'])
		Embed.set_author(name=member.name, icon_url=member.avatar_url)
		return await self.bot.send_message(channel, embed=Embed)

	async def send_valid_message(self, ctx, message):
		channel = ctx.message.channel
		member = ctx.message.author
		Embed = discord.Embed(description=message, colour=COLORS['valid'])
		Embed.set_author(name=member.name, icon_url=member.avatar_url)
		return await self.bot.send_message(channel, embed=Embed)

	async def send_information_message(self, ctx, message):
		channel = ctx.message.channel
		member = ctx.message.author
		Embed = discord.Embed(description=message, colour=COLORS['information'])
		Embed.set_author(name=member.name, icon_url=member.avatar_url)
		return await self.bot.send_message(channel, embed=Embed)


class Boss:
	def __init__(self, level = (0, 100), blank = False):
		if blank:
			return
		self.level = random.randrange(level[0], level[1], 1)
		if self.level < 20:
			self.Name = getRandomName('easy')
			self.Moves = 5
		elif self.level < 50:
			self.Name = getRandomName('medium')
			self.Moves = 8
		elif self.level < 80:
			self.Name = getRandomName('hard')
			self.Moves = 10
		else:
			self.Name = getRandomName('insane')
			self.Moves = 15
		
		self.Health = int(666 * self.level * self.Moves / 8 * random.randrange(75, 125, 1) / 100)
		self.StartingHealth = self.Health
		self.Image = getImage(self.Name)
		self.Name = self.Name.capitalize()
		self.Damage = {}
		self.isDefeated = False
		self.hasBeenRevealed = False
		self.combination = [random.choice(["N","F","W","G","P","D","S","E","B","I"]) for x in range(0, self.Moves, 1)]
		self.lastUsedCombo = ""
		self.summoner = ""

	def change1(self):
		choose = random.choice(range(0, self.Moves, 1))
		self.combination[choose] = random.choice(["N","F","W","G","P","D","S","E","B","I"])

	def kill(self):
		self.level = None
		self.isDefeated = True
		self.Health = 0

	def changeHalf(self):
		choose = random.sample(range(0, self.Moves, 1), int(self.Moves/2))
		for x in choose:
			choice = random.choice(["N","F","W","G","P","D","S","E","B","I"])
			while choice == self.combination[x]:
				choice = random.choice(["N","F","W","G","P","D","S","E","B","I"])
			self.combination[x] = choice

	def changeQuarter(self):
		choose = random.sample(range(0, self.Moves, 1), int(self.Moves/4))
		for x in choose:
			choice = random.choice(["N","F","W","G","P","D","S","E","B","I"])
			while choice == self.combination[x]:
				choice = random.choice(["N","F","W","G","P","D","S","E","B","I"])
			self.combination[x] = choice

class Enemy:
	def __init__(self, name, level):
		self.name = name.capitalize()
		self.level = level

def setup(bot):
	bot.add_cog(Games(bot))