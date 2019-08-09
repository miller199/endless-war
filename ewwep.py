import asyncio
import time
import random
import math

import ewcfg
import ewutils
import ewitem
import ewmap
import ewrolemgr
import ewstats

from ew import EwUser
from ewitem import EwItem
from ewmarket import EwMarket
from ewslimeoid import EwSlimeoid
from ewdistrict import EwDistrict
from ewplayer import EwPlayer

""" A weapon object which adds flavor text to kill/shoot. """
class EwWeapon:

	item_type = "weapon"

	# A unique name for the weapon. This is used in the database and typed by
	# users, so it should be one word, all lowercase letters.
	id_weapon = ""

	# An array of names that might be used to identify this weapon by the player.
	alias = []

	# Displayed when !equip-ping this weapon
	str_equip = ""

	# Displayed when this weapon is used for a !kill
	str_kill = ""

	# Displayed to the dead victim in the sewers. Brief phrase such as "gunned down" etc.
	str_killdescriptor = ""

	# Displayed when viewing the !trauma of another player.
	str_trauma = ""

	# Displayed when viewing the !trauma of yourself.
	str_trauma_self = ""
	
	# Displayed when viewing the !weapon of another player.
	str_weapon = ""

	# Displayed when viewing the !weapon of yourself.
	str_weapon_self = ""

	# Same as weapon and weapon_self, but used when the player's weapon skill is max.
	str_weaponmaster = ""
	str_weaponmaster_self = ""

	# Displayed when a non-lethal hit occurs.
	str_damage = ""

	# Displayed when two players wielding the same weapon !spar with each other.
	str_duel = ""

	# Function that applies the special effect for this weapon.
	fn_effect = None

	# Displayed when a weapon effect causes a critical hit.
	str_crit = ""

	# Displayed when a weapon effect causes a miss.
	str_miss = ""

	# Displayed when !inspect-ing
	str_description = ""

	acquisition = "dojo"
	def __init__(
		self,
		id_weapon = "",
		alias = [],
		str_equip = "",
		str_kill = "",
		str_killdescriptor = "",
		str_trauma = "",
		str_trauma_self = "",
		str_weapon = "",
		str_weapon_self = "",
		str_damage = "",
		str_duel = "",
		str_weaponmaster = "",
		str_weaponmaster_self = "",
		fn_effect = None,
		str_crit = "",
		str_miss = "",
		str_description = "",
		acquisition = "dojo"
	):
		self.item_type = ewcfg.it_weapon

		self.id_weapon = id_weapon
		self.alias = alias
		self.str_equip = str_equip
		self.str_kill = str_kill
		self.str_killdescriptor = str_killdescriptor
		self.str_trauma = str_trauma
		self.str_trauma_self = str_trauma_self
		self.str_weapon = str_weapon
		self.str_weapon_self = str_weapon_self
		self.str_damage = str_damage
		self.str_duel = str_duel
		self.str_weaponmaster = str_weaponmaster
		self.str_weaponmaster_self = str_weaponmaster_self
		self.fn_effect = fn_effect
		self.str_crit = str_crit
		self.str_miss = str_miss
		self.str_description = str_description
		self.acquisition = acquisition

		self.str_name = self.str_weapon


""" A data-moving class which holds references to objects we want to modify with weapon effects. """
class EwEffectContainer:
	miss = False
	crit = False
	strikes = 0
	slimes_damage = 0
	slimes_spent = 0
	user_data = None
	shootee_data = None

	# Debug method to dump out the members of this object.
	def dump(self):
		print("effect:\nmiss: {miss}\ncrit: {crit}\nstrikes: {strikes}\nslimes_damage: {slimes_damage}\nslimes_spent: {slimes_spent}".format(
			miss = self.miss,
			crit = self.crit,
			strikes = self.strikes,
			slimes_damage = self.slimes_damage,
			slimes_spent = self.slimes_spent
		))

	def __init__(
		self,
		miss = False,
		crit = False,
		strikes = 0,
		slimes_damage = 0,
		slimes_spent = 0,
		user_data = None,
		shootee_data = None
	):
		self.miss = miss
		self.crit = crit
		self.strikes = strikes
		self.slimes_damage = slimes_damage
		self.slimes_spent = slimes_spent
		self.user_data = user_data
		self.shootee_data = shootee_data

""" Player deals damage to another player. """
async def attack(cmd):
	time_now = int(time.time())
	response = ""
	deathreport = ""
	levelup_response = ""
	coinbounty = 0
	resp_cont = ewutils.EwResponseContainer(id_server = cmd.message.server.id)
	market_data = EwMarket(id_server = cmd.message.server.id)

	user_data = EwUser(member = cmd.message.author)
	slimeoid = EwSlimeoid(member = cmd.message.author)
	weapon = None
	weapon_item = None
	if user_data.weapon >= 0:
		weapon_item = EwItem(id_item = user_data.weapon)
		weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))


	if ewmap.channel_name_is_poi(cmd.message.channel.name) == False:
		response = "You can't commit violence from here."
		resp_cont.add_channel_response(cmd.message.channel.name, response)
	elif ewmap.poi_is_pvp(user_data.poi) == False:
		response = "You must go elsewhere to commit gang violence."
		resp_cont.add_channel_response(cmd.message.channel.name, response)
	elif cmd.mentions_count > 1:
		response = "One shot at a time!"
		resp_cont.add_channel_response(cmd.message.channel.name, response)
	elif cmd.mentions_count <= 0:
		response = "Your bloodlust is appreciated, but ENDLESS WAR didn't understand that name."
		resp_cont.add_channel_response(cmd.message.channel.name, response)
	elif user_data.hunger >= ewutils.hunger_max_bylevel(user_data.slimelevel):
		response = "You are too exhausted for gang violence right now. Go get some grub!"
		resp_cont.add_channel_response(cmd.message.channel.name, response)
	elif cmd.mentions_count == 1:
		# Get shooting player's info
		if user_data.slimelevel <= 0: 
			user_data.slimelevel = 1
			user_data.persist()

		# Get target's info.
		member = cmd.mentions[0]
		if member.id == cmd.message.author.id:
			response = "Try {}.".format(ewcfg.cmd_suicide)
			resp_cont.add_channel_response(cmd.message.channel.name, response)
			return await resp_cont.post()
		else:
			shootee_data = EwUser(member = member)
		shootee_slimeoid = EwSlimeoid(member = member)

		user_mutations = user_data.get_mutations()
		shootee_mutations = shootee_data.get_mutations()

		district_data = EwDistrict(district = user_data.poi, id_server = cmd.message.server.id)

		miss = False
		crit = False
		strikes = 0

		slimes_spent = int(ewutils.slime_bylevel(user_data.slimelevel) / 20)
		slimes_damage = int((slimes_spent * 4) * (100 + (user_data.weaponskill * 10)) / 100.0)

		if weapon is None:
			slimes_damage /= 2  # penalty for not using a weapon, otherwise fists would be on par with other weapons
		slimes_dropped = shootee_data.totaldamage + shootee_data.slimes

		#fumble_chance = (random.randrange(10) - 4)
		#if fumble_chance > user_data.weaponskill:
			#miss = True

		user_iskillers = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_killers
		user_isrowdys = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_rowdys
		user_isslimecorp = user_data.life_state in [ewcfg.life_state_lucky, ewcfg.life_state_executive]

		if shootee_data.life_state == ewcfg.life_state_kingpin:
			# Disallow killing generals.
			response = "He is hiding in his ivory tower and playing video games like a retard."
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif (slimes_spent > user_data.slimes):
			# Not enough slime to shoot.
			response = "You don't have enough slime to attack. ({:,}/{:,})".format(user_data.slimes, slimes_spent)
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif (time_now - user_data.time_lastkill) < ewcfg.cd_kill:
			# disallow kill if the player has killed recently
			response = "Take a moment to appreciate your last slaughter."
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif shootee_data.poi != user_data.poi:
			response = "You can't reach them from where you are."
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif ewmap.poi_is_pvp(shootee_data.poi) == False:
			response = "{} is not mired in the ENDLESS WAR right now.".format(member.display_name)
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif user_iskillers == False and user_isrowdys == False and user_isslimecorp == False:
			# Only killers, rowdys, the cop killer, and rowdy fucker can shoot people.
			if user_data.life_state == ewcfg.life_state_juvenile:
				response = "Juveniles lack the moral fiber necessary for violence."
			else:
				response = "You lack the moral fiber necessary for violence."
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif (time_now - shootee_data.time_lastrevive) < ewcfg.invuln_onrevive:
			# User is currently invulnerable.
			response = "{} has died too recently and is immune.".format(member.display_name)
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif shootee_data.life_state == ewcfg.life_state_corpse and user_data.ghostbust == True:
			# Attack a ghostly target
			was_busted = True

			#hunger drain
			user_data.hunger += ewcfg.hunger_pershot * ewutils.hunger_cost_mod(user_data.slimelevel)
			
			# Remove !revive invulnerability.
			user_data.time_lastrevive = 0

			# Spend slimes, to a minimum of zero
			user_data.change_slimes(n = (-user_data.slimes if slimes_spent >= user_data.slimes else -slimes_spent), source = ewcfg.source_spending)

			# Damage stats
			ewstats.track_maximum(user = user_data, metric = ewcfg.stat_max_hitdealt, value = slimes_damage)
			ewstats.change_stat(user = user_data, metric = ewcfg.stat_lifetime_damagedealt, n = slimes_damage)

			# Remove repeat killing protection if.
			if user_data.id_killer == shootee_data.id_user:
				user_data.id_killer = ""

			if was_busted:
				coinbounty = int(shootee_data.bounty / ewcfg.slimecoin_exchangerate)
				user_data.change_slimecoin(n = coinbounty, coinsource = ewcfg.coinsource_bounty)

				ewstats.track_maximum(user = user_data, metric = ewcfg.stat_biggest_bust_level, value = shootee_data.slimelevel)

				# Steal items
				ewitem.item_loot(member = member, id_user_target = cmd.message.author.id)

				shootee_data.die(cause = ewcfg.cause_busted)

				response = "{name_target}\'s ghost has been **BUSTED**!!".format(name_target = member.display_name)

				deathreport = "Your ghost has been busted by {}. {}".format(cmd.message.author.display_name, ewcfg.emote_bustin)
				deathreport = "{} ".format(ewcfg.emote_bustin) + ewutils.formatMessage(member, deathreport)
				
				if coinbounty > 0:
					response += "\n\n SlimeCorp transfers {} SlimeCoin to {}\'s account.".format(str(coinbounty), cmd.message.author.display_name)

				#adjust busts
				ewstats.increment_stat(user = user_data, metric = ewcfg.stat_ghostbusts)


			# Persist every users' data.
			user_data.persist()
			shootee_data.persist()
			resp_cont.add_channel_response(cmd.message.channel.name, response)
			if deathreport != "":
				resp_cont.add_channel_response(ewcfg.channel_sewers, deathreport)

			await ewrolemgr.updateRoles(client = cmd.client, member = cmd.message.server.get_member(shootee_data.id_user))

		elif shootee_data.life_state == ewcfg.life_state_corpse and shootee_data.busted == True:
			# Target is already dead and not a ghost.
			response = "{} is already dead.".format(member.display_name)
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		elif shootee_data.life_state == ewcfg.life_state_corpse and user_data.ghostbust == False:
			# Target is a ghost but user is not able to bust 
			response = "You don't know how to fight a ghost."
			resp_cont.add_channel_response(cmd.message.channel.name, response)

		else:
			# Slimes from this shot might be awarded to the boss.
			role_boss = (ewcfg.role_copkiller if user_iskillers else ewcfg.role_rowdyfucker)
			boss_slimes = 0
			user_inital_level = user_data.slimelevel

			was_juvenile = False
			was_killed = False
			was_shot = False

			if shootee_data.life_state in [ewcfg.life_state_enlisted, ewcfg.life_state_juvenile, ewcfg.life_state_lucky, ewcfg.life_state_executive]:
				# User can be shot.
				if shootee_data.life_state == ewcfg.life_state_juvenile:
					was_juvenile = True

				was_shot = True

			if was_shot:
				#hunger drain
				user_data.hunger += ewcfg.hunger_pershot * ewutils.hunger_cost_mod(user_data.slimelevel)
				
				# Weaponized flavor text.
				randombodypart = ewcfg.hitzone_list[random.randrange(len(ewcfg.hitzone_list))]

				# Weapon-specific adjustments
				if weapon != None and weapon.fn_effect != None:
					# Build effect container
					ctn = EwEffectContainer(
						miss = miss,
						crit = crit,
						slimes_damage = slimes_damage,
						slimes_spent = slimes_spent,
						user_data = user_data,
						shootee_data = shootee_data
					)

					# Make adjustments
					weapon.fn_effect(ctn)

					# Apply effects for non-reference values
					miss = ctn.miss
					crit = ctn.crit
					slimes_damage = ctn.slimes_damage
					slimes_spent = ctn.slimes_spent
					strikes = ctn.strikes
					# user_data and shootee_data should be passed by reference, so there's no need to assign them back from the effect container.

				# can't hit lucky lucy
				if shootee_data.life_state == ewcfg.life_state_lucky:
					miss = True

				if miss:
					slimes_damage = 0

				# Remove !revive invulnerability.

				user_data.time_lastrevive = 0
				if ewcfg.mutation_id_lonewolf in user_mutations:
					allies_in_district = district_data.get_players_in_district(
						min_level = math.ceil((1/10) ** 0.25 * user_data.slimelevel),
						life_states = [ewcfg.life_state_enlisted],
						factions = [user_data.faction]
					)
					if user_data.id_user in allies_in_district:
						allies_in_district.remove(user_data.id_user)

					if len(allies_in_district) == 0:
						slimes_damage *= 1.5

				if ewcfg.mutation_id_organicfursuit in user_mutations and (
					(market_data.day % 31 == 0 and market_data.clock >= 20)
					or (market_data.day % 31 == 1 and market_data.clock < 6)
				):
					slimes_damage *= 2
				if ewcfg.mutation_id_organicfursuit in shootee_mutations and (
					(market_data.day % 31 == 0 and market_data.clock >= 20)
					or (market_data.day % 31 == 1 and market_data.clock < 6)
				):
					slimes_damage *= 0.1
				if ewcfg.mutation_id_fatchance in shootee_mutations and shootee_data.hunger / shootee_data.get_hunger_max() > 0.5:
					slimes_damage *= 0.75
				if ewcfg.mutation_id_socialanimal in user_mutations:
					allies_in_district = district_data.get_players_in_district(
						min_level = math.ceil((1/10) ** 0.25 * user_data.slimelevel),
						life_states = [ewcfg.life_state_enlisted],
						factions = [user_data.faction]
					)
					if user_data.id_user in allies_in_district:
						allies_in_district.remove(user_data.id_user)

					slimes_damage *= 1 + 0.1 * len(allies_in_district)
				if ewcfg.mutation_id_dressedtokill in user_mutations:
					items = ewitem.inventory(
						id_user = cmd.message.author.id,
						id_server = cmd.message.server.id,
						item_type_filter = ewcfg.it_cosmetic
					)

					adorned_items = 0
					for it in items:
						i = EwItem(it.get('id_item'))
						if i.item_props['adorned'] == 'true':
							adorned_items += 1

					if adorned_items >= ewutils.max_adorn_bylevel(user_data.slimelevel):
						slimes_damage *= 2

				# Spend slimes, to a minimum of zero
				user_data.change_slimes(n = (-user_data.slimes if slimes_spent >= user_data.slimes else -slimes_spent), source = ewcfg.source_spending)

				# Damage stats
				ewstats.track_maximum(user = user_data, metric = ewcfg.stat_max_hitdealt, value = slimes_damage)
				ewstats.change_stat(user = user_data, metric = ewcfg.stat_lifetime_damagedealt, n = slimes_damage)

				# Remove repeat killing protection if.
				if user_data.id_killer == shootee_data.id_user:
					user_data.id_killer = ""

				user_data.persist()
				shootee_data = EwUser(member = member)


				if slimes_damage >= shootee_data.slimes - shootee_data.bleed_storage:
					was_killed = True
					if ewcfg.mutation_id_thickerthanblood in user_mutations:
						slimes_damage = 0
					else:
						slimes_damage = max(shootee_data.slimes - shootee_data.bleed_storage, 0)

				sewer_data = EwDistrict(district = ewcfg.poi_id_thesewers, id_server = cmd.message.server.id)
				# move around slime as a result of the shot
				if was_juvenile or user_data.faction == shootee_data.faction:
					slimes_drained = int(3 * slimes_damage / 4) # 3/4
					slimes_toboss = 0
				else:
					slimes_drained = 0
					slimes_toboss = int(slimes_damage / 2)

				damage = str(slimes_damage)

				slimes_tobleed = int((slimes_damage - slimes_toboss - slimes_drained) / 2)
				if ewcfg.mutation_id_nosferatu in user_mutations and (market_data.clock < 6 or market_data.clock >= 20):
					slimes_tobleed = 0
				if ewcfg.mutation_id_bleedingheart in shootee_mutations:
					slimes_tobleed *= 2

				slimes_directdamage = slimes_damage - slimes_tobleed
				slimes_splatter = slimes_damage - slimes_toboss - slimes_tobleed - slimes_drained

				boss_slimes += slimes_toboss
				district_data.change_slimes(n = slimes_splatter, source = ewcfg.source_killing)
				shootee_data.bleed_storage += slimes_tobleed
				shootee_data.change_slimes(n = - slimes_directdamage, source = ewcfg.source_damage)
				sewer_data.change_slimes(n = slimes_drained)
				sewer_data.persist()

				if was_killed:
					#adjust statistics
					ewstats.increment_stat(user = user_data, metric = ewcfg.stat_kills)
					ewstats.track_maximum(user = user_data, metric = ewcfg.stat_biggest_kill, value = int(slimes_dropped))
					if user_data.slimelevel > shootee_data.slimelevel:
						ewstats.increment_stat(user = user_data, metric = ewcfg.stat_lifetime_ganks)
					elif user_data.slimelevel < shootee_data.slimelevel:
						ewstats.increment_stat(user = user_data, metric = ewcfg.stat_lifetime_takedowns)

					# Collect bounty
					coinbounty = int(shootee_data.bounty / ewcfg.slimecoin_exchangerate)  # 100 slime per coin
					
					if shootee_data.slimes >= 0:
						user_data.change_slimecoin(n = coinbounty, coinsource = ewcfg.coinsource_bounty)


					# Steal items
					ewitem.item_loot(member = member, id_user_target = cmd.message.author.id)

					#add bounty
					user_data.add_bounty(n = (shootee_data.bounty / 2) + (slimes_dropped / 4))

					# Give a bonus to the player's weapon skill for killing a stronger player.
					if shootee_data.slimelevel >= user_data.slimelevel and weapon is not None:
						user_data.add_weaponskill(n = 1, weapon_type = weapon.id_weapon)
					
					explode_damage = ewutils.slime_bylevel(shootee_data.slimelevel) / 5
					# explode, damaging everyone in the district

					# release bleed storage
					if ewcfg.mutation_id_thickerthanblood in user_mutations:
						slimes_todistrict = 0
						slimes_tokiller = shootee_data.slimes
					else:
						slimes_todistrict = shootee_data.slimes / 2
						slimes_tokiller = shootee_data.slimes / 2
					district_data.change_slimes(n = slimes_todistrict, source = ewcfg.source_killing)
					levelup_response = user_data.change_slimes(n = slimes_tokiller, source = ewcfg.source_killing)
					if ewcfg.mutation_id_fungalfeaster in user_mutations:
						user_data.hunger = 0

					# Player was killed.
					shootee_data.id_killer = user_data.id_user
					shootee_data.die(cause = ewcfg.cause_killing)
					shootee_data.change_slimes(n = -slimes_dropped / 10, source = ewcfg.source_ghostification)

					

					kill_descriptor = "beaten to death"
					if weapon != None:
						response = weapon.str_damage.format(
							name_player = cmd.message.author.display_name,
							name_target = member.display_name,
							hitzone = randombodypart,
							strikes = strikes
						)
						kill_descriptor = weapon.str_killdescriptor
						if crit:
							response += " {}".format(weapon.str_crit.format(
								name_player = cmd.message.author.display_name,
								name_target = member.display_name
							))

						response += "\n\n{}".format(weapon.str_kill.format(
							name_player = cmd.message.author.display_name,
							name_target = member.display_name,
							emote_skull = ewcfg.emote_slimeskull
						))
						shootee_data.trauma = weapon.id_weapon

					else:
						response = "{name_target} is hit!!\n\n{name_target} has died.".format(name_target = member.display_name)

						shootee_data.trauma = ""

					if slimeoid.life_state == ewcfg.slimeoid_state_active:
						brain = ewcfg.brain_map.get(slimeoid.ai)
						response += "\n\n" + brain.str_kill.format(slimeoid_name = slimeoid.name)

					if shootee_slimeoid.life_state == ewcfg.slimeoid_state_active:
						brain = ewcfg.brain_map.get(shootee_slimeoid.ai)
						response += "\n\n" + brain.str_death.format(slimeoid_name = shootee_slimeoid.name)

					deathreport = "You were {} by {}. {}".format(kill_descriptor, cmd.message.author.display_name, ewcfg.emote_slimeskull)
					deathreport = "{} ".format(ewcfg.emote_slimeskull) + ewutils.formatMessage(member, deathreport)
					
					if coinbounty > 0:
						response += "\n\n SlimeCorp transfers {} SlimeCoin to {}\'s account.".format(str(coinbounty), cmd.message.author.display_name)

					shootee_data.persist()
					user_data.persist()
					resp_cont.add_channel_response(ewcfg.channel_sewers, deathreport)
					resp_cont.add_channel_response(cmd.message.channel.name, response)
					if ewcfg.mutation_id_spontaneouscombustion in shootee_mutations:
						explode_resp = "\n{} spontaneously combusts, horribly dying in a fiery explosion of slime and shrapnel!! Oh, the humanity!".format(member.display_name)
						resp_cont.add_channel_response(cmd.message.channel.name, explode_resp)
						explosion = explode(damage = explode_damage, district_data = district_data)
						resp_cont.add_response_container(explosion)
					user_data = EwUser(member = cmd.message.author)
					shootee_data = EwUser(member = member)
				else:
					# A non-lethal blow!

					if weapon != None:
						if miss:
							response = "{}".format(weapon.str_miss.format(
								name_player = cmd.message.author.display_name,
								name_target = member.display_name
							))
						else:
							response = weapon.str_damage.format(
								name_player = cmd.message.author.display_name,
								name_target = member.display_name,
								hitzone = randombodypart,
								strikes = strikes
							)
							if crit:
								response += " {}".format(weapon.str_crit.format(
									name_player = cmd.message.author.display_name,
									name_target = member.display_name
								))
							response += " {target_name} loses {damage} slime!".format(
								target_name = member.display_name,
								damage = damage
							)
					else:
						if miss:
							response = "{target_name} dodges your strike.".format(target_name = member.display_name)
						else:
							response = "{target_name} is hit!! {target_name} loses {damage} slime!".format(
								target_name = member.display_name,
								damage = damage
							)
					resp_cont.add_channel_response(cmd.message.channel.name, response)
			else:
				response = 'You are unable to attack {}.'.format(member.display_name)
				resp_cont.add_channel_response(cmd.message.channel.name, response)

			# Add level up text to response if appropriate
			if user_inital_level < user_data.slimelevel:
				resp_cont.add_channel_response(cmd.message.channel.name, "\n" + levelup_response)
			# Team kills don't award slime to the kingpin.
			if user_data.faction != shootee_data.faction:
				# Give slimes to the boss if possible.
				kingpin = ewutils.find_kingpin(id_server = cmd.message.server.id, kingpin_role = role_boss)

				if kingpin:
					kingpin.change_slimes(n = boss_slimes)
					kingpin.persist()

			# Persist every users' data.
			user_data.persist()
			shootee_data.persist()

			district_data.persist()

			# Assign the corpse role to the newly dead player.
			if was_killed:
				await ewrolemgr.updateRoles(client = cmd.client, member = member)
				# announce death in kill feed channel
				#killfeed_channel = ewutils.get_channel(cmd.message.server, ewcfg.channel_killfeed)
				killfeed_resp = resp_cont.channel_responses[cmd.message.channel.name]
				for r in killfeed_resp:
					resp_cont.add_channel_response(ewcfg.channel_killfeed, r)
				resp_cont.format_channel_response(ewcfg.channel_killfeed, cmd.message.author)
				resp_cont.add_channel_response(ewcfg.channel_killfeed, "`-------------------------`")
				#await ewutils.send_message(cmd.client, killfeed_channel, ewutils.formatMessage(cmd.message.author, killfeed_resp))

	# Send the response to the player.
	resp_cont.format_channel_response(cmd.message.channel.name, cmd.message.author)
	await resp_cont.post()


""" player kills themself """
async def suicide(cmd):
	response = ""
	deathreport = ""

	# Only allowed in the combat zone.
	if ewmap.channel_name_is_poi(cmd.message.channel.name) == False:
		response = "You must go into the city to commit {}.".format(cmd.tokens[0][1:])
	else:
		# Get the user data.
		user_data = EwUser(member = cmd.message.author)

		user_iskillers = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_killers
		user_isrowdys = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_rowdys
		user_isgeneral = user_data.life_state == ewcfg.life_state_kingpin
		user_isjuvenile = user_data.life_state == ewcfg.life_state_juvenile
		user_isdead = user_data.life_state == ewcfg.life_state_corpse
		user_isexecutive = user_data.life_state == ewcfg.life_state_executive
		user_islucky = user_data.life_state == ewcfg.life_state_lucky

		if user_isdead:
			response = "Too late for that."
		elif user_isjuvenile:
			response = "Juveniles are too cowardly for suicide."
		elif user_isgeneral:
			response = "\*click* Alas, your gun has jammed."
		elif user_iskillers or user_isrowdys or user_isexecutive or user_islucky:
			#Give slime to challenger if player suicides mid russian roulette
			if user_data.rr_challenger != "":
				challenger = EwUser(id_user= user_data.rr_challenger, id_server= user_data.id_server)
				challenger.change_slimes(n = user_data.slimes, source = ewcfg.source_killing)
				ewitem.item_loot(member = cmd.message.author, id_user_target = user_data.rr_challenger)
				challenger.persist()
				
			district_data = EwDistrict(district = user_data.poi, id_server = cmd.message.server.id)
			district_data.change_slimes(n = user_data.slimes + user_data.bleed_storage, source = ewcfg.source_killing)
			district_data.persist()

			# Set the id_killer to the player himself, remove his slime and slime poudrins.
			user_data.id_killer = cmd.message.author.id
			user_data.die(cause = ewcfg.cause_suicide)
			user_data.persist()

			# Assign the corpse role to the player. He dead.
			await ewrolemgr.updateRoles(client = cmd.client, member = cmd.message.author)

			response = '{} has willingly returned to the slime. {}'.format(cmd.message.author.display_name, ewcfg.emote_slimeskull)
			deathreport = "You arrive among the dead by your own volition. {}".format(ewcfg.emote_slimeskull)
			deathreport = "{} ".format(ewcfg.emote_slimeskull) + ewutils.formatMessage(cmd.message.author, deathreport)
		else:
			# This should never happen. We handled all the role cases. Just in case.
			response = "\*click* Alas, your gun has jammed."

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	if deathreport != "":
		sewerchannel = ewutils.get_channel(cmd.message.server, ewcfg.channel_sewers)
		await ewutils.send_message(cmd.client, sewerchannel, deathreport)

""" Damage all players in a district """
def explode(damage = 0, district_data = None):
	id_server = district_data.id_server
	poi = district_data.name

	resp_cont = ewutils.EwResponseContainer(id_server = id_server)
	response = ""
	channel = ewcfg.id_to_poi.get(poi).channel

	life_states = [ewcfg.life_state_juvenile, ewcfg.life_state_enlisted, ewcfg.life_state_executive]
	users = district_data.get_players_in_district(life_states = life_states)

	for user in users:
		user_data = EwUser(id_user = user, id_server = id_server)
		mutations = user_data.get_mutations()

		if True:
			player_data = EwPlayer(id_user = user_data.id_user)
			response = "{} is blown back by the explosion’s sheer force! They lose {} slime!!".format(player_data.display_name, damage)
			resp_cont.add_channel_response(channel, response)
			slimes_damage = damage
			if user_data.slimes < slimes_damage + user_data.bleed_storage:
				# die in the explosion
				district_data.change_slimes(n = user_data.slimes, source = ewcfg.source_killing)
				district_data.persist()
				slimes_dropped = user_data.totaldamage + user_data.slimes
				explode_damage = ewutils.slime_bylevel(user_data.slimelevel)

				user_data.die(cause = ewcfg.cause_killing)
				user_data.change_slimes(n = -slimes_dropped / 10, source = ewcfg.source_ghostification)
				user_data.persist()

				response = "Alas, {} was caught too close to the blast. They are consumed by the flames, and die in the explosion.".format(player_data.display_name)
				resp_cont.add_channel_response(channel, response)

				if ewcfg.mutation_id_spontaneouscombustion in mutations:
					sub_explosion = explode(explode_damage, district_data)
					resp_cont.add_response_container(sub_explosion)
			else:
				# survive
				slime_splatter = 0.5 * slimes_damage
				district_data.change_slimes(n = slime_splatter, source = ewcfg.source_killing)
				district_data.persist()
				slimes_damage -= slime_splatter
				user_data.bleed_storage += slimes_damage
				user_data.change_slimes(n = -slime_splatter, source = ewcfg.source_killing)
				user_data.persist()
	return resp_cont
	


""" Player spars with a friendly player to gain slime. """
async def spar(cmd):
	time_now = int(time.time())
	response = ""

	if cmd.message.channel.name != ewcfg.channel_dojo:
		response = "You must go to the dojo to spar."

	elif cmd.mentions_count > 1:
		response = "One sparring partner at a time!"
		
	elif cmd.mentions_count == 1:
		member = cmd.mentions[0]

		if(member.id == cmd.message.author.id):
			response = "How do you expect to spar with yourself?"
		else:
			# Get killing player's info.
			user_data = EwUser(member = cmd.message.author)
			weapon_item = EwItem(id_item = user_data.weapon)

			# Get target's info.
			sparred_data = EwUser(member = member)
			sparred_weapon_item = EwItem(id_item = sparred_data.weapon)

			user_iskillers = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_killers
			user_isrowdys = user_data.life_state == ewcfg.life_state_enlisted and user_data.faction == ewcfg.faction_rowdys
			user_isdead = user_data.life_state == ewcfg.life_state_corpse

			if user_data.hunger >= ewutils.hunger_max_bylevel(user_data.slimelevel):
				response = "You are too exhausted to train right now. Go get some grub!"
			elif user_data.poi != ewcfg.poi_id_dojo or sparred_data.poi != ewcfg.poi_id_dojo:
				response = "Both players need to be in the dojo to spar."
			elif sparred_data.hunger >= ewutils.hunger_max_bylevel(sparred_data.slimelevel):
				response = "{} is too exhausted to train right now. They need a snack!".format(member.display_name)
			elif user_isdead == True:
				response = "The dead think they're too cool for conventional combat. Pricks."
			elif user_iskillers == False and user_isrowdys == False:
				# Only killers, rowdys, the cop killer, and the rowdy fucker can spar
				response = "Juveniles lack the backbone necessary for combat."
			else:
				was_juvenile = False
				was_sparred = False
				was_dead = False
				was_player_tired = False
				was_target_tired = False
				was_enemy = False
				duel = False

				#Determine if the !spar is a duel:
				weapon = None
				if user_data.weapon >= 0 and sparred_data.weapon >= 0 and weapon_item.item_props.get("weapon_type") == sparred_weapon_item.item_props.get("weapon_type"):
					weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))
					duel = True

				if sparred_data.life_state == ewcfg.life_state_corpse:
					# Target is already dead.
					was_dead = True
				elif (user_data.time_lastspar + ewcfg.cd_spar) > time_now:
					# player sparred too recently
					was_player_tired = True
				elif (sparred_data.time_lastspar + ewcfg.cd_spar) > time_now:
					# taret sparred too recently
					was_target_tired = True
				elif sparred_data.life_state == ewcfg.life_state_juvenile:
					# Target is a juvenile.
					was_juvenile = True

				elif (user_iskillers and (sparred_data.life_state == ewcfg.life_state_enlisted and sparred_data.faction == ewcfg.faction_killers)) or (user_isrowdys and (sparred_data.life_state == ewcfg.life_state_enlisted and sparred_data.faction == ewcfg.faction_rowdys)):
					# User can be sparred.
					was_sparred = True
				elif (user_iskillers and (sparred_data.life_state == ewcfg.life_state_enlisted and sparred_data.faction == ewcfg.faction_rowdys)) or (user_isrowdys and (sparred_data.life_state == ewcfg.life_state_enlisted and sparred_data.faction == ewcfg.faction_killers)):
					# Target is a member of the opposing faction.
					was_enemy = True


				#if the duel is successful
				if was_sparred:
					weaker_player = sparred_data if sparred_data.slimes < user_data.slimes else user_data
					stronger_player = sparred_data if user_data is weaker_player else user_data

					# Weaker player gains slime based on the slime of the stronger player.
					possiblegain = int(ewcfg.slimes_perspar_base * (2.2 ** weaker_player.slimelevel))
					slimegain = min(possiblegain, stronger_player.slimes / 20)
					weaker_player.change_slimes(n = slimegain)
					
					#hunger drain for both players
					user_data.hunger += ewcfg.hunger_perspar * ewutils.hunger_cost_mod(user_data.slimelevel)
					sparred_data.hunger += ewcfg.hunger_perspar * ewutils.hunger_cost_mod(sparred_data.slimelevel)

					# Bonus 50% slime to both players in a duel.
					if duel:
						weaker_player.change_slimes(n = slimegain / 2)
						stronger_player.change_slimes(n = slimegain / 2)

						if weaker_player.weaponskill < 5 or (weaker_player.weaponskill + 1) < stronger_player.weaponskill:
							weaker_player.add_weaponskill(n = 1, weapon_type = weapon.id_weapon)

						if stronger_player.weaponskill < 5 or (stronger_player.weaponskill + 1) < weaker_player.weaponskill:
							stronger_player.add_weaponskill(n = 1, weapon_type = weapon.id_weapon)

					weaker_player.time_lastspar = time_now

					user_data.persist()
					sparred_data.persist()

					# player was sparred with
					if duel and weapon != None:
						response = weapon.str_duel.format(name_player = cmd.message.author.display_name, name_target = member.display_name)
					else:
						response = '{} parries the attack. :knife: {}'.format(member.display_name, ewcfg.emote_slime5)

					#Notify if max skill is reached	
					if weapon != None:
						if user_data.weaponskill >= 5:
							response += ' {} is a master of the {}.'.format(cmd.message.author.display_name, weapon.id_weapon)
						if sparred_data.weaponskill >= 5:
							response += ' {} is a master of the {}.'.format(member.display_name, weapon.id_weapon)

				else:
					if was_dead:
						# target is already dead
						response = '{} is already dead.'.format(member.display_name)
					elif was_target_tired:
						# target has sparred too recently
						response = '{} is too tired to spar right now.'.format(member.display_name)
					elif was_player_tired:
						# player has sparred too recently
						response = 'You are too tired to spar right now.'
					elif was_enemy:
						# target and player are different factions
						response = "You cannot spar with your enemies."
					else:
						#otherwise unkillable
						response = '{} cannot spar now.'.format(member.display_name)
	else:
		response = 'Your fighting spirit is appreciated, but ENDLESS WAR didn\'t understand that name.'

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

""" equip a weapon """
async def equip(cmd):
	user_data = EwUser(member = cmd.message.author)
	response = ""

	item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])

	item_sought = ewitem.find_item(item_search = item_search, id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

	if item_sought:
		item = EwItem(id_item = item_sought.get("id_item"))

		if item.item_type == ewcfg.it_weapon:
			response = user_data.equip(item)
			user_data.persist()
		else:
			response = "Not a weapon you ignorant juvenile"
	else:
		response = "You don't have one"

	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

""" get a weapon into your inventory"""
async def arm(cmd):
	response = ""
	user_data = EwUser(member = cmd.message.author)
	weapon_item = EwItem(id_item = user_data.weapon)

	weapons_held = ewitem.inventory(
		id_user = user_data.id_user,
		id_server = cmd.message.server.id,
		item_type_filter = ewcfg.it_weapon
	)

	if cmd.message.channel.name != ewcfg.channel_dojo:
		response = "You must go to the #{} to get new equipment.".format(ewcfg.channel_dojo)
	elif user_data.life_state == ewcfg.life_state_corpse:
		response = "Ghosts can't hold weapons."
	elif len(weapons_held) >= user_data.get_weapon_capacity():
		response = "You can't carry any more weapons."
	else:
		value = None
		if cmd.tokens_count > 1:
			value = cmd.tokens[1]
			value = value.lower()

		weapon = ewcfg.weapon_map.get(value)

		if weapon != None:
			if weapon.acquisition != ewcfg.acquisition_dojo:
				weapon = None

		if weapon != None:
			if weapon.id_weapon != 'gun' and ewcfg.weapon_fee > user_data.slimecoin:
				response = "The fee for taking a weapon is {} slimecoin and you only have {}.".format(ewcfg.weapon_fee, user_data.slimecoin)
				
			else:
				response = "You "
				item_props = ewitem.gen_item_props(weapon)

				ewitem.item_create(
					item_type = ewcfg.it_weapon,
					id_user = cmd.message.author.id,
					id_server = cmd.message.server.id,
					item_props = item_props
				)

				if weapon.id_weapon != 'gun':
					user_data.change_slimecoin(n = -ewcfg.weapon_fee, coinsource=ewcfg.source_spending)
					user_data.persist()
					response += "pay {} slimecoin and ".format(ewcfg.weapon_fee)

				response += "take {}.".format(weapon.str_weapon)
		else:
			weapon_names = []

			for weapon in ewcfg.weapon_list:
				if weapon.acquisition == ewcfg.acquisition_dojo:
					weapon_names.append(weapon.id_weapon)

			response = "Choose your weapon: {}".format(ewutils.formatNiceList(names = weapon_names, conjunction = "or"))

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

""" name a weapon using a slime poudrin """
async def annoint(cmd):
	response = ""

	if cmd.tokens_count < 2:
		response = "Specify a name for your weapon!"
	else:
		annoint_name = cmd.message.content[(len(ewcfg.cmd_annoint)):].strip()

		if len(annoint_name) > 32:
			response = "That name is too long. ({:,}/32)".format(len(annoint_name))
		else:
			user_data = EwUser(member = cmd.message.author)

			poudrin = ewitem.find_item(item_search = "slimepoudrin", id_user = cmd.message.author.id, id_server = cmd.message.server.id if cmd.message.server is not None else None)

			all_weapons = ewitem.inventory(
				id_server = cmd.message.server.id,
				item_type_filter = ewcfg.it_weapon
			)
			for weapon in all_weapons:
				if weapon.get("name") == annoint_name and weapon.get("id_item") != user_data.weapon:
					response = "**ORIGINAL WEAPON NAME DO NOT STEAL.**"
					return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


			if poudrin is None:
				response = "You need a slime poudrin."
			elif user_data.slimes < 100:
				response = "You need more slime."
			elif user_data.weapon < 0:
				response = "Equip a weapon first."
			else:
				# Perform the ceremony.
				user_data.change_slimes(n = -100, source = ewcfg.source_spending)
				weapon_item = EwItem(id_item = user_data.weapon)
				weapon_item.item_props["weapon_name"] = annoint_name
				weapon_item.persist()

				if user_data.weaponskill < 10:
					user_data.add_weaponskill(n = 1, weapon_type = weapon_item.item_props.get("weapon_type"))

				# delete a slime poudrin from the player's inventory
				ewitem.item_delete(id_item = poudrin.get('id_item'))

				user_data.persist()

				response = "You place your weapon atop the poudrin and annoint it with slime. It is now known as {}!\n\nThe name draws you closer to your weapon. The poudrin was destroyed in the process.".format(annoint_name)

	# Send the response to the player.
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


async def marry(cmd):
	user_data = EwUser(member = cmd.message.author)
	weapon_item = EwItem(id_item = user_data.weapon)
	weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))
	display_name = cmd.message.author.display_name
	weapon_name = weapon_item.item_props.get("weapon_name") if len(weapon_item.item_props.get("weapon_name")) > 0 else weapon.str_weapon

	#Checks to make sure you're in the dojo.
	if user_data.poi != ewcfg.poi_id_dojo:
		response = "Do you really expect to just get married on the side of the street in this war torn concrete jungle? No way, you need to see a specialist for this type of thing, someone who can empathize with a man’s love for his arsenal. Maybe someone in the Dojo can help, *hint hint*."
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	#Informs you that you cannot be a fucking faggot.
	elif cmd.mentions_count > 0:
		response = "Ewww, gross! You can’t marry another juvenile! That’s just degeneracy, pure and simple. What happened to the old days, where you could put a bullet in someone’s brain for receiving a hug? You people have gone soft on me, I tells ya."
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	#Makes sure you have a weapon to marry.
	elif weapon is None:
		response = "How do you plan to get married to your weapon if you aren’t holding any weapon? Goddamn, think these things through, I have to spell out everything for you."
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	#Makes sure you have a displayed rank 6 or higher weapon.
	elif user_data.weaponskill < 10:
		response = "Slow down, Casanova. You do not nearly have a close enough bond with your {} to engage in holy matrimony with it. You’ll need to reach rank 8 mastery or higher to get married.".format(weapon_name)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	#Makes sure you aren't trying to farm the extra weapon mastery ranks by marrying over and over again.
	elif user_data.weaponmarried == True:
		response = "Ah, to recapture the magic of the first nights together… Sadly, those days are far behind you now. You’ve already had your special day, now it’s time to have the same boring days forever. Aren’t you glad you got married??"
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	else:
		#Preform the ceremony 2: literally this time
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"You decide it’s finally time to take your relationship with your {} to the next level. You approach the Dojo Master with your plight, requesting his help to circumvent the legal issues of marrying your weapon. He takes a moment to unfurl his brow before letting out a raspy chuckle. He hasn’t been asked to do something like this for a long time, or so he says. You scroll up to the last instance of this flavor text and conclude he must have Alzheimer's or something. Regardless, he agrees.".format(weapon.str_weapon)
		))
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"Departing from the main floor of the Dojo, he rounds a corner and disappears for a few minutes before returning with illegally doctor marriage paperwork and cartoonish blotches of ink on his face and hands to visually communicate the hard work he’s put into the forgeries. You see, this is a form of visual shorthand that artists utilize so they don’t have to explain every beat of their narrative explicitly, but I digress."
		))
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"You express your desire to get things done as soon as possible so that you can stop reading this boring wall of text and return to your busy agenda of murder, and so he prepares to officiate immediately. You stand next to your darling {}, the only object of your affection in this godforsaken city. You shiver with anticipation for the most anticipated in-game event of your ENDLESS WAR career. A crowd of enemy and allied gangsters alike forms around you three as the Dojo Master begins the ceremony...".format(weapon_name)
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"”We are gathered here today to witness the combined union of {} and {}.".format(display_name, weapon_name)
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"Two of the greatest threats in the current metagame. No greater partners, no worse adversaries."
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"Through thick and thin, these two have stood together, fought together, and gained experience points--otherwise known as “EXP”--together."
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"It was not through hours mining or stock exchanges that this union was forged, but through iron and slime."
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"Without the weapon, the wielder would be defenseless, and without the wielder, the weapon would have no purpose."
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"It is this union that we are here today to officially-illegally affirm.”"
		))
		await asyncio.sleep(6)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"He takes a pregnant pause to increase the drama, and allow for onlookers to press 1 in preparation."
		))
		await asyncio.sleep(6)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"“I now pronounce you juvenile and armament!! You may anoint the {}”".format(weapon.str_weapon)
		))
		await asyncio.sleep(3)
		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(
			cmd.message.author,
			"You begin to tear up, fondly regarding your last kill with your {} that you love so much. You lean down and kiss your new spouse on the handle, anointing an extra two mastery ranks with pure love. It remains completely motionless, because it is an inanimate object. The Dojo Master does a karate chop midair to bookend the entire experience. Sick, you’re married now!".format(weapon_name)
		))

		#Sets their weaponmarried table to true, so that "you are married to" appears instead of "you are wielding" intheir !data, you get an extra two mastery levels, and you can't change your weapon.
		user_data = EwUser(member = cmd.message.author)
		user_data.weaponmarried = True
		user_data.add_weaponskill(n = 2, weapon_type = weapon.id_weapon)
		user_data.persist()
		weapon_item.item_props["married"] = user_data.id_user
		weapon_item.persist()
		return


async def divorce(cmd):
	user_data = EwUser(member = cmd.message.author)
	weapon_item = EwItem(id_item = user_data.weapon)
	weapon = ewcfg.weapon_map.get(weapon_item.item_props.get("weapon_type"))
	weapon_name = weapon_item.item_props.get("weapon_name") if len(weapon_item.item_props.get("weapon_name")) > 0 else weapon.str_weapon

	# Checks to make sure you're in the dojo.
	if weapon != None:
		if user_data.poi != ewcfg.poi_id_dojo:
			response = "As much as it would be satisfying to just chuck your {} down an alley and be done with it, here in civilization we deal with things *maturely.* You’ll have to speak to the guy that got you into this mess in the first place, or at least the guy that allowed you to make the retarded decision in the first place. Luckily for you, they’re the same person, and he’s at the Dojo.".format(weapon.str_weapon)
		#Makes sure you have a partner to divorce.
		elif user_data.weaponmarried == False:
			response = "I appreciate your forward thinking attitude, but how do you expect to get a divorce when you haven’t even gotten married yet? Throw your life away first, then we can talk."
		else:
			#Unpreform the ceremony
			response = "You decide it’s finally time to end the frankly obviously retarded farce that is your marriage with your {}. Things were good at first, you both wanted the same things out of life. But, that was then and this is now. You reflect briefly on your myriad of woes; the constant bickering, the mundanity of your everyday routine, the total lack of communication. You’re a slave. But, a slave you will be no longer! You know what you must do." \
					   "\nYou approach the Dojo Master yet again, and explain to him your troubles. He solemnly nods along to every beat of your explanation. Luckily, he has a quick solution. He rips apart the marriage paperwork he forged last flavor text, and just like that you’re divorced from {}. It receives half of your SlimeCoin in the settlement, a small price to pay for your freedom. You hand over what used to be your most beloved possession and partner to the old man, probably to be pawned off to whatever bumfuck juvie waddles into the Dojo next. You don’t care, you just don’t want it in your data. " \
					   "So, yeah. You’re divorced. Damn, that sucks.".format(weapon.str_weapon, weapon_name)

			#You divorce your weapon, discard it, lose it's rank, and loose half your SlimeCoin in the aftermath.
			user_data.weaponmarried = False
			user_data.weapon = -1
			ewutils.weaponskills_set(member = cmd.message.author, weapon = weapon_item.item_props.get("weapon_type"), weaponskill = 0)

			fee = (user_data.slimecoin / 2)
			user_data.change_slimecoin(n = -fee, coinsource = ewcfg.coinsource_revival)

			user_data.persist()

			#delete weapon item
			ewitem.item_delete(id_item = weapon_item.id_item)

		await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

