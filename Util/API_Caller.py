from bs4 import BeautifulSoup
import requests
import random
import re
import urllib.request
import cgi

def Status():
	r = requests.get("http://limitlessmc.net/")
	soup = BeautifulSoup(r.text, "html.parser")
	val = soup.select("#serverstatus")
	return val[0].text

def wotd():
	packet = {}
	r = requests.get("https://www.merriam-webster.com/word-of-the-day")
	soup = BeautifulSoup(r.text, "html.parser")
	val = soup.select("div")
	soup = BeautifulSoup(str(val[44]), "html.parser")
	val = soup.select("span")
	packet['Day'] = val[0].text[11:]

def ForumPost(url : str, num = 0):
	r = requests.get(url)
	soup = BeautifulSoup(r.text, "html.parser")
	Side = soup.select("div.pull-left")
	val = soup.select("div.content")

	#mainclean = val[0].text

	text = str(val[num]).split('<br/>')
	text[num] = text[num].replace('<div class="content">', '')
	text[len(text)-1] = text[len(text)-1].replace('</div>', '')
	nText = []
	for l in text:
		nText.append(cleanLine(l))
	mainclean = '\n'.join(nText)


	clean = "**" + Side[2].text.replace("\n", '') + "**" + Side[3].text.replace('\t', '') + "------------------------------------" + "\n" + mainclean
	if(len(clean) > 1500):
		clean = clean[:1450] + "...\n------------------------------------\n*If you would like to read more, click the link below!*\n{}".format(url)


	#print(clean)
	return clean

def fmlText():
	r = requests.get("http://www.fmylife.com/random")
	soup = BeautifulSoup(r.text, "html.parser")
	val = soup.find_all(class_='block')[0]
	return val.text.replace("\n", '')

def MAL_anime_info(url):
	# I really wish the MAL API wasn't total trash, I really do. This is ugly. Don't mimic this code.

	# To ensure the link is safe to use, we need to make sure the link doesn't include the potentially-ascii-filled ending
	# A split link should look like this:
	# ['http:', '', ''myanimelist.net', 'anime', (some number), (some text)]
	split_url = url.split('/') 
	url = '/'.join(split_url[0:5]) # Up to, but not including, the 5th index (aka some text)

	indiv_output = [None] * 5
	page = urllib.request.urlopen(url)
	soup = BeautifulSoup(page.read().decode(), 'html.parser')

	indiv_output[0] = '**{}**'.format(soup.find('span', {'itemprop': 'name'}).text.strip())
	indiv_output[1] = 'Link: {}'.format(url)
	indiv_output[2] = '**Episodes**: {}'.format(soup.find('span', text='Episodes:').next_sibling.strip())
	indiv_output[3] = '**Status**: {}'.format(soup.find('span', text='Status:').next_sibling.strip())

	if indiv_output[3] != 'Not yet aired':
		rating_value = soup.find('span', {'itemprop': 'ratingValue'}).text.strip()
		rating_count = soup.find('span', {'itemprop': 'ratingCount'}).text.strip()
		indiv_output[4] = '**Rating**: {} (by {} users)'.format(rating_value, rating_count)
	else:
		indiv_output[4] = '**Rating**: None (unaired)'

	return indiv_output

def MAL_anime_search(query):
	indiv_output = [None] * 2
	query = cgi.escape(query.replace(' ','%20')).encode('ascii', 'xmlcharrefreplace')
	page = urllib.request.urlopen('http://myanimelist.net/anime.php?q={}'.format(query))
	soup = BeautifulSoup(page.read().decode(), 'html.parser')

	return soup.find_all('td', class_="bgColor0")[1].a

def cleanLine(line):
	print('cleaning')
	#print(line)
	if('<span style="font-weight: bold">' in line):
		line = line.replace('<span style="font-weight: bold">', '**')
		line = line.replace('</span>', '**')
		line.replace("\n", '')
		#line = "**" + line + "**\n"
	line = line.replace('<img alt=";)" src="./images/smilies/icon_e_wink.gif" title="Wink"/>', ';)')
	line = line.replace('<img alt=":(" src="./images/smilies/icon_e_sad.gif" title="Sad"/>', ':(')
	line = line.replace("<strong>", "**")
	line = line.replace("</strong>", "**")
	if('<a class="postlink" href="' in line):
		line = line.replace('<a class="postlink" href="', '')
		line = line.replace('</a>', '')
	return line

def youtube(input1:str):
	r = requests.get("https://www.youtube.com/results?sp=EgIQAVAU&search_query="+input1)
	songs = []
	soup = BeautifulSoup(r.text, "html.parser")
	for v in soup.find_all(class_='yt-lockup-title'):
		if len(v.find('a').get('href')) == 20:
			songs.append(v.find('a').get('href'))
	songs = songs[:18]
	return ['https://www.youtube.com' + song for song in songs]

def radio(startingURL):
	r = requests.get(startingURL)
	soup = BeautifulSoup(r.text, "html.parser")
	val = soup.find(class_='yt-pl-watch-queue-overlay')
	ListID = val.find('span').find('button').find('ul').find('li').get('data-list-id')
	mix = requests.get(startingURL + '&list={}'.format(ListID))
	mixsoup = BeautifulSoup(mix.text, "html.parser")
	FoundSongs = []
	for song in mixsoup.find(id = 'playlist-autoscroll-list').find_all(class_='yt-uix-scroller-scroll-unit'):
		FoundSongs.append(song.get('data-video-id'))
	return ['https://www.youtube.com/watch?v=' + x for x in FoundSongs[:10]]

def wouldYouRather():
	r = requests.get("http://either.io/")
	soup = BeautifulSoup(r.text, "html.parser")
	val = soup.select("span")
	return [(val[6].text, val[11].text) , (val[7].text, val[15].text)]

def getYoutubePlaylistSongs(playlistURL):
	r = requests.get(playlistURL)
	soup = BeautifulSoup(r.text, "html.parser")
	songs = []
	for val in soup.find_all(class_='pl-video yt-uix-tile '):
		songs.append(str(val['data-video-id']))
	return ['https://www.youtube.com/watch?v=' + song for song in songs]

# r = requests.get("https://www.merriam-webster.com/word-of-the-day")
# soup = BeautifulSoup(r.text, "html.parser")
# val = soup.select("div")
# #print(val[44])
# soup = BeautifulSoup(str(val[44]), "html.parser")
# val = soup.select("span")
# # #print(val[20])
# # m = re.search('href="/watch\?v=(.{11})"', str(val[20]))
# # print('https://www.youtube.com/watch?v=' + m.group(0)[15:-1])
# # count = 0
# # for v in val:
# # 	if count < 20:
# # 		try:
# # 			print(str(count), v.text)
# # 		except Exception as e:
# # 			print(e, "Error")
# # 	count += 1

# print(val[0].text[11:])

# packet = {}
# r = requests.get("https://www.merriam-webster.com/word-of-the-day")
# soup = BeautifulSoup(r.text, "html.parser")
# val = soup.select("div")

# soup2 = BeautifulSoup(str(val[44]), "html.parser")
# val2 = soup2.select("span")
# packet['Day'] = val2[0].text[11:-8]

# val3 = soup2.select("div")
# packet['Word'] = val3[4].text[1:-7]

# val4 = soup.select("p")
# packet['Defintion = ']
# count = 0
# for v in val4:
# 	if count < 20:
# 		try:
# 			print(str(count), v.text)
# 		except Exception as e:
# 			print(e, "Error")
# 	count += 1


# r = requests.get("http://either.io/")
# soup = BeautifulSoup(r.text, "html.parser")
# val = soup.select("span")
# count = 0
# for v in val:
# 	if count < 20:
# 		try:
# 			print(str(count), v.text)
# 		except Exception as e:
# 			print(e, "Error")
# 	count += 1

# print(val[6].text, val[11].text)
# print(val[7].text, val[15].text)


# for x in val3:
# 	print(x.text)
#print(val3)
#print(packet)


# print(val.text)
# while val[num].text == "Cacophony":
# 	num =+ 1
# 	try:
# 		print(val[num].text)
# 	except Exception:
# 		print("ERROR")

# f = open(val[23].text.strip(), 'r')
# print(f.read())




########### Getting Pictures #########################
# r = requests.get("http://pokemondb.net/pokedex/national")
# soup = BeautifulSoup(r.text, "html.parser")
# val = soup.select(".infocard-tall")



# name = "Venusaur"

# #print(val[ID(name) - 1]['class'])
# val2 = val[ID(name) - 1].select("a")
# count = 0
# print(val2[0]["data-sprite"])