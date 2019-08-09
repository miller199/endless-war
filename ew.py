import time
import random
import asyncio

import ewutils
import ewcfg
import ewstats
import ewitem

""" Market data model for database persistence """

""" User model for database persistence """
class EwUser:
	id_user = ""
	id_server = ""
	id_killer = ""

	slimes = 0
	slimecoin = 0
	slime_donations = 0
	poudrin_donations = 0
	slimelevel = 1
	hunger = 0
	totaldamage = 0
	bleed_storage = 0
	bounty = 0
	weapon = -1
	weaponskill = 0
	trauma = ""
	poi_death = ""
	ghostbust = False
	inebriation = 0
	faction = ""
	poi = ""
	life_state = 0
	busted = False
	rr_challenger = ""
	time_last_action = 0
	weaponmarried = False
	arrested = False
	fish_space = 0
	unclaimed_prizes = 0

	time_lastkill = 0
	time_lastrevive = 0
	time_lastspar = 0
	time_lasthaunt = 0
	time_lastinvest = 0
	time_lastscavenge = 0
	time_lastenter = 0
	time_lastoffline = 0
	time_joined = 0

	move_speed = 1 # not a database column

	""" fix data in this object if it's out of acceptable ranges """
	def limit_fix(self):
		if self.hunger > self.get_hunger_max():
			self.hunger = self.get_hunger_max()

		if self.inebriation < 0:
			self.inebriation = 0

		if self.poi == '':
			self.poi = ewcfg.poi_id_downtown

		if self.time_last_action <= 0:
			self.time_last_action = int(time.time())

		if self.move_speed <= 0:
			self.move_speed = 1

	""" gain or lose slime, recording statistics and potentially leveling up. """
	def change_slimes(self, n = 0, source = None):
		change = int(n)
		self.slimes += change
		response = ""

		if n >= 0:
			ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimes, n = change)
			ewstats.track_maximum(user = self, metric = ewcfg.stat_max_slimes, value = self.slimes)

			if source == ewcfg.source_mining:
				ewstats.change_stat(user = self, metric = ewcfg.stat_slimesmined, n = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimesmined, n = change)

			if source == ewcfg.source_killing:
				ewstats.change_stat(user = self, metric = ewcfg.stat_slimesfromkills, n = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimesfromkills, n = change)

			if source == ewcfg.source_farming:
				ewstats.change_stat(user = self, metric = ewcfg.stat_slimesfarmed, n = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimesfarmed, n = change)

			if source == ewcfg.source_scavenging:
				ewstats.change_stat(user = self, metric = ewcfg.stat_slimesscavenged, n = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimesscavenged, n = change)

		else:
			change *= -1 # convert to positive number
			if source != ewcfg.source_spending and source != ewcfg.source_ghostification:
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimeloss, n = change)

			if source == ewcfg.source_damage or source == ewcfg.source_bleeding:
				self.totaldamage += change
				ewstats.track_maximum(user = self, metric = ewcfg.stat_max_hitsurvived, value = change)

			if source == ewcfg.source_self_damage:
				self.totaldamage += change
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_selfdamage, n = change)

			if source == ewcfg.source_decay:
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimesdecayed, n = change)

			if source == ewcfg.source_haunter:
				ewstats.track_maximum(user = self, metric = ewcfg.stat_max_hauntinflicted, value = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimeshaunted, n = change)

		# potentially level up
		new_level = ewutils.level_byslime(self.slimes)
		if new_level > self.slimelevel:
			if self.life_state != ewcfg.life_state_corpse:
				response += "You have been empowered by slime and are now a level {} slimeboi.".format(new_level)
			for level in range(self.slimelevel+1, new_level+1):
				if level in ewcfg.mutation_milestones and self.life_state != ewcfg.life_state_corpse:
					current_mutations = self.get_mutations()
					new_mutation = random.choice(list(ewcfg.mutation_ids))
					while new_mutation in current_mutations:
						new_mutation = random.choice(list(ewcfg.mutation_ids))

					add_success = self.add_mutation(new_mutation)
					if add_success:
						response += "\n\nWhat’s this? You are mutating!! {}".format(ewcfg.mutations_map[new_mutation].str_acquire)
						
			self.slimelevel = new_level
			if self.life_state == ewcfg.life_state_corpse:
				ewstats.track_maximum(user = self, metric = ewcfg.stat_max_ghost_level, value = self.slimelevel)
			else:
				ewstats.track_maximum(user = self, metric = ewcfg.stat_max_level, value = self.slimelevel)

		return response

		
	def die(self, cause = None):
		if cause == ewcfg.cause_busted:
			self.busted = True
			self.slimes = int(self.slimes * 0.9)
		else:
			self.busted = False  # reset busted state on normal death; potentially move this to ewspooky.revive
			self.slimes = 0
			self.life_state = ewcfg.life_state_corpse
			self.poi_death = self.poi
			ewstats.increment_stat(user = self, metric = ewcfg.stat_lifetime_deaths)
			ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimeloss, n = self.slimes)
			if cause != ewcfg.cause_killing and cause != ewcfg.cause_suicide and cause != ewcfg.cause_bleeding:
				ewstats.increment_stat(user = self, metric = ewcfg.stat_lifetime_pve_deaths)
		ewitem.item_dedorn_cosmetics(id_server = self.id_server, id_user = self.id_user)
		ewitem.item_dropall(id_server = self.id_server, id_user = self.id_user)
		self.poi = ewcfg.poi_id_thesewers
		self.bounty = 0
		self.totaldamage = 0
		self.bleed_storage = 0
		self.slimelevel = 1
		self.hunger = 0
		self.inebriation = 0
		self.ghostbust = False
		# Clear weapon and weaponskill.
		self.weapon = -1
		self.weaponskill = 0
		self.weaponmarried = False
		ewutils.moves_active[self.id_user] = 0
		ewutils.weaponskills_clear(id_server = self.id_server, id_user = self.id_user)
		ewstats.clear_on_death(id_server = self.id_server, id_user = self.id_user)
		
		self.clear_mutations()
		#ewitem.item_destroyall(id_server = self.id_server, id_user = self.id_user)

		ewutils.logMsg('server {}: {} was killed by {} - cause was {}'.format(self.id_server, self.id_user, self.id_killer, cause))

	def add_bounty(self, n = 0):
		self.bounty += int(n)
		ewstats.track_maximum(user = self, metric = ewcfg.stat_max_bounty, value = self.bounty)

	def change_slimecoin(self, n = 0, coinsource = None):
		change = int(n)
		self.slimecoin += change

		if change >= 0:
			ewstats.track_maximum(user = self, metric = ewcfg.stat_max_slimecoin, value = self.slimecoin)
			ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_slimecoin, n = change)
			if coinsource == ewcfg.coinsource_bounty:
				ewstats.change_stat(user = self, metric = ewcfg.stat_bounty_collected, n = change)
			if coinsource == ewcfg.coinsource_casino:
				ewstats.track_maximum(user = self, metric = ewcfg.stat_biggest_casino_win, value = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_casino_winnings, n = change)
			if coinsource == ewcfg.coinsource_withdraw:
				ewstats.change_stat(user = self, metric = ewcfg.stat_total_slimecoin_withdrawn, n = change)
		else:
			change *= -1
			if coinsource == ewcfg.coinsource_revival:
				ewstats.change_stat(user = self, metric = ewcfg.stat_slimecoin_spent_on_revives, n = change)
			if coinsource == ewcfg.coinsource_casino:
				ewstats.track_maximum(user = self, metric = ewcfg.stat_biggest_casino_loss, value = change)
				ewstats.change_stat(user = self, metric = ewcfg.stat_lifetime_casino_losses, n = change)
			if coinsource == ewcfg.coinsource_invest:
				ewstats.change_stat(user = self, metric = ewcfg.stat_total_slimecoin_invested, n = change)

	def add_weaponskill(self, n = 0, weapon_type = None):
		# Save the current weapon's skill
		if self.weapon != None and self.weapon >= 0:
			if self.weaponskill == None:
				self.weaponskill = 0

			self.weaponskill += int(n)
			ewstats.track_maximum(user = self, metric = ewcfg.stat_max_wepskill, value = self.weaponskill)

			ewutils.weaponskills_set(
				id_server = self.id_server,
				id_user = self.id_user,
				weapon = weapon_type,
				weaponskill = self.weaponskill
			)

	def eat(self, food_item = None):
		item_props = food_item.item_props
		mutations = self.get_mutations()

		if ewcfg.mutation_id_spoiledappetite not in mutations and float(food_item.time_expir if food_item.time_expir is not None else 0) < time.time():
			response = "You realize that the food you were trying to eat is already spoiled. In disgust, you throw it away."
			ewitem.item_drop(food_item.id_item)
		else:
			hunger_restored = int(item_props['recover_hunger'])
			if self.id_user in ewutils.food_multiplier and ewutils.food_multiplier.get(self.id_user) > 0:
				if ewcfg.mutation_id_bingeeater in mutations:
					hunger_restored *= ewutils.food_multiplier.get(self.id_user)
				ewutils.food_multiplier[self.id_user] += 1
			else:
				ewutils.food_multiplier[self.id_user] = 1
				
			self.hunger -= hunger_restored
			if self.hunger < 0:
				self.hunger = 0
			self.inebriation += int(item_props['inebriation'])
			if self.inebriation > 20:
				self.inebriation = 20

			try:
				if item_props['id_food'] in ["coleslaw","bloodcabbagecoleslaw"]:
					self.ghostbust = True
					#Bust player if they're a ghost
					if self.life_state == ewcfg.life_state_corpse:
						self.die(cause = ewcfg.cause_busted)
			except:
				# An exception will occur if there's no id_food prop in the database. We don't care.
				pass

			response = item_props['str_eat'] + ("\n\nYou're stuffed!" if self.hunger <= 0 else "")

			ewitem.item_delete(food_item.id_item)

		return response


	def add_mutation(self, id_mutation):
		mutations = self.get_mutations()
		if id_mutation in mutations:
			return False
		try:
			ewutils.execute_sql_query("REPLACE INTO mutations({id_server}, {id_user}, {id_mutation}) VALUES (%s, %s, %s)".format(
					id_server = ewcfg.col_id_server,
					id_user = ewcfg.col_id_user,
					id_mutation = ewcfg.col_id_mutation
				),(
					self.id_server,
					self.id_user,
					id_mutation
				))

			return True
		except:
			ewutils.logMsg("Failed to add mutation for user {}.".format(self.id_user))
			return False


	def get_mutations(self):
		result = []
		try:
			mutations = ewutils.execute_sql_query("SELECT {id_mutation} FROM mutations WHERE {id_server} = %s AND {id_user} = %s;".format(
					id_mutation = ewcfg.col_id_mutation,
					id_server = ewcfg.col_id_server,
					id_user = ewcfg.col_id_user
				),(
					self.id_server,
					self.id_user
				))
    
			for mutation_data in mutations:
				result.append(mutation_data[0])
		except:
			ewutils.logMsg("Failed to fetch mutations for user {}.".format(self.id_user))

		finally:
			return result

	def clear_mutations(self):
		try:
			ewutils.execute_sql_query("DELETE FROM mutations WHERE {id_server} = %s AND {id_user} = %s".format(
					id_server = ewcfg.col_id_server,
					id_user = ewcfg.col_id_user
				),(
					self.id_server,
					self.id_user
				))
		except:
			ewutils.logMsg("Failed to clear mutations for user {}.".format(self.id_user))

	def equip(self, weapon_item = None):
		if self.life_state == ewcfg.life_state_corpse:
			response = "Ghosts can't equip weapons."
		elif self.life_state == ewcfg.life_state_juvenile:
			response = "Juvies can't equip weapons."
		elif self.weaponmarried == True:
			current_weapon = ewitem.EwItem(id_item = self.weapon)
			response = "You reach to pick up a new weapon, but your old {} remains motionless with jealousy. You dug your grave, now decompose in it.".format(current_weapon.item_props.get("weapon_name") if len(current_weapon.item_props.get("weapon_name")) > 0 else "partner")
			#Have to load the item again or the wrong item props are used
			weapon_item = ewitem.EwItem(id_item = weapon_item.id_item)
		else:
			response = "You equip your " + (weapon_item.item_props.get("weapon_type") if len(weapon_item.item_props.get("weapon_name")) == 0 else weapon_item.item_props.get("weapon_name"))
			self.weapon = weapon_item.id_item

		return response

	def get_weapon_capacity(self):
		mutations = self.get_mutations()
		base_capacity = ewutils.weapon_carry_capacity_bylevel(self.slimelevel)
		if ewcfg.mutation_id_2ndamendment in mutations:
			return base_capacity + 1
		else:
			return base_capacity

	def get_food_capacity(self):
		mutations = self.get_mutations()
		base_capacity = ewutils.food_carry_capacity_bylevel(self.slimelevel)
		if ewcfg.mutation_id_bigbones in mutations:
			return 2 * base_capacity
		else:
			return base_capacity

	def get_hunger_max(self):
		return ewutils.hunger_max_bylevel(self.slimelevel)


	def get_mention(self):
		return "<@{id_user}>".format(id_user = self.id_user)

	def ban(self, faction = None):
		if faction is None:
			return
		ewutils.execute_sql_query("REPLACE INTO bans ({id_user}, {id_server}, {faction}) VALUES (%s,%s,%s)".format(
			id_user = ewcfg.col_id_user,
			id_server = ewcfg.col_id_server,
			faction = ewcfg.col_faction
		),(
			self.id_user,
			self.id_server,
			faction
		))

	def unban(self, faction = None):
		if faction is None:
			return
		ewutils.execute_sql_query("DELETE FROM bans WHERE {id_user} = %s AND {id_server} = %s AND {faction} = %s".format(
			id_user = ewcfg.col_id_user,
			id_server = ewcfg.col_id_server,
			faction = ewcfg.col_faction
		),(
			self.id_user,
			self.id_server,
			faction
		))

	def get_bans(self):
		bans = []
		data = ewutils.execute_sql_query("SELECT {faction} FROM bans WHERE {id_user} = %s AND {id_server} = %s".format(
			id_user = ewcfg.col_id_user,
			id_server = ewcfg.col_id_server,
			faction = ewcfg.col_faction
		),(
			self.id_user,
			self.id_server
		))

		for row in data:
			bans.append(row[0])

		return bans

	def get_stored_fish(self):
		fish = []
		data = ewutils.execute_sql_query("SELECT {id_item} FROM items WHERE {id_user} = %s AND {id_server} = %s".format(
			id_item = ewcfg.col_id_item,
			id_user = ewcfg.col_id_user,
			id_server = ewcfg.col_id_server
		), (
			ewcfg.tank_poi+self.id_user,
			self.id_server
		))

		for row in data:
			fish.append(row[0])

		return fish

	""" Create a new EwUser and optionally retrieve it from the database. """
	def __init__(self, member = None, id_user = None, id_server = None):
		if(id_user == None) and (id_server == None):
			if(member != None):
				id_server = member.server.id
				id_user = member.id

		# Retrieve the object from the database if the user is provided.
		if(id_user != None) and (id_server != None):
			self.id_server = id_server
			self.id_user = id_user

			try:
				conn_info = ewutils.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor();

				# Retrieve object
				cursor.execute("SELECT {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {} FROM users WHERE id_user = %s AND id_server = %s".format(
					ewcfg.col_slimes,
					ewcfg.col_slimelevel,
					ewcfg.col_hunger,
					ewcfg.col_totaldamage,
					ewcfg.col_bounty,
					ewcfg.col_weapon,
					ewcfg.col_trauma,
					ewcfg.col_slimecoin,
					ewcfg.col_time_lastkill,
					ewcfg.col_time_lastrevive,
					ewcfg.col_id_killer,
					ewcfg.col_time_lastspar,
					ewcfg.col_time_lasthaunt,
					ewcfg.col_time_lastinvest,
					ewcfg.col_ghostbust,
					ewcfg.col_inebriation,
					ewcfg.col_faction,
					ewcfg.col_poi,
					ewcfg.col_life_state,
					ewcfg.col_busted,
					ewcfg.col_rrchallenger,
					ewcfg.col_time_last_action,
					ewcfg.col_weaponmarried,
					ewcfg.col_time_lastscavenge,
					ewcfg.col_bleed_storage,
					ewcfg.col_time_lastenter,
					ewcfg.col_time_lastoffline,
					ewcfg.col_time_joined,
					ewcfg.col_poi_death,
					ewcfg.col_slime_donations,
					ewcfg.col_poudrin_donations,
					ewcfg.col_arrested,
					ewcfg.col_fish_space,
					ewcfg.col_unclaimed_prizes,
				), (
					id_user,
					id_server
				))
				result = cursor.fetchone();

				if result != None:
					# Record found: apply the data to this object.
					self.slimes = result[0]
					self.slimelevel = result[1]
					self.hunger = result[2]
					self.totaldamage = result[3]
					self.bounty = result[4]
					self.weapon = result[5]
					self.trauma = result[6]
					self.slimecoin = result[7]
					self.time_lastkill = result[8]
					self.time_lastrevive = result[9]
					self.id_killer = result[10]
					self.time_lastspar = result[11]
					self.time_lasthaunt = result[12]
					self.time_lastinvest = result[13]
					self.ghostbust = (result[14] == 1)
					self.inebriation = result[15]
					self.faction = result[16]
					self.poi = result[17]
					self.life_state = result[18]
					self.busted = (result[19] == 1)
					self.rr_challenger = result[20]
					self.time_last_action = result[21]
					self.weaponmarried = (result[22] == 1)
					self.time_lastscavenge = result[23]
					self.bleed_storage = result[24]
					self.time_lastenter = result[25]
					self.time_lastoffline = result[26]
					self.time_joined = result[27]
					self.poi_death = result[28]
					self.slime_donations = result[29]
					self.poudrin_donations = result[30]
					self.arrested = (result[31] == 1)
					self.fish_space = result[32]
					self.unclaimed_prizes = result[33]
				else:
					self.poi = ewcfg.poi_id_downtown
					self.life_state = ewcfg.life_state_juvenile
					# Create a new database entry if the object is missing.
					cursor.execute("REPLACE INTO users(id_user, id_server, poi, life_state) VALUES(%s, %s, %s, %s)", (
						id_user,
						id_server,
						ewcfg.poi_id_downtown,
						ewcfg.life_state_juvenile
					))
					
					conn.commit()

				if (self.time_joined == 0) and (member != None) and (member.joined_at != None):
					self.time_joined = int(member.joined_at.timestamp())

				# Get the skill for the user's current weapon.
				if self.weapon != None and self.weapon >= 0:
					skills = ewutils.weaponskills_get(
						id_server = id_server,
						id_user = id_user
					)

					weapon_item = ewitem.EwItem(id_item = self.weapon)

					skill_data = skills.get(weapon_item.item_props.get("weapon_type"))
					if skill_data != None:
						self.weaponskill = skill_data['skill']
					else:
						self.weaponskill = 0

					if self.weaponskill == None:
						self.weaponskill = 0
				else:
					self.weaponskill = 0

				self.move_speed = ewutils.get_move_speed(self)
				self.limit_fix();
			finally:
				# Clean up the database handles.
				cursor.close()
				ewutils.databaseClose(conn_info)

	""" Save this user object to the database. """
	def persist(self):
	
		try:
			# Get database handles if they weren't passed.
			conn_info = ewutils.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor();

			self.limit_fix();

			# Save the object.
			cursor.execute("REPLACE INTO users({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(
				ewcfg.col_id_user,
				ewcfg.col_id_server,
				ewcfg.col_slimes,
				ewcfg.col_slimelevel,
				ewcfg.col_hunger,
				ewcfg.col_totaldamage,
				ewcfg.col_bounty,
				ewcfg.col_weapon,
				ewcfg.col_weaponskill,
				ewcfg.col_trauma,
				ewcfg.col_slimecoin,
				ewcfg.col_time_lastkill,
				ewcfg.col_time_lastrevive,
				ewcfg.col_id_killer,
				ewcfg.col_time_lastspar,
				ewcfg.col_time_lasthaunt,
				ewcfg.col_time_lastinvest,
				ewcfg.col_ghostbust,
				ewcfg.col_inebriation,
				ewcfg.col_faction,
				ewcfg.col_poi,
				ewcfg.col_life_state,
				ewcfg.col_busted,
				ewcfg.col_rrchallenger,
				ewcfg.col_time_last_action,
				ewcfg.col_weaponmarried,
				ewcfg.col_time_lastscavenge,
				ewcfg.col_bleed_storage,
				ewcfg.col_time_lastenter,
				ewcfg.col_time_lastoffline,
				ewcfg.col_time_joined,
				ewcfg.col_poi_death,
				ewcfg.col_slime_donations,
				ewcfg.col_poudrin_donations,
				ewcfg.col_arrested,
				ewcfg.col_fish_space,
				ewcfg.col_unclaimed_prizes
			), (
				self.id_user,
				self.id_server,
				self.slimes,
				self.slimelevel,
				self.hunger,
				self.totaldamage,
				self.bounty,
				self.weapon,
				self.weaponskill,
				self.trauma,
				self.slimecoin,
				self.time_lastkill,
				self.time_lastrevive,
				self.id_killer,
				self.time_lastspar,
				self.time_lasthaunt,
				self.time_lastinvest,
				(1 if self.ghostbust else 0),
				self.inebriation,
				self.faction,
				self.poi,
				self.life_state,
				(1 if self.busted else 0),
				self.rr_challenger,
				self.time_last_action,
				(1 if self.weaponmarried else 0),
				self.time_lastscavenge,
				self.bleed_storage,
				self.time_lastenter,
				self.time_lastoffline,
				self.time_joined,
				self.poi_death,
				self.slime_donations,
				self.poudrin_donations,
				(1 if self.arrested else 0),
				self.fish_space,
				self.unclaimed_prizes
			))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			ewutils.databaseClose(conn_info)
