import discord
import time
from discord.ext import commands
from subprocess import Popen
import asyncio
import json

EXTENTIONS = ['Modules.StaffCmds', 'Modules.Interaction', 'Modules.Music', 'Modules.Games']

def isStaff(ctx):
	if ctx.message.author.server_permissions.administrator or ctx.message.author.id == '134441036905840640':
		return True
	return False

class StaffCmds:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context = True)
	async def mute(self, ctx, member : str):
	    if not isStaff(ctx):
	        return
	    overwrite = discord.PermissionOverwrite()
	    overwrite.send_messages = False
	    try:
	    	await self.bot.edit_channel_permissions(ctx.message.channel, ctx.message.server.get_member_named(member), overwrite);
	    except Exception as e:
	    	await self.bot.say("Something went Wrong: {}".format(type(e).__name__))
	    	return
	    await self.bot.say("Muted {}".format(member))

	@commands.command(pass_context = True)
	async def unmute(self, ctx, member : str):
	    if not isStaff(ctx):
	        return
	    overwrite = discord.PermissionOverwrite()
	    overwrite.send_messages = True
	    try:
	    	await self.bot.edit_channel_permissions(ctx.message.channel, ctx.message.server.get_member_named(member), overwrite);
	    except Exception as e:
	    	await self.bot.say("Something went Wrong: {}".format(type(e).__name__))
	    	return

	    await self.bot.say("Unmuted {}".format(member))

	@commands.command(pass_context = True)
	async def tempmute(self, ctx, member : str, timeToMute : int):
	    if not isStaff(ctx):
	        return
	    overwrite = discord.PermissionOverwrite()
	    overwrite.send_messages = False
	    try:
	    	await self.bot.edit_channel_permissions(ctx.message.channel, ctx.message.server.get_member_named(member), overwrite);
	    except Exception as e:
	   		await self.bot.say("Something went Wrong: {}".format(type(e).__name__))
	   		return
	    await self.bot.say("Muted {}".format(member))

	    await asyncio.sleep(timeToMute)

	    overwrite = discord.PermissionOverwrite()
	    overwrite.send_messages = True
	    try:
	    	await self.bot.edit_channel_permissions(ctx.message.channel, ctx.message.server.get_member_named(member), overwrite);
	    except Exception as e:
	    	await self.bot.say("Something went Wrong: {}".format(type(e).__name__))
	    	return
	    await self.bot.say("Unmuted {}".format(member))

	@commands.command(pass_context = True)
	async def mutelist(self, ctx):
		channel = ctx.message.channel
		mutedList = []
		for x in channel.server.members:
			if(x.permissions_in(channel).send_messages == False):
				mutedList.append(x.name)
		if len(mutedList) != 0:
			await self.bot.say("Muted Players in this Channel...")
			await self.bot.say(", ".join(mutedList))
		else:
			await self.bot.say("No One is Muted in this Channel!")

	@commands.command(pass_context = True)
	async def unmuteall(self,ctx):
	    'Unmutes ALL muted players'
	    if not isStaff(ctx):
	        return
	    channel = ctx.message.channel
	    mutedList = []
	    for x in channel.server.members:
	        if(x.permissions_in(channel).send_messages == False):
	            mutedList.append(x.name)

	    overwrite = discord.PermissionOverwrite()
	    overwrite.send_messages = True
	    try:
	        for player in mutedList:
	            await self.bot.edit_channel_permissions(ctx.message.channel, ctx.message.server.get_member_named(player), overwrite);
	    except Exception as e:
	        await self.bot.say("Something went Wrong")
	        return
	    await self.bot.say("Unmuting all players...")

	@commands.command(pass_context = True)
	async def stoggle(self, ctx, command_name = None):
	    "Allows you to toggle command usage for servers"
	    if not isStaff(ctx):
	        return
	    with open("Resc/Toggled_Commands.json", 'r') as f:
	        Toggle = json.load(f)

	    if command_name == "toggle" or command_name == "status":
	        await self.bot.say("I'm sorry, you can't disable this command!")
	        return

	    Server = Toggle.get(ctx.message.server.id, [])

	    if command_name == None:
	        await self.bot.say("The following commands/features are disabled:\n{}".format(", ".join(Server)))
	        return

	    if command_name in Server:
	        Server.remove(command_name.lower())
	    else:
	        Server.append(command_name.lower())

	    Toggle[ctx.message.server.id] = Server

	    await self.bot.say("`{}` is now {} SERVER-WIDE".format(command_name, "Enabled" if command_name not in Server else "Disabled"))

	    with open("Resc/Toggled_Commands.json", 'w') as f:
	        json.dump(Toggle, f, indent = 4)

	@commands.command(pass_context = True)
	async def ctoggle(self, ctx, command_name = None):
	    "Allows you to toggle command usage for channels"
	    if not isStaff(ctx):
	        return
	    with open("Resc/Toggled_Commands.json", 'r') as f:
	        Toggle = json.load(f)

	    if command_name == "toggle":
	        await self.bot.say("I'm sorry, you can't disable this command!")
	        return

	    Channel = Toggle.get(ctx.message.channel.id, [])

	    if command_name == None:
	        await self.bot.say("The following commands/features are disabled:\n{}".format(", ".join(Channel)))
	        return

	    if command_name in Channel:
	        Channel.remove(command_name.lower())
	    else:
	        Channel.append(command_name.lower())

	    Toggle[ctx.message.channel.id] = Channel

	    await self.bot.say("`{}` is now {} CHANNEL-WIDE".format(command_name, "Enabled" if command_name not in Channel else "Disabled"))

	    with open("Resc/Toggled_Commands.json", 'w') as f:
	        json.dump(Toggle, f, indent = 4)

def setup(bot):
	bot.add_cog(StaffCmds(bot))