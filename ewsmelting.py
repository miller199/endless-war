import random
import time

import ewcfg
import ewitem
import ewutils

from ew import EwUser

"""
	Smelting Recipe Model Object
"""

class EwSmeltingRecipe:
	# The proper name of the recipe.
	id_recipe = ""

	# The string name of the recipe.
	str_name = ""

	# A list of alternative names.
	alias = []

	# The ingredients for the recipe, by str_name of the object.
	ingredients = []

	# The product(s) created by the recipe, A tuple of the item type (it_food, it_cosmetic, etc) and item_props.
	products = []

	def __init__(
		self,
		id_recipe="",
		str_name="",
		alias = [],
		ingredients = [],
		products = [],
	):
		self.id_recipe = id_recipe
		self.str_name = str_name
		self.alias = alias
		self.ingredients = ingredients
		self.products = products

# Smelting command. It's like other games call "crafting"... but BETTER and for FREE!!
async def smelt(cmd):
	user_data = EwUser(member = cmd.message.author)

	# Find sought recipe.
	if cmd.tokens_count > 1:
		sought_result = cmd.tokens[1].lower()
		found_recipe = ewcfg.smelting_recipe_map.get(sought_result)

		if found_recipe != None:
			# Checks what ingredients are needed to smelt the recipe.
			necessary_ingredients = found_recipe.ingredients

			owned_ingredients = []

			# Seeks out the necessary ingredients in your inventory.
			for matched_item in necessary_ingredients:
				sought_item = ewitem.find_item(item_search = matched_item, id_user = user_data.id_user, id_server = user_data.id_server)
				if sought_item != None:
					ewitem.item_drop(sought_item.get('id_item'))
					owned_ingredients.append(matched_item)
				else:
					pass

			for dropped_ingredients in owned_ingredients:
				ewitem.item_lootspecific(item_search = dropped_ingredients, id_user = user_data.id_user, id_server = user_data.id_server)  # Returns items.

			# If you don't have all the necessary ingredients.
			if len(necessary_ingredients) > len(owned_ingredients):
				response = "You’ve never done this before, have you? To smelt {}, you’ll need to combine a *{}*.".format(found_recipe.str_name, ewutils.formatNiceList(names = necessary_ingredients, conjunction = "and"))

				if len(owned_ingredients) != 0:
					response += " You only have a *{}*.".format(ewutils.formatNiceList(names = owned_ingredients, conjunction = "and"))

			else:
				# If you try to smelt a random cosmetic, use old smelting code to calculate what your result will be.
				if found_recipe.id_recipe == "cosmetic":
					patrician_rarity = 20
					patrician_smelted = random.randint(1, patrician_rarity)
					patrician = False

					if patrician_smelted == 1:
						patrician = True

					cosmetics_list = []

					for result in ewcfg.cosmetic_items_list:
						if result.acquisition == ewcfg.acquisition_smelting:
							cosmetics_list.append(result)
						else:
							pass

					items = []

					for cosmetic in cosmetics_list:
						if patrician and cosmetic.rarity == ewcfg.rarity_patrician:
							items.append(cosmetic)
						elif not patrician and cosmetic.rarity == ewcfg.rarity_plebeian:
							items.append(cosmetic)

					item = items[random.randint(0, len(items) - 1)]

					ewitem.item_create(
						item_type = ewcfg.it_cosmetic,
						id_user = cmd.message.author.id,
						id_server = cmd.message.server.id,
						item_props = {
							'id_cosmetic': item.id_cosmetic,
							'cosmetic_name': item.str_name,
							'cosmetic_desc': item.str_desc,
							'rarity': item.rarity,
							'adorned': 'false'
						}
					)

				# If you're trying to smelt a specific item.
				else:
					possible_results = []

					# Matches the recipe's listed products to actual items.
					for result in ewcfg.smelt_results:
						if hasattr(result, 'id_item'):
							if result.id_item not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_food'):
							if result.id_food not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_cosmetic'):
							if result.id_cosmetic not in found_recipe.products:
								pass
							else:
								possible_results.append(result)

					# If there are multiple possible products, randomly select one.
					item = random.choice(possible_results)

					if hasattr(item, 'id_item'):
						ewitem.item_create(
							item_type = ewcfg.it_item,
							id_user = cmd.message.author.id,
							id_server = cmd.message.server.id,
							item_props = {
								'id_item': item.id_item,
								'context': item.context,
								'item_name': item.str_name,
								'item_desc': item.str_desc,
							}
						),

					elif hasattr(item, 'id_food'):
						ewitem.item_create(
							item_type = ewcfg.it_food,
							id_user = cmd.message.author.id,
							id_server = cmd.message.server.id,
							item_props = {
								'id_food': item.id_food,
								'food_name': item.str_name,
								'food_desc': item.str_desc,
								'recover_hunger': item.recover_hunger,
								'inebriation': item.inebriation,
								'str_eat': item.str_eat,
								'time_expir': time.time() + ewcfg.farm_food_expir
							}
						),

					elif hasattr(item, 'id_cosmetic'):
						ewitem.item_create(
							item_type = ewcfg.it_cosmetic,
							id_user = cmd.message.author.id,
							id_server = cmd.message.server.id,
							item_props = {
								'id_cosmetic': item.id_cosmetic,
								'cosmetic_name': item.str_name,
								'cosmetic_desc': item.str_desc,
								'rarity': item.rarity,
								'adorned': 'false'
							}
						),

				while len(owned_ingredients) > 0:
					for matched_item in owned_ingredients:
							sought_item = ewitem.find_item(item_search = matched_item, id_user = user_data.id_user, id_server = user_data.id_server)
							ewitem.item_delete(id_item = sought_item.get('id_item'))
							owned_ingredients.remove(matched_item)

				response = "You sacrifice your {} to smelt a {}!!".format(ewutils.formatNiceList(names = necessary_ingredients, conjunction = "and"), item.str_name)

				user_data.persist()

		else:
			response = "There is no recipe by the name."

	else:
		response = "Please specify a desired smelt result."

	# Send response
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def unwrap(id_user = None, id_server = None, item = None):
	response = "You eagerly rip open a pack of Secreatures™ trading cards!!"
	ewitem.item_delete(item.id_item)
	slimexodia = False

	slimexodia_chance = 1 / 1000

	if random.random() < slimexodia_chance:
		slimexodia = True

	if slimexodia == True:
		# If there are multiple possible products, randomly select one.
		slimexodia_item = random.choice(ewcfg.slimexodia_parts)

		response += " There’s a single holographic card poking out of the swathes of repeats and late edition cards..."
		response += " ***...What’s this?! It’s the legendary card {}!! If you’re able to collect the remaining pieces of Slimexodia, you might be able to smelt something incomprehensibly powerful!!***".format(slimexodia_item.str_name)

		ewitem.item_create(
			item_type = ewcfg.it_item,
			id_user = id_user.id,
			id_server = id_server.id,
			item_props = {
				'id_item': slimexodia_item.id_item,
				'context': slimexodia_item.context,
				'item_name': slimexodia_item.str_name,
				'item_desc': slimexodia_item.str_desc,
			}
		),

	else:
		response += " But… it’s mostly just repeats and late edition cards. You toss them away."

	return response
