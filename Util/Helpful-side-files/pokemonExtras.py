import requests
import json
List = []
First = []
Second = []
Third = []
for x in range(1, 366, 1):
	entry = []
	r = requests.get("http://pokeapi.co/api/v2/evolution-chain/"+str(x))
	Json = r.json()
	if 'chain' not in Json:
		continue
	Json = Json["chain"]
	entry.append(Json['species']['name'])
	Json = Json['evolves_to']
	while len(Json) is not 0:
		Json = Json[0]
		entry.append(Json['species']['name'])
		Json = Json['evolves_to']
	List.append((entry))

print("Finished Creating List")

for entry in List:
	if len(entry) >= 2:
		First.append(entry[0])
		Second.append(entry[1])
	if len(entry) >= 3:
		Third.append(entry[2])

print("Finished Creating Sub-List")

with open('EvoChains.txt', 'w') as f:
	f.write("")

with open('EvoChains.txt', 'a') as f:
	for entry in List:
		f.write("{}\n".format(", ".join(entry)))

with open('first.txt' ,'w') as f:
	f.write('\n'.join(First))

with open('second.txt' ,'w') as f:
	f.write('\n'.join(Second))

with open('third.txt' ,'w') as f:
	f.write('\n'.join(Third))