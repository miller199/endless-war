import math
import time
import random
import asyncio

import ewutils
import ewcfg
import ewstats
import ewrolemgr
import ewsmelting
from ew import EwUser
from ewplayer import EwPlayer

"""
	EwItemDef is a class used to model base items. These are NOT the items
	owned by players, but rather the description of what those items are.
"""
class EwItemDef:
	# This is the unique reference name for this item.
	item_type = ""

	# If this is true, the item can not be traded or stolen.
	soulbound = False

	# If this value is positive, the item may actually be a pile of the same type of item, up to the specified size.
	stack_max = -1

	# If this value is greater than one, creating this item will actually give the user that many of them.
	stack_size = 1

	# Nice display name for this item.
	str_name = ""

	# The long description of this item's appearance.
	str_desc = ""

	# A map of default additional properties.
	item_props = None

	def __init__(
		self,
		item_type = "",
		str_name = "",
		str_desc = "",
		soulbound = False,
		stack_max = -1,
		stack_size = 1,
		item_props = None
	):
		self.item_type = item_type
		self.str_name = str_name
		self.str_desc = str_desc
		self.soulbound = soulbound
		self.stack_max = stack_max
		self.stack_size = stack_size
		self.item_props = item_props

"""
	EwItem is the instance of an item (described by EwItemDef, linked by
	item_type) which is possessed by a player and stored in the database.
"""
class EwItem:
	id_item = -1
	id_server = ""
	id_owner = ""
	item_type = ""
	time_expir = -1

	stack_max = -1
	stack_size = 0
	soulbound = False

	item_props = None

	def __init__(
		self,
		id_item = None
	):
		if(id_item != None):
			self.id_item = id_item

			self.item_props = {}
			# the item props don't reset themselves automatically which is why the items_prop table had tons of extraneous rows (like food items having medal_names)
			#self.item_props.clear()

			try:
				conn_info = ewutils.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor()

				# Retrieve object
				cursor.execute("SELECT {}, {}, {}, {}, {}, {}, {} FROM items WHERE id_item = %s".format(
					ewcfg.col_id_server,
					ewcfg.col_id_user,
					ewcfg.col_item_type,
					ewcfg.col_time_expir,
					ewcfg.col_stack_max,
					ewcfg.col_stack_size,
					ewcfg.col_soulbound
				), (
					self.id_item,
				))
				result = cursor.fetchone();

				if result != None:
					# Record found: apply the data to this object.
					self.id_server = result[0]
					self.id_owner = result[1]
					self.item_type = result[2]
					self.time_expir = result[3]
					self.stack_max = result[4]
					self.stack_size = result[5]
					self.soulbound = (result[6] != 0)

					# Retrieve additional properties
					cursor.execute("SELECT {}, {} FROM items_prop WHERE id_item = %s".format(
						ewcfg.col_name,
						ewcfg.col_value
					), (
						self.id_item,
					))

					for row in cursor:
						# this try catch is only necessary as long as extraneous props exist in the table
						try:
							self.item_props[row[0]] = row[1]
						except:
							ewutils.logMsg("extraneous item_prop row detected.")

				else:
					# Item not found.
					self.id_item = -1

			finally:
				# Clean up the database handles.
				cursor.close()
				ewutils.databaseClose(conn_info)

	""" Save item data object to the database. """
	def persist(self):
		try:
			conn_info = ewutils.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor()

			# Save the object.
			cursor.execute("REPLACE INTO items({}, {}, {}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)".format(
				ewcfg.col_id_item,
				ewcfg.col_id_server,
				ewcfg.col_id_user,
				ewcfg.col_item_type,
				ewcfg.col_time_expir,
				ewcfg.col_stack_max,
				ewcfg.col_stack_size,
				ewcfg.col_soulbound
			), (
				self.id_item,
				self.id_server,
				self.id_owner,
				self.item_type,
				self.time_expir if self.time_expir is not None else self.item_props['time_expir'] if 'time_expir' in self.item_props.keys() else 0,
				self.stack_max,
				self.stack_size,
				(1 if self.soulbound else 0)
			))

			# Remove all existing property rows.
			cursor.execute("DELETE FROM items_prop WHERE {} = %s".format(
				ewcfg.col_id_item
			), (
				self.id_item,
			))

			# Write out all current property rows.
			for name in self.item_props:
				cursor.execute("INSERT INTO items_prop({}, {}, {}) VALUES(%s, %s, %s)".format(
					ewcfg.col_id_item,
					ewcfg.col_name,
					ewcfg.col_value
				), (
					self.id_item,
					name,
					self.item_props[name]
				))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			ewutils.databaseClose(conn_info)

"""
	These are unassuming, tangible, multi-faceted, customizable items that you can actually interact with in-game.
"""
class EwGeneralItem:
	item_type = "item"
	id_item = " "
	alias = []
	context = ""
	str_name = ""
	str_desc = ""
	ingredients = ""
	acquisition = ""
	price = 0
	vendors = []

	def __init__(
		self,
		id_item = " ",
		alias = [],
		context = "",
		str_name = "",
		str_desc = "",
		ingredients = "",
		acquisition = "",
		price = 0,
		vendors = [],
	):
		self.item_type = ewcfg.it_item
		self.id_item = id_item
		self.alias = alias
		self.context = context
		self.str_name = str_name
		self.str_desc = str_desc
		self.ingredients = ingredients
		self.acquisition = acquisition
		self.price = price
		self.vendors = vendors


"""
	Delete the specified item by ID. Also deletes all items_prop values.
"""
def item_delete(
	id_item = None
):
	try:
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		# Create the item in the database.
		cursor.execute("DELETE FROM items WHERE {} = %s".format(
			ewcfg.col_id_item
		), (
			id_item,
		))

		conn.commit()
	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)


"""
	Drop item into current district.
"""
def item_drop(
	id_item = None
):
	try:
		item_data = EwItem(id_item = id_item)
		user_data = EwUser(id_user = item_data.id_owner, id_server = item_data.id_server)
		if item_data.item_type == ewcfg.it_cosmetic:
			item_data.item_props["adorned"] = "false"
		item_data.persist()
		give_item(id_user = user_data.poi, id_server = item_data.id_server, id_item = item_data.id_item)
	except:
		ewutils.logMsg("Failed to drop item {}.".format(id_item))

"""
	Create a new item and give it to a player.

	Returns the unique database ID of the newly created item.
"""
def item_create(
	item_type = None,
	id_user = None,
	id_server = None,
	item_props = None
):
	item_def = ewcfg.item_def_map.get(item_type)

	if item_def == None:
		ewutils.logMsg('Tried to create invalid item_type: {}'.format(item_type))
		return

	try:
		# Get database handles if they weren't passed.
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		# Create the item in the database.
		cursor.execute("INSERT INTO items({}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s)".format(
			ewcfg.col_item_type,
			ewcfg.col_id_user,
			ewcfg.col_id_server,
			ewcfg.col_soulbound,
			ewcfg.col_stack_max,
			ewcfg.col_stack_size
		), (
			item_type,
			id_user,
			id_server,
			(1 if item_def.soulbound else 0),
			item_def.stack_max,
			item_def.stack_size
		))

		item_id = cursor.lastrowid
		conn.commit()

		if item_id > 0:
			# If additional properties are specified in the item definition or in this create call, create and persist them.
			if item_props != None or item_def.item_props != None:
				item_inst = EwItem(id_item = item_id)

				if item_def.item_props != None:
					item_inst.item_props.update(item_def.item_props)

				if item_props != None:
					item_inst.item_props.update(item_props)

				item_inst.persist()

			conn.commit()
	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)


	return item_id

"""
	Drop all of a player's non-soulbound items into their district
"""
def item_dropall(
	id_server = None,
	id_user = None
):
	
	try:
		user_data = EwUser(id_server = id_server, id_user = id_user)
		
		ewutils.execute_sql_query(
			"UPDATE items SET id_user = %s WHERE id_user = %s AND id_server = %s AND soulbound = 0",(
				user_data.poi,
				id_user,
				id_server
			))

	except:
		ewutils.logMsg('Failed to drop items for user with id {}'.format(id_user))


"""
	Dedorn all of a player's cosmetics
"""
def item_dedorn_cosmetics(
	id_server = None,
	id_user = None
):
	try:
		
		ewutils.execute_sql_query(
			"UPDATE items_prop SET value = 'false' WHERE (name = 'adorned' or name = 'slimeoid') AND {id_item} IN (\
				SELECT {id_item} FROM items WHERE {id_user} = %s AND {id_server} = %s\
			)".format(
				id_item = ewcfg.col_id_item,
				id_user = ewcfg.col_id_user,
				id_server = ewcfg.col_id_server
			),(
				id_user,
				id_server
			))

	except:
		ewutils.logMsg('Failed to dedorn cosmetics for user with id {}'.format(id_user))


def item_lootspecific(id_server = None, id_user = None, item_search = None):
	response = ""
	if id_server is not None and id_user is not None:
		user_data = EwUser(id_user = id_user, id_server = id_server)
		item_sought = find_item(
			item_search = item_search, 
			id_server = user_data.id_server, 
			id_user = user_data.poi
		)
		if item_sought is not None:
			item_type = item_sought.get("item_type")
			response += "You found a {}!".format(item_sought.get("name"))
			can_loot = check_inv_capacity(id_server = id_server, id_user = id_user, item_type = item_type)
			if can_loot:
				give_item(
					id_item = item_sought.get("id_item"),
					id_user = user_data.id_user,
					id_server = user_data.id_server
				)
			else:
				response += " But you couldn't carry any more {} items, so you tossed it back.".format(item_type)
	return response


"""
	Transfer a random item from district inventory to player inventory
"""
def item_lootrandom(id_server = None, id_user = None):
	response = ""

	try:

		user_data = EwUser(id_server = id_server, id_user = id_user)

		items_in_poi = ewutils.execute_sql_query("SELECT {id_item} FROM items WHERE {id_owner} = %s AND {id_server} = %s".format(
				id_item = ewcfg.col_id_item,
				id_owner = ewcfg.col_id_user,
				id_server = ewcfg.col_id_server
			),(
				user_data.poi,
				id_server
			))

		if len(items_in_poi) > 0:
			id_item = random.choice(items_in_poi)[0]

			item_sought = find_item(item_search = str(id_item), id_user = user_data.poi, id_server = id_server)

			response += "You found a {}!".format(item_sought.get('name'))

			if item_sought.get('item_type') == ewcfg.it_food:
				food_items = inventory(
					id_user = id_user,
					id_server = id_server,
					item_type_filter = ewcfg.it_food
				)

				if len(food_items) >= user_data.get_food_capacity():
					response += " But you couldn't carry any more food items, so you tossed it back."
				else:
					give_item(id_user = id_user, id_server = id_server, id_item = id_item)
			elif item_sought.get('item_type') == ewcfg.it_weapon:
				weapons_held = inventory(
					id_user = id_user,
					id_server = id_server,
					item_type_filter = ewcfg.it_weapon
				)

				if len(weapons_held) > user_data.get_weapon_capacity():
					response += " But you couldn't carry any more weapons, so you tossed it back."
				else:
					give_item(id_user = id_user, id_server = id_server, id_item = id_item)

			else:
				if item_sought.get('name') == "Slime Poudrin":
					ewstats.change_stat(
						id_server = user_data.id_server,
						id_user = user_data.id_user,
						metric = ewcfg.stat_poudrins_looted,
						n = 1
					)
				give_item(id_user = id_user, id_server = id_server, id_item = id_item)




		else:
			response += "You found a... oh, nevermind, it's just a piece of trash."

	except:
		ewutils.logMsg("Failed to loot random item")

	finally:
		return response
"""
	Destroy all of a player's non-soulbound items.
"""
def item_destroyall(id_server = None, id_user = None, member = None):
	if member != None:
		id_server = member.server.id
		id_user = member.id

	if id_server != None and id_user != None:
		try:
			# Get database handles if they weren't passed.
			conn_info = ewutils.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor()

			cursor.execute("DELETE FROM items WHERE {id_server} = %s AND {id_user} = %s AND {soulbound} = 0".format(
				id_user = ewcfg.col_id_user,
				id_server = ewcfg.col_id_server,
				soulbound = ewcfg.col_soulbound,
			), (
				id_server,
				id_user
			))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			ewutils.databaseClose(conn_info)


"""
	Loot all non-soulbound items from a player upon killing them, reassinging to id_user_target.
"""
def item_loot(
	member = None,
	id_user_target = ""
):
	if member == None or len(id_user_target) == 0:
		return

	try:
		target_data = EwUser(id_user = id_user_target, id_server = member.server.id)
		source_data = EwUser(member = member)

		# Transfer adorned cosmetics
		data = ewutils.execute_sql_query(
			"SELECT id_item FROM items " +
			"WHERE id_user = %s AND id_server = %s AND soulbound = 0 AND item_type = %s AND id_item IN (" +
				"SELECT id_item FROM items_prop " +
				"WHERE name = 'adorned' AND value = 'true' " +
			")"
		,(
			member.id,
			member.server.id,
			ewcfg.it_cosmetic
		))

		for row in data:
			item_data = EwItem(id_item = row[0])
			item_data.item_props["adorned"] = 'false'
			item_data.id_owner = id_user_target
			item_data.persist()
				

		ewutils.logMsg('Transferred {} cosmetic items.'.format(len(data)))

		if source_data.weapon >= 0:
			weapons_held = inventory(
				id_user = target_data.id_user,
				id_server = target_data.id_server,
				item_type_filter = ewcfg.it_weapon
			)

			if len(weapons_held) <= target_data.get_weapon_capacity():
				give_item(id_user = target_data.id_user, id_server = target_data.id_server, id_item = source_data.weapon)

	except:
		ewutils.logMsg("Failed to loot items from user {}".format(member.id))
			





def check_inv_capacity(id_user = None, id_server = None, item_type = None):
	if id_user is not None and id_server is not None and item_type is not None:
		user_data = EwUser(id_user = id_user, id_server = id_server)
		if item_type == ewcfg.it_food:
			food_items = inventory(
				id_user = id_user,
				id_server = id_server,
				item_type_filter = ewcfg.it_food
			)

			if len(food_items) >= user_data.get_food_capacity():
				return False
			else:
				return True
		elif item_type == ewcfg.it_weapon:
			weapons_held = inventory(
				id_user = id_user,
				id_server = id_server,
				item_type_filter = ewcfg.it_weapon
			)

			if len(weapons_held) >= user_data.get_weapon_capacity():
				return False
			else:
				return True
		else:
			return True
		
	else:
		return False

"""
	Check how many items are in a given district or player's inventory
"""
def get_inventory_size(owner = None, id_server = None):
	if owner != None and id_server != None:
		try:
			items_in_poi = ewutils.execute_sql_query("SELECT {id_item} FROM items WHERE {id_owner} = %s AND {id_server} = %s".format(
					id_item = ewcfg.col_id_item,
					id_owner = ewcfg.col_id_user,
					id_server = ewcfg.col_id_server
				),(
					owner,
					id_server
				))

			return len(items_in_poi)

		except:
			return 0
	else:
		return 0
	

"""
	Returns true if the command string is !inv or equivalent.
"""
def cmd_is_inventory(cmd):
	return (cmd == ewcfg.cmd_inventory or cmd == ewcfg.cmd_inventory_alt1 or cmd == ewcfg.cmd_inventory_alt2 or cmd == ewcfg.cmd_inventory_alt3)

"""
	Get a list of items for the specified player.

	Specify an item_type_filter to get only those items. Be careful: This is
	inserted into SQL without validation/sanitation.
"""
def inventory(
	id_user = None,
	id_server = None,
	item_type_filter = None,
):
	items = []

	try:

		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		sql = "SELECT {}, {}, {}, {}, {} FROM items WHERE {} = %s"
		if id_user != None:
			sql += " AND {} = '{}'".format(ewcfg.col_id_user, str(id_user))
		if item_type_filter != None:
			sql += " AND {} = '{}'".format(ewcfg.col_item_type, item_type_filter)

		if id_server != None:
			cursor.execute(sql.format(
				ewcfg.col_id_item,
				ewcfg.col_item_type,
				ewcfg.col_soulbound,
				ewcfg.col_stack_max,
				ewcfg.col_stack_size,

				ewcfg.col_id_server
			), [
				id_server
			])

			for row in cursor:
				id_item = row[0]
				item_type = row[1]
				soulbound = (row[2] == 1)
				stack_max = row[3]
				stack_size = row[4]

				if item_type == 'slimepoudrin':
					item_data = EwItem(id_item = id_item)
					item_type = ewcfg.it_item
					item_data.item_type = item_type
					for item in ewcfg.item_list:
						if item.context == "poudrin":
							item_props = {
								'id_item': item.id_item,
								'context': item.context,
								'item_name': item.str_name,
								'item_desc': item.str_desc
							}
					item_def = ewcfg.item_def_map.get(item_type)
					item_data.item_props.update(item_def.item_props)
					item_data.item_props.update(item_props)
					item_data.persist()

					ewutils.logMsg('Updated poudrin to new format: {}'.format(id_item))
					    
				item_def = ewcfg.item_def_map.get(item_type)

				if(item_def != None):
					items.append({
						'id_item': id_item,
						'item_type': item_type,
						'soulbound': soulbound,
						'stack_max': stack_max,
						'stack_size': stack_size,

						'item_def': item_def
					})

			for item in items:
				item_def = item.get('item_def')
				id_item = item.get('id_item')
				name = item_def.str_name

				quantity = 0
				if item.get('stack_max') > 0:
					quantity = item.get('stack_size')

				item['quantity'] = quantity

				# Name requires variable substitution. Look up the item properties.
				if name.find('{') >= 0:
					item_inst = EwItem(id_item = id_item)

					if item_inst != None and item_inst.id_item >= 0:
						name = name.format_map(item_inst.item_props)

						if name.find('{') >= 0:
							name = name.format_map(item_inst.item_props)

				#if a weapon has no name show its type instead
				if name == "" and item_inst.item_type == ewcfg.it_weapon:
					name = item_inst.item_props.get("weapon_type")

				item['name'] = name
	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)

	return items


"""
	Dump out a player's inventory.
"""
async def inventory_print(cmd):
	can_message_user = True

	player = EwPlayer(id_user = cmd.message.author.id)

	items = inventory(
		id_user = cmd.message.author.id,
		id_server = player.id_server
	)

	if len(items) == 0:
		response = "You don't have anything."
	else:
		response = "You are holding:"

	try:
		await ewutils.send_message(cmd.client, cmd.message.author, response)
	except:
		can_message_user = False
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	if len(items) > 0:
		response = ""

		for item in items:
			id_item = item.get('id_item')
			quantity = item.get('quantity')

			response_part = "\n{id_item}: {soulbound_style}{name}{soulbound_style}{quantity}".format(
				id_item = item.get('id_item'),
				name = item.get('name'),
				soulbound_style = ("**" if item.get('soulbound') else ""),
				quantity = (" x{:,}".format(quantity) if (quantity > 0) else "")
			)
			if len(response) + len(response_part) > 1492:
				if can_message_user:
					await ewutils.send_message(cmd.client, cmd.message.author, response)
				else:
					await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

				response = ""

			response += response_part

		if can_message_user:
			await ewutils.send_message(cmd.client, cmd.message.author, response)
		else:
			await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


"""
	Dump out the visual description of an item.
"""
async def item_look(cmd):
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	author = cmd.message.author
	server = cmd.message.server
	user_data = EwUser(member = author)
	mutations = user_data.get_mutations()

	item_sought = find_item(item_search = item_search, id_user = author.id, id_server = server.id if server is not None else None)

	if item_sought:
		item = EwItem(id_item = item_sought.get('id_item'))

		id_item = item.id_item
		name = item_sought.get('name')
		response = item_sought.get('item_def').str_desc

		# Replace up to two levels of variable substitutions.
		if response.find('{') >= 0:
			response = response.format_map(item.item_props)

			if response.find('{') >= 0:
				response = response.format_map(item.item_props)

		if item.item_type == ewcfg.it_food:
			if float(item.item_props.get('time_expir') if not None else 0) < time.time():
				response += " This food item is rotten"
				if ewcfg.mutation_id_spoiledappetite in mutations:
					response += ". Yummy!"
				else:
					response += ", so you decide to throw it away."
					item_drop(id_item)
		
		if item.item_type == ewcfg.it_cosmetic:
			hue = ewcfg.hue_map.get(item.item_props.get('hue'))
			if hue != None:
				response += " It's been dyed in {} paint.".format(hue.str_name)

		response = name + "\n\n" + response

		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	else:
		if item_search:  # if they didnt forget to specify an item and it just wasn't found
			response = "You don't have one."
		else:
			response = "Inspect which item? (check **!inventory**)"

		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# this is basically just the item_look command with some other stuff at the bottom
async def item_use(cmd):
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	author = cmd.message.author
	server = cmd.message.server

	item_sought = find_item(item_search = item_search, id_user = author.id, id_server = server.id)

	if item_sought:		
		# Load the user before the item so that the right item props are used
		user_data = EwUser(member = author)

		item = EwItem(id_item = item_sought.get('id_item'))

		response = "The item doesn't have !use functionality"  # if it's not overwritten

		if item.item_type == ewcfg.it_food:
			response = user_data.eat(item)
			user_data.persist()
			asyncio.ensure_future(ewutils.decrease_food_multiplier(user_data.id_user))

		if item.item_type == ewcfg.it_weapon:
			response = user_data.equip(item)
			user_data.persist()

		if item.item_type == ewcfg.it_item:
			name = item_sought.get('name')
			if name == "Trading Cards":
				response = ewsmelting.unwrap(id_user = author, id_server = server, item = item)


		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
		await ewrolemgr.updateRoles(client = cmd.client, member = cmd.message.author)

	else:
		if item_search:  # if they didnt forget to specify an item and it just wasn't found
			response = "You don't have one."
		else:
			response = "Use which item? (check **!inventory**)"

		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

"""
	Assign an existing item to a player
"""
def give_item(
	member = None,
	id_item = None,
	id_user = None,
	id_server = None
):

	if id_user is None and id_server is None and member is not None:
		id_server = member.server.id
		id_user = member.id

	if id_server is not None and id_user is not None and id_item is not None:
		ewutils.execute_sql_query(
			"UPDATE items SET id_user = %s WHERE id_server = %s AND {id_item} = %s".format(
				id_item = ewcfg.col_id_item
			), (
				id_user,
				id_server,
				id_item
			)
		)

	return


def soulbind(id_item):
	item = EwItem(id_item = id_item)
	item.soulbound = True
	item.persist()

"""
	Find a single item in the player's inventory (returns either a (non-EwItem) item or None)
"""
def find_item(item_search = None, id_user = None, id_server = None):
	item_sought = None

	# search for an ID instead of a name
	try:
		item_search_int = int(item_search)
	except:
		item_search_int = None

	if item_search:
		items = inventory(id_user = id_user, id_server = id_server)
		item_sought = None

		# find the first (i.e. the oldest) item that matches the search
		for item in items:
			if item.get('id_item') == item_search_int or item_search in ewutils.flattenTokenListToString(item.get('name')):
				item_sought = item
				break

	return item_sought


"""
	Find every item matching the search in the player's inventory (returns a list of (non-EwItem) item)
"""
def find_item_all(item_search = None, id_user = None, id_server = None, item_type_filter = None):
	items_sought = []
	props_to_search = [
		'weapon_type',
		'id_item',
		'id_food',
		'id_cosmetic'
	]


	if item_search:
		items = inventory(id_user = id_user, id_server = id_server, item_type_filter = item_type_filter)

		# find the first (i.e. the oldest) item that matches the search
		for item in items:
			item_data = EwItem(id_item = item.get('id_item'))
			for prop in props_to_search:
				if prop in item_data.item_props and \
				ewutils.flattenTokenListToString(item_data.item_props.get(prop)) == item_search:
					items_sought.append(item)
					break

	return items_sought

"""
	Finds the amount of Slime Poudrins inside your inventory.
"""
def find_poudrin(id_user = None, id_server = None):

	items = inventory(
		id_user = id_user,
		id_server = id_server,
		item_type_filter = ewcfg.it_item
	)

	poudrins = []

	for poudrin in items:
		name = poudrin.get('name')
		if name != "Slime Poudrin":
			pass
		else:
			poudrins.append(poudrin)

	poudrins_amount = len(poudrins)

	return poudrins_amount

"""
	Command that lets players !give others items
"""
async def give(cmd):
	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
	author = cmd.message.author
	server = cmd.message.server

	if cmd.mentions:  # if they're not empty
		recipient = cmd.mentions[0]
	else:
		response = "You have to specify the recipient of the item."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	user_data = EwUser(member = author)
	recipient_data = EwUser(member = recipient)

	if user_data.poi != recipient_data.poi:
		response = "You must be in the same location as the person you want to gift your item to, bitch."
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	item_sought = find_item(item_search = item_search, id_user = author.id, id_server = server.id)

	if item_sought:  # if an item was found

		# don't let people give others food when they shouldn't be able to carry more food items
		if item_sought.get('item_type') == ewcfg.it_food:
			food_items = inventory(
				id_user = recipient.id,
				id_server = server.id,
				item_type_filter = ewcfg.it_food
			)

			if len(food_items) >= recipient_data.get_food_capacity():
				response = "They can't carry any more food items."
				return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

		if item_sought.get('item_type') == ewcfg.it_weapon:
			weapons_held = inventory(
				id_user = recipient.id,
				id_server = server.id,
				item_type_filter = ewcfg.it_weapon
			)

			if user_data.weaponmarried and user_data.weapon == item_sought.get('id_item'):
				response = "Your cuckoldry is appreciated, but your {} will always remain faithful to you.".format(item_sought.get('name'))
				return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
			elif recipient_data.life_state == ewcfg.life_state_corpse:
				response = "Ghosts can't hold weapons."
				return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
			elif len(weapons_held) >= recipient_data.get_weapon_capacity():
				response  = "They can't carry any more weapons."
				return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

		if item_sought.get('item_type') == ewcfg.it_cosmetic:
			item_data = EwItem(id_item = item_sought.get('id_item'))
			item_data.item_props["adorned"] = 'false'
			item_data.persist()


		if item_sought.get('soulbound'):
			response = "You can't just give away soulbound items."
		else:
			give_item(
				member = recipient,
				id_item = item_sought.get('id_item')
			)

			response = "You gave {recipient} a {item}".format(
				recipient = recipient.display_name,
				item = item_sought.get('name')
			)

			if item_sought.get('id_item') == user_data.weapon:
				user_data.weapon = -1
				user_data.persist()
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

	else:
		if item_search:  # if they didnt forget to specify an item and it just wasn't found
			response = "You don't have one."
		else:
			response = "Give which item? (check **!inventory**)"

		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

"""
	Throw away an item
"""
async def discard(cmd):
	user_data = EwUser(member = cmd.message.author)
	response = ""

	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])

	item_sought = find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if item_sought:
		item = EwItem(id_item = item_sought.get("id_item"))

		if not item.soulbound:
			if item.item_type == ewcfg.it_weapon and user_data.weapon >= 0 and item.id_item == user_data.weapon:
				if user_data.weaponmarried:
					weapon = ewcfg.weapon_map.get(item.item_props.get("weapon_type"))
					response = "As much as it would be satisfying to just chuck your {} down an alley and be done with it, here in civilization we deal with things *maturely.* You’ll have to speak to the guy that got you into this mess in the first place, or at least the guy that allowed you to make the retarded decision in the first place. Luckily for you, they’re the same person, and he’s at the Dojo.".format(weapon.str_weapon)
					return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
				else:
					user_data.weapon = -1
					user_data.persist()
				
			response = "You throw away your " + item_sought.get("name")
			item_drop(id_item = item.id_item)

		else:
			response = "You can't throw away soulbound items."
	else:
		if item_search:
			response = "You don't have one"
		else:
			response = "Discard which item? (check **!inventory**)"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def gen_item_props(item):
	item_props = {}
	if not hasattr(item, "item_type"):
		return item_props
	if item.item_type == ewcfg.it_food:
		
		item_props = {
			'id_food': item.id_food,
			'food_name': item.str_name,
			'food_desc': item.str_desc,
			'recover_hunger': item.recover_hunger,
			'inebriation': item.inebriation,
			'str_eat': item.str_eat,
			'time_expir': int(time.time()) + item.time_expir,
		}
	elif item.item_type == ewcfg.it_item:
		item_props = {
			'id_item': item.id_item,
			'context': item.context,
			'item_name': item.str_name,
			'item_desc': item.str_desc,
			'ingredients': item.ingredients,
			'acquisition': item.acquisition,
		}
	elif item.item_type == ewcfg.it_weapon:
		item_props = {
			"weapon_type": item.id_weapon,
			"weapon_name": "",
			"weapon_desc": item.str_description,
			"married": ""
		}

	elif item.item_type == ewcfg.it_cosmetic:
		item_props = {
			'id_cosmetic': item.id_cosmetic,
			'cosmetic_name': item.str_name,
			'cosmetic_desc': item.str_desc,
			'rarity': item.rarity,
			'adorned': 'false'
		}

	return item_props
		
		
