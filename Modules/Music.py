import discord
from discord.ext import commands
import asyncio
import random
import datetime
import json
import requests
from Util.API_Caller import youtube
from Util.API_Caller import radio
from Util.API_Caller import getYoutubePlaylistSongs
import sys


MIN_VIEWS = 5000
MAX_PERCENT_DISLIKE = 0.25
MAX_LENGTH = 1200000
MAX_SONGS_SHOWN = 10
MAXLOOPS = 5
VERSION = "0.4.3"
OPTS = {
            'quiet': True,
            'no_warnings' : True
    }

RADIO = True

try:
	RADIO_OPTIONS = json.loads(requests.get("http://temp.discord.fm/libraries/json").text)
	RADIO_PRINT = "**Please choose one of these options**: \n```py\n{}```\nExample: `;Radio Purely Pop`".format("\n".join("{:18s}".format(x['name']) + "https://temp.discord.fm/libraries/{}".format(x['id']) for x in RADIO_OPTIONS))
except:
	RADIO = False
class SmartQueue:
	def __init__(self, SP):
		self.queue = []
		self.SP = SP

	async def append(self, youtubePlayer):
		self.queue.append({
			'url' : youtubePlayer[0].url, 
			'requester' : youtubePlayer[1], 
			'duration' : youtubePlayer[0].duration,
			'title' : youtubePlayer[0].title
			})
		youtubePlayer[0].process.kill()

	async def pop(self, index):
		entry = self.queue.pop(index)
		ret = await self.SP.voice.create_ytdl_player(entry['url'], ytdl_options=OPTS)
		return (ret, entry['requester'])

	async def removeRequester(self, requester):
		count = len(self.queue)
		self.queue = [song for song in self.queue if song['requester'] != requester]
		return count - len(self.queue)

	async def shuffle(self):
		random.shuffle(self.queue)

	def clear(self):
		self.queue = []

	async def insert(self, loc, youtubePlayer):
			self.queue.insert(loc, {
			'url' : youtubePlayer[0].url, 
			'requester' : youtubePlayer[1], 
			'duration' : youtubePlayer[0].duration,
			'title' : youtubePlayer[0].title
			})
			youtubePlayer[0].process.kill()

	def nameAt(self, loc):
		return self.queue[loc]['requester']

	def __len__(self):
		return len(self.queue)

	def __str__(self):
		ret = ""
		if len(self.queue) == 0:
			return "The Queue is Empty! Add some songs using ;youtube [Link] or ;search [keywords]"
		ret += "There are **{}** songs in the Queue\n\n".format(len(self.queue))
		count = 1
		for song in self.queue:
			if count > MAX_SONGS_SHOWN:
				break
			ret += "**{}**. {}\nRequested By: **{}**\n{}\n\n".format(count, song['title'] if len(song['title']) <= 55 else song['title'][:55] + "...", song['requester'], song['url'])
			count += 1
		if count - 1 != len(self.queue):
			ret += "Plus **{}** more songs not shown...\n".format(len(self.queue) - (count -1))
		seconds = sum([song['duration'] for song in self.queue])
		ret += "Queue Length: {}".format(str(datetime.timedelta(seconds=seconds)))
		return ret

class ServerPlayer:
	def __init__(self, server):

		# Connected server
		self.server = server

		# Voice connected
		self.voice = None

		# Current player object
		self.player = None

		# Current Queue of songs
		self.queue = SmartQueue(self)

		# Radio mode
		self.radio = False

		# List of IDs of people who request skip
		self.skipList = []

		# The Requester of the current song
		self.requester = None

		# ID of the person who previously looped a song
		self.previousLooper = "0"

		# Toggle Recommending Songs
		self.recommend = False

		# Toggle re-adding finished songs to queue
		self.cycle = False

		# Current Song info
		self.extract_info = None

		# Has the Queue failed?
		self.QueueFailure = False

		self.paused = False

	def __str__(self):
		ret = ""
		ret += "Connected Channel: {}\n".format(self.voice.channel)
		ret += "Queue Length: {}\n".format(len(self.queue))
		if self.radio:
			ret += "**Radio Mode Enabled**\n - Adding songs is disabled and songs will be added from the selected radio station.\n"
		if self.recommend:
			ret += "**Auto Recommend Songs Enabled**\n - Songs will be automatically added based off of the current playing song.\n"
		if self.cycle:
			ret += "**Cycle mode Enabled**\n - Completed songs will be re-added to the end of the Queue.\n"
		if self.QueueFailure:
			ret += "WARNING: QUEUE HAS FAILED. ATTEMPTING TO RESTART IT\n"
		return ret

	def currentSonginfo(self):
		if self.player == None or self.player.is_done():
			self.player = None
			return None

		ret = ""
		ret += "**Name**: {}\n".format(str(self.player.title))
		ret += "**Requester**: {}\n".format(str(self.requester))
		ret += "**URL**: {}\n".format(str(self.player.url))
		ret += "**Length**: {}\n".format(str(datetime.timedelta(seconds = self.player.duration)))
		ret += "```py\n"
		ret += "Views: {}\n".format(str(format(self.player.views, ',d')))
		try:
			ret += "Likes: {}, {}%\n".format(str(format(self.player.likes, ',d')), str(round(self.player.likes/(self.player.likes + self.player.dislikes) * 100, 2)))
			ret += "Dislikes: {}, {}%\n".format(str(format(self.player.dislikes, ',d')), str(round(self.player.dislikes/(self.player.likes + self.player.dislikes) * 100, 2)))
		except:
			ret += "Likes: N/A\nDislikes: N/A\n"
		ret += "Skips: {}/{}\n".format(str(len(self.skipList)), str(int(2*(len(self.voice.channel.voice_members)-1)/3)))
		ret += "```"
		return ret

class MusicPlayer:
	def hasAdmin(self, ctx):
		if ctx.message.author.server_permissions.administrator or ctx.message.author.id == '134441036905840640':
			return True
		return False

	def __init__(self, bot):
		with open('Resc/Playlists.json', 'r') as f:
			self.playList = json.load(f)
		self.bot = bot
		self.serverPlayers = {}

	@commands.command(pass_context=True)
	async def music(self, ctx):
		'Returns the current status of the Music Bot'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		await self.bot.send_message(ctx.message.channel, embed=discord.Embed(title="Music in **{}**\n".format(SP.server), description=str(SP), colour=0x8989E5).set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url))
		if SP.QueueFailure:
			await self.useQueue(SP)


	@commands.command(pass_context = True,  aliases = ['queue'])
	async def songs(self, ctx):
		'Prints the songs in the queue'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		ret = str(SP.queue)
		await self.bot.send_message(ctx.message.channel, embed=discord.Embed(title='Current Queue', description=ret, colour=0x8989E5).set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url))

	@commands.command(pass_context = True)
	async def shuffle(self, ctx):
		'Shuffles the songs the queue'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		'Shuffles the songs in the Queue'
		await SP.queue.shuffle()
		await self.bot.say("Shuffled songs!")

	@commands.command(pass_context = True)
	async def remove(self, ctx, input):
		'removes a song from a queue by index'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		try:
			number = int(input)
			if(len(SP.queue) < number):
				await self.bot.say("The Queue isnt that long!")
				return
			currentName = SP.queue.nameAt(number-1)
			if currentName == ctx.message.author.name or ctx.message.author.id == "134441036905840640" or currentName == "Radio":
				current = (await SP.queue.pop(number - 1))[0]
				current.process.kill()
				await self.bot.say("Removed: " + current.title)
			else:
				await self.bot.say("You must be the requester of the song to remove it from queue!")
		except Exception as e:
			print(e)
			if ctx.message.author.name == input or self.hasAdmin(ctx):
				amount = await SP.queue.removeRequester(input)
				await self.bot.say("Removed {} that {} requested".format(amount, input))

	@commands.command(hidden = True, pass_context = True)
	async def forceplay(self,ctx, link : str):
		if not self.hasAdmin(ctx):
			return
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		SP.requester = ctx.message.author.name
		current = await SP.voice.create_ytdl_player(link, ytdl_options=OPTS)
		if(SP.player != None):
			SP.player.stop()
		SP.player = current
		SP.player.start()
		SP.skipList = []
		print("Done forceplay")

	@commands.command(pass_context = True)
	async def recommend(self, ctx):
		'Allow the bot to add up to 5 songs to the queue to have infinite music playing.\nChooses songs based off of the current playing song and YouTube\'s Mix feature.'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		try:
			SP.player.title
		except:
			await self.bot.say('Please add a song with {}search first'.format(self.bot.command_prefix))
			return
		SP.recommend = not SP.recommend
		await self.bot.say("Recommend Songs to play: {}".format(SP.recommend))

	@commands.command(pass_context = True)
	async def cycle(self, ctx):
		'Tells the bot to cycle the current songs in the queue'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		SP.cycle = not SP.cycle
		await self.bot.say("Cycle Mode: {}".format(SP.cycle))
	@commands.command(pass_context = True)
	async def loop(self, ctx, num = 1):
		'Plays the current song again'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		ID = ctx.message.author.id
		if ID not in [x.id for x in SP.voice.channel.voice_members]:
			await self.bot.say("You need to be in the voice channel!")
			return
		if(num > MAXLOOPS/(len(SP.voice.channel.voice_members)-1) and ctx.message.author.id != "134441036905840640"):
			await self.bot.say("Can not loop that many times!")
			return
		if(SP.previousLooper == ctx.message.author.id and len(SP.voice.channel.voice_members) > 2 and ctx.message.author.id != "134441036905840640"):
			await self.bot.say("You can not loop more than once in a row! Please wait for someone else to loop a song.")
			return
		SP.previousLooper = ctx.message.author.id

		current = await SP.voice.create_ytdl_player(SP.player.url, ytdl_options=OPTS)
		final = (current, ctx.message.author.name)
		for x in range(0,num,1):
			await SP.queue.insert(0, final)
		await self.bot.say("Added '*{}*' **{}** more times".format(SP.player.title, num))

	@commands.command(pass_context = True)
	async def playlists(self, ctx):
		'Shows all the current playlists'
		await self.bot.send_typing(ctx.message.channel)
		with open('Resc/Playlists.json', 'r') as f:
			self.playList = json.load(f)
		Names = []
		for name, songs in self.playList.items():
			if(songs != None and name != None):
				Names.append(name + "[" + str(len(songs)) + "]")
		await self.bot.say(", ".join(Names))


	# Adding songs Section
	@commands.command(pass_context = True, aliases = ['soundcloud'])
	async def youtube(self,ctx, * links : str):
		'Adds a Song for the Bot to Play'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		if SP.radio:
			await self.bot.say("Turn off Radio mode first! (`;Radio off`)")
			return
		ID = ctx.message.author.id
		if ID not in [x.id for x in SP.voice.channel.voice_members]:
			await self.bot.say("You need to be in the voice channel!")
			return

		if(SP.voice == None):
			await self.bot.say("I am not connected to a Voice Chat!")
			return

		for link in links:
			if("www.youtube.com/watch?v" not in link and "https://youtu.be/" not in link and "https://soundcloud.com/" not in link):
				await self.bot.say("Not a Valid Link, Please only use URLs from youtube.com or soundcloud.com")
				break
			link = link.split("&")[0]
			try:
				current = await SP.voice.create_ytdl_player(link, ytdl_options=OPTS)
			except Exception as e:
				self.bot.say(e)
				break
			if "https://soundcloud.com/" not in link and current.views < MIN_VIEWS:
				await self.bot.say("Sorry, that video has too little views to be Trustworthy. Needs [{}] but has [{}]".format(format(MIN_VIEWS, ",d"), format(current.views, ",d")))
				current.process.kill()
				break
			# elif (current.dislikes / (current.dislikes + current.likes) > MAX_PERCENT_DISLIKE):
			# 	await self.bot.say("Sorry, too many people dislike that video. Needs to be below [{}%] but was [{}%]".format(MAX_PERCENT_DISLIKE * 100, round(current.dislikes / (current.dislikes + current.likes) * 100,2)))
			# 	current.process.kill()
			# 	break
			elif "https://soundcloud.com/" not in link and current.duration > MAX_LENGTH:
				await self.bot.say("Sorry, that video is too long, it must be under [{}] minutes!".format(MAX_LENGTH/60))
				current.process.kill()
				break
			await self.bot.say("Added {} to the queue".format(current.title))
			await SP.queue.append((current, ctx.message.author.name))
			print("Added Song to Queue")

	@commands.command(pass_context = True)
	async def search(self, ctx, * Pinput : str):
		'Searches for a song'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		if SP.radio:
			await self.bot.say("Turn off Radio mode first! (`;Radio off`)")
			return
		if " ".join(Pinput) == "":
			await self.bot.say("Search for SOMETHING you bum")
			return
		ID = ctx.message.author.id
		if ID not in [x.id for x in SP.voice.channel.voice_members]:
			await self.bot.say("You need to be in the voice channel!")
			return
		if(SP.voice == None):
			await self.bot.say("I am not connected to a Voice Chat!")
			return

		links = youtube(" ".join(Pinput))
		try:
			for link in links:
				await self.bot.send_typing(ctx.message.channel)
				current = await SP.voice.create_ytdl_player(link, ytdl_options=OPTS)
				# current.dislikes / (current.dislikes + current.likes) > MAX_PERCENT_DISLIKE
				# current.dislikes == None or current.likes == None
				if current == None or current.views < MIN_VIEWS or current.duration > MAX_LENGTH:
					current.process.kill()
				else:
					await self.bot.say("Added {} to the queue".format(current.title))
					await self.bot.say(link)
					await SP.queue.append((current, ctx.message.author.name))
					return
		except:	
			pass
		await self.bot.say("Sorry, couldnt find anything :(")

	@commands.command(pass_context = True)
	async def yplaylist(self, ctx, playlistURL):
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return

		if SP.radio:
			await self.bot.say("Turn off Radio mode first! (`;Radio off`)")
			return

		songs = getYoutubePlaylistSongs(playlistURL)
		for song in songs:
			await self.bot.send_typing(ctx.message.channel)
			try:
				current = await SP.voice.create_ytdl_player(song, ytdl_options=OPTS)
				await SP.queue.append((current, ctx.message.author.name))
			except Exception as e:
				print("Could Not Add a Song... Skipping it: <{}>".format(e))
		await self.bot.say("Finished Adding songs from playlist")

	async def useQueue(self, SP):
		print("Running Queue in {}".format(SP.server.name))
		SP.QueueFailure = False
		
		while not self.bot.is_closed and SP.voice is not None:
			try:
				# Main Queue
				if len(SP.queue) != 0:
					if SP.player is None:
						song = await SP.queue.pop(0)
						SP.requester = song[1]
						await self.playSong(song[0], SP, song[1])
					elif SP.player.is_done():
						song = await SP.queue.pop(0)
						SP.requester = song[1]
						await self.playSong(song[0], SP, song[1])

				# Radio Mode
				if SP.radio and len(SP.queue) < 5:
					try:
						Options = json.loads(requests.get("http://temp.discord.fm/libraries/{}/json".format(SP.radioType['id'])).text)
						while len(SP.queue) < 5:
							choice = random.choice(Options)
							current = await SP.voice.create_ytdl_player("https://www.youtube.com/watch?v="+choice['identifier'], ytdl_options=OPTS)
							await SP.queue.append((current, "Radio: " + SP.radioType['name']))
					except:
						print("We Broke something :( {}".format(choice))

				# Recommender
				elif SP.recommend and len(SP.queue) < 5:
					try:
						songs = radio(SP.player.url)
						random.shuffle(songs)
						#print(songs)
						while len(songs) > 0 and len(SP.queue) < 5:
							song = songs.pop()
							current = await SP.voice.create_ytdl_player(song, ytdl_options=OPTS)
							# current.dislikes == None or current.likes == None
							# current.dislikes / (current.dislikes + current.likes) > MAX_PERCENT_DISLIKE
							if current == None or current.views < MIN_VIEWS or current.duration > MAX_LENGTH:
								#print("Filtered", current.url)
								current.process.kill()
								continue
							else:
								#print("Found song")
								await SP.queue.append((current, 'Radio: {}'.format(SP.player.title[:10])))
					except Exception as e:
						print("Bad video", SP.player.url, e)

				if SP.voice.ws.close_code != None:
					channel = SP.voice.channel
					await SP.voice.disconnect()
					SP.voice = await self.bot.join_voice_channel(channel)
					print("Repairing connection to voice Automatically!")

				await asyncio.sleep(1)
			except Exception as e:
				print(e)
				SP.QueueFailure = True
				break
		print("Finished Queue in {}".format(SP.server.name))
		print("Errored = {}".format(SP.QueueFailure))
			
	async def playSong(self, current, SP, requester):
		if(SP.player != None):
			SP.player.stop()
		link = current.url
		if not current.is_done():
			current.start()
		current.stop()
		if SP.cycle:
			await SP.queue.append((await SP.voice.create_ytdl_player(SP.player.url, ytdl_options=OPTS), requester))
		beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" 
		SP.player = await SP.voice.create_ytdl_player(link, ytdl_options=OPTS, before_options = beforeArgs)
		print("Playing {} in {}".format(SP.player.title, SP.server.name))
		await self.bot.change_presence(game=discord.Game(name='{}'.format(SP.player.title)))
		SP.player.start()
		SP.player.volume = 1
		SP.skipList = []
		SP.extract_info = SP.player.yt.extract_info(SP.player.url, download = False)

	@commands.command(pass_context = True, name = 'radio')
	async def Radio(self, ctx, * choice):
		'Enables Radio Mode'
		global RADIO_PRINT
		await self.bot.send_typing(ctx.message.channel)

		if not RADIO:
			await self.bot.say("The Radio feature is currently down :(")
			return
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return

		# Invalid input
		if " ".join(choice).lower() not in [x['name'].lower() for x in RADIO_OPTIONS] and " ".join(choice).lower() != "off":
			await self.bot.say(RADIO_PRINT)
			if SP.radio:
				await self.bot.say("Currently listening to the *{}* radio channel".format(SP.radioType['name']))
			return

		# Turn Radio off
		elif " ".join(choice).lower() == "off":
			await self.bot.say("Radio mode OFF")
			SP.radio = False
			SP.queue.clear()
			return

		if SP.radio == True:
			SP.recommend = False
			SP.cycle = False
			SP.radioType = [x for x in RADIO_OPTIONS if x['name'].lower() == " ".join(choice).lower()][0]
			await self.bot.say("Now listening to **{}** radio channel".format(SP.radioType['name']))
			SP.queue.clear()
		else:
			SP.radio = True
			SP.recommend = False
			SP.cycle = False
			SP.radioType = [x for x in RADIO_OPTIONS if x['name'].lower() == " ".join(choice).lower()][0]
			await self.bot.say("Now listening to **{}** radio channel".format(SP.radioType['name']))

	@commands.command(pass_context = True)
	async def join(self,ctx):
		'Joins the Voice channel you are currently in'
		await self.bot.send_typing(ctx.message.channel)
		SP = self.serverPlayers.get(ctx.message.server.id, None)
		if SP == None or SP.voice == None:
			channel = ctx.message.author.voice_channel
			if channel is None:
				await self.bot.say("You are not connected to a voice channel!")
			else:
				try:
					self.serverPlayers[ctx.message.server.id] = ServerPlayer(ctx.message.server)
					SP = self.serverPlayers[ctx.message.server.id]
					SP.voice = await self.bot.join_voice_channel(channel)
					await self.bot.say("Connected channel!")
				except:
					self.serverPlayers[ctx.message.server.id] = ServerPlayer(ctx.message.server)
					SP = self.serverPlayers[ctx.message.server.id]
					SP.voice = ctx.message.server.voice_client
					await self.bot.say("Reconnected channel!")
		else:
			await self.bot.say("Sorry, I'm already connected to a channel")
			return
		await self.useQueue(SP)

	@commands.command(pass_context=True)
	async def reconnect(self, ctx):
		await self.bot.send_typing(ctx.message.channel)
		if ctx.message.server.id not in self.serverPlayers.keys():
			await self.bot.say("Bot is not connected to voice on this server!")
		else:
			SP = self.serverPlayers[ctx.message.server.id]
			channel = SP.voice.channel
			await SP.voice.disconnect()
			SP.voice = await self.bot.join_voice_channel(channel)
			if SP.QueueFailure:
				await self.useQueue(SP)
			await self.bot.say("Reconnected channel!")

	@commands.command(pass_context = True)
	async def leave(self, ctx):
		'Leaves the Join chat'
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		# IF Broken and not Admin and not only one in the room
		if not self.hasAdmin(ctx) and len(SP.voice.channel.voice_members)-1 != 1:
			return
		SP.queue.clear()
		await SP.voice.disconnect()
		SP.voice = None

	@commands.command(pass_context=True, hidden=True)
	async def musicdebug(self, ctx, *, code : str):
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
	async def clear(self, ctx):
		'Clears the Queue'
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		if not self.hasAdmin(ctx) and len(SP.voice.channel.voice_members)-1 != 1:
			await self.bot.say("You do not have permission to do this.")
			return
		await self.bot.send_typing(ctx.message.channel)
		SP.queue.clear()
		await self.bot.say("Cleared Queue!")

	@commands.command(pass_context = True)
	async def song(self, ctx):
		'Returns information about the current playing song'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		ret = SP.currentSonginfo()
		if ret != None:
			if SP.extract_info == None:
				SP.extract_info = SP.player.yt.extract_info(SP.player.url)
			Thumbnail = SP.extract_info['thumbnails'][0]['url']
			await self.bot.send_message(ctx.message.channel, embed=discord.Embed(title='Current Song', description=ret, colour=0x8989E5).set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url).set_thumbnail(url=Thumbnail))
		else:
			await self.bot.send_message(ctx.message.channel, embed=discord.Embed(title='Current Song', description="There is no Song Currently playing", colour=0x8989E5).set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url))

	@commands.command(pass_context = True)
	async def skip(self, ctx, forcevote = None):
		'Skips the Current song'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		ID = ctx.message.author.id

		# Only people in the channel can mute
		if ID not in [x.id for x in SP.voice.channel.voice_members]:
			await self.bot.say("You need to be in the voice channel!")
			return

		# Requester wants to skip
		if ctx.message.author.name == SP.requester and forcevote.lower() != "vote":
			await self.bot.say("Skipping {} by request of the requester".format(SP.player.title))
			SP.player.stop()
			SP.skipList = []
			return

		# Its a Radio Song 
		if "Radio: " in SP.requester and forcevote != None and forcevote.lower() != "vote":
			await self.bot.say("Skipping {} by request (Radio Song)".format(SP.player.title))
			SP.player.stop()
			SP.skipList = []
			return

		if self.hasAdmin(ctx) and forcevote != None and forcevote.lower() != "vote":
			await self.bot.say("Skipping {} by ADMIN request".format(SP.player.title))
			SP.player.stop()
			SP.skipList = []
			return

		NeededToSkip = int(2*(len(SP.voice.channel.voice_members)-1)/3)

		# Add a new `Skipper` to the list
		if ID not in SP.skipList:
			SP.skipList.append(ID)
			await self.bot.say("{}/{} votes to skip".format(len(SP.skipList), NeededToSkip))
		else:
			await self.bot.say("You have already voted to skip this song!")
		# If Enough votes, skip the song
		if len(SP.skipList) >= NeededToSkip:
			await self.bot.say("Skipping {} by popular vote.".format(SP.player.title))
			SP.player.stop()
			SP.skipList = []

	# Playlist Stuff
	@commands.command(pass_context = True)
	async def playlist(self, ctx, *names : str):
		'Adds songs from a predefined playlist to the songs list'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return

		if SP.radio:
			await self.bot.say("Turn off Radio mode first! (`;Radio off`)")
			return
		with open('Resc/Playlists.json', 'r') as f:
			self.playlist = json.load(f)
		for name in names:
			random.shuffle(self.playList[name])
			for song in self.playList[name]:
				try:
					current = await SP.voice.create_ytdl_player(song, ytdl_options=OPTS)
					await SP.queue.append((current, ctx.message.author.name))
				except Exception as e:
					print("Could Not Add a Song... Skipping it: <{}>".format(e))

		print("Added Playlists [{}] to {}".format(", ".join(names), SP.server.name))					
		await self.bot.say("Finished Adding songs from playlist(s)")

	@commands.command(pass_context = True)
	async def makeplaylist(self, ctx, name, *links : str):
		'Makes a custom playlist for the bot to save'
		await self.bot.send_typing(ctx.message.channel)
		with open('Resc/Playlists.json', 'r') as f:
			self.playList = json.load(f)
		if(name in self.playList.keys()):
			await self.bot.say("Playlist already exists")
			return
		self.playList[name] = list(links)
		with open('Resc/Playlists.json', 'w') as f:
			json.dump(self.playList, f)
		await self.bot.say("Created Playlist {} with {} songs".format(name, len(list(links))))

	@commands.command(pass_context = True)
	async def viewplaylist(self, ctx, name):
		'Views the songs of a playlists'
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		with open('Resc/Playlists.json', 'r') as f:
			self.playList = json.load(f)
		if(name not in self.playList.keys()):
			await self.bot.say("Playlist does not exists")
			return
		try:
			songNames = await self.getNames(self.playList[name], SP)
		except Exception as e:
			await self.bot.say(e)
			return
		await self.bot.say("\n".join(songNames))

	async def getNames(self, names, SP):
		cleanNames = []
		for name in names:
			try:
				song = await SP.voice.create_ytdl_player(name)
				cleanNames.append(song.title + " <{}>".format(song.url))
				song.start()
				song.stop()
			except Exception as e:
				print("{}\nBAD SONG IN A PLAYLIST".format(e))
		return cleanNames

	@commands.command(pass_context = True)
	async def extendplaylist(self, ctx, name, *links : str):
		'Extends a custom playlist'
		await self.bot.send_typing(ctx.message.channel)
		with open('Resc/Playlists.json', 'r') as f:
			self.playList = json.load(f)
		if(name not in self.playList.keys()):
			await self.bot.say("Playlist does not exists")
			return
		self.playList[name].extend(list(links))
		with open('Resc/Playlists.json', 'w') as f:
			json.dump(self.playList, f)
		await self.bot.say("Extended Playlist {} with {} more songs".format(name, len(list(links))))

	@commands.command(hidden = True)
	async def removeplaylist(self, name):
		'Removes a custom playlist'
		if not self.hasAdmin(ctx):
			return
		# await self.bot.send_typing(ctx.message.channel)
		with open('Resc/Playlists.json', 'r') as f:	
			self.playList = json.load(f)
		if(name not in self.playList.keys()):
			await self.bot.say("Playlist does not exists")
			return
		del self.playList[name]
		with open('Resc/Playlists.json', 'w') as f:
			json.dump(self.playList, f)
		await self.bot.say("Removed {}".format(name))
	
	@commands.command(pass_context = True)
	async def pause(self, ctx):
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say("The Bot isnt connected in this server!")
			return
		if not SP.player.is_playing():

			await self.bot.say('Nothing to pause!')
			return
		if SP.paused == True:
			await self.bot.say('Already paused!')
		SP.paused = True
		SP.player.pause()
		await self.bot.change_presence(game=discord.Game(name='Paused'))
	
	@commands.command(pass_context = True)
	async def resume(self, ctx):
		await self.bot.send_typing(ctx.message.channel)
		try:
			SP = self.serverPlayers[ctx.message.server.id]
		except:
			await self.bot.say('The bot isnt connected to this server!')
			return
		try:
			SP.player.is_playing
		except:
			await self.bot.say('Nothing to resume!')
			return
		if SP.paused == False:
			await self.bot.say('Nothing is paused!')
		SP.player.resume()
		SP.paused = False
		await self.bot.change_presence(game=discord.Game(name='{}'.format(SP.player.title)))
def setup(bot):
	bot.add_cog(MusicPlayer(bot))

	
