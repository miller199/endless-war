import math
import time
import asyncio

import ewcfg
import ewitem
import ewutils
import ewrolemgr
from ew import EwUser
from ewmarket import EwMarket, EwCompany, EwStock

""" Food model object """
class EwFood:
	item_type = "food"

	# The main name of this food.
	id_food = ""

	# A list of alternative names.
	alias = []

	# Hunger reduced by eating this food.
	recover_hunger = 0

	# Cost in SlimeCoin to eat this food.
	price = 0

	# A nice string name describing this food.
	str_name = ""

	# Names of the vendors selling this food in the food court.
	vendors = []

	# Flavor text displayed when you eat this food.
	str_eat = ""

	# Alcoholic effect
	inebriation = 0

	# Flavor text displayed when you inspect this food.
	str_desc = ""

	# Expiration time (can be left blank for standard expiration time)
	time_expir = 0

	# The ingredients necessary to make this item via it's acquisition method
	ingredients = ""

	# The way that you can acquire this item. If blank, it's not relevant.
	acquisition = ""

	def __init__(
		self,
		id_food = "",
		alias = [],
		recover_hunger = 0,
		price = 0,
		str_name = "",
		vendors = [],
		str_eat = "",
		inebriation = 0,
		str_desc = "",
		time_expir = 0,
		ingredients = "",
		acquisition = "",
	):
		self.item_type = ewcfg.it_food

		self.id_food = id_food
		self.alias = alias
		self.recover_hunger = recover_hunger
		self.price = price
		self.str_name = str_name
		self.vendors = vendors
		self.str_eat = str_eat
		self.inebriation = inebriation
		self.str_desc = str_desc
		self.time_expir = time_expir if time_expir > 0 else ewcfg.std_food_expir
		self.ingredients = ingredients
		self.acquisition = acquisition


""" show all available food items """
async def menu(cmd):
	user_data = EwUser(member = cmd.message.author)
	poi = ewcfg.id_to_poi.get(user_data.poi)
	market_data = EwMarket(id_server = cmd.message.server.id)

	if poi == None or len(poi.vendors) == 0:
		# Only allowed in the food court.
		response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."
	else:
		response = "{} Menu:\n\n".format(poi.str_name)

		for vendor in poi.vendors:
			items = []
			# If the vendor is the bazaar get the current rotation of items from the market_data
			vendor_inv = ewcfg.vendor_inv[vendor] if vendor != ewcfg.vendor_bazaar else market_data.bazaar_wares.values()
			for item_name in vendor_inv:
				item_item = ewcfg.item_map.get(item_name)
				food_item = ewcfg.food_map.get(item_name)
				cosmetic_item = ewcfg.cosmetic_map.get(item_name)

				# increase profits for the stock market
				stock_data = None
				if vendor in ewcfg.vendor_stock_map:
					stock = ewcfg.vendor_stock_map.get(vendor)
					stock_data = EwStock(id_server = user_data.id_server, stock = stock)

				value = 0

				if item_item:
					value = item_item.price

				if food_item:
					value = food_item.price

				if cosmetic_item:
					value = cosmetic_item.price

				if stock_data is not None:
					value *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2

				value = int(value)

				if value != 0:
					items.append('{name} ({price})'.format(name = item_name, price = value))
				else:
					items.append(item_name)

			response += "**{}**: *{}*\n".format(vendor, ewutils.formatNiceList(names = items))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# Buy items.
async def order(cmd):
	user_data = EwUser(member = cmd.message.author)
	poi = ewcfg.id_to_poi.get(user_data.poi)
	market_data = EwMarket(id_server = cmd.message.server.id)

	if len(poi.vendors) == 0:
		# Only allowed in locations with a vendor.
		response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."

	else:
		value = ewutils.flattenTokenListToString(cmd.tokens[1:])
		#if cmd.tokens_count > 1:
		#	value = cmd.tokens[1]
		#	value = value.lower()

		# Finds the item if it's an EwGeneralItem.

		item = ewcfg.item_map.get(value)
		item_type = ewcfg.it_item
		if item != None:
			item_id = item.id_item

		# Finds the item if it's an EwFood item.
		if item == None:
			item = ewcfg.food_map.get(value)
			item_type = ewcfg.it_food
			if item != None:
				item_id = item.id_food

		# Finds the item if it's an EwCosmeticItem.
		if item == None:
			item = ewcfg.cosmetic_map.get(value)
			item_type = ewcfg.it_cosmetic
			if item != None:
				item_id = item.id_cosmetic

		if item != None:
			item_type = item.item_type
			# Gets a vendor that the item is available and the player currently located in
			try:
				current_vendor = (set(item.vendors).intersection(set(poi.vendors))).pop()
			except:
				current_vendor = None

			# Check if the item is available in the current bazaar item rotation
			if current_vendor == ewcfg.vendor_bazaar:
				if item_id not in market_data.bazaar_wares.values():
					current_vendor = None

			if current_vendor is None or len(current_vendor) < 1:
				response = "Check the {} for a list of items you can {}.".format(ewcfg.cmd_menu, ewcfg.cmd_order)

			else:
				response = ""

				value = item.price

				stock_data = None
				company_data = None
				# factor in the current stocks
				for vendor in item.vendors:
					if vendor in ewcfg.vendor_stock_map:
						stock = ewcfg.vendor_stock_map.get(vendor)
						company_data = EwCompany(id_server = user_data.id_server, stock = stock)
						stock_data = EwStock(id_server = user_data.id_server, stock = stock)

				if stock_data is not None:
					value *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2

				value = int(value)

				# Kingpins eat free.
				if user_data.life_state == ewcfg.life_state_kingpin or user_data.life_state == ewcfg.life_state_grandfoe:
					value = 0

				if value > user_data.slimes:
					# Not enough money.
					response = "A {} costs {:,} slime, and you only have {:,}.".format(item.str_name, value, user_data.slimes)
				else:
					if item_type == ewcfg.it_food:
						food_items = ewitem.inventory(
							id_user = cmd.message.author.id,
							id_server = cmd.message.server.id,
							item_type_filter = ewcfg.it_food
						)

						if len(food_items) >= user_data.get_food_capacity():
							# user_data never got persisted so the player won't lose money unnecessarily
							response = "You can't carry any more food than that."
							return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


					user_data.change_slimes(n = -value, source = ewcfg.source_spending)

					if company_data is not None:
						company_data.recent_profits += value
						company_data.persist()

					item_props = ewitem.gen_item_props(item)


					ewitem.item_create(
						item_type = item_type,
						id_user = cmd.message.author.id,
						id_server = cmd.message.server.id,
						item_props = item_props
					)

					response = "You slam {:,} slime down on the counter at {} for {}.".format(value, current_vendor, item.str_name)
					user_data.persist()

		else:
			response = "Check the {} for a list of items you can {}.".format(ewcfg.cmd_menu, ewcfg.cmd_order)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
