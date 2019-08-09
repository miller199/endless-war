import random
import asyncio
import time

import ewcfg
import ewutils
import ewitem
import ewrolemgr
import ewstats
import ewmap

from ew import EwUser
from ewmarket import EwMarket
from ewdistrict import EwDistrict
from ewplayer import EwPlayer
from ewitem import EwItem

active_slimeoidbattles = {}

""" Slimeoid data model for database persistence """
class EwSlimeoid:
	id_slimeoid = 0
	id_user = ""
	id_server = ""

	life_state = 0
	body = ""
	head = ""
	legs = ""
	armor = ""
	weapon = ""
	special = ""
	ai = ""
	sltype = "Lab"
	name = ""
	atk = 0
	defense = 0
	intel = 0
	level = 0
	time_defeated = 0
	clout = 0
	hue = ""
	poi = ""

	#slimeoid = EwSlimeoid(member = cmd.message.author, )
	#slimeoid = EwSlimeoid(id_slimeoid = 12)

	""" Load the slimeoid data for this user from the database. """
	def __init__(self, member = None, id_slimeoid = None, life_state = None, id_user = None, id_server = None, sltype = "Lab"):
		query_suffix = ""

		if id_slimeoid != None:
			query_suffix = " WHERE id_slimeoid = '{}'".format(id_slimeoid)
		else:
			if member != None:
				id_user = member.id
				id_server = member.server.id

			if id_user != None and id_server != None:
				query_suffix = " WHERE id_user = '{}' AND id_server = '{}'".format(id_user, id_server)
				if life_state != None:
					query_suffix += " AND life_state = '{}'".format(life_state)
				if sltype != None:
					query_suffix += " AND type = '{}'".format(sltype)

		if query_suffix != "":
			try:
				conn_info = ewutils.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor();

				# Retrieve object
				cursor.execute("SELECT {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {} FROM slimeoids{}".format(
					ewcfg.col_id_slimeoid,
					ewcfg.col_id_user,
					ewcfg.col_id_server,
					ewcfg.col_life_state,
					ewcfg.col_body,
					ewcfg.col_head,
					ewcfg.col_legs,
					ewcfg.col_armor,
					ewcfg.col_weapon,
					ewcfg.col_special,
					ewcfg.col_ai,
					ewcfg.col_type,
					ewcfg.col_name,
					ewcfg.col_atk,
					ewcfg.col_defense,
					ewcfg.col_intel,
					ewcfg.col_level,
					ewcfg.col_time_defeated,
					ewcfg.col_clout,
					ewcfg.col_hue,
					ewcfg.col_poi,
					query_suffix
				))
				result = cursor.fetchone();

				if result != None:
					# Record found: apply the data to this object.
					self.id_slimeoid = result[0]
					self.id_user = result[1]
					self.id_server = result[2]
					self.life_state = result[3]
					self.body = result[4]
					self.head = result[5]
					self.legs = result[6]
					self.armor = result[7]
					self.weapon = result[8]
					self.special = result[9]
					self.ai= result[10]
					self.sltype = result[11]
					self.name = result[12]
					self.atk = result[13]
					self.defense = result[14]
					self.intel = result[15]
					self.level = result[16]
					self.time_defeated = result[17]
					self.clout = result[18]
					self.hue = result[19]
					self.poi = result[20]

			finally:
				# Clean up the database handles.
				cursor.close()
				ewutils.databaseClose(conn_info)


	""" Save slimeoid data object to the database. """
	def persist(self):
		try:
			conn_info = ewutils.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor();

			# Save the object.
			cursor.execute("REPLACE INTO slimeoids({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(
				ewcfg.col_id_slimeoid,
				ewcfg.col_id_user,
				ewcfg.col_id_server,
				ewcfg.col_life_state,
				ewcfg.col_body,
				ewcfg.col_head,
				ewcfg.col_legs,
				ewcfg.col_armor,
				ewcfg.col_weapon,
				ewcfg.col_special,
				ewcfg.col_ai,
				ewcfg.col_type,
				ewcfg.col_name,
				ewcfg.col_atk,
				ewcfg.col_defense,
				ewcfg.col_intel,
				ewcfg.col_level,
				ewcfg.col_time_defeated,
				ewcfg.col_clout,
				ewcfg.col_hue,
				ewcfg.col_poi
			), (
				self.id_slimeoid,
				self.id_user,
				self.id_server,
				self.life_state,
				self.body,
				self.head,
				self.legs,
				self.armor,
				self.weapon,
				self.special,
				self.ai,
				self.sltype,
				self.name,
				self.atk,
				self.defense,
				self.intel,
				self.level,
				self.time_defeated,
				self.clout,
				self.hue,
				self.poi
			))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			ewutils.databaseClose(conn_info)

	def die(self):
		self.life_state = ewcfg.slimeoid_state_dead
		self.id_user = ''


	def delete(self):
		ewutils.execute_sql_query("DELETE FROM slimeoids WHERE {id_slimeoid} = %s".format(
			id_slimeoid = ewcfg.col_id_slimeoid
		),(
			self.id_slimeoid,
		))
	
	def haunt(self):
		resp_cont = ewutils.EwResponseContainer(id_server = self.id_server)
		if (self.sltype != ewcfg.sltype_nega) or active_slimeoidbattles.get(self.id_slimeoid):
			return resp_cont
		market_data = EwMarket(id_server = self.id_server)
		ch_name = ewcfg.id_to_poi.get(self.poi).channel

		data = ewutils.execute_sql_query("SELECT {id_user} FROM users WHERE {poi} = %s AND {id_server} = %s".format(
			id_user = ewcfg.col_id_user,
			poi = ewcfg.col_poi,
			id_server = ewcfg.col_id_server
		),(
			self.poi,
			self.id_server
		))

		for row in data:
			haunted_data = EwUser(id_user = row[0], id_server = self.id_server)
			haunted_player = EwPlayer(id_user = row[0])

			if haunted_data.life_state in [ewcfg.life_state_juvenile, ewcfg.life_state_enlisted]:
				haunted_slimes = 2 * int(haunted_data.slimes / ewcfg.slimes_hauntratio)

				haunt_cap = 10 ** (self.level-1)
				haunted_slimes = min(haunt_cap, haunted_slimes) # cap on for how much you can haunt

				haunted_data.change_slimes(n = -haunted_slimes, source = ewcfg.source_haunted)
				market_data.negaslime -= haunted_slimes

				# Persist changes to the database.
				haunted_data.persist()
		response = "{} lets out a blood curdling screech. Everyone in the district loses slime.".format(self.name)
		resp_cont.add_channel_response(ch_name, response)
		market_data.persist()

		return resp_cont

	def move(self):
		resp_cont = ewutils.EwResponseContainer(id_server = self.id_server)
		if active_slimeoidbattles.get(self.id_slimeoid):
			return resp_cont
		try:
			destinations = ewcfg.poi_neighbors.get(self.poi).intersection(set(ewcfg.capturable_districts))
			if len(destinations) > 0:
				self.poi = random.choice(list(destinations))
				poi_def = ewcfg.id_to_poi.get(self.poi)
				ch_name = poi_def.channel
		
				response = "The air grows colder and color seems to drain from the streets and buildings around you. {} has arrived.".format(self.name)
				resp_cont.add_channel_response(ch_name, response)
				response = "There are reports of a sinister presence in {}.".format(poi_def.str_name)
				resp_cont.add_channel_response(ewcfg.channel_rowdyroughhouse, response)
				resp_cont.add_channel_response(ewcfg.channel_copkilltown, response)
		finally:
			return resp_cont

""" slimeoid model object """
class EwBody:
	id_body = ""
	alias = []
	str_create = ""
	str_body = ""
	def __init__(
		self,
		id_body = "",
		alias = [],
		str_create = "",
		str_body = "",
		str_observe = ""
	):
		self.id_body = id_body
		self.alias = alias
		self.str_create = str_create
		self.str_body = str_body
		self.str_observe = str_observe

class EwHead:
	id_head = ""
	alias = []
	str_create = ""
	str_head = ""
	def __init__(
		self,
		id_head = "",
		alias = [],
		str_create = "",
		str_head = "",
		str_feed = "",
		str_fetch = ""
	):
		self.id_head = id_head
		self.alias = alias
		self.str_create = str_create
		self.str_head = str_head
		self.str_feed = str_feed
		self.str_fetch = str_fetch
	
class EwMobility:
	id_mobility = ""
	alias = []
	str_advance = ""
	str_retreat = ""
	str_create = ""
	str_mobility = ""
	def __init__(
		self,
		id_mobility = "",
		alias = [],
		str_advance = "",
		str_advance_weak = "",
		str_retreat = "",
		str_retreat_weak = "",
		str_create = "",
		str_mobility = "",
		str_defeat = "",
		str_walk = ""
	):
		self.id_mobility = id_mobility
		self.alias = alias
		self.str_advance = str_advance
		self.str_advance_weak = str_advance_weak
		self.str_retreat = str_retreat
		self.str_retreat_weak = str_retreat_weak
		self.str_create = str_create
		self.str_mobility = str_mobility
		self.str_defeat = str_defeat
		self.str_walk = str_walk

class EwOffense:
	id_offense = ""
	alias = []
	str_attack = ""
	str_create = ""
	str_offense = ""
	def __init__(
		self,
		id_offense = "",
		alias = [],
		str_attack = "",
		str_attack_weak = "",
		str_attack_coup = "",
		str_create = "",
		str_offense = "",
		str_observe = ""
	):
		self.id_offense = id_offense
		self.alias = alias
		self.str_attack = str_attack
		self.str_attack_weak = str_attack_weak
		self.str_attack_coup = str_attack_coup
		self.str_create = str_create
		self.str_offense = str_offense
		self.str_observe = str_observe

class EwDefense:
	id_defense = ""
	alias = []
	str_create = ""
	str_defense = ""
	def __init__(
		self,
		id_defense = "",
		alias = [],
		str_create = "",
		str_defense = "",
		str_armor = "",
		str_pet = ""
	):
		self.id_defense = id_defense
		self.alias = alias
		self.str_create = str_create
		self.str_defense = str_defense
		self.str_armor = str_armor
		self.str_pet = str_pet

class EwSpecial:
	id_special = ""
	alias = []
	str_special_attack = ""
	str_create = ""
	str_special = ""
	def __init__(
		self,
		id_special = "",
		alias = [],
		str_special_attack = "",
		str_special_attack_weak = "",
		str_special_attack_coup = "",
		str_create = "",
		str_special = "",
		str_observe = ""
	):
		self.id_special = id_special
		self.alias = alias
		self.str_special_attack = str_special_attack
		self.str_special_attack_weak = str_special_attack_weak
		self.str_special_attack_coup = str_special_attack_coup
		self.str_create = str_create
		self.str_special = str_special
		self.str_observe = str_observe

class EwBrain:
	id_brain = ""
	alias = []
	str_create = ""
	str_brain = ""
	def __init__(
		self,
		id_brain = "",
		alias = [],
		str_create = "",
		str_brain = "",
		str_dissolve = "",
		str_spawn = "",
		str_revive = "",
		str_death = "",
		str_victory = "",
		str_battlecry = "",
		str_battlecry_weak = "",
		str_movecry = "",
		str_movecry_weak = "",
		str_kill = "",
		str_walk = "",
		str_pet = "",
		str_observe = ""
	):
		self.id_brain = id_brain
		self.alias = alias
		self.str_create = str_create
		self.str_brain = str_brain
		self.str_dissolve = str_dissolve
		self.str_spawn = str_spawn
		self.str_revive = str_revive
		self.str_death = str_death
		self.str_victory = str_victory
		self.str_battlecry = str_battlecry
		self.str_battlecry_weak = str_battlecry_weak
		self.str_movecry = str_movecry
		self.str_movecry_weak = str_movecry_weak
		self.str_kill = str_kill
		self.str_pet = str_pet
		self.str_walk = str_walk
		self.str_observe = str_observe

"""
	Commands
"""

# play with your slimeoid
async def playfetch(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	time_now = int(time.time())

	if user_data.life_state == ewcfg.life_state_corpse:
			response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You do not have a Slimeoid to play fetch with."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
			response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	elif (time_now - slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "{} is too beat up from its last battle to play fetch right now.".format(slimeoid.name)

	else:
		head = ewcfg.head_map.get(slimeoid.head)
		response = head.str_fetch.format(
			slimeoid_name = slimeoid.name
		)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def observeslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	time_now = int(time.time())

	if user_data.life_state == ewcfg.life_state_corpse:
			response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You do not have a Slimeoid to observe."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
			response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	elif (time_now - slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "{} lies totally inert, recuperating from being recently pulverized in the Arena.".format(slimeoid.name)

	else:
		options = [
			'body',
			'weapon',
			'special',
			'brain',
		]

		roll = random.randrange(len(options))
		result = options[roll]

		if result == 'body':
			part = ewcfg.body_map.get(slimeoid.body)

		if result == 'weapon':
			part = ewcfg.offense_map.get(slimeoid.weapon)

		if result == 'special':
			part = ewcfg.special_map.get(slimeoid.special)

		if result == 'brain':
			part = ewcfg.brain_map.get(slimeoid.ai)

		response = part.str_observe.format(
			slimeoid_name = slimeoid.name
		)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def petslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	time_now = int(time.time())

	if user_data.life_state == ewcfg.life_state_corpse:
			response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You do not have a Slimeoid to pet."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
			response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	elif (time_now - slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "{} whimpers. It's still recovering from being beaten up in the Arena.".format(slimeoid.name)

	else:
		armor = ewcfg.defense_map.get(slimeoid.armor)
		response = armor.str_pet.format(
			slimeoid_name = slimeoid.name
		)
		response += " "
		brain = ewcfg.brain_map.get(slimeoid.ai)
		response += brain.str_pet.format(
			slimeoid_name = slimeoid.name
		)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def walkslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	time_now = int(time.time())

	if user_data.life_state == ewcfg.life_state_corpse:
			response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You do not have a Slimeoid to take for a walk."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
			response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	elif (time_now - slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "{} can barely move. It's still recovering from its injuries from the Arena.".format(slimeoid.name)

	else:
		brain = ewcfg.brain_map.get(slimeoid.ai)
		response = brain.str_walk.format(
			slimeoid_name = slimeoid.name
		)
		poi = ewcfg.id_to_poi.get(user_data.poi)
		response += " With that done, you go for a leisurely stroll around {}, while ".format(poi.str_name)
		legs = ewcfg.mobility_map.get(slimeoid.legs)
		response += legs.str_walk.format(
			slimeoid_name = slimeoid.name
		)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# read the instructions
async def instructions(cmd):
	user_data = EwUser(member = cmd.message.author)
	#roles_map_user = ewutils.getRoleMap(message.author.roles)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "There's no instructions to read here."

	else:
		response = "Welcome to SlimeCorp's Brawlden Laboratory Facilities."
		response += "\n\nThis facility specializes in the emerging technology of Slimeoids, or slime-based artificial lifeforms. Research into the properties of Slimeoids is ongoing, but already great advancements in the field have been made and we are proud to be the first to make them commercially available."
		response += "\n\nThis laboratory is equipped with everything required for the creation of a Slimeoid from scratch. To create a Slimeoid, you will need to supply one (1) Slime Poudrin, which will serve as the locus around which your Slimeoid will be based. You will also need to supply some Slime. You may supply as much or as little slime as you like, but greater Slime contribution will lead to superior Slimeoid genesis. To begin the Slimeoid creation process, use **!incubateslimeoid** followed by the amount of slime you wish to use."
		response += "\n\nAfter beginning incubation, you will need to use the console to adjust your Slimeoid's features while it is still forming. Use **!growbody**, **!growhead**, **!growlegs**, **!growweapon**, **!growarmor**, **!growspecial**, or **!growbrain** followed by a letter (A - G) to choose the appearance, abilities, and temperament of your Slimeoid. You will also need to give youe Slimeoid a name. Use **!nameslimeoid** followed by your desired name. These traits may be changed at any time before the incubation is completed."
		response += "\n\nIn addition to physical features, you will need to allocate your Slimeoid's attributes. Your Slimeoid will have a different amount of potential depending on how much slime you invested in its creation. You must distribute this potential across the three Slimeoid attributes, Moxie, Grit, and Chutzpah. Use **!raisemoxie**, **!lowermoxie**, **!raisegrit**, **!lowergrit**, **!raisechutzpah**, and **!lowerchutzpah** to adjust your Slimeoid's attributes to your liking."
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
		response = "\n\nWhen all of your Slimeoid's traits are confirmed, use **!spawnslimeoid** to end the incubation and eject your Slimeoid from the gestation vat. Be aware that once spawned, the Slimeoid's traits are finalized and cannot be changed, so be sure you are happy with your Slimeoid's construction before spawning. Additionally, be aware that you may only have one Slimeoid at a time, meaning should you ever want a new Slimeoid, you will need to euthanise your old one with **!dissolveslimeoid**. SlimeCorp assumes no responsibility for accidents, injuries, infections, physical disabilities, or ideological radicalizations that may occur due to prolonged contact with slime-based lifeforms."
		response += "\n\nYou can read a full description of your or someone else's Slimeoid with the **!slimeoid** command. Note that your Slimeoid, having been made out of slime extracted from your body, will recognize you as its master and follow you until such time as you choose to dispose of it. It will react to your actions, including when you kill an opponent, when you are killed, when you return from the dead, and when you !howl. In addition, you can also perform activities with your Slimeoid. Try **!observeslimeoid**, **!petslimeoid**, **!walkslimeoid**, and **!playfetch** and see what happens."
		response += "\n\nSlimeoid research is ongoing, and the effects of a Slimeoid's physical makeup, brain structure, and attribute allocation on its abilities are a rapidly advancing field. Field studies into the effects of these variables on one-on-one Slimeoid battles are set to begin in the near future. In the meantime, report any unusual findings or behaviors to the Cop Killer and Rowdy Fucker, who have much fewer important things to spend their time on than SlimeCorp employees."
		response += "\n\nThank you for choosing SlimeCorp.{}".format(ewcfg.emote_slimecorp)


	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# Create a slimeoid
async def incubateslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	#roles_map_user = ewutils.getRoleMap(message.author.roles)

	poudrin = ewitem.find_item(item_search = ewcfg.item_id_slimepoudrin, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
		response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif poudrin is None:
		response = "You need a slime poudrin."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = ewutils.getIntToken(tokens = cmd.tokens, allow_all = True)
		if value != None:
			user_data = EwUser(member = cmd.message.author)
			slimeoid = EwSlimeoid(member = cmd.message.author)
			market_data = EwMarket(id_server = cmd.message.author.server.id)
			if value == -1:
				value = user_data.slimes

			if slimeoid.life_state == ewcfg.slimeoid_state_active:
				response = "You have already created a Slimeoid. Dissolve your current slimeoid before incubating a new one."

			elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
				response = "You are already in the process of incubating a Slimeoid."

			elif value > user_data.slimes:
				response = "You do not have that much slime to sacrifice."

			else:
				# delete a slime poudrin from the player's inventory
				ewitem.item_delete(id_item = poudrin.get('id_item'))

				level = len(str(value))
				user_data.change_slimes(n = -value)
				slimeoid.life_state = ewcfg.slimeoid_state_forming
				slimeoid.level = level
				slimeoid.id_user = user_data.id_user
				slimeoid.id_server = user_data.id_server

				user_data.persist()
				slimeoid.persist()

				response = "You place a poudrin into a small opening on the console. As you do, a needle shoots up and pricks your finger, intravenously extracting {} slime from your body. The poudrin is then dropped into the gestation tank. Looking through the observation window, you see what was once your slime begin to seep into the tank and accrete around the poudrin. The incubation of a new Slimeoid has begun! {}".format(str(value), ewcfg.emote_slime2)

		else:
			response = "You must contribute some of your own slime to create a Slimeoid. Specify how much slime you will sacrifice."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# Create a slimeoid
async def dissolveslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	#roles_map_user = ewutils.getRoleMap(message.author.roles)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
		response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
		response = "You have no slimeoid to dissolve."

	else:
		if slimeoid.life_state == ewcfg.slimeoid_state_forming:
			response = "You hit a large red button with a white X on it. Immediately a buzzer goes off and the half-formed body of what would have been your new Slimeoid is flushed out of the gestation tank and down a drainage tube, along with your poudrin and slime. What a waste."
		else:
			brain = ewcfg.brain_map.get(slimeoid.ai)
			response = brain.str_dissolve.format(
				slimeoid_name = slimeoid.name
			)
			response += "{}".format(ewcfg.emote_slimeskull)

			cosmetics = ewitem.inventory(
				id_user = cmd.message.author.id,
				id_server = cmd.message.server.id,
				item_type_filter = ewcfg.it_cosmetic
			)

			# get the cosmetics worn by the slimeoid
			for item in cosmetics:
				cos = EwItem(id_item = item.get('id_item'))
				if cos.item_props.get('slimeoid') == 'true':
					cos.item_props['slimeoid'] = 'false'
					cos.persist()

		slimeoid.life_state = ewcfg.slimeoid_state_none
		slimeoid.body = ""
		slimeoid.head = ""
		slimeoid.legs = ""
		slimeoid.armor = ""
		slimeoid.weapon = ""
		slimeoid.special = ""
		slimeoid.ai = ""
		slimeoid.type = ""
		slimeoid.name = ""
		slimeoid.atk = 0
		slimeoid.defense = 0
		slimeoid.intel = 0
		slimeoid.level = 0
		slimeoid.clout = 0

		user_data.persist()
		slimeoid.persist()

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's body

async def growbody(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			body = ewcfg.body_map.get(value)
			if body != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(body.str_create)
					slimeoid.body = body.id_body
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the body console labelled A through G."
			else:
				response = "Choose an option from the buttons on the body console labelled A through G."
		else:
			response = "You must specify a body type. Choose an option from the buttons on the body console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


# shape your slimeoid's head
async def growhead(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			head = ewcfg.head_map.get(value)
			if head != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(head.str_create)
					slimeoid.head = head.id_head
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the head console labelled A through G."
			else:
				response = "Choose an option from the buttons on the head console labelled A through G."
		else:
			response = "You must specify a head type. Choose an option from the buttons on the head console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's legs
async def growlegs(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			mobility = ewcfg.mobility_map.get(value)
			if mobility != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(mobility.str_create)
					slimeoid.legs = mobility.id_mobility
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the mobility console labelled A through G."
			else:
				response = "Choose an option from the buttons on the mobility console labelled A through G."
		else:
			response = "You must specify means of locomotion. Choose an option from the buttons on the mobility console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's weapon
async def growweapon(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			offense = ewcfg.offense_map.get(value)
			if offense != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(offense.str_create)
					slimeoid.weapon = offense.id_offense
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the weapon console labelled A through G."
			else:
				response = "Choose an option from the buttons on the weapon console labelled A through G."
		else:
			response = "You must specify a means of attack. Choose an option from the buttons on the weapon console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's armor
async def growarmor(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			defense = ewcfg.defense_map.get(value)
			if defense != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(defense.str_create)
					slimeoid.armor = defense.id_defense
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the armor console labelled A through G."
			else:
				response = "Choose an option from the buttons on the armor console labelled A through G."
		else:
			response = "You must specify a method of protection. Choose an option from the buttons on the armor console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's special ability
async def growspecial(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			special = ewcfg.special_map.get(value)
			if special != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(special.str_create)
					slimeoid.special = special.id_special
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the special attack console labelled A through G."
			else:
				response = "Choose an option from the buttons on the special attack console labelled A through G."
		else:
			response = "You must specify a special attack type. Choose an option from the buttons on the special attack console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# shape your slimeoid's brain.
async def growbrain(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()
			brain = ewcfg.brain_map.get(value)
			if brain != None:
				if value in ["a", "b", "c", "d", "e", "f", "g"]:
					response = " {}".format(brain.str_create)
					slimeoid.ai = brain.id_brain
					slimeoid.persist()
				else:
					response = "Choose an option from the buttons on the brain console labelled A through G."
			else:
				response = "Choose an option from the buttons on the brain console labelled A through G."
		else:
			response = "You must specify a brain structure. Choose an option from the buttons on the brain console labelled A through G."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# Name your slimeoid.
async def nameslimeoid(cmd):
	name = ""
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid already has a name."


	else:

		if cmd.tokens_count < 2:
			response = "You must specify a name."
		else:
			name = cmd.message.content[(len(ewcfg.cmd_nameslimeoid)):].strip()

			if len(name) > 32:
				response = "That name is too long. ({:,}/32)".format(len(name))

			else:
				slimeoid.name = str(name)

				user_data.persist()
				slimeoid.persist()

				response = "You enter the name {} into the console.".format(str(name))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to ATK
async def raisemoxie(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if ((slimeoid.atk + slimeoid.defense + slimeoid.intel) >= (slimeoid.level)):
			response = "You have allocated all of your Slimeoid's potential. Try !lowering some of its attributes first."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.atk += 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid gains more moxie."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to ATK
async def lowermoxie(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if (slimeoid.atk <= 0):
			response = "You cannot reduce your slimeoid's moxie any further."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.atk -= 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid loses some moxie."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to DEF
async def raisegrit(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if ((slimeoid.atk + slimeoid.defense + slimeoid.intel) >= (slimeoid.level)):
			response = "You have allocated all of your Slimeoid's potential. Try !lowering some of its attributes first."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.defense += 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid gains more grit."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to ATK
async def lowergrit(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if (slimeoid.defense <= 0):
			response = "You cannot reduce your slimeoid's grit any further."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.defense -= 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid loses some grit."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to DEF
async def raisechutzpah(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if ((slimeoid.atk + slimeoid.defense + slimeoid.intel) >= (slimeoid.level)):
			response = "You have allocated all of your Slimeoid's potential. Try !lowering some of its attributes first."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.intel += 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid gains more chutzpah."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

#allocate a point to ATK
async def lowerchutzpah(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You must begin incubating a new slimeoid first."

	elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "Your slimeoid is already fully formed."


	else:

		if (slimeoid.intel <= 0):
			response = "You cannot reduce your slimeoid's chutzpah any further."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))

		else:
			slimeoid.intel -= 1
			points = (slimeoid.level - slimeoid.atk - slimeoid.defense - slimeoid.intel)

			user_data.persist()
			slimeoid.persist()

			response = "Your gestating slimeoid loses some chutzpah."
			response += "\nMoxie: {}".format(str(slimeoid.atk))
			response += "\nGrit: {}".format(str(slimeoid.defense))
			response += "\nChutzpah: {}".format(str(slimeoid.intel))
			response += "\nPoints remaining: {}".format(str(points))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))




# complete a slimeoid
async def spawnslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	response = ""
	#roles_map_user = ewutils.getRoleMap(message.author.roles)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to create a Slimeoid."

	elif user_data.life_state == ewcfg.life_state_corpse:
			response = "Ghosts cannot interact with the SlimeCorp Lab apparati."


	else:

		if slimeoid.life_state == ewcfg.slimeoid_state_active:
			response = "You have already created a Slimeoid. Dissolve your current slimeoid before incubating a new one."

		elif slimeoid.life_state == ewcfg.slimeoid_state_none:
			response = "You have not yet begun incubating a slimeoid."

		else:
			needsbody = False
			needshead = False
			needslegs = False
			needsarmor = False
			needsweapon = False
			needsspecial = False
			needsbrain = False
			needsname = False
			needsstats = False
			incomplete = False

			if (slimeoid.body == ""):
				needsbody = True
				incomplete = True
			if (slimeoid.head == ""):
				needshead = True
				incomplete = True
			if (slimeoid.legs == ""):
				needslegs = True
				incomplete = True
			if (slimeoid.armor == ""):
				needsarmor = True
				incomplete = True
			if (slimeoid.weapon == ""):
				needsweapon = True
				incomplete = True
			if (slimeoid.special == ""):
				needsspecial = True
				incomplete = True
			if (slimeoid.ai == ""):
				needsbrain = True
				incomplete = True
			if (slimeoid.name == ""):
				needsname = True
				incomplete = True
			if ((slimeoid.atk + slimeoid.defense + slimeoid.intel) < (slimeoid.level)):
				needsstats = True
				incomplete = True

			if incomplete == True:
				response = "Your slimeoid is not yet ready to be spawned from the gestation vat."
				if needsbody == True:
					response += "\nIts body has not yet been given a distinct form."
				if needshead == True:
					response += "\nIt does not yet have a head."
				if needslegs == True:
					response += "\nIt has no means of locomotion."
				if needsarmor == True:
					response += "\nIt lacks any form of protection."
				if needsweapon == True:
					response += "\nIt lacks a means of attack."
				if needsspecial == True:
					response += "\nIt lacks a special ability."
				if needsbrain == True:
					response += "\nIt does not yet have a brain."
				if needsstats == True:
					response += "\nIt still has potential that must be distributed between Moxie, Grit and Chutzpah."
				if needsname == True:
					response += "\nIt needs a name."
			else:
				slimeoid.life_state = ewcfg.slimeoid_state_active
				response = "You press the big red button labelled 'SPAWN'. The console lights up and there is a rush of mechanical noise as the fluid drains rapidly out of the gestation tube. The newly born Slimeoid within writhes in confusion before being sucked down an ejection chute and spat out messily onto the laboratory floor at your feet. Happy birthday, {} the Slimeoid!! {}".format(slimeoid.name, ewcfg.emote_slimeheart)

				response += "\n\n{} is a {}-foot-tall Slimeoid.".format(slimeoid.name, str(slimeoid.level))
				response += slimeoid_describe(slimeoid)

				brain = ewcfg.brain_map.get(slimeoid.ai)
				response += "\n\n" + brain.str_spawn.format(
					slimeoid_name = slimeoid.name
				)

			user_data.persist()
			slimeoid.persist()

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

"""
	Describe the specified slimeoid. Used for the !slimeoid command and while it's being created.
"""
def slimeoid_describe(slimeoid):
	response = ""

	body = ewcfg.body_map.get(slimeoid.body)
	if body != None:
		response += " {}".format(body.str_body)

	head = ewcfg.head_map.get(slimeoid.head)
	if head != None:
		response += " {}".format(head.str_head)

	mobility = ewcfg.mobility_map.get(slimeoid.legs)
	if mobility != None:
		response += " {}".format(mobility.str_mobility)

	offense = ewcfg.offense_map.get(slimeoid.weapon)
	if offense != None:
		response += " {}".format(offense.str_offense)

	defense = ewcfg.defense_map.get(slimeoid.armor)
	if defense != None:
		response += " {}".format(defense.str_armor)

	special = ewcfg.special_map.get(slimeoid.special)
	if special != None:
		response += " {}".format(special.str_special)

	brain = ewcfg.brain_map.get(slimeoid.ai)
	if brain != None:
		response += " {}".format(brain.str_brain)

	hue = ewcfg.hue_map.get(slimeoid.hue)
	if hue != None:
		response += " {}".format(hue.str_desc)

	stat_desc = []

	stat = slimeoid.atk
	if stat == 0:
		statlevel = "almost no"
	if stat == 1:
		statlevel = "just a little bit of"
	if stat == 2:
		statlevel = "a decent amount of"
	if stat == 3:
		statlevel = "quite a bit of"
	if stat == 4:
		statlevel = "a whole lot of"
	if stat == 5:
		statlevel = "loads of"
	if stat == 6:
		statlevel = "massive amounts of"
	if stat == 7:
		statlevel = "seemingly inexhaustible stores of"
	if stat >= 8:
		statlevel = "truly godlike levels of"
	stat_desc.append("{} moxie".format(statlevel))

	stat = slimeoid.defense
	if stat == 0:
		statlevel = "almost no"
	if stat == 1:
		statlevel = "just a little bit of"
	if stat == 2:
		statlevel = "a decent amount of"
	if stat == 3:
		statlevel = "quite a bit of"
	if stat == 4:
		statlevel = "a whole lot of"
	if stat == 5:
		statlevel = "loads of"
	if stat == 6:
		statlevel = "massive amounts of"
	if stat == 7:
		statlevel = "seemingly inexhaustible stores of"
	if stat >= 8:
		statlevel = "truly godlike levels of"
	stat_desc.append("{} grit".format(statlevel))

	stat = slimeoid.intel
	if stat == 0:
		statlevel = "almost no"
	if stat == 1:
		statlevel = "just a little bit of"
	if stat == 2:
		statlevel = "a decent amount of"
	if stat == 3:
		statlevel = "quite a bit of"
	if stat == 4:
		statlevel = "a whole lot of"
	if stat == 5:
		statlevel = "loads of"
	if stat == 6:
		statlevel = "massive amounts of"
	if stat == 7:
		statlevel = "seemingly inexhaustible stores of"
	if stat >= 8:
		statlevel = "truly godlike levels of"
	stat_desc.append("{} chutzpah".format(statlevel))

	response += " It has {}.".format(ewutils.formatNiceList(names = stat_desc))

	clout = slimeoid.clout
	if slimeoid.sltype != ewcfg.sltype_nega:
		if clout >= 50:
			response += " A **LIVING LEGEND** on the arena."
		elif clout >= 30:
			response += " A **BRUTAL CHAMPION** on the arena."
		elif clout >= 15:
			response += " This slimeoid has proven itself on the arena."
		elif clout == 0:
			response += " A pitiable baby, this slimeoid has no clout whatsoever."

	if (int(time.time()) - slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response += " It is currently incapacitated after being defeated in the Battle Arena."

	return response

# Show a player's slimeoid data.
async def slimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	member = None
	selfcheck = True
	response = ""

	if cmd.mentions_count == 0:
		selfcheck = True
		slimeoid = EwSlimeoid(member = cmd.message.author)
	else:
		selfcheck = False
		member = cmd.mentions[0]
		user_data = EwUser(member = member)
		slimeoid = EwSlimeoid(member = member)

	if user_data.life_state == ewcfg.life_state_corpse:
		response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
		if selfcheck == True:
			response = "You have not yet created a slimeoid."
		else:
			response = "{} has not yet created a slimeoid.".format(member.display_name)

	else:
		if slimeoid.life_state == ewcfg.slimeoid_state_forming:
			if selfcheck == True:
				response = "Your Slimeoid is still forming in the gestation vat. It is about {} feet from end to end.".format(str(slimeoid.level))
			else:
				response = "{}'s Slimeoid is still forming in the gestation vat. It is about {} feet from end to end.".format(member.display_name, str(slimeoid.level))
		elif slimeoid.life_state == ewcfg.slimeoid_state_active:
			if selfcheck == True:
				response = "You are accompanied by {}, a {}-foot-tall Slimeoid.".format(slimeoid.name, str(slimeoid.level))
			else:
				response = "{} is accompanied by {}, a {}-foot-tall Slimeoid.".format(member.display_name, slimeoid.name, str(slimeoid.level))

		response += slimeoid_describe(slimeoid)

		cosmetics = ewitem.inventory(
			id_user = user_data.id_user,
			id_server = cmd.message.server.id,
			item_type_filter = ewcfg.it_cosmetic
		)

		# get the cosmetics worn by the slimeoid
		adorned_cosmetics = []
		for item in cosmetics:
			cos = EwItem(id_item = item.get('id_item'))
			if cos.item_props.get('slimeoid') == 'true':
				hue = ewcfg.hue_map.get(cos.item_props.get('hue'))
				adorned_cosmetics.append((hue.str_name + " colored " if hue != None else "") + cos.item_props.get('cosmetic_name'))

		if len(adorned_cosmetics) > 0:
			response += "\n\nIt has {} adorned.".format(ewutils.formatNiceList(adorned_cosmetics, "and"))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


# Show a player's slimeoid data.
async def negaslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	response = ""

	if cmd.mentions_count > 0:
		# Can't mention any players
		response = "Negaslimeoids obey no masters. You'll have to address the beast directly."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	if cmd.tokens_count < 2:
		response = "Name the horror you wish to behold."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	slimeoid_search = cmd.message.content[len(cmd.tokens[0]):].lower().strip()


	potential_slimeoids = ewutils.get_slimeoids_in_poi(id_server = cmd.message.server.id, sltype = ewcfg.sltype_nega)

	negaslimeoid = None
	for id_slimeoid in potential_slimeoids:
		
		slimeoid_data = EwSlimeoid(id_slimeoid = id_slimeoid)
		name = slimeoid_data.name.lower()
		if slimeoid_search in name:
			negaslimeoid = slimeoid_data
			break

	if negaslimeoid is None:
		response = "There is no Negaslimeoid by that name."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	response = "{} is a {}-foot-tall Negaslimeoid.".format(negaslimeoid.name, negaslimeoid.level)
	response += slimeoid_describe(negaslimeoid)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def check(str):
	if str.content == ewcfg.cmd_accept or str.content == ewcfg.cmd_refuse:
		return True

async def slimeoidbattle(cmd):

	if cmd.message.channel.name != ewcfg.channel_arena:
		#Only at the arena
		response = "You can only have Slimeoid Battles at the Battle Arena."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if cmd.mentions_count != 1:
		#Must mention only one player
		response = "Mention the player you want to challenge."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	author = cmd.message.author
	member = cmd.mentions[0]

	if author.id == member.id:
		response = "You can't challenge yourself, dumbass."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	challenger = EwUser(member = author)
	challenger_slimeoid = EwSlimeoid(member = author)
	challengee = EwUser(member = member)
	challengee_slimeoid = EwSlimeoid(member = member)

	#Players have been challenged
	if active_slimeoidbattles.get(challenger_slimeoid.id_slimeoid):
		response = "You are already in the middle of a challenge."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if active_slimeoidbattles.get(challengee_slimeoid.id_slimeoid):
		response = "{} is already in the middle of a challenge.".format(member.display_name).replace("@", "\{at\}")
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if challenger.poi != challengee.poi:
		#Challangee must be in the arena
		response = "Both players must be in the Battle Arena."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if challenger_slimeoid.life_state != ewcfg.slimeoid_state_active:
		response = "You do not have a Slimeoid ready to battle with!"

	if challengee_slimeoid.life_state != ewcfg.slimeoid_state_active:
		response = "{} does not have a Slimeoid ready to battle with!".format(member.display_name)

	time_now = int(time.time())

	if (time_now - challenger_slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "Your Slimeoid is still recovering from its last defeat!"
			return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if (time_now - challengee_slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "{}'s Slimeoid is still recovering from its last defeat!".format(member.display_name)
			return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	#Players have to be enlisted
	if challenger.life_state == ewcfg.life_state_corpse or challengee.life_state == ewcfg.life_state_corpse:
		if challenger.life_state == ewcfg.life_state_corpse:
			response = "Your Slimeoid won't battle for you while you're dead.".format(author.display_name).replace("@", "\{at\}")
			return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

		elif challengee.life_state == ewcfg.life_state_corpse:
			response = "{}'s Slimeoid won't battle for them while they're dead.".format(member.display_name).replace("@", "\{at\}")
			return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	#Assign a challenger so players can't be challenged
	active_slimeoidbattles[challenger_slimeoid.id_slimeoid] = True
	active_slimeoidbattles[challengee_slimeoid.id_slimeoid] = True

	challengee.rr_challenger = challenger.id_user

	challengee.persist()

	response = "You have been challenged by {} to a Slimeoid Battle. Do you !accept or !refuse?".format(author.display_name).replace("@", "\{at\}")
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(member, response))

	#Wait for an answer
	accepted = 0
	try:
		msg = await cmd.client.wait_for_message(timeout = 30, author = member, check = check)

		if msg != None:
			if msg.content == "!accept":
				accepted = 1
	except:
		accepted = 0

	challengee = EwUser(member = member)
	challenger = EwUser(member = author)

	challengee.rr_challenger = ""
	challenger.rr_challenger = ""

	challengee.persist()
	challenger.persist()

	#Start game
	if accepted == 1:
		result = await battle_slimeoids(id_s1 = challengee_slimeoid.id_slimeoid, id_s2 = challenger_slimeoid.id_slimeoid, poi = ewcfg.poi_id_arena, battle_type = ewcfg.battle_type_arena)
		if result == -1:
			response = "\n**{} has won the Slimeoid battle!! The crowd erupts into cheers for {} and {}!!** :tada:".format(challenger_slimeoid.name, challenger_slimeoid.name, author.display_name)
			await ewutils.send_message(cmd.client, cmd.message.channel, response)
		elif result == 1:
			response = "\n**{} has won the Slimeoid battle!! The crowd erupts into cheers for {} and {}!!** :tada:".format(challengee_slimeoid.name, challengee_slimeoid.name, member.display_name)
			await ewutils.send_message(cmd.client, cmd.message.channel, response)

	else:
		response = "{} was too cowardly to accept your challenge.".format(member.display_name).replace("@", "\{at\}")

		# Send the response to the player.
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	active_slimeoidbattles[challenger_slimeoid.id_slimeoid] = False
	active_slimeoidbattles[challengee_slimeoid.id_slimeoid] = False

async def negaslimeoidbattle(cmd):

	if not ewmap.channel_name_is_poi(cmd.message.channel.name):
		response = "You must go into the city to challenge an eldritch abomination."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if cmd.mentions_count > 0:
		# Can't mention any players
		response = "Negaslimeoids obey no masters. You'll have to address the beast directly."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if cmd.tokens_count < 2:
		response = "Name the horror you wish to face."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	slimeoid_search = cmd.message.content[len(cmd.tokens[0]):].lower().strip()

	author = cmd.message.author

	challenger = EwUser(member = author)
	challenger_slimeoid = EwSlimeoid(member = author)

	#Player has to be alive
	if challenger.life_state == ewcfg.life_state_corpse:
		response = "Your Slimeoid won't battle for you while you're dead.".format(author.display_name).replace("@", "\{at\}")
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))


	potential_challengees = ewutils.get_slimeoids_in_poi(id_server = cmd.message.server.id, poi = challenger.poi, sltype = ewcfg.sltype_nega)

	challengee_slimeoid = None
	for id_slimeoid in potential_challengees:
		
		slimeoid_data = EwSlimeoid(id_slimeoid = id_slimeoid)
		name = slimeoid_data.name.lower()
		if slimeoid_search in name:
			challengee_slimeoid = slimeoid_data
			break

	if challengee_slimeoid is None:
		response = "There is no Negaslimeoid by that name here."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	#Players have been challenged
	if active_slimeoidbattles.get(challenger_slimeoid.id_slimeoid):
		response = "Your slimeoid is already in the middle of a battle."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if active_slimeoidbattles.get(challengee_slimeoid.id_slimeoid):
		response = "{} is already in the middle of a battle.".format(challengee_slimeoid.name)
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	if challenger_slimeoid.life_state != ewcfg.slimeoid_state_active:
		response = "You do not have a Slimeoid ready to battle with!"

	time_now = int(time.time())

	if (time_now - challenger_slimeoid.time_defeated) < ewcfg.cd_slimeoiddefeated:
			response = "Your Slimeoid is still recovering from its last defeat!"
			return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(author, response))

	#Assign a challenger so players can't be challenged
	active_slimeoidbattles[challenger_slimeoid.id_slimeoid] = True
	active_slimeoidbattles[challengee_slimeoid.id_slimeoid] = True


	#Start game
	try:
		result = await battle_slimeoids(id_s1 = challengee_slimeoid.id_slimeoid, id_s2 = challenger_slimeoid.id_slimeoid, poi = challengee_slimeoid.poi, battle_type = ewcfg.battle_type_nega)
		if result == -1:
			# Losing in a nega battle means death
			district_data = EwDistrict(district = challenger.poi, id_server = cmd.message.server.id)
			slimes = int(2 * 10 ** (challengee_slimeoid.level - 2))
			district_data.change_slimes(n = slimes)
			district_data.persist()
			challengee_slimeoid.delete()
			response = "The dulled colors become vibrant again, as {} fades back into its own reality.".format(challengee_slimeoid.name)
			await ewutils.send_message(cmd.client, cmd.message.channel, response)
		elif result == 1:
			# Dedorn all items
			cosmetics = ewitem.inventory(
				id_user = cmd.message.author.id,
				id_server = cmd.message.server.id,
				item_type_filter = ewcfg.it_cosmetic
			)
			# get the cosmetics worn by the slimeoid
			for item in cosmetics:
				cos = EwItem(id_item = item.get('id_item'))
				if cos.item_props.get('slimeoid') == 'true':
					cos.item_props['slimeoid'] = 'false'
					cos.persist()
			# Losing in a nega battle means death
			item_props = {
				'context': ewcfg.context_slimeoidheart,
				'subcontext': challenger_slimeoid.id_slimeoid,
				'item_name': "Heart of {}".format(challenger_slimeoid.name),
				'item_desc': "A poudrin-like crystal. If you listen carefully you can hear something that sounds like a faint heartbeat."
			}
			ewitem.item_create(
				id_user = cmd.message.author.id,
				id_server = cmd.message.server.id,
				item_type = ewcfg.it_item,
				item_props = item_props
			)
			challenger_slimeoid.die()
			challenger_slimeoid.persist()
			response = "{} feasts on {}'s slime. All that remains is a small chunk of crystallized slime.".format(challengee_slimeoid.name, challenger_slimeoid.name)
			response += "\n\n{} is no more. {}".format(challenger_slimeoid.name, ewcfg.emote_slimeskull)
			if challenger_slimeoid.level > challengee_slimeoid.level:
				challengee_slimeoid.level += 1
				rand = random.randrange(3)
				if rand == 0:
					challengee_slimeoid.atk += 1
				elif rand == 1:
					challengee_slimeoid.defense += 1
				else:
					challengee_slimeoid.intel += 1
				challengee_slimeoid.persist()
				response += "\n\n{} was empowered by the slaughter and grew a foot taller.".format(challengee_slimeoid.name)
			await ewutils.send_message(cmd.client, cmd.message.channel, response)
	except:
		ewutils.logMsg("An error occured in the Negaslimeoid battle against {}".format(challengee_slimeoid.name))
	finally:
		active_slimeoidbattles[challenger_slimeoid.id_slimeoid] = False
		active_slimeoidbattles[challengee_slimeoid.id_slimeoid] = False

# Slimeoids lose more clout for losing at higher levels.
def calculate_clout_loss(clout):
	if clout >= 100:
		clout -= 6
	elif clout >= 40:
		clout -= 5
	elif clout >= 30:
		clout -= 4
	elif clout >= 20:
		clout -= 3
	elif clout >= 10:
		clout -= 2
	elif clout >= 1:
		clout -= 1

	return clout

def calculate_clout_gain(clout):
	clout += 2

	if clout > 100:
		clout = 100

	return clout

class EwHue:
	id_hue = ""
	alias = []
	str_saturate = ""
	str_name= ""
	str_desc = ""
	effectiveness = {}
	def __init__(
		self,
		id_hue = "",
		alias = [],
		str_saturate = "",
		str_name= "",
		str_desc = "",
		effectiveness = {},
	):
		self.id_hue = id_hue
		self.alias = alias
		self.str_saturate = str_saturate
		self.str_name= str_name
		self.str_desc = str_desc
		self.effectiveness = effectiveness

async def saturateslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if user_data.life_state == ewcfg.life_state_corpse:
		response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
		response = "Wow, great idea! Too bad you don’t even have a slimeoid with which to saturate! You’d think you’d remember really obvious stuff like that, but no. What a dumbass."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
		response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	elif item_sought:
		value = item_search
		hue = ewcfg.hue_map.get(value)

		if hue != None:
			response = "You saturate your {} with the {} dye! {}".format(slimeoid.name, hue.str_name, hue.str_saturate)
			slimeoid.hue = hue.id_hue
			slimeoid.persist()

			ewitem.item_delete(id_item = item_sought.get('id_item'))
			user_data.persist()

		else:
			response = "You can only saturate your slimeoid with dyes."

	else:
		if item_search:  # if they didn't forget to specify an item and it just wasn't found
			response = "You can only saturate your slimeoid with dyes."
		else:
			response = "Saturate your slimeoid with what, exactly? (check **!inventory**)"

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def restoreslimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if cmd.message.channel.name != ewcfg.channel_slimeoidlab:
		response = "You must go to the SlimeCorp Laboratories in Brawlden to restore a Slimeoid."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if user_data.life_state == ewcfg.life_state_corpse:
		response = "Ghosts cannot interact with the SlimeCorp Lab apparati."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if slimeoid.life_state != ewcfg.slimeoid_state_none:
		response = "You already have an active slimeoid."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	
	if item_sought is None:
		if item_search:
			response = "You need a slimeoid's heart to restore it to life."
		else:
			response = "Restore which slimeoid?"
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	item_data = ewitem.EwItem(id_item = item_sought.get('id_item'))

	if item_data.item_props.get('context') != ewcfg.context_slimeoidheart:
		response = "You need a slimeoid's heart to restore it to life."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	slimeoid = EwSlimeoid(id_slimeoid = item_data.item_props.get('subcontext'))
	slimes_to_restore = 2 * 10 ** (slimeoid.level - 2) # 1/5 of the original cost

	if user_data.slimes < slimes_to_restore:
		response = "You need at least {} slime to restore this slimeoid.".format(slimes_to_restore)
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
		

	slimeoid.life_state = ewcfg.slimeoid_state_active
	slimeoid.id_user = user_data.id_user
	slimeoid.persist()

	ewitem.item_delete(id_item = item_data.id_item)

	response = "You insert the heart of your beloved {} into one of the restoration tanks. A series of clattering sensors analyze the crystalline core. Then, just like when it was first incubated, the needle pricks you and extracts slime from your body, which coalesces around the poudrin-like heart. Bit by bit the formless mass starts to assume a familiar shape.\n\n{} has been restored to its former glory!".format(slimeoid.name, slimeoid.name)
	return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
			
		


async def battle_slimeoids(id_s1, id_s2, poi, battle_type):

	challengee_slimeoid = EwSlimeoid(id_slimeoid = id_s1)
	challenger_slimeoid = EwSlimeoid(id_slimeoid = id_s2)
	challengee = EwPlayer(id_user = challengee_slimeoid.id_user)
	challenger = EwPlayer(id_user = challenger_slimeoid.id_user)

	poi_data = ewcfg.id_to_poi.get(poi)

	client = ewutils.get_client()
	server = ewcfg.server_list.get(challengee_slimeoid.id_server)
	channel = ewutils.get_channel(server = server, channel_name = poi_data.channel)
	
	s1name = str(challengee_slimeoid.name)
	s1weapon = ewcfg.offense_map.get(challengee_slimeoid.weapon)
	s1armor = ewcfg.defense_map.get(challengee_slimeoid.armor)
	s1special = ewcfg.special_map.get(challengee_slimeoid.special)
	s1legs = ewcfg.mobility_map.get(challengee_slimeoid.legs)
	s1brain = ewcfg.brain_map.get(challengee_slimeoid.ai)
	s1moxie = challengee_slimeoid.atk + 1
	s1grit = challengee_slimeoid.defense + 1
	s1chutzpah = challengee_slimeoid.intel + 1

	s2name = str(challenger_slimeoid.name)
	s2weapon = ewcfg.offense_map.get(challenger_slimeoid.weapon)
	s2armor = ewcfg.defense_map.get(challenger_slimeoid.armor)
	s2special = ewcfg.special_map.get(challenger_slimeoid.special)
	s2legs = ewcfg.mobility_map.get(challenger_slimeoid.legs)
	s2brain = ewcfg.brain_map.get(challenger_slimeoid.ai)
	s2moxie = challenger_slimeoid.atk + 1
	s2grit = challenger_slimeoid.defense + 1
	s2chutzpah = challenger_slimeoid.intel + 1

	challenger_resistance = ""
	challengee_resistance = ""
	challenger_weakness = ""
	challengee_weakness = ""

	#challengee resistance/weakness
	if challengee_slimeoid.armor == 'scales':
		if challenger_slimeoid.weapon == 'electricity':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s scales conduct the electricity away from its vitals!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'TK':
			s2chutzpah += 2
			challengee_weakness = " {}'s scales refract and amplify the disrupting brainwaves inside its skull!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'boneplates':
		if challenger_slimeoid.weapon == 'blades':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s bone plates block the worst of the damage!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'spines':
			s2chutzpah += 2
			challengee_weakness = " {}'s bone plates only drive the quills deeper into its body as it moves!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'formless':
		if challenger_slimeoid.weapon == 'bludgeon':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s squishy body easily absorbs the blows!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'webs':
			s2chutzpah += 2
			challengee_weakness = " {}'s squishy body easily adheres to and becomes entangled by the webs!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'regeneration':
		if challenger_slimeoid.weapon == 'spikes':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {} quickly begins regenerating the small puncture wounds inflicted by the spikes!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'spit':
			s2chutzpah += 2
			challengee_weakness = " {}'s regeneration is impeded by the corrosive chemicals!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'stench':
		if challenger_slimeoid.weapon == 'teeth':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s noxious fumes make its opponent hesitant to put its mouth anywhere near it!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'throw':
			s2chutzpah += 2
			challengee_weakness = " {}'s foul odor gives away its position, making it easy to target with thrown projectiles!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'oil':
		if challenger_slimeoid.weapon == 'grip':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s slippery coating makes it extremely difficult to grab on to!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'fire':
			s2chutzpah += 2
			challengee_weakness = " {}'s oily coating is flammable, igniting as it contacts the flame!".format(challengee_slimeoid.name)
	if challengee_slimeoid.armor == 'quantumfield':
		if challenger_slimeoid.weapon == 'slam':
			s2moxie -= 2
			if s2moxie <= 1:
				s2moxie = 1
			challengee_resistance = " {}'s quantum superposition makes it difficult to hit head-on!".format(challengee_slimeoid.name)
		if challenger_slimeoid.special == 'laser':
			s2chutzpah += 2
			challengee_weakness = " {}'s quantum particles are excited by the high-frequency radiation, destabilizing its structure!".format(challengee_slimeoid.name)

	#challenger resistance/weakness
	if challenger_slimeoid.armor == 'scales':
		if challengee_slimeoid.weapon == 'electricity':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s scales conduct the electricity away from its vitals!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'TK':
			s1chutzpah += 2
			challenger_weakness = " {}'s scales refract and amplify the disrupting brainwaves inside its skull!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'boneplates':
		if challengee_slimeoid.weapon == 'blades':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s bone plates block the worst of the damage!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'spines':
			s1chutzpah += 2
			challenger_weakness = " {}'s bone plates only drive the quills deeper into its body as it moves!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'formless':
		if challengee_slimeoid.weapon == 'bludgeon':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s squishy body easily absorbs the blows!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'webs':
			s1chutzpah += 2
			challenger_weakness = " {}'s squishy body easily adheres to and becomes entangled by the webs!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'regeneration':
		if challengee_slimeoid.weapon == 'spikes':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {} quickly begins regenerating the small puncture wounds inflicted by the spikes!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'spit':
			s1chutzpah += 2
			challenger_weakness = " {}'s regeneration is impeded by the corrosive chemicals!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'stench':
		if challengee_slimeoid.weapon == 'teeth':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s noxious fumes make its opponent hesitant to put its mouth anywhere near it!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'throw':
			s1chutzpah += 2
			challenger_weakness = " {}'s foul odor gives away its position, making it easy to target with thrown projectiles!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'oil':
		if challengee_slimeoid.weapon == 'grip':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s slippery coating makes it extremely difficult to grab on to!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'fire':
			s1chutzpah += 2
			challenger_weakness = " {}'s oily coating is flammable, igniting as it contacts the flame!".format(challenger_slimeoid.name)
	if challenger_slimeoid.armor == 'quantumfield':
		if challengee_slimeoid.weapon == 'slam':
			s1moxie -= 2
			if s1moxie <= 1:
				s1moxie = 1
			challenger_resistance = " {}'s quantum superposition makes it difficult to hit head-on!".format(challenger_slimeoid.name)
		if challengee_slimeoid.special == 'laser':
			s1chutzpah += 2
			challenger_weakness = " {}'s quantum particles are excited by the high-frequency radiation, destabilizing its structure!".format(challenger_slimeoid.name)

	challenger_splitcomplementary = ""
	challenger_analogous = ""
	challengee_splitcomplementary = ""
	challengee_analogous = ""

	s1hue = ewcfg.hue_map.get(challengee_slimeoid.hue)
	s2hue = ewcfg.hue_map.get(challenger_slimeoid.hue)

	color_matchup = ewcfg.hue_neutral
	# get color matchups
	if s1hue is not None:
		color_matchup = s1hue.effectiveness.get(challenger_slimeoid.hue)

	if color_matchup is None:
		color_matchup = ewcfg.hue_neutral

	if color_matchup < 0:
		s2grit += 2
		challenger_analogous = "It's not very effective against {}...".format(challenger_slimeoid.name)
			
	elif color_matchup > 0:
		if color_matchup == ewcfg.hue_atk_complementary:
			s1moxie += 2
		elif color_matchup == ewcfg.hue_special_complementary:
			s1chutzpah += 2
		elif color_matchup == ewcfg.hue_full_complementary:
			s1moxie += 2
			s1chutzpah += 2
		challenger_splitcomplementary = "It's Super Effective against {}!".format(challenger_slimeoid.name)


	color_matchup = ewcfg.hue_neutral

	if s2hue is not None:
		color_matchup = s2hue.effectiveness.get(challengee_slimeoid.hue)

	if color_matchup is None:
		color_matchup = ewcfg.hue_neutral

	if color_matchup < 0:
		s1grit += 2
		challengee_analogous = "It's not very effective against {}...".format(challengee_slimeoid.name)
			
	elif color_matchup > 0:
		if color_matchup == ewcfg.hue_atk_complementary:
			s2moxie += 2
		elif color_matchup == ewcfg.hue_special_complementary:
			s2chutzpah += 2
		elif color_matchup == ewcfg.hue_full_complementary:
			s2moxie += 2
			s2chutzpah += 2
		challengee_splitcomplementary = "It's Super Effective against {}!".format(challengee_slimeoid.name)
			

	s1_active = False
	in_range = False

	if challengee_slimeoid.defense > challenger_slimeoid.defense:
		s1_active = True
	elif challengee_slimeoid.defense == challenger_slimeoid.defense:
		coinflip = random.randrange(1,3)
		if coinflip == 1:
			s1_active = True

	if battle_type == ewcfg.battle_type_arena:
		response = "**{} sends {} out into the Battle Arena!**".format(challenger.display_name, s2name)
		await ewutils.send_message(client, channel, response)
		await asyncio.sleep(1)
		response = "**{} sends {} out into the Battle Arena!**".format(challengee.display_name, s1name)
		await ewutils.send_message(client, channel, response)
		await asyncio.sleep(1)
		response = "\nThe crowd erupts into cheers! The battle between {} and {} has begun! :crossed_swords:".format(s1name, s2name)
#		response += "\n{} {} {} {} {} {}".format(str(s1moxie),str(s1grit),str(s1chutzpah),str(challengee_slimeoid.weapon),str(challengee_slimeoid.armor),str(challengee_slimeoid.special))
#		response += "\n{} {} {} {} {} {}".format(str(s2moxie),str(s2grit),str(s2chutzpah),str(challenger_slimeoid.weapon),str(challenger_slimeoid.armor),str(challenger_slimeoid.special))
#		response += "\n{}, {}".format(str(challengee_resistance),str(challengee_weakness))
#		response += "\n{}, {}".format(str(challenger_resistance),str(challenger_weakness))
		await ewutils.send_message(client, channel, response)
		await asyncio.sleep(3)


	s1hpmax = 50 + (challengee_slimeoid.level * 20)

	s2hpmax = 50 + (challenger_slimeoid.level * 20)

	s1hp = s1hpmax
	s2hp = s2hpmax

	turncounter = 100
	while s1hp > 0 and s2hp > 0 and turncounter > 0:
		# Limit the number of turns in battle.
		turncounter -= 1

		response = ""
		battlecry = random.randrange(1,4)
		thrownobject = ewcfg.thrownobjects_list[random.randrange(len(ewcfg.thrownobjects_list))]
		if s1_active:
			if in_range == False:

				#determine strat based on ai
				if challengee_slimeoid.ai in ['a', 'g']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'attack'
					else:
						strat = 'move'
				elif challengee_slimeoid.ai in ['b', 'd', 'f']:
					ranged_strat = random.randrange(1,3)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challengee_slimeoid.ai in ['c', 'e']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'

				#potentially add brain-based flavor text
				if strat == 'attack' and battlecry == 1:
					if (s1hpmax/s1hp) > 3:
						response = s1brain.str_battlecry_weak.format(
							slimeoid_name=s1name
						)
					else:
						response = s1brain.str_battlecry.format(
							slimeoid_name=s1name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				elif strat == 'move' and battlecry == 1:
					if (s1hpmax/s1hp) > 3:
						response = s1brain.str_movecry_weak.format(
							slimeoid_name=s1name
						)
					else:
						response = s1brain.str_movecry.format(
							slimeoid_name=s1name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				#perform action
				if strat == 'move':
					if (s1hpmax/s1hp) > 3:
						in_range = True
						response = s1legs.str_advance_weak.format(
							active=s1name,
							inactive=s2name,
						)
					else:
						in_range = True
						response = s1legs.str_advance.format(
							active=s1name,
							inactive=s2name,
						)
#					response += " *s1close*"

				else:
					hp = s2hp
					damage = (s1chutzpah * 10)
					s2hp -= damage
					response = "**"
					if s2hp <= 0:
						response += s1special.str_special_attack_coup.format(
							active=s1name,
							inactive=s2name,
							object=thrownobject
						)
						challenger_weakness = ""
						challenger_splitcomplementary = ""
					elif (s1hpmax/s1hp) > 3:
						response += s1special.str_special_attack_weak.format(
							active=s1name,
							inactive=s2name,
							object=thrownobject
						)
					else:
						response += s1special.str_special_attack.format(
							active=s1name,
							inactive=s2name,
							object=thrownobject
						)
					response += "**"
					response += " :boom:"
#					response += " strat:{}".format(str(ranged_strat))

					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

					if challenger_weakness != "" or challenger_splitcomplementary != "" or s2hp > 0:
						response = ""
						if challenger_weakness != "":
							response = challenger_weakness

						if challenger_splitcomplementary != "":
							response += " {}".format(challenger_splitcomplementary)


						if s2hp > 0:
							if hp/damage > 10:
								response += " {} barely notices the damage.".format(challenger_slimeoid.name)
							elif hp/damage > 6:
								response += " {} is hurt, but shrugs it off.".format(challenger_slimeoid.name)
							elif hp/damage > 4:
								response += " {} felt that one!".format(challenger_slimeoid.name)
							elif hp/damage >= 3:
								response += " {} really felt that one!".format(challenger_slimeoid.name)
							elif hp/damage < 3:
								response += " {} reels from the force of the attack!!".format(challenger_slimeoid.name)
#					response += " *s1shoot{}*".format(str(damage))
#					response += " *({}/{} s2hp)*".format(s2hp, s2hpmax)

			else:
				#determine strat based on ai
				if challengee_slimeoid.ai in ['a', 'b', 'c']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challengee_slimeoid.ai in ['d']:
					ranged_strat = random.randrange(1,3)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challengee_slimeoid.ai in ['e', 'f', 'g']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'attack'
					else:
						strat = 'move'

				#potentially add brain-based flavor text
				if strat == 'attack' and battlecry == 1:
					if (s1hpmax/s1hp) > 3:
						response = s1brain.str_battlecry_weak.format(
							slimeoid_name=s1name
						)
					else:
						response = s1brain.str_battlecry.format(
							slimeoid_name=s1name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				elif strat == 'move' and battlecry == 1:
					if (s1hpmax/s1hp) > 3:
						response = s1brain.str_movecry_weak.format(
							slimeoid_name=s1name
						)
					else:
						response = s1brain.str_movecry.format(
							slimeoid_name=s1name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				#perform action
				if strat == 'attack':
					hp = s2hp
					damage = int((s1moxie / s2grit) * 15)
					s2hp -= damage
					response = "**"
					if s2hp <= 0:
						response += s1weapon.str_attack_coup.format(
							active=s1name,
							inactive=s2name,
						)
						challenger_resistance = ""
						challenger_analogous = ""
					elif (s1hpmax/s1hp) > 3:
						response += s1weapon.str_attack_weak.format(
							active=s1name,
							inactive=s2name,
						)
					else:
						response += s1weapon.str_attack.format(
							active=s1name,
							inactive=s2name,
						)
					response += "**"
					response += " :boom:"
#					response += " strat:{}".format(str(ranged_strat))

					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

					if challenger_resistance != "" or challenger_analogous != "" or s2hp > 0:
						response = ""
						if challenger_resistance != "":
							response += challenger_resistance
						if challenger_analogous != "":
							response += " {}".format(challenger_analogous)
						if s2hp > 0:
							if hp/damage > 10:
								response += " {} barely notices the damage.".format(challenger_slimeoid.name)
							elif hp/damage > 6:
								response += " {} is hurt, but shrugs it off.".format(challenger_slimeoid.name)
							elif hp/damage > 4:
								response += " {} felt that one!".format(challenger_slimeoid.name)
							elif hp/damage >= 3:
								response += " {} really felt that one!".format(challenger_slimeoid.name)
							elif hp/damage < 3:
								response += " {} reels from the force of the attack!!".format(challenger_slimeoid.name)
#					response += " *s1hit{}*".format(str(damage))
#					response += " *({}/{}s2hp)*".format(s2hp, s2hpmax)

				else:
					if (s1hpmax/s1hp) > 3:
						in_range = False
						response = s1legs.str_retreat_weak.format(
							active=s1name,
							inactive=s2name,
						)
					else:
						in_range = False
						response = s1legs.str_retreat.format(
							active=s1name,
							inactive=s2name,
						)
#					response += " *s1flee*"

			s1_active = False

		else:
			if in_range == False:

				#determine strat based on ai
				if challenger_slimeoid.ai in ['a', 'g']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'attack'
					else:
						strat = 'move'
				elif challenger_slimeoid.ai in ['b', 'd', 'f']:
					ranged_strat = random.randrange(1,3)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challenger_slimeoid.ai in ['c', 'e']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'

				#potentially add brain-based flavor text
				if strat == 'attack' and battlecry == 1:
					if (s2hpmax/s2hp) > 3:
						response = s2brain.str_battlecry_weak.format(
							slimeoid_name=s2name
						)
					else:
						response = s2brain.str_battlecry.format(
							slimeoid_name=s2name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				elif strat == 'move' and battlecry == 1:
					if (s2hpmax/s2hp) > 3:
						response = s2brain.str_movecry_weak.format(
							slimeoid_name=s2name
						)
					else:
						response = s2brain.str_movecry.format(
							slimeoid_name=s2name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				#perform action
				if strat == 'move':
					if (s2hpmax/s2hp) > 3:
						in_range = True
						response = s2legs.str_advance_weak.format(
							active=s2name,
							inactive=s1name,
						)
					else:
						in_range = True
						response = s2legs.str_advance.format(
							active=s2name,
							inactive=s1name,
						)
#					response += " *s2close*"

				else:
					hp = s1hp
					damage = (s2chutzpah * 10)
					s1hp -= damage
					response = "**"
					if s1hp <= 0:
						response += s2special.str_special_attack_coup.format(
							active=s2name,
							inactive=s1name,
							object=thrownobject
						)
						challengee_weakness = ""
						challengee_splitcomplementary = ""
					elif (s2hpmax/s2hp) > 3:
						response += s2special.str_special_attack_weak.format(
							active=s2name,
							inactive=s1name,
							object=thrownobject
						)
					else:
						response += s2special.str_special_attack.format(
							active=s2name,
							inactive=s1name,
							object=thrownobject
						)
					response += "**"
					response += " :boom:"
#					response += " strat:{}".format(str(ranged_strat))

					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

					if challengee_weakness != "" or challengee_splitcomplementary != "" or s1hp > 0:
						response = ""
						if challengee_weakness != "":
							response += challengee_weakness
						if challengee_splitcomplementary != "":
							response += " {}".format(challengee_splitcomplementary)
						if s1hp > 0:
							if hp/damage > 10:
								response += " {} barely notices the damage.".format(challengee_slimeoid.name)
							elif hp/damage > 6:
								response += " {} is hurt, but shrugs it off.".format(challengee_slimeoid.name)
							elif hp/damage > 4:
								response += " {} felt that one!".format(challengee_slimeoid.name)
							elif hp/damage >= 3:
								response += " {} really felt that one!".format(challengee_slimeoid.name)
							elif hp/damage < 3:
								response += " {} reels from the force of the attack!!".format(challengee_slimeoid.name)
#					response += " *s2shoot{}*".format(str(damage))
#					response += " *({}/{} s1hp)*".format(s1hp, s1hpmax)
			else:

				#determine strat based on ai
				if challenger_slimeoid.ai in ['a', 'b', 'c']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challenger_slimeoid.ai in ['d']:
					ranged_strat = random.randrange(1,3)
					if ranged_strat < 2:
						strat = 'move'
					else:
						strat = 'attack'
				elif challenger_slimeoid.ai in ['e', 'f', 'g']:
					ranged_strat = random.randrange(1,5)
					if ranged_strat < 2:
						strat = 'attack'
					else:
						strat = 'move'

				#potentially add brain-based flavor text
				if strat == 'attack' and battlecry == 1:
					if (s2hpmax/s2hp) > 3:
						response = s2brain.str_battlecry_weak.format(
							slimeoid_name=s2name
						)
					else:
						response = s2brain.str_battlecry.format(
							slimeoid_name=s2name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				elif strat == 'move' and battlecry == 1:
					if (s2hpmax/s2hp) > 3:
						response = s2brain.str_movecry_weak.format(
							slimeoid_name=s2name
						)
					else:
						response = s2brain.str_movecry.format(
							slimeoid_name=s2name
						)
					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

				#perform action
				if strat == 'attack':
					hp = s1hp
					damage = int((s2moxie / s1grit) * 15)
					s1hp -= damage
					response = "**"
					if s1hp <= 0:
						response += s2weapon.str_attack_coup.format(
							active=s2name,
							inactive=s1name,
						)
						challengee_resistance = ""
						challengee_analogous = ""
					elif (s2hpmax/s2hp) > 3:
						response += s2weapon.str_attack_weak.format(
							active=s2name,
							inactive=s1name,
						)
					else:
						response += s2weapon.str_attack.format(
							active=s2name,
							inactive=s1name,
						)
					response += "**"
					response += " :boom:"
#					response += " strat:{}".format(str(ranged_strat))

					await ewutils.send_message(client, channel, response)
					await asyncio.sleep(1)

					if challengee_resistance != "" or challengee_analogous != "" or s2hp > 0:
						response = ""
						if challengee_resistance != "":
							response = challengee_resistance

						if challengee_analogous != "":
							response += " {}".format(challengee_analogous)

						if s1hp > 0:
							if hp/damage > 10:
								response += " {} barely notices the damage.".format(challengee_slimeoid.name)
							elif hp/damage > 6:
								response += " {} is hurt, but shrugs it off.".format(challengee_slimeoid.name)
							elif hp/damage > 4:
								response += " {} felt that one!".format(challengee_slimeoid.name)
							elif hp/damage >= 3:
								response += " {} really felt that one!".format(challengee_slimeoid.name)
							elif hp/damage < 3:
								response += " {} reels from the force of the attack!!".format(challengee_slimeoid.name)

#					response += " *s2hit{}*".format(str(damage))
#					response += " *({}/{} s1hp)*".format(s1hp, s1hpmax)

				else:
					if (s2hpmax/s2hp) > 3:
						in_range = False
						response = s2legs.str_retreat_weak.format(
							active=s2name,
							inactive=s1name,
						)
					else:
						in_range = False
						response = s2legs.str_retreat.format(
							active=s2name,
							inactive=s1name,
						)
#					response += " *s2flee*"

			s1_active = True

		# Send the response to the player.
		if s1hp > 0 and s2hp > 0:
			await ewutils.send_message(client, channel, response)
			await asyncio.sleep(2)

	if s1hp <= 0:
		result = -1
		response = "\n" + s1legs.str_defeat.format(
			slimeoid_name=s1name
		)
		response += " {}".format(ewcfg.emote_slimeskull)
		response += "\n" + s2brain.str_victory.format(
			slimeoid_name=s2name
		)

		challenger_slimeoid = EwSlimeoid(id_slimeoid = id_s2)
		challengee_slimeoid = EwSlimeoid(id_slimeoid = id_s1)

		# Losing slimeoid loses clout and has a time_defeated cooldown.
		challengee_slimeoid.clout = calculate_clout_loss(challengee_slimeoid.clout)
		challengee_slimeoid.time_defeated = int(time.time())
		challengee_slimeoid.persist()

		challenger_slimeoid.clout = calculate_clout_gain(challenger_slimeoid.clout)
		challenger_slimeoid.persist()

		await ewutils.send_message(client, channel, response)
		await asyncio.sleep(2)
	else:
		result = 1
		response = "\n" + s2legs.str_defeat.format(
			slimeoid_name=s2name
		)
		response += " {}".format(ewcfg.emote_slimeskull)
		response += "\n" + s1brain.str_victory.format(
			slimeoid_name=s1name
		)

		challenger_slimeoid = EwSlimeoid(id_slimeoid = id_s2)
		challengee_slimeoid = EwSlimeoid(id_slimeoid = id_s1)
	
		# store defeated slimeoid's defeat time in the database
		challenger_slimeoid.clout = calculate_clout_loss(challenger_slimeoid.clout)
		challenger_slimeoid.time_defeated = int(time.time())
		challenger_slimeoid.persist()

		challengee_slimeoid.clout = calculate_clout_gain(challengee_slimeoid.clout)
		challengee_slimeoid.persist()

		await ewutils.send_message(client, channel, response)
		await asyncio.sleep(2)
	return result

async def slimeoid_tick_loop(id_server):
	while not ewutils.TERMINATE:
		await asyncio.sleep(ewcfg.slimeoid_tick_length)
		await slimeoid_tick(id_server)

async def slimeoid_tick(id_server):
	data = ewutils.execute_sql_query("SELECT {id_slimeoid} FROM slimeoids WHERE {sltype} = %s AND {id_server} = %s".format(
		id_slimeoid = ewcfg.col_id_slimeoid,
		sltype = ewcfg.col_type,
		id_server = ewcfg.col_id_server
	),(
		ewcfg.sltype_nega,
		id_server
	))

	resp_cont = ewutils.EwResponseContainer(id_server = id_server)
	for row in data:
		slimeoid_data = EwSlimeoid(id_slimeoid = row[0])
		haunt_resp = slimeoid_data.haunt()
		resp_cont.add_response_container(haunt_resp)
		if random.random() < 0.1:
			move_resp = slimeoid_data.move()
			resp_cont.add_response_container(move_resp)
		slimeoid_data.persist()

	await resp_cont.post()

async def dress_slimeoid(cmd):
	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)

	if user_data.life_state == ewcfg.life_state_corpse:
		response = "Slimeoids don't fuck with ghosts."

	elif slimeoid.life_state == ewcfg.slimeoid_state_none:
		response = "You'll have to create a slimeoid if you want to play dress up."

	elif slimeoid.life_state == ewcfg.slimeoid_state_forming:
		response = "Your Slimeoid is not yet ready. Use !spawnslimeoid to complete incubation."

	else:
		item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
		item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

		cosmetics = ewitem.inventory(
			id_user = cmd.message.author.id,
			id_server = cmd.message.server.id,
			item_type_filter = ewcfg.it_cosmetic
		)

		# get the cosmetics worn by the slimeoid
		adorned_cosmetics = []
		for item in cosmetics:
			cos = EwItem(id_item = item.get('id_item'))
			if cos.item_props.get('slimeoid') == 'true':
				adorned_cosmetics.append(cos)

		if item_sought != None and item_sought.get('item_type') == ewcfg.it_cosmetic:
			cosmetic = EwItem(id_item = item_sought.get('id_item'))
			response = "You "

			# Remove hat
			if cosmetic.item_props.get('slimeoid') == 'true':
				response += "take the {} back from {}".format(cosmetic.item_props.get('cosmetic_name'), slimeoid.name)
				cosmetic.item_props['slimeoid'] = 'false'
			# Give hat
			else:
				if len(adorned_cosmetics) < slimeoid.level:
					# Remove hat from player if adorned
					if cosmetic.item_props.get('adorned') == 'true':
						cosmetic.item_props['adorned'] = 'false'
						response += "take off your {} and give it to {}.".format(cosmetic.item_props.get('cosmetic_name'), slimeoid.name)
					else:
						response += "give {} a {}.".format(slimeoid.name, cosmetic.item_props.get('cosmetic_name'))
					
					cosmetic.item_props['slimeoid'] = 'true'
				else:
					response = 'Your slimeoid is too small to wear any more clothes.'
					
			cosmetic.persist()
		else:
			response = 'Adorn which cosmetic? Check your **!inventory**.'
		
	
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
