import random
import discord
import asyncio
import time
import ewcfg
import ewutils
import ewitem
import ewleaderboard

from ewmarket import EwMarket
from ew import EwUser
from ewitem import EwItem
from ewcasino import check

class EwFisher:
	fishing = False
	bite = False
	current_fish = ""
	current_size = ""
	pier = ""
	bait = False
	slime_type = ""
	rod_type = ""

fishers = {}
current_tourney = []
tourney = False

class EwOffer:
	id_server = ""
	id_user = ""
	offer_give = 0
	offer_receive = ""
	time_sinceoffer = 0

	def __init__(
		self,
		id_server = None,
		id_user = None,
		offer_give = None,

	):
		if id_server is not None and id_user is not None and offer_give is not None:
			self.id_server = id_server
			self.id_user = id_user
			self.offer_give = offer_give

			data = ewutils.execute_sql_query(
				"SELECT {time_sinceoffer} FROM offers WHERE id_server = %s AND id_user = %s AND {col_offer_give} = %s".format(
					time_sinceoffer = ewcfg.col_time_sinceoffer,
					col_offer_give = ewcfg.col_offer_give,
				), (
					id_server,
					id_user,
					offer_give,
				)
			)

			if len(data) > 0:  # if data is not empty, i.e. it found an entry
				# data is always a two-dimensional array and if we only fetch one row, we have to type data[0][x]
				self.time_sinceoffer = data[0][0]

			data = ewutils.execute_sql_query(
				"SELECT {col_offer_receive} FROM offers WHERE id_server = %s AND id_user = %s AND {col_offer_give} = %s".format(
					col_offer_receive = ewcfg.col_offer_receive,
					col_offer_give = ewcfg.col_offer_give,
				), (
					id_server,
					id_user,
					offer_give,
				)
			)

			if len(data) > 0:  # if data is not empty, i.e. it found an entry
				# data is always a two-dimensional array and if we only fetch one row, we have to type data[0][x]
				self.offer_receive = data[0][0]

			else:  # create new entry
				ewutils.execute_sql_query(
					"REPLACE INTO offers(id_server, id_user, {col_offer_give}) VALUES (%s, %s, %s)".format(
						col_offer_give = ewcfg.col_offer_give,
					), (
						id_server,
						id_user,
						offer_give,
					)
				)

	def persist(self):
		ewutils.execute_sql_query(
			"REPLACE INTO offers(id_server, id_user, {col_offer_give}, {col_offer_receive}, {col_time_sinceoffer}) VALUES (%s, %s, %s, %s, %s)".format(
				col_offer_give = ewcfg.col_offer_give,
				col_offer_receive = ewcfg.col_offer_receive,
				col_time_sinceoffer = ewcfg.col_time_sinceoffer
			), (
				self.id_server,
				self.id_user,
				self.offer_give,
				self.offer_receive,
				self.time_sinceoffer
			)
		)

	def deal(self):
		ewutils.execute_sql_query("DELETE FROM offers WHERE {id_user} = %s AND {id_server} = %s AND {col_offer_give} = %s".format(
			id_user = ewcfg.col_id_user,
			id_server = ewcfg.col_id_server,
			col_offer_give = ewcfg.col_offer_give,
		),(
			self.id_user,
			self.id_server,
			self.offer_give
		))

class EwTourneyEntry:
	id_server = ""
	id_user = ""
	id_tourney = 0
	id_fish = ""
	float_size = 0
	rank_int = 0

	def __init__(
			self,
			id_server = None,
			id_user = None,
			id_tourney = None,
			id_fish = None,
			float_size = None,
			rank_int = None,
	):

		if id_server is not None and id_user is not None and id_tourney is not None and id_fish is not None and float_size is not None:
			self.id_server = id_server
			self.id_user = id_user
			self.id_tourney = id_tourney
			self.id_fish = id_fish
			self.float_size = float_size
			self.rank_int = rank_int

			data = ewutils.execute_sql_query(
				"SELECT {}, {}, {}, {}, {}, {} FROM tourney_entries WHERE id_server = %s AND id_user = %s".format(
					ewcfg.col_id_server,
					ewcfg.col_id_user,
					ewcfg.col_id_tourney,
					ewcfg.col_id_fish,
					ewcfg.col_float_size,
					ewcfg.col_rank_int,
				), (
					id_server,
					id_user,
				)
			)

	def persist(self):
		ewutils.execute_sql_query(
			"REPLACE INTO tourney_entries(id_server, id_user, {col_id_tourney}, {col_id_fish}, {col_float_size}, {col_rank_int}) VALUES (%s, %s, %s, %s, %s, %s)".format(
				col_id_tourney = ewcfg.col_id_tourney,
				col_id_fish = ewcfg.col_id_fish,
				col_float_size = ewcfg.col_float_size,
				col_rank_int = ewcfg.col_rank_int,
			), (
				self.id_server,
				self.id_user,
				self.id_tourney,
				self.id_fish,
				self.float_size,
				self.rank_int
			)
		)

class EwFish:
	# A unique name for the fish. This is used in the database and typed by users, so it should be one word, all lowercase letters.
	id_fish = ""

	# A list of alternative names.
	alias = []

	# Name of the fish.
	str_name = ""

	# Size of fish. Only assigned upon generation.
	size = ""

	# How rare a fish species is.
	rarity = ""

	# When it can be caught.
	catch_time = None

	# What weather the fish can be exclusively caught in.
	catch_weather = None

	# Description of the fish.
	str_desc = ""

	# What type of slime it exclusively resides in. None means both.
	slime = None

	# List of the vendors selling this item. (This will basically exclusively be none.)
	vendors = []

	def __init__(
			self,
			id_fish = "",
			str_name = "",
			size = "",
			rarity = "",
			catch_time = None,
			catch_weather = None,
			str_desc = "",
			slime = None,
			vendors = []
	):
		self.id_fish = id_fish
		self.str_name = str_name
		self.size = size
		self.rarity = rarity
		self.catch_time = catch_time
		self.catch_weather = catch_weather
		self.str_desc = str_desc
		self.slime = slime
		self.vendors = vendors


# Randomly generates a fish.
def gen_fish(x, cmd, fishingrod):
	fish_pool = []

	if fishingrod != "":
		has_fishingrod = True

	rarity_number = random.randint(0, 100)

	if has_fishingrod == True:
		if rarity_number >= 0 and rarity_number < 21:  # 20%
			fish = "item"
			return fish

		elif rarity_number >= 21 and rarity_number < 31:  # 10%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_common:
					fish_pool.append(fish)

		elif rarity_number >= 31 and rarity_number < 71:  # 40%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_uncommon:
					fish_pool.append(fish)

		elif rarity_number >= 71 and rarity_number < 91:  # 20%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_rare:
					fish_pool.append(fish)
		else:  # 10%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_promo:
					fish_pool.append(fish)

	else:
		if rarity_number >= 0 and rarity_number < 11: # 10%
			if fishingrod != 'poudrinoff':
				fish = "item"
				return fish
			else:
				rarity_number += 11

		elif rarity_number >= 11 and rarity_number < 61: # 50%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_common:
					fish_pool.append(fish)

		elif rarity_number >= 61 and rarity_number < 91: # 30%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_uncommon:
					fish_pool.append(fish)

		elif rarity_number >= 91 and rarity_number < 100: # 9%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_rare:
					fish_pool.append(fish)
		else: # 1%
			for fish in ewcfg.fish_names:
				if ewcfg.fish_map[fish].rarity == ewcfg.fish_rarity_promo:
					fish_pool.append(fish)

	market_data = x #todo ?
	weather_data = ewcfg.weather_map.get(market_data.weather)

	if weather_data.name != "rainy":
		for fish in fish_pool:
			if ewcfg.fish_map[fish].catch_time == ewcfg.fish_catchtime_rain:
				fish_pool.remove(fish)

	if market_data.clock < 20 or market_data.clock > 5:
		for fish in fish_pool:
			if ewcfg.fish_map[fish].catch_time == ewcfg.fish_catchtime_night:
				fish_pool.remove(fish)
	elif market_data.clock < 8 or market_data.clock > 17:
		for fish in fish_pool:
			if ewcfg.fish_map[fish].catch_time == ewcfg.fish_catchtime_day:
				fish_pool.remove(fish)
	else:
		for fish in fish_pool:
			if ewcfg.fish_map[fish].catch_time != None:
				fish_pool.remove(fish)

	if cmd.message.channel.name in ["slimes-end-pier", "ferry"]:
		for fish in fish_pool:
			if ewcfg.fish_map[fish].slime == ewcfg.fish_slime_freshwater:
				fish_pool.remove(fish)

	elif cmd.message.channel.name in ["jaywalker-plain-pier", "little-chernobyl-pier"]:
		for fish in fish_pool:
			if ewcfg.fish_map[fish].slime == ewcfg.fish_slime_saltwater:
				fish_pool.remove(fish)

	fish = random.choice(fish_pool)

	if fishingrod == "poudrinlover":
		fish = "item"

	elif fishingrod == "thejunker":
		fish = "weapon"

	return fish

# Determines the size of the fish
def gen_fish_size(has_fishingrod):
	size_number = random.randint(0, 100)

	if has_fishingrod == True:
		if size_number >= 0 and size_number < 6:  # 5%
			size = ewcfg.fish_size_miniscule
		elif size_number >= 6 and size_number < 11:  # 5%
			size = ewcfg.fish_size_small
		elif size_number >= 11 and size_number < 31:  # 20%
			size = ewcfg.fish_size_average
		elif size_number >= 31 and size_number < 71:  # 40%
			size = ewcfg.fish_size_big
		elif size_number >= 71 and size_number < 91:  # 20
			size = ewcfg.fish_size_huge
		else:  # 10%
			size = ewcfg.fish_size_colossal

	else:
		if size_number >= 0 and size_number < 6:  # 5%
			size = ewcfg.fish_size_miniscule
		elif size_number >= 6 and size_number < 21:  # 15%
			size = ewcfg.fish_size_small
		elif size_number >= 21 and size_number < 71:  # 50%
			size = ewcfg.fish_size_average
		elif size_number >= 71 and size_number < 86:  # 15%
			size = ewcfg.fish_size_big
		elif size_number >= 86 and size_number < 100:  # 4
			size = ewcfg.fish_size_huge
		else:  # 1%
			size = ewcfg.fish_size_colossal

	return size

# Determines bite text
def gen_bite_text(size):
	if size == "item":
		text = "You feel a distinctly inanimate tug at your fishing pole!"

	elif size == ewcfg.fish_size_miniscule:
		text = "You feel a wimpy tug at your fishing pole!"
	elif size == ewcfg.fish_size_small:
		text = "You feel a mediocre tug at your fishing pole!"
	elif size == ewcfg.fish_size_average:
		text = "You feel a modest tug at your fishing pole!"
	elif size == ewcfg.fish_size_big:
		text = "You feel a mildly threatening tug at your fishing pole!"
	elif size == ewcfg.fish_size_huge:
		text = "You feel a startlingly strong tug at your fishing pole!"
	else:
		text = "You feel a tug at your fishing pole so intense that you nearly get swept off your feet!"

	text += " **!REEL NOW!!!!!**"
	return text

""" Casts a line into the Slime Sea """
async def cast(cmd):
	has_reeled = False
	user_data = EwUser(member = cmd.message.author)
	market_data = EwMarket(id_server = cmd.message.author.server.id)

	if cmd.message.author.id not in fishers.keys():
		fishers[cmd.message.author.id] = EwFisher()

	fisher = fishers[cmd.message.author.id]

	# Ghosts cannot fish.
	if user_data.life_state == ewcfg.life_state_corpse:
		response = "You can't fish while you're dead. Try {}.".format(ewcfg.cmd_revive)

	# Players who are already cast a line cannot cast another one.
	elif fisher.fishing == True:
		response = "You've already cast a line."

	# Only fish at The Pier
	elif cmd.message.channel.name in [ewcfg.channel_tt_pier, ewcfg.channel_jp_pier, ewcfg.channel_cl_pier, ewcfg.channel_afb_pier, ewcfg.channel_vc_pier, ewcfg.channel_se_pier, ewcfg.channel_ferry]:
		if user_data.hunger >= ewutils.hunger_max_bylevel(user_data.slimelevel):
			response = "You're too hungry to fish right now."

		else:
			has_fishingrod = False

			if user_data.weapon >= 0:
				weapon_item = EwItem(id_item = user_data.weapon)
				weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))
				if weapon.id_weapon in ["fishingrod", "fishpick", "portalhook", "poudrinlover", "gamblersdelight", "thesmoker", "poudrinlover", "thejunker", "stickpole", "ultrarod", "thefreezer"]:
					has_fishingrod = True
					fisher.rod_type = weapon.id_weapon

			fisher.current_fish = gen_fish(market_data, cmd, has_fishingrod)
			fisher.fishing = True
			fisher.bait = False
			fisher.pier = user_data.poi
			if cmd.message.channel.name in [ewcfg.channel_afb_pier, ewcfg.channel_vc_pier, ewcfg.channel_se_pier, ewcfg.channel_ferry]:
				fisher.slime_type = "salt"
			else:
				fisher.slime_type = "fresh"
			item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
			author = cmd.message.author
			server = cmd.message.server

			item_sought = ewitem.find_item(item_search = item_search, id_user = author.id, id_server = server.id)

			if item_sought:
				item = EwItem(id_item = item_sought.get('id_item'))

				if item.item_type == ewcfg.it_food and item.item_props["acquisition"] != ewcfg.acquisition_fishing:

					str_name = item.item_props['food_name']
					fisher.bait = True

					if item in ewcfg.plebe_bait:
						fisher.current_fish = "plebefish"

					elif item == "doublestuffedcrust":
						if random.randrange(5) == 3:
							fisher.current_fish = "doublestuffedflounder"

					elif item in ["chickenbucket", "familymeal"]:
						if random.randrange(5) == 3:
							fisher.current_fish = "seacolonel"

					elif item in ["steakvolcanoquesomachorito", "nachosupreme"]:
						if random.randrange(5) == 3:
							fisher.current_fish = "marlinsupreme"

					elif item in ["blacklimes", "blacklimesour"]:
						if random.randrange(2) == 1:
							fisher.current_fish = "blacklimesalmon"

					elif item in ["pinkrowddishes", "pinkrowdatouille"]:
						if random.randrange(2) == 1:
							fisher.current_fish = "thrash"

					elif item in ["purplekilliflowercrustpizza", "purplekilliflower"]:
						if random.randrange(2) == 1:
							fisher.current_fish = "dab"

					elif item == "kingpincrab":
						if random.randrange(5) == 1:
							fisher.current_fish = "kingpincrab"

					elif float(item.time_expir if item.time_expir is not None else 0) < time.time():
						if random.randrange(2) == 1:
							fisher.current_fish = "plebefish"
					ewitem.item_delete(item_sought.get('id_item'))

			if fisher.current_fish == "item":
				fisher.current_size = "item"

			else:
				fisher.current_size = gen_fish_size(has_fishingrod)

			if fisher.bait == False:
				response = "You cast your fishing line into the "
			else:
				response = "You attach your {} to the hook as bait and then cast your fishing line into the ".format(str_name)


			if fisher.slime_type == "salt":
				response += "vast Slime Sea."
			else:
				response += "glowing Slime Lake."

			user_data.hunger += ewcfg.hunger_perfish * ewutils.hunger_cost_mod(user_data.slimelevel)
			user_data.persist()
			
			await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	
			bite_text = gen_bite_text(fisher.current_size)
			
			# User has a 1/10 chance to get a bite
			fun = 10

			if fisher.bait == True:
				# Bait attatched, user has a 1/7 chance to get a bite
				fun = 7
			bun = 0

			while not ewutils.TERMINATE:
				
				if fun <= 0:
					fun = 1
				else:
					damp = random.randrange(fun)
					
				timer = 0
				while timer <= 60:
					await asyncio.sleep(1)
					user_data = EwUser(member = cmd.message.author)

					if user_data.poi != fisher.pier:
						fisher.fishing = False
						return
					if user_data.life_state == ewcfg.life_state_corpse:
						fisher.fishing = False
						return
					if fisher.fishing == False:
						return
					timer += 1
				if damp > 10:
					await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, random.choice(ewcfg.nobite_text)))
					fun -= 2
					bun += 1
					if bun >= 5:
						fun -= 1
					if bun >= 7:
						fun -= 2
					if bun >= 9:
						fun -= 2
					continue
				elif fisher.rod_type == "stickpole":
					continue
				else:
					break


			fisher.bite = True
			await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, bite_text))

			await asyncio.sleep(8)

			if fisher.bite != False:
				fisher.fishing = False
				fisher.bite = False
				fisher.current_fish = ""
				fisher.current_size = ""
				fisher.bait = False
				fisher.slime_type = ""
				if fisher.rod_type == "gamblersdelight":
					user_data.id_killer = cmd.message.author.id
					user_data.die(cause=ewcfg.cause_suicide)
					user_data.persist()
				return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "The fish got away..."))
			else:
				has_reeled = True

	else:
		response = "You can't fish here. Go to a pier."
	
	# Don't send out a response if the user actually reeled in a fish, since that gets sent by the reel command instead.
	if has_reeled == False:
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
		


""" Reels in the fishing line.. """
async def reel(cmd):
	user_data = EwUser(member = cmd.message.author)
	if cmd.message.author.id not in fishers.keys():
		fishers[cmd.message.author.id] = EwFisher()
	fisher = fishers[cmd.message.author.id]
	market = EwMarket(id_server=cmd.message.author.server.id)
	day = market.day

	# Ghosts cannot fish.
	if user_data.life_state == ewcfg.life_state_corpse:
		response = "You can't fish while you're dead. Try {}.".format(ewcfg.cmd_revive)

	elif cmd.message.channel.name in [ewcfg.channel_tt_pier, ewcfg.channel_jp_pier, ewcfg.channel_cl_pier, ewcfg.channel_afb_pier, ewcfg.channel_vc_pier, ewcfg.channel_se_pier, ewcfg.channel_ferry]:
		# Players who haven't cast a line cannot reel.
		if fisher.fishing == False:
			response = "You haven't cast your hook yet. Try !cast."

		# If a fish isn't biting, then a player reels in nothing.
		elif fisher.bite == False and fisher.fishing == True:
			fisher.current_fish = ""
			fisher.current_size = ""
			fisher.fishing = False
			fisher.pier = ""
			response = "You reeled in too early! Nothing was caught."

		# On successful reel.
		else:
			if fisher.current_fish == "item":
				item = random.choice(ewcfg.mine_results)

				weapon_choices = []

				if fisher.rod_type == "thejunker":
					for weapon in ewcfg.weapon_list:
						if weapon.acquisition == ewcfg.acquisition_dojo:
							weapon_choices.append(weapon)
					item = random.choice(weapon_choices)



				unearthed_item_amount = 1 if random.randint(1, 3) != 1 else 2  # 33% chance of extra drop

				item_props = ewitem.gen_item_props(item)

				for creation in range(unearthed_item_amount):
					ewitem.item_create(
						item_type = item.item_type,
						id_user = cmd.message.author.id,
						id_server = cmd.message.server.id,
						item_props = item_props
					),

				if unearthed_item_amount == 1:
					response = "You reel in a {}!".format(item.str_name)
				else:
					response = "You reel in two {}s!".format(item.str_name)

				fisher.fishing = False
				fisher.bite = False
				fisher.current_fish = ""
				fisher.current_size = ""
				fisher.pier = ""
				user_data.persist()

			else:
				user_initial_level = user_data.slimelevel

				gang_bonus = False

				has_fishingrod = False

				if user_data.weapon >= 0:
					weapon_item = EwItem(id_item = user_data.weapon)
					weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))
					if weapon.id_weapon == "fishingrod":
						has_fishingrod = True

				value = 0

				if fisher.rod_type != 'ultrarod':
					if fisher.current_size == ewcfg.fish_size_miniscule:
						slime_gain = ewcfg.fish_gain * 1
						value += 10

					elif fisher.current_size == ewcfg.fish_size_small:
						slime_gain = ewcfg.fish_gain * 2

						value += 20

					elif fisher.current_size == ewcfg.fish_size_average:
						slime_gain = ewcfg.fish_gain * 3
						value += 30

					elif fisher.current_size == ewcfg.fish_size_big:
						slime_gain = ewcfg.fish_gain * 4
						value += 40

					elif fisher.current_size == ewcfg.fish_size_huge:
						slime_gain = ewcfg.fish_gain * 5
						value += 50

					else:
						slime_gain = ewcfg.fish_gain * 6
						value += 60

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_common:
						value += 10

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_uncommon:
						value += 20

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_rare:
						value += 30

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_promo:
						value += 40
				else:
					if fisher.current_size == ewcfg.fish_size_miniscule:
						value += 10

					elif fisher.current_size == ewcfg.fish_size_small:

						value += 20

					elif fisher.current_size == ewcfg.fish_size_average:
						value += 30

					elif fisher.current_size == ewcfg.fish_size_big:
						value += 40

					elif fisher.current_size == ewcfg.fish_size_huge:
						value += 50

					else:
						value += 60

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_common:
						slime_gain = ewcfg.fish_gain * 3
						value += 10

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_uncommon:
						slime_gain = ewcfg.fish_gain * 4
						value += 20

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_rare:
						slime_gain = ewcfg.fish_gain * 7
						value += 30

					if ewcfg.fish_map[fisher.current_fish].rarity == ewcfg.fish_rarity_promo:
						slime_gain = ewcfg.fish_gain * 10
						value += 40

				if user_data.life_state == 2:
					if ewcfg.fish_map[fisher.current_fish].catch_time == ewcfg.fish_catchtime_day and user_data.faction == ewcfg.faction_rowdys:
						gang_bonus = True
						slime_gain = slime_gain * 1.5
						value += 20

					if ewcfg.fish_map[fisher.current_fish].catch_time == ewcfg.fish_catchtime_night and user_data.faction == ewcfg.faction_killers:
						gang_bonus = True
						slime_gain = slime_gain * 1.5
						value += 20

				if has_fishingrod == True:
					slime_gain = slime_gain * 2
				if fisher.rod_type == "gamblersdelight":
					slime_gain = slime_gain * 5

				float_size = gen_size_int(fisher.current_size, ewcfg.fish_map[fisher.current_fish].rarity)
				if fisher.rod_type == "thefreezer":
					time_expir = time.time() + ewcfg.farm_food_expir
				else:
					time_expir = time.time() + ewcfg.std_food_expir

				if fisher.rod_type != "thesmoker":
					if fisher.rod_type == "portalhook":
						current_fishes = user_data.get_stored_fish()
						if user_data.fish_space != current_fishes:
							id_user = ewcfg.tank_poi+cmd.message.author.id
						else:
							id_user = cmd.message.author.id
					else:
						id_user = cmd.message.author.id
					ewitem.item_create(
						id_user = id_user,
						id_server = cmd.message.server.id,
						item_type = ewcfg.it_food,
						item_props = {
							'id_food': ewcfg.fish_map[fisher.current_fish].id_fish,
							'food_name': ewcfg.fish_map[fisher.current_fish].str_name,
							'food_desc': ewcfg.fish_map[fisher.current_fish].str_desc+" Caught on day {}.".format(day),
							'recover_hunger': 20,
							'str_eat': ewcfg.str_eat_raw_material.format(ewcfg.fish_map[fisher.current_fish].str_name),
							'rarity': ewcfg.fish_map[fisher.current_fish].rarity,
							'float_size': float_size,
							'size': fisher.current_size,
							'time_expir': time_expir,
							'acquisition': ewcfg.acquisition_fishing,
							'value': value,
							'date_caught': day,
							'measured': False
						}
					)
				else:
					size = ewcfg.fish_map[fisher.current_fish].size
					if size == ewcfg.fish_size_miniscule:
						hunger_multiplier = 1
					elif size == ewcfg.fish_size_small:
						hunger_multiplier = 2
					elif size == ewcfg.fish_size_average:
						hunger_multiplier = 3
					elif size == ewcfg.fish_size_big:
						hunger_multiplier = 4
					elif size == ewcfg.fish_size_huge:
						hunger_multiplier = 5
					elif size == ewcfg.fish_size_colossal:
						hunger_multiplier = 6
					ewitem.item_create(
						id_user=cmd.message.author.id,
						id_server=cmd.message.server.id,
						item_type=ewcfg.it_food,
						item_props={
							'id_food': "grilled{}".format(ewcfg.fish_map[fisher.current_fish].id_fish),
							'food_name': "grilled {}".format(ewcfg.fish_map[fisher.current_fish].str_name),
							'food_desc': "Some delicious looking grilled {}.".format(ewcfg.fish_map[fisher.current_fish].str_name),
							'recover_hunger': ewcfg.base_grill_hunger * hunger_multiplier,
							'str_eat': ewcfg.grill_str_eat.format(size, ewcfg.fish_map[fisher.current_fish].str_name),
							'time_expir': time.time() + ewcfg.std_food_expir,
							'acquisition': ewcfg.acquisition_grilling,
						}
					)

				response = "You reel in a {fish}! {flavor} You grab hold and wring {slime} slime from it. also its {size}"\
					.format(fish = ewcfg.fish_map[fisher.current_fish].str_name, flavor = ewcfg.fish_map[fisher.current_fish].str_desc, slime = str(slime_gain), size = str(float_size))

				if gang_bonus:
					if user_data.faction == ewcfg.faction_rowdys:
						response += "The Rowdy-pride this fish is showing gave you more slime than usual. "
					elif user_data.faction == ewcfg.faction_killers:
						response += "The Killer-pride this fish is showing gave you more slime than usual. "

				levelup_response = user_data.change_slimes(n = slime_gain, source = ewcfg.source_fishing)

				was_levelup = True if user_initial_level < user_data.slimelevel else False

				# Tell the player their slime level increased.
				if was_levelup:
					response += levelup_response

				fisher.fishing = False
				fisher.bite = False
				fisher.current_fish = ""
				fisher.current_size = ""
				fisher.pier = ""
				user_data.persist()
	else:
		response = "You cast your fishing rod unto a sidewalk. That is to say, you've accomplished nothing. Go to a pier if you want to fish."

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def gen_size_int(size, rarity):
	if rarity == ewcfg.fish_rarity_common:
		rarity_multiplier = 1
	elif rarity == ewcfg.fish_rarity_uncommon:
		rarity_multiplier = 1.3
	elif rarity == ewcfg.fish_rarity_rare:
		rarity_multiplier = 1.6
	else:
		rarity_multiplier = 1.9

	if size == ewcfg.fish_size_miniscule:
		size_int = 0
		size_int += (random.randint(1, 5) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 5) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 5) * rarity_multiplier) / 100
		size_int += (random.randint(1, 5) * rarity_multiplier) / 10
		size_int += (random.randint(1, 5) * rarity_multiplier) / 1
	elif size == ewcfg.fish_size_small:
		size_int = 10
		size_int += (random.randint(1, 5) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 5) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 5) * rarity_multiplier) / 100
		size_int += (random.randint(1, 5) * rarity_multiplier) / 10
		size_int += (random.randint(1, 5) * rarity_multiplier) / 1
	elif size == ewcfg.fish_size_average:
		size_int = 20
		size_int += (random.randint(1, 10) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 10) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 10) * rarity_multiplier) / 100
		size_int += (random.randint(1, 10) * rarity_multiplier) / 10
		size_int += (random.randint(1, 10) * rarity_multiplier) / 1
	elif size == ewcfg.fish_size_big:
		size_int = 40
		size_int += (random.randint(1, 20) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 20) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 20) * rarity_multiplier) / 100
		size_int += (random.randint(1, 20) * rarity_multiplier) / 10
		size_int += (random.randint(1, 20) * rarity_multiplier) / 1
	elif size == ewcfg.fish_size_huge:
		size_int = 80
		size_int += (random.randint(1, 40) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 40) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 40) * rarity_multiplier) / 100
		size_int += (random.randint(1, 40) * rarity_multiplier) / 10
		size_int += (random.randint(1, 40) * rarity_multiplier) / 1
	else:
		size_int = 160
		size_int += (random.randint(1, 80) * rarity_multiplier) / 10000
		size_int += (random.randint(1, 80) * rarity_multiplier) / 1000
		size_int += (random.randint(1, 80) * rarity_multiplier) / 100
		size_int += (random.randint(1, 80) * rarity_multiplier) / 10
		size_int += (random.randint(1, 80) * rarity_multiplier) / 1
	if size_int <= 0:
		size_int = 0.0001
	size_int = int(size_int*10000)/10000
	return size_int

async def appraise(cmd):
	user_data = EwUser(member = cmd.message.author)
	market_data = EwMarket(id_server = user_data.id_server)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)
	payment = ewitem.find_item(item_search = "manhattanproject", id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	# Checking availability of appraisal
	#if market_data.clock < 8 or market_data.clock > 17:
	#	response = "You ask the bartender if he knows someone who would want to trade you something for your recently caught fish. Apparently, at night, an old commodore by the name of Captain Albert Alexander comes to drown his sorrows at this very tavern. You guess you’ll just have to sit here and wait for him, then."

	if cmd.message.channel.name not in [ewcfg.channel_speakeasy, ewcfg.channel_bassed_pro_shop]:
		if cmd.message.channel.name in [ewcfg.channel_tt_pier, ewcfg.channel_jp_pier, ewcfg.channel_cl_pier, ewcfg.channel_afb_pier, ewcfg.channel_vc_pier, ewcfg.channel_se_pier, ewcfg.channel_ferry]:
			response = 'You ask a nearby fisherman if he could appraise this fish you just caught. He tells you to fuck off, but also helpfully informs you that there’s an old sea captain that frequents the Speakeasy that might be able to help you. What an inexplicably helpful/grouchy fisherman!'
		else:
			response = 'What random passerby is going to give two shits about your fish? You’ll have to consult a fellow fisherman… perhaps you’ll find some on a pier?'

	elif item_sought:
		name = item_sought.get('name')
		fish = EwItem(id_item = item_sought.get('id_item'))
		item_props = fish.item_props
		# str_fish = fish.item_props.get('str_name')
		# id_fish = item_props['id_food']
		acquisition = item_props.get('acquisition')

		if cmd.message.channel.name == ewcfg.channel_bassed_pro_shop:
			payment = ewitem.find_item(item_search="slimepoudrin", id_user=cmd.message.author.id, id_server=cmd.message.server.id if cmd.message.server is not None else None)

			response = 'You approach a man of moderately swashbuckling appearence, adorned in a fisher\'s vest, clout goggles and a Bassed Pro Shop name-tag reading "Captain Christopher McCartney". He asks you what he can do for you. You submit your {} for appraisal'.format(name)

			if acquisition != ewcfg.acquisition_fishing:
				response += '. \n"look budd, theyre paying me to measure fish here."'

			elif float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
				response += '. \n"look budd, this fish is a bit over-ripened for me to measure."'

			elif item_props["measured"] == True:
				response += '. \n"i already measured this fish. try !inpecting it."'

			elif payment == None:
				response += ", but he says he won’t provide his services for free... but, if you bring him a Poudrin, you might be able to get an appraisal."

			else:
				item_props = fish.item_props
				rarity = item_props['rarity']
				size = item_props['size']
				value = int(item_props['value'])

				response += ' and offer him a poudrin as payment. \n"Let me get the yard stick...'

				if "float_size" not in item_props.keys():
					item_props["float_size"] = gen_size_int(size, rarity)
				response += " This fish looks to be {} centimeters.".format(item_props["float_size"])

				item_props['measured'] = True
				item_props['food_desc'] += " Captain Christopher McCartney informed you that it is {} centimeters.".format(item_props["float_size"])
				fish.persist()

				ewitem.item_delete(id_item=payment.get('id_item'))

				user_data.persist()

		else:

			response = "You approach a man of particularly swashbuckling appearance, adorned in an old sea captain's uniform and bicorne cap, and surrounded by empty glass steins. You ask him if he is Captain Albert Alexander and he replies that he hasn’t heard that name in a long time. You submit your {} for appraisal".format(name)

			if acquisition != ewcfg.acquisition_fishing:
				response += '. \n"Have you lost yer mind, laddy? That’s not a fish!! Just what’re you trying to pull??"'

			elif float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
				response += '. \n"Have you lost yer mind, laddy? This fish is rotten! Just what’re you trying to pull??"'

			else:

				if payment == None:
					response += ", but he says he won’t provide his services for free... but, if you bring him a Manhattan Project, you might be able to get an appraisal."

				else:
					item_props = fish.item_props
					rarity = item_props['rarity']
					size = item_props['size']
					value = int(item_props['value'])

					response += ' and offer him a Manhattan Project as payment. \n"Hm, alright, let’s see here...'

					if rarity == ewcfg.fish_rarity_common:
						response += "Ah, a {}, that’s a pretty common fish... ".format(name)

					if rarity == ewcfg.fish_rarity_uncommon:
						response += "Interesting, a {}, that’s a pretty uncommon fish you’ve got there... ".format(name)

					if rarity == ewcfg.fish_rarity_rare:
						response += "Amazing, it’s a {}! Consider yourself lucky, that’s a pretty rare fish! ".format(name)

					if rarity == ewcfg.fish_rarity_promo:
						response += "Shiver me timbers, is that a {}?? Unbelievable, that’s an extremely rare fish!! It was only ever released as a promotional item in Japan during the late ‘90s. ".format(name)

					if size == ewcfg.fish_size_miniscule:
						response += "Or, is it just a speck of dust? Seriously, that {} is downright miniscule! ".format(name)

					if size == ewcfg.fish_size_small:
						response += "Hmmm, it’s a little small, don’t you think? "

					if size == ewcfg.fish_size_average:
						response += "It’s an average size for the species. "

					if size == ewcfg.fish_size_big:
						response += "Whoa, that’s a big one, too! "

					if size == ewcfg.fish_size_huge:
						response += "Look at the size of that thing, it’s huge! "

					if size == ewcfg.fish_size_colossal:
						response += "By Neptune’s beard, what a sight to behold, this {name} is absolutely colossal!! In all my years in the Navy, I don’t think I’ve ever seen a {name} as big as yours!! ".format(name = name)

					response += "So, I’d say this fish "

					if value <= 20:
						response += 'is absolutely worthless."'

					if value <= 40 and value >= 21:
						response += 'isn’t worth very much."'

					if value <= 60 and value >= 41:
						response += 'is somewhat valuable."'

					if value <= 80 and value >= 61:
						response += 'is highly valuable!"'

					if value <= 99 and value >= 81:
						response += 'is worth a fortune!!"'

					if value >= 100:
						response += 'is the most magnificent specimen I’ve ever seen!"'

					ewitem.item_delete(id_item = payment.get('id_item'))

					user_data.persist()
	else:
		if item_search:  # If they didn't forget to specify an item and it just wasn't found.
			response = "You don't have one."

		else:
			if cmd.message.channel.name == ewcfg.channel_speakeasy:
				response = "Ask Captain Albert Alexander to appraise which fish? (check **!inventory**)"
			else:
				response = "Ask Captain Christopher McCartney to appraise which fish? (check **!inventory**)"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


async def barter(cmd):
	user_data = EwUser(member = cmd.message.author)
	market_data = EwMarket(id_server = user_data.id_server)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	# Checking availability of appraisal
	#if market_data.clock < 8 or market_data.clock > 17:
	#	response = "You ask the bartender if he knows someone who would want to trade you something for your recently caught fish. Apparently, at night, an old commodore by the name of Captain Albert Alexander comes to drown his sorrows at this very tavern. You guess you’ll just have to sit here and wait for him, then."

	if cmd.message.channel.name not in [ewcfg.channel_speakeasy, ewcfg.channel_bassed_pro_shop]:
		if cmd.message.channel.name in [ewcfg.channel_tt_pier, ewcfg.channel_jp_pier, ewcfg.channel_cl_pier, ewcfg.channel_afb_pier, ewcfg.channel_vc_pier, ewcfg.channel_se_pier, ewcfg.channel_ferry]:
			response = 'You ask a nearby fisherman if he wants to trade you anything for this fish you just caught. He tells you to fuck off, but also helpfully informs you that there’s an old sea captain that frequents the Speakeasy that might be able to help you. What an inexplicably helpful/grouchy fisherman!'
		else:
			response = 'What random passerby is going to give two shits about your fish? You’ll have to consult a fellow fisherman… perhaps you’ll find some on a pier?'

	elif item_sought:
		name = item_sought.get('name')
		fish = EwItem(id_item = item_sought.get('id_item'))
		id_fish = fish.id_item
		item_props = fish.item_props
		acquisition = item_props.get('acquisition')
		if cmd.message.channel.name == ewcfg.channel_speakeasy:
			response = "You approach a man of particularly swashbuckling appearance, adorned in an old sea captain's uniform and bicorne cap, and surrounded by empty glass steins. You ask him if he is Captain Albert Alexander and he replies that he hasn’t heard that name in a long time. You submit your {} for bartering".format(name)
		else:
			response = 'You approach a man of moderately swashbuckling appearence, adorned in a fisher\'s vest, clout goggles and a Bassed Pro Shop name-tag reading "Captain Christopher McCartney". He asks you what he can do for you. You submit your {} for bartering'.format(name)

		if cmd.message.channel.name == ewcfg.channel_bassed_pro_shop:
			if item_props.get("id_food") != "thebassedgod":
				response += '. \n"look, if it aint The Bassed God, i aint interested."'
			else:
				response += '. \n"oh fuck! its **THE** Bassed God! ill offer you a mixtape if you give him to me."\n**!accept** or **!refuse** Captain Christopher McCartney\'s deal.'

				offer = EwOffer(
					id_server=cmd.message.server.id,
					id_user=cmd.message.author.id,
					offer_give=id_fish
				)

				mixtapes = ewcfg.item_list
				for item in mixtapes:
					if item.acquisition == ewcfg.acquisition_lilb:
						pass
					else:
						mixtapes.remove(item)

				offer.offer_receive = random.choice(mixtapes).id_item
				offer.time_sinceoffer = int(time.time() / 60)
				offer.persist()

				await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

				# Wait for an answer
				accepted = False

				try:
					message = await cmd.client.wait_for_message(timeout=20, author=cmd.message.author, check=check)

					if message != None:
						if message.content.lower() == "!accept":
							accepted = True
						if message.content.lower() == "!refuse":
							accepted = False
				except:
					accepted = False

				user_data = EwUser(member=cmd.message.author)
				fish = EwItem(id_item=id_fish)

				# cancel deal if fish is no longer in user's inventory
				if fish.id_owner != user_data.id_user:
					accepted = False

				# cancel deal if the user has left the speakeasy
				if user_data.poi != ewcfg.poi_id_bassedproshop:
					accepted = False

				# cancel deal if the offer has been deleted
				if offer.time_sinceoffer == 0:
					accepted = False

				if accepted == True:
					offer_receive = str(offer.offer_receive)

					item_props = ewitem.gen_item_props(item)

					ewitem.item_create(
						item_type=item.item_type,
						id_user=cmd.message.author.id,
						id_server=cmd.message.server.id,
						item_props=item_props
					)

					ewitem.item_delete(id_item=item_sought.get('id_item'))

					user_data.persist()

					offer.deal()

					response = '"enjoy the tape."'

				else:

					response = '"cmon man i really need that fish..."'

		else:
			if acquisition != ewcfg.acquisition_fishing:
				response += '. \n"Have you lost yer mind, laddy? That’s not a fish!! Just what’re you trying to pull??"'

			elif float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
				response += '. \n"Have you lost yer mind, laddy? This fish is rotten! Just what’re you trying to pull??"'

			else:
				value = int(item_props['value'])

				items = []

				# Filters out all non-generic items without the current fish as an ingredient.
				for result in ewcfg.appraise_results:
					if result.ingredients == fish.item_props.get('id_item') or result.ingredients == "generic" and result.acquisition == ewcfg.acquisition_bartering:  # Generic means that it can be made with any fish.
						items.append(result)
					else:
						pass

				# Filters out items of greater value than your fish.
				for value_filter in items:
					if value < value_filter.context:
						items.remove(value_filter)
					else:
						pass

				else:
					offer = EwOffer(
						id_server = cmd.message.server.id,
						id_user = cmd.message.author.id,
						offer_give = id_fish
					)

					cur_time_min = time.time() / 60
					time_offered = cur_time_min - offer.time_sinceoffer

					if offer.time_sinceoffer > 0 and time_offered < ewcfg.fish_offer_timeout:
						offer_receive = str(offer.offer_receive)

						if offer_receive.isdigit() == True:
							slime_gain = int(offer.offer_receive)

							response = '\n"Well, back again I see! My offer still stands, I’ll trade ya {} slime for your {}"'.format(slime_gain, name)

						else:
							for result in ewcfg.appraise_results:
								if hasattr(result, 'id_item'):
									if result.id_item != offer.offer_receive:
										pass
									else:
										item = result

								if hasattr(result, 'id_food'):
									if result.id_food != offer.offer_receive:
										pass
									else:
										item = result

								if hasattr(result, 'id_cosmetic'):
									if result.id_cosmetic != offer.offer_receive:
										pass
									else:
										item = result

							response = '\n"Well, back again I see! My offer still stands, I’ll trade ya a {} for your {}"'.format(item.str_name, name)

						response += "\n**!accept** or **!refuse** Captain Albert Alexander's deal."

						await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

					else:
						# Random choice between 0, 1, and 2
						offer_decision = random.randint(0, 2)

						if offer_decision != 2: # If Captain Albert Alexander wants to offer you slime for your fish. 66% chance.
							max_value = value * 6000 # 600,000 slime for a colossal promo fish, 120,000 for a miniscule common fish.
							min_value = max_value / 10 # 60,000 slime for a colossal promo fish, 12,000 for a miniscule common fish.

							slime_gain = random.randint(min_value, max_value)

							offer.offer_receive = slime_gain

							response = '"Hm, alright… for this {}... I’ll offer you {} slime! Trust me, you’re not going to get a better deal anywhere else, laddy."'.format(name, slime_gain)

						else: # If Captain Albert Alexander wants to offer you an item for your fish. 33% chance. Once there are more unique items, we'll make this 50%.
							item = random.choice(items)

							if hasattr(item, 'id_item'):
								offer.offer_receive = item.id_item

							if hasattr(item, 'id_food'):
								offer.offer_receive = item.id_food

							if hasattr(item, 'id_cosmetic'):
								offer.offer_receive = item.id_cosmetic

							response = '"Hm, alright… for this {}... I’ll offer you a {}! Trust me, you’re not going to get a better deal anywhere else, laddy."'.format(name, item.str_name)

						offer.time_sinceoffer = int(time.time() / 60)
						offer.persist()

						response += "\n**!accept** or **!refuse** Captain Albert Alexander's deal."

						await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

					# Wait for an answer
					accepted = False

					try:
						message = await cmd.client.wait_for_message(timeout = 20, author = cmd.message.author, check = check)

						if message != None:
							if message.content.lower() == "!accept":
								accepted = True
							if message.content.lower() == "!refuse":
								accepted = False
					except:
						accepted = False

					offer = EwOffer(
						id_server = cmd.message.server.id,
						id_user = cmd.message.author.id,
						offer_give = id_fish
					)

					user_data = EwUser(member = cmd.message.author)
					fish = EwItem(id_item = id_fish)

					# cancel deal if fish is no longer in user's inventory
					if fish.id_owner != user_data.id_user:
						accepted = False

					# cancel deal if the user has left the speakeasy
					if user_data.poi != ewcfg.poi_id_speakeasy:
						accepted = False

					# cancel deal if the offer has been deleted
					if offer.time_sinceoffer == 0:
						accepted = False


					if accepted == True:
						offer_receive = str(offer.offer_receive)

						response = ""

						if offer_receive.isdigit() == True:
							slime_gain = int(offer_receive)

							user_initial_level = user_data.slimelevel

							levelup_response = user_data.change_slimes(n = slime_gain, source = ewcfg.source_fishing)

							was_levelup = True if user_initial_level < user_data.slimelevel else False

							# Tell the player their slime level increased.
							if was_levelup:
								response += levelup_response
								response += "\n\n"

						else:
							item_props = ewitem.gen_item_props(item)

							ewitem.item_create(
								item_type = item.item_type,
								id_user = cmd.message.author.id,
								id_server = cmd.message.server.id,
								item_props = item_props
							)


						ewitem.item_delete(id_item = item_sought.get('id_item'))

						user_data.persist()

						offer.deal()

						response += '"Pleasure doing business with you, laddy!"'

					else:
						response = '"Ah, what a shame. Maybe you’ll change your mind in the future…?"'

	else:
		if item_search:  # If they didn't forget to specify an item and it just wasn't found.
			response = "You don't have one."
		else:
			if cmd.message.channel.name == ewcfg.channel_speakeasy:
				response = "Offer Captain Albert Alexander which fish? (check **!inventory**)"
			else:
				response = "Offer Captain Christopher McCartney which fish? (check **!inventory**)"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def kill_dead_offers(id_server):
	time_now = int(time.time() / 60)
	ewutils.execute_sql_query("DELETE FROM offers WHERE {id_server} = %s AND {time_sinceoffer} < %s".format(
		id_server = ewcfg.col_id_server,
		time_sinceoffer = ewcfg.col_time_sinceoffer,
	),(
		id_server,
		time_now - ewcfg.fish_offer_timeout,
	))

async def grill(cmd):
	user_data = EwUser(member = cmd.message.author)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)
	if cmd.message.channel.name not in [ewcfg.channel_bassed_pro_shop, ewcfg.channel_seafood]:
		response = "There's no grill here. Head on over to The Bassed Pro Shop or Red Mobster."

	elif item_sought:
		name = item_sought.get('name')
		fish = EwItem(id_item=item_sought.get('id_item'))
		item_props = fish.item_props
		acquisition = item_props.get('acquisition')

		if acquisition != ewcfg.acquisition_fishing:
			if cmd.message.channel.name == ewcfg.channel_seafood:
				response = 'You attempt to hand the Red Mobster employee your {}, but they give you a confused look and says, "We only cook fish here."'.format(name)
			else:
				response = 'You find Captain Christopher McCartney and attempt to hand him your {}, but he slaps it away in disgust and says, "I can\'t grill that!"'.format(name)

		elif float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
			if cmd.message.channel.name == ewcfg.channel_seafood:
				response = 'You attempt to hand the Red Mobster employee your {}, but they give you a disgusted look and says, "That fish is spoiled."'.format(name)
			else:
				response = 'You find Captain Christopher McCartney and attempt to hand him your {}, but he slaps it away in disgust and says, "I can\'t grill that! It\'s expired!"'.format(name)

		else:
			size = item_props["size"]
			if size == ewcfg.fish_size_miniscule:
				hunger_multiplier = 1
			elif size == ewcfg.fish_size_small:
				hunger_multiplier = 2
			elif size == ewcfg.fish_size_average:
				hunger_multiplier = 3
			elif size == ewcfg.fish_size_big:
				hunger_multiplier = 4
			elif size == ewcfg.fish_size_huge:
				hunger_multiplier = 5
			elif size == ewcfg.fish_size_colossal:
				hunger_multiplier = 6

			value = ewcfg.base_grill_cost * hunger_multiplier

			if value > user_data.slimes:
				# Not enough money.
				response = "Grilling your {} costs {:,} slime, and you only have {:,}.".format(name, value, user_data.slimes)

			else:
				user_data.change_slimes(n=-value, source=ewcfg.source_spending)

				ewitem.item_create(
					id_user=cmd.message.author.id,
					id_server=cmd.message.server.id,
					item_type=ewcfg.it_food,
					item_props={
						'id_food': "grilled{}".format(item_props["id_food"]),
						'food_name': "grilled {}".format(item_props["food_name"]),
						'food_desc': "Some delicious looking grilled {}.".format(item_props["food_name"]),
						'recover_hunger': ewcfg.base_grill_hunger*hunger_multiplier,
						'str_eat': ewcfg.grill_str_eat.format(size, item_props["food_name"]),
						'time_expir': time.time() + ewcfg.std_food_expir,
						'acquisition': ewcfg.acquisition_grilling,
					}
				)

				ewitem.item_delete(id_item=item_sought.get('id_item'))

				user_data.persist()

				if cmd.message.channel.name == ewcfg.channel_seafood:
					response = 'You hand your {} off to the Red Mobster employee at the counter, along with {} slime.\nThey take a metal spike and stick it into the fish\'s brain stem, then they toss it onto the stove top for a few minutes...\n10 minutes later, they serve you your grilled {} in a brown paper bag with a Red Mobster insignia on it.'.format(name, value, name)
				else:
					response = 'You hand your {} off to Captain Christopher McCartney, along with {} slime.\nHe takse a metal spike and sticks it into the fish\'s brain stem, then he tosses it onto the grill top for a few minutes...\n8 minutes later, he serves you your grilled {} in a brown paper bag with a Bassed Pro Shop insignia on it.'.format(name, value, name)

	else:
		if item_search:
			response = "You don't have one."
		else:
			response = "Grill what fish? (check **!inventory**)"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def enter_tourney(cmd):
	market_data = EwMarket(id_server = cmd.message.server.id)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if cmd.message.channel.name != ewcfg.channel_bassed_pro_shop:
		response = "Go to the Bassed Pro Shop if you want to enter a fish into the current tourney."

	elif item_sought:
		name = item_sought.get('name')
		fish = EwItem(id_item=item_sought.get('id_item'))
		item_props = fish.item_props
		acquisition = item_props.get('acquisition')
		date_caught = item_props.get('date_caught')
		response = 'You approach a man of moderately swashbuckling appearence, adorned in a fisher\'s vest, clout goggles and a Bassed Pro Shop name-tag reading "Captain Christopher McCartney". He asks you what he can do for you. You submit your {} for the tourney'.format(name)
		tourney_range = range(int(market_data.day / 28) * 28, int(market_data.day / 28) * 28)

		if not tourney:
			response += '. \n"there aint a tourney happening right now."'

		elif not date_caught in tourney_range:
			response += '. \n"you can only enter fish caught during the tourney."'

		elif acquisition != ewcfg.acquisition_fishing:
			response += '. \n"listen here, this izza FISHING tourney, not a {} tourney."'.format(name)

		elif float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
			response += '. \n"look budd, this fish izza bit over-ripened for the tourney."'

		else:
			response += '. \n"aight, ill enter yr {fish} into the current tourney."\nHe takes your {fish}, and shoves it into a drawer in his desk labeled tourney #{tourney}. \n"make sure you check the stats of the current **!tourney** every once in a while"'.format(
				fish = name,
				tourney = int(market_data.day/7)
			)
			entry = EwTourneyEntry(
				id_server = cmd.message.server.id,
				id_user = cmd.message.author.id,
				id_tourney = int(market_data.day/28),
				id_fish = item_props["food_name"],
				float_size = item_props["float_size"],
				rank_int = 0
			)
			entry.persist()

			ewitem.item_delete(id_item=item_sought.get('id_item'))

	else:
		if item_search:
			response = "You don't have one."
		else:
			response = "Enter what fish? (check **!inventory**)"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def buy_tank_space(cmd):
	user_data = EwUser(member = cmd.message.author)
	item_sought = ewitem.find_item(item_search="slimepoudrin", id_user=cmd.message.author.id, id_server=cmd.message.server.id if cmd.message.server is not None else None)

	if cmd.message.channel.name != ewcfg.channel_bassed_pro_shop:
		response = "You can't buy any tank space here. Head on over to the Bassed Pro Shop."

	elif item_sought:
		user_data.fish_space += 5
		user_data.persist()
		ewitem.item_delete(id_item=item_sought.get('id_item'))
		response = "You hand Captain Christopher McCartney a poudrin, and in return the maximum amount of fish you can store here has been upgraded to {}.".format(user_data.fish_space)

	else:
		response = "You need a poudrin to upgrade your fish space."

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def store_fish(cmd):
	user_data = EwUser(member = cmd.message.author)
	max_space = user_data.fish_space
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)
	current_space = len(user_data.get_stored_fish())

	if not item_sought:
		if item_search:
			response = "You don't have one."
		else:
			response = "Store which fish?"

	elif cmd.message.channel.name != ewcfg.channel_bassed_pro_shop:
		response = "You toss your {} onto the ground, and then promptly pick it back up when you realize how fucking retarded storing something on the ground would be. Try storing it at the Bassed Pro Shop.".format(name = item_sought.get('name'))

	else:
		name = item_sought.get('name')
		fish = EwItem(id_item=item_sought.get('id_item'))
		if float(fish.time_expir if fish.time_expir is not None else 0) < time.time():
			response = "You cannot store a rotten fish."
		elif current_space == max_space:
			if current_space == 0:
				response = "First you have to buy tank space for the low, low price of a poudrin (which gets you 5 slots)."
			else:
				response = "Your fish tank is at capacity! **!buytankspace** for a poudrin if you want to store more fish."
		else:
			item_props = fish.item_props
			item_props["time_expir"] = None
			fish.persist()
			ewitem.give_item(id_user=ewcfg.tank_poi+cmd.message.author.id, id_server=fish.id_server, id_item=fish.id_item)
			response = "You give Captain Christopher McCartney your {}, and he tosses it in one of the many fish tanks found around the store.".format(name)

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def take_fish(cmd):
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search=item_search, id_user=ewcfg.tank_poi+cmd.message.author.id, id_server=cmd.message.server.id if cmd.message.server is not None else None)

	if not item_search:
		response = "Take which fish?"

	elif not item_sought:
		response = "You don't have that in storage."

	elif cmd.message.channel.name != ewcfg.channel_bassed_pro_shop:
		response = "You try to take your {} out of storage, only to realize that this is not your beautiful fish. This is not your beautiful wife. Letting the days go by, letting the slime hold you down. Try heading to the Bassed Pro Shop if you want to take a fish out of storage".format(name = item_sought.get('name'))

	else:
		name = item_sought.get('name')
		fish = EwItem(id_item=item_sought.get('id_item'))
		item_props = fish.item_props
		item_props["time_expir"] = time.time() + ewcfg.std_food_expir
		fish.persist()
		ewitem.give_item(id_user=cmd.message.author.id, id_server=fish.id_server, id_item=fish.id_item)
		response = "Captain Christopher McCartney scurries around the Shop to find the fish tank with your name on it, until he finally spots your {}, right where he left it. Reunited, at last.".format(name)

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def get_tourney(server = None):
	market_data = EwMarket(id_server = server)
	current_day = market_data.day
	state_int = current_day % 28
	if state_int <= 6:
		tourney_state = True
	else:
		tourney_state = False
	return tourney_state

async def tourney(cmd):
	market_data = EwMarket(id_server=cmd.message.server.id)
	remain = market_data.day % 28
	if not tourney:
		days_until = 28 - remain
		response = "There is currently no Fishing Tourney active. There will be one in {} day(s), in-game.".format(days_until)
	else:
		days_left = 6 - remain
		if days_left != 0:
			response = "The weekly Fishing Tourney is active. There are {} in-game day(s) left.".format(days_left)
		else:
			response = "The weekly Fishing Tourney is active. This is the last day to enter."
		response += ewleaderboard.make_fishing_top_board(server=cmd.message.server)

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def tank(cmd):
	items = ewitem.inventory(
		id_user=ewcfg.tank_poi+cmd.message.author.id,
		id_server=cmd.message.server.id
	)

	if len(items) == 0:
		response = "You phone up Captain Christopher McCartney, only for him to inform you that you haven't stored anything in your fish tank."

	else:
		response = "You phone up Captain Christopher McCartney and he begins to list off the fish you've stored:"
		for item in items:
			quantity = item.get('quantity')

			response_part = "\n{id_item}: {soulbound_style}{name}{soulbound_style}{quantity}".format(
				id_item=item.get('id_item'),
				name=item.get('name'),
				soulbound_style=("**" if item.get('soulbound') else ""),
				quantity=(" x{:,}".format(quantity) if (quantity > 0) else "")
			)
			if len(response) + len(response_part) > 1492:
				await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

				response = ""

			response += response_part

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def get_tourney_winners(server = None):
	data = ewutils.execute_sql_query((
			"SELECT el.id_user " +
			"FROM tourney_entries AS el " +
			"WHERE el.id_server = %s " +
			"ORDER BY el.float_size DESC LIMIT 3"
	), (
		server.id,
	))
	for row in data:
		try:
			user = discord.utils.get(server.members, id=row[0])
			user_data = EwUser(member = user)
			user_data.unclaimed_prizes += 1
			user_data.persist()
		except:
			pass

async def claim(cmd):
	user_data = EwUser(member = cmd.message.author)
	unclaimed_prizes = user_data.unclaimed_prizes
	if unclaimed_prizes == 0:
		response = "You have no prizes to claim!"
	elif unclaimed_prizes >= 1:
		prize = random.choice(ewcfg.pole_prizes)
		item_props = ewitem.gen_item_props(prize)

		ewitem.item_create(
			item_type=ewcfg.it_weapon,
			id_user=cmd.message.author.id,
			id_server=cmd.message.server.id,
			item_props=item_props
		)
		user_data.unclaimed_prizes -= 1
		user_data.persist()

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
