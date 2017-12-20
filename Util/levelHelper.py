from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from colorthief import ColorThief
import io
import requests

import aiohttp
import asyncio

from Util.PokemonJson import getImageFromName

IMAGESIZE = (600, 300)
# 575 by 400
DEFAULTIMAGE = "Resc/DefaultBackground.jpg"
DEFAULTAVATAR = "Resc/DefaultAvatar.png"

POKEBATTLE = "Resc/BackgroundPokebattle.png"



COLORS = {
	'normal' : (170, 168 ,121),
	'bug' : (168 , 183 , 38),
	'fighting' : (197 , 45 , 44),
	'ghost' : (113 , 88 , 147),
	'electric': (247 , 213 , 48),
	'flying': (170 , 146 , 237),
	'steel': (183, 185, 206),
	'psychic': (253 , 94 , 141),
	'poison': (164 , 63 , 163),
	'fire' : (239, 128, 50),
	'ice' : (152, 216, 216),
	'ground' : (224 , 195, 105),
	'water' : (103, 146, 240),
	'dragon' : (111, 59 , 234),
	'rock' : (184, 159, 56),
	'grass' : (122, 194, 82),
	'dark' : (110, 89, 72)
}

async def getLevelCard(player, avatar_url, toLevelUp):
	if "image" in player.keys():
		try:
			async with aiohttp.get(player['image']) as x:
				RawImage = io.BytesIO(await x.read())
				image = Image.open(RawImage).resize(IMAGESIZE, Image.ANTIALIAS)
				palette = ColorThief(RawImage).get_palette(color_count=4)
		except Exception as e:
			print(e)
			palette = ColorThief(DEFAULTIMAGE).get_palette(color_count=4)
			image = Image.open(DEFAULTIMAGE).resize(IMAGESIZE, Image.ANTIALIAS)
	else:
		palette = ColorThief(DEFAULTIMAGE).get_palette(color_count=4)
		image = Image.open(DEFAULTIMAGE).resize(IMAGESIZE, Image.ANTIALIAS)

	name_font = ImageFont.truetype("Resc/custom.ttf", 30)
	info_font = ImageFont.truetype("Resc/custom.ttf", 22)
	xp_font = ImageFont.truetype("Resc/custom.ttf", 20)
	rank_font = ImageFont.truetype("Resc/custom.ttf", 60)
	draw = ImageDraw.Draw(image, 'RGBA')


	if 'text_color' in player.keys():
		TextColor = tuple(player['text_color'])
	else:
		r, g, b = palette[1]
		r = 255 - r
		g = 255 - g
		b = 255 - b
		TextColor = (r, g, b)
		player['text_color'] = (r, g, b)

	if 'box_color' in player.keys():
		BoxColor = tuple(player['box_color'])
	else:
		BoxColor = palette[0]
		player['box_color'] = palette[1]

	if 'bar_color' in player.keys():
		XPColor = tuple(player['bar_color'])
	else:
		XPColor = palette[2]
		player['bar_color'] = palette[2]

	if 'title_color' in player.keys():
		TitleColor = tuple(player['title_color'])
	else:
		TitleColor = palette[3]
		player['title_color'] = palette[3]

	#PlayerData
	playerName = player['Name']
	level = player['Level']
	try:
		async with aiohttp.get(avatar_url) as x:
			# print(avatar_url)
			if "gif" in avatar_url:
				with open("image.gif", 'wb') as f:
					f.write(await x.read())
				temp = Image.open("image.gif")
				avatar = Image.new("RGBA", temp.size)
				avatar.paste(temp)
			else:
				avatar = Image.open(io.BytesIO(await x.read()))
	except Exception as e:
		print(e, type(e))
		avatar = Image.open(DEFAULTAVATAR)

	# fill=(TypeColor + tuple([80]))
	#TypeColor = (51, 51, 204)
	takedowns = player.get('Takedowns', 0)
	largestDamage = player.get('largest_damage', 0)
	pokedex =  round((len(player["Pokemon"]) - 1) / 721 * 100, 2)
	if toLevelUp[1] != None:
		xp = "XP: {:,} / {:,}".format(toLevelUp[0], toLevelUp[1])
	else:
		xp = "XP: {:,} / N/A".format(toLevelUp[0])
	prestige = Image.open("Resc/prestiges/normal.png")
	score = player.get('score', 0)
	rank = player.get('ranking', "--")

	#LargeBox & Line
	draw.rectangle([25,25,575,250], fill=(BoxColor + tuple([50])))
	draw.rectangle([35,60,565,61], fill=(0, 0, 0, 200))

	#Username
	draw.text((35, 30), playerName, TitleColor, name_font)

	#Level
	draw.text((490, 30), "Lv. {}".format(level), TitleColor, name_font)
	image.paste(prestige, (470, 40, 486, 55), prestige)

	#InfoBox
	draw.rectangle([200, 110, 565, 233], fill=(0, 0, 0, 80))
	draw.text((210, 120), "Boss Takedowns: {}\nLargest Damage: {:,}\nPokedex: {}%\nScore: {:,}".format(takedowns, largestDamage, pokedex, score), TextColor, info_font)

	draw.text((490, 120), "Rank", TextColor, name_font)
	w, h = draw.textsize("Rank", font=name_font)
	w2, h2 = draw.textsize(str(rank), font=rank_font)
	draw.text((494+ w/2 - w2/2, 145), "{}".format(rank), TextColor, rank_font)

	typeImage = Image.open('Resc/s_{}_en.png'.format(player['Type'].lower())).resize((64, 23))
	image.paste(typeImage, (210 + 285, 195 + 8, 274 + 285, 218 + 8), typeImage)


	#Avatar
	# 155 by 155
	avatarImage = avatar.resize((155, 155), Image.ANTIALIAS).convert('RGBA')

	bands = list(avatarImage.split())
	if len(bands) == 4:
	    # Assuming alpha is the last band
	    bands[3] = bands[3].point(lambda x: x*0.85)
	avatarImage = Image.merge(avatarImage.mode, bands)

	try:
		image.paste(avatarImage,(35, 78, 190, 233), avatarImage)
	except:
		print("ERROR")
		image.paste(avatarImage,(35, 78, 190, 233))

	#XP Bar
	draw.rectangle([200, 78, 565, 98], fill = (255, 255, 255, 120))
	if toLevelUp[1] != None:
		draw.rectangle([200, 78, 200 + int((565-200)*toLevelUp[0]/toLevelUp[1]), 98], fill=(XPColor + tuple([120])))
	else:
		draw.rectangle([200, 78, 200 + int((565-200)), 98], fill=(XPColor + tuple([120])))
	w, h = draw.textsize(xp, font=info_font)
	draw.text((200 + ((565-200) - w)/2, 78), xp, (20, 20, 20), xp_font)

	#Show Image
	#image.show()
	image.save("Resc/Output.png")
	return player

async def getRankingSheet(sorted_players):
	images = []
	for x in range(0, 3, 1):
		await getLevelCard(sorted_players[x][0], sorted_players[x][1], sorted_players[x][2])
		Image.open("Resc/Output.png").resize((300, 150), Image.ANTIALIAS).show()

