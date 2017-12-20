level = 100


Options = {
			"Large Rock" : {
				"Count" : (7 * (level - 5)) + 100, 
				"Value" : 0.00,
				"Flavor Text" : "A useless rock. Makes a good paper weight!",
				"Note" : ""
			},
			"Common TYPE Gem" : {
				"Count" : 175,
				"Value" : 0.12,
				"Flavor Text" : "A small gem worth a little experience. Its not really worth your time.",
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
				"Value" : 0.40, #### Change to 0.4 for drop table testing, and 0.1 for live
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


total_count = sum([Options[x]['Count'] for x in Options.keys()])

total_value = sum([(Options[x]['Value'] - 0.1) * Options[x]['Count'] for x in Options.keys()])


print("Lv - {}".format(level))
print("Total Drops in Table: {}\nAverage Value of a Drop: {}% Level Progress".format(total_count, round(total_value/total_count * 100, 2)))
#print(total_count, total_value)