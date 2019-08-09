#!/usr/bin/python3
#
# endless-war
# mperron (2018)
#
# a chat bot for the RFCK discord server

import discord
import asyncio
import random
import sys
import time
import json
import subprocess
import traceback
import re
import os
import shlex
import math

import ewutils
import ewcfg
import ewfarm
import ewcmd
import ewcasino
import ewfood
import ewwep
import ewjuviecmd
import ewmarket
import ewspooky
import ewkingpin
import ewplayer
import ewserver
import ewitem
import ewmap
import ewrolemgr
import ewraidboss
import ewleaderboard
import ewcosmeticitem
import ewslimeoid
import ewdistrict
import ewmutation
import ewquadrants
import ewtransport
import ewsmelting
import ewfish

from ewitem import EwItem
from ew import EwUser
from ewmarket import EwMarket
from ewmarket import EwStock
from ewdistrict import EwDistrict

ewutils.logMsg('Starting up...')

client = discord.Client()

# A map containing user IDs and the last time in UTC seconds since we sent them
# the help doc via DM. This is to prevent spamming.
last_helped_times = {}

# Map of server ID to a map of active users on that server.
active_users_map = {}


# Map of all command words in the game to their implementing function.
cmd_map = {
	# Attack another player
	ewcfg.cmd_kill: ewwep.attack,
	ewcfg.cmd_shoot: ewwep.attack,
	ewcfg.cmd_shoot_alt1: ewwep.attack,
	ewcfg.cmd_shoot_alt2: ewwep.attack,
	ewcfg.cmd_attack: ewwep.attack,

	# Get a weapon into your inventory
	ewcfg.cmd_arm: ewwep.arm,
	ewcfg.cmd_arsenalize: ewwep.arm,

	# Choose your weapon
	ewcfg.cmd_equip: ewwep.equip,

	# Kill yourself
	ewcfg.cmd_suicide: ewwep.suicide,
	ewcfg.cmd_suicide_alt1: ewwep.suicide,
	ewcfg.cmd_suicide_alt2: ewwep.suicide,

	# Spar with an ally
	ewcfg.cmd_spar: ewwep.spar,

	# Name your current weapon.
	ewcfg.cmd_annoint: ewwep.annoint,
	ewcfg.cmd_annoint_alt1: ewwep.annoint,

	#Marry and divorce your current wepaon.
	ewcfg.cmd_marry: ewwep.marry,
	ewcfg.cmd_divorce: ewwep.divorce,

	# move from juvenile to one of the armies (rowdys or killers)
	ewcfg.cmd_enlist: ewjuviecmd.enlist,
	ewcfg.cmd_renounce: ewjuviecmd.renounce,

	# gives slime to the miner (message.author)
	ewcfg.cmd_mine: ewjuviecmd.mine,

	# flags a vein as dangerous
	ewcfg.cmd_flag: ewjuviecmd.flag,

	# Show the current slime score of a player.
	ewcfg.cmd_score: ewcmd.score,
	ewcfg.cmd_score_alt1: ewcmd.score,

	# Show a player's combat data.
	ewcfg.cmd_data: ewcmd.data,

	#check what time it is, and the weather
	ewcfg.cmd_time: ewcmd.weather,
	ewcfg.cmd_clock: ewcmd.weather,
	ewcfg.cmd_weather: ewcmd.weather,


	# Rowdys thrash and Killers dab.
	ewcfg.cmd_thrash: ewcmd.thrash,
	ewcfg.cmd_dab: ewcmd.dab,

	# Show the total of negative slime in the world.
	ewcfg.cmd_negaslime: ewspooky.negaslime,

	# Display the progress towards the current Quarterly Goal.
	ewcfg.cmd_quarterlyreport: ewmarket.quarterlyreport,

	# revive yourself as a juvenile after having been killed.
	ewcfg.cmd_revive: ewspooky.revive,

	# Ghosts can haunt enlisted players to reduce their slime score.
	ewcfg.cmd_haunt: ewspooky.haunt,

	# how ghosts leave the sewers
	ewcfg.cmd_manifest: ewspooky.manifest,

	# Play slime pachinko!
	ewcfg.cmd_slimepachinko: ewcasino.pachinko,

	# Toss the dice at slime craps!
	ewcfg.cmd_slimecraps: ewcasino.craps,

	# Pull the lever on a slot machine!
	ewcfg.cmd_slimeslots: ewcasino.slots,

	# Play slime roulette!
	ewcfg.cmd_slimeroulette: ewcasino.roulette,

	# Play slime baccarat!
	ewcfg.cmd_slimebaccarat: ewcasino.baccarat,

        # Play slime skat!
        ewcfg.cmd_slimeskat: ewcasino.skat,
        ewcfg.cmd_slimeskat_join: ewcasino.skat_join,
        ewcfg.cmd_slimeskat_decline: ewcasino.skat_decline,
        ewcfg.cmd_slimeskat_bid: ewcasino.skat_bid,
        ewcfg.cmd_slimeskat_call: ewcasino.skat_call,
        ewcfg.cmd_slimeskat_pass: ewcasino.skat_pass,
        ewcfg.cmd_slimeskat_play: ewcasino.skat_play,
        ewcfg.cmd_slimeskat_hearts: ewcasino.skat_hearts,
        ewcfg.cmd_slimeskat_slugs: ewcasino.skat_slugs,
        ewcfg.cmd_slimeskat_hats: ewcasino.skat_hats,
        ewcfg.cmd_slimeskat_shields: ewcasino.skat_shields,
        ewcfg.cmd_slimeskat_grand: ewcasino.skat_grand,
        ewcfg.cmd_slimeskat_null: ewcasino.skat_null,
        ewcfg.cmd_slimeskat_take: ewcasino.skat_take,
        ewcfg.cmd_slimeskat_hand: ewcasino.skat_hand,
        ewcfg.cmd_slimeskat_choose: ewcasino.skat_choose,


	# Russian Roulette
	ewcfg.cmd_russian: ewcasino.russian_roulette,
	ewcfg.cmd_accept: ewcmd.accept,
	ewcfg.cmd_refuse: ewcmd.refuse,


	# See what's for sale in the Food Court.
	ewcfg.cmd_menu: ewfood.menu,
	ewcfg.cmd_menu_alt1: ewfood.menu,
	ewcfg.cmd_menu_alt2: ewfood.menu,

	# Order refreshing food and drinks!
	ewcfg.cmd_order: ewfood.order,
	ewcfg.cmd_buy: ewfood.order,

	# Transfer slime between players. Shares a cooldown with investments.
	ewcfg.cmd_transfer: ewmarket.xfer,
	ewcfg.cmd_transfer_alt1: ewmarket.xfer,

	# Show the player's slime coin.
	ewcfg.cmd_slimecoin: ewmarket.slimecoin,
	ewcfg.cmd_slimecoin_alt1: ewmarket.slimecoin,
	ewcfg.cmd_slimecoin_alt2: ewmarket.slimecoin,
	ewcfg.cmd_slimecoin_alt3: ewmarket.slimecoin,

	# Donate your slime to SlimeCorp in exchange for SlimeCoin.
	ewcfg.cmd_donate: ewmarket.donate,

	# Invest slimecoin into a stock
	ewcfg.cmd_invest: ewmarket.invest,

	# Withdraw slimecoin from your shares
	ewcfg.cmd_withdraw: ewmarket.withdraw,

	# show the exchange rate of a given stock
	ewcfg.cmd_exchangerate: ewmarket.rate,
	ewcfg.cmd_exchangerate_alt1: ewmarket.rate,
	ewcfg.cmd_exchangerate_alt2: ewmarket.rate,
	ewcfg.cmd_exchangerate_alt3: ewmarket.rate,
	ewcfg.cmd_exchangerate_alt4: ewmarket.rate,

	# show player's current shares in a compant
	ewcfg.cmd_shares: ewmarket.shares,

	# check available stocks
	ewcfg.cmd_stocks: ewmarket.stocks,

	# show player inventory
	ewcfg.cmd_inventory: ewitem.inventory_print,
	ewcfg.cmd_inventory_alt1: ewitem.inventory_print,
	ewcfg.cmd_inventory_alt2: ewitem.inventory_print,
	ewcfg.cmd_inventory_alt3: ewitem.inventory_print,

	# get an item's description
	ewcfg.cmd_inspect: ewitem.item_look,
	ewcfg.cmd_inspect_alt1: ewitem.item_look,

	# use an item
	ewcfg.cmd_use: ewitem.item_use,


	# Remove a megaslime (1 mil slime) from a general.
	ewcfg.cmd_deadmega: ewkingpin.deadmega,

	# Release a player from their faction.
	ewcfg.cmd_pardon: ewkingpin.pardon,
	ewcfg.cmd_banish: ewkingpin.banish,

	# Navigate the world map.
	ewcfg.cmd_move: ewmap.move,
	ewcfg.cmd_move_alt1: ewmap.move,
	ewcfg.cmd_move_alt2: ewmap.move,
	ewcfg.cmd_move_alt3: ewmap.move,

	# Cancel all moves in progress.
	ewcfg.cmd_halt: ewmap.halt,
	ewcfg.cmd_halt_alt1: ewmap.halt,

	# public transportation
	ewcfg.cmd_embark: ewtransport.embark,
	ewcfg.cmd_embark_alt1: ewtransport.embark,
	ewcfg.cmd_disembark: ewtransport.disembark,
	ewcfg.cmd_disembark_alt1: ewtransport.disembark,
	ewcfg.cmd_checkschedule: ewtransport.check_schedule,

	# Look around the POI you find yourself in.
	ewcfg.cmd_look: ewmap.look,

	# Look around an adjacent POI
	ewcfg.cmd_scout: ewmap.scout,
	ewcfg.cmd_scout_alt1: ewmap.scout,

	# Check your current POI capture progress
	ewcfg.cmd_capture_progress: ewdistrict.capture_progress,

	# link to the world map
	ewcfg.cmd_map: ewcmd.map,

	#farming
	ewcfg.cmd_sow: ewfarm.sow,
	ewcfg.cmd_reap: ewfarm.reap,
	ewcfg.cmd_mill: ewfarm.mill,

	# Fishing
	ewcfg.cmd_cast: ewfish.cast,
	ewcfg.cmd_reel: ewfish.reel,
	ewcfg.cmd_appraise: ewfish.appraise,
	ewcfg.cmd_appraise_alt1: ewfish.appraise,
	ewcfg.cmd_barter: ewfish.barter,

	# Bassed Pro Shop
	ewcfg.cmd_grill: ewfish.grill,
	ewcfg.cmd_enter: ewfish.enter_tourney,
	ewcfg.cmd_store: ewfish.store_fish,
	ewcfg.cmd_take: ewfish.take_fish,
	ewcfg.cmd_buyspace: ewfish.buy_tank_space,
	ewcfg.cmd_tourney: ewfish.tourney,
	ewcfg.cmd_tank: ewfish.tank,

	 #scavenging
	ewcfg.cmd_scavenge: ewjuviecmd.scavenge,

	#cosmetics
	ewcfg.cmd_adorn: ewcosmeticitem.adorn,
	ewcfg.cmd_create: ewkingpin.create,
	ewcfg.cmd_dyecosmetic: ewcosmeticitem.dye,
	ewcfg.cmd_dyecosmetic_alt1: ewcosmeticitem.dye,
	ewcfg.cmd_dyecosmetic_alt2: ewcosmeticitem.dye,
	ewcfg.cmd_dyecosmetic_alt3: ewcosmeticitem.dye,

	#smelting
	ewcfg.cmd_smelt: ewsmelting.smelt,

	#give an item to another player
	ewcfg.cmd_give: ewitem.give,

	# drop item into your current district
	ewcfg.cmd_discard: ewitem.discard,
	ewcfg.cmd_discard_alt1: ewitem.discard,

	# kill all players in your district; could be re-used for a future raid boss
	#ewcfg.cmd_writhe: ewraidboss.writhe,

	# Link to the guide.
	ewcfg.cmd_help: ewcmd.help,
	ewcfg.cmd_help_alt1: ewcmd.help,
	ewcfg.cmd_help_alt2: ewcmd.help,
	ewcfg.cmd_help_alt3: ewcmd.help,

	# Misc
	ewcfg.cmd_howl: ewcmd.cmd_howl,
	ewcfg.cmd_howl_alt1: ewcmd.cmd_howl,
	ewcfg.cmd_harvest: ewcmd.harvest,
	ewcfg.cmd_salute: ewcmd.salute,
	ewcfg.cmd_unsalute: ewcmd.unsalute,
	ewcfg.cmd_hurl: ewcmd.hurl,
	ewcfg.cmd_news: ewcmd.patchnotes,
	ewcfg.cmd_patchnotes: ewcmd.patchnotes,
	ewcfg.cmd_wiki: ewcmd.wiki,
	ewcfg.cmd_booru: ewcmd.booru,
	ewcfg.cmd_leaderboard: ewcmd.leaderboard,
	ewcfg.cmd_leaderboard_alt1: ewcmd.leaderboard,


	# Slimeoids

	ewcfg.cmd_incubateslimeoid: ewslimeoid.incubateslimeoid,
	ewcfg.cmd_growbody: ewslimeoid.growbody,
	ewcfg.cmd_growhead: ewslimeoid.growhead,
	ewcfg.cmd_growlegs: ewslimeoid.growlegs,
	ewcfg.cmd_growweapon: ewslimeoid.growweapon,
	ewcfg.cmd_growarmor: ewslimeoid.growarmor,
	ewcfg.cmd_growspecial: ewslimeoid.growspecial,
	ewcfg.cmd_growbrain: ewslimeoid.growbrain,
	ewcfg.cmd_nameslimeoid: ewslimeoid.nameslimeoid,
	ewcfg.cmd_raisemoxie: ewslimeoid.raisemoxie,
	ewcfg.cmd_lowermoxie: ewslimeoid.lowermoxie,
	ewcfg.cmd_raisegrit: ewslimeoid.raisegrit,
	ewcfg.cmd_lowergrit: ewslimeoid.lowergrit,
	ewcfg.cmd_raisechutzpah: ewslimeoid.raisechutzpah,
	ewcfg.cmd_lowerchutzpah: ewslimeoid.lowerchutzpah,
	ewcfg.cmd_spawnslimeoid: ewslimeoid.spawnslimeoid,
	ewcfg.cmd_dissolveslimeoid: ewslimeoid.dissolveslimeoid,
	ewcfg.cmd_slimeoid: ewslimeoid.slimeoid,
	ewcfg.cmd_instructions: ewslimeoid.instructions,
	ewcfg.cmd_playfetch: ewslimeoid.playfetch,
	ewcfg.cmd_petslimeoid: ewslimeoid.petslimeoid,
	ewcfg.cmd_walkslimeoid: ewslimeoid.walkslimeoid,
	ewcfg.cmd_observeslimeoid: ewslimeoid.observeslimeoid,
	ewcfg.cmd_slimeoidbattle: ewslimeoid.slimeoidbattle,
	ewcfg.cmd_saturateslimeoid: ewslimeoid.saturateslimeoid,
	ewcfg.cmd_restoreslimeoid: ewslimeoid.restoreslimeoid,
	ewcfg.cmd_dress_slimeoid: ewslimeoid.dress_slimeoid,
	ewcfg.cmd_dress_slimeoid_alt1: ewslimeoid.dress_slimeoid,

	# Negaslimeoids

	ewcfg.cmd_negaslimeoid: ewslimeoid.negaslimeoid,
	ewcfg.cmd_summonnegaslimeoid: ewspooky.summon_negaslimeoid,
	ewcfg.cmd_summonnegaslimeoid_alt1: ewspooky.summon_negaslimeoid,
	ewcfg.cmd_summonnegaslimeoid_alt2: ewspooky.summon_negaslimeoid,
	ewcfg.cmd_battlenegaslimeoid: ewslimeoid.negaslimeoidbattle,
	ewcfg.cmd_battlenegaslimeoid_alt1: ewslimeoid.negaslimeoidbattle,

	# troll romance
	ewcfg.cmd_add_quadrant: ewquadrants.add_quadrant,
	ewcfg.cmd_get_quadrants: ewquadrants.get_quadrants,
	ewcfg.cmd_get_flushed: ewquadrants.get_flushed,
	ewcfg.cmd_get_flushed_alt1: ewquadrants.get_flushed,
	ewcfg.cmd_get_pale: ewquadrants.get_pale,
	ewcfg.cmd_get_pale_alt1: ewquadrants.get_pale,
	ewcfg.cmd_get_caliginous: ewquadrants.get_caliginous,
	ewcfg.cmd_get_caliginous_alt1: ewquadrants.get_caliginous,
	ewcfg.cmd_get_ashen: ewquadrants.get_ashen,
	ewcfg.cmd_get_ashen_alt1: ewquadrants.get_ashen,

        # mutations
        ewcfg.cmd_reroll_mutation: ewmutation.reroll_last_mutation,
        ewcfg.cmd_clear_mutations: ewmutation.clear_mutations,

	ewcfg.cmd_teleport: ewmap.teleport,
	# restores poi roles to their proper names, only usable by admins
	ewcfg.cmd_restoreroles: ewrolemgr.restoreRoleNames,

	# ban a player from using commands
	ewcfg.cmd_arrest: ewcmd.arrest,
}

debug = True
while sys.argv:
	if sys.argv[0].lower() == '--debug':
		debug = True

	sys.argv = sys.argv[1:]

# When debug is enabled, additional commands are turned on.
if debug == True:
	ewutils.logMsg('Debug mode enabled.')

@client.event
async def on_member_remove(member):
	# Kill players who leave the server.
	try:
		user_data = EwUser(member = member)
		user_data.die(cause = ewcfg.cause_leftserver)
		user_data.persist()

		ewutils.logMsg('Player killed for leaving the server.')
	except:
		ewutils.logMsg('Failed to kill member who left the server.')

@client.event
async def on_member_update(before, after):
	# update last offline time if they went from offline to online
	try:
		if before.status == discord.Status.offline and after.status != discord.Status.offline:

			user_data = EwUser(member = after)
			user_data.time_lastoffline = int(time.time())
			user_data.persist()
	except:
		ewutils.logMsg('Failed to update member\'s last offline time.')

@client.event
async def on_ready():
	ewcfg.set_client(client)
	ewutils.logMsg('Logged in as {} ({}).'.format(client.user.name, client.user.id))

	ewutils.logMsg("Loaded NLACakaNM world map. ({}x{})".format(ewmap.map_width, ewmap.map_height))
	ewmap.map_draw()

	# Flatten role names to all lowercase, no spaces.
	fake_observer = EwUser()
	fake_observer.life_state = ewcfg.life_state_observer
	for poi in ewcfg.poi_list:
		if poi.role != None:
			poi.role = ewutils.mapRoleName(poi.role)

		neighbors = []
		neighbor_ids = []
		if poi.coord != None:
			neighbors = ewmap.path_to(coord_start = poi.coord, user_data = fake_observer)
		#elif poi.id_poi == ewcfg.poi_id_thesewers:
		#	neighbors = ewcfg.poi_list

		if neighbors != None:
			for neighbor in neighbors:
				neighbor_ids.append(neighbor.id_poi)

		ewcfg.poi_neighbors[poi.id_poi] = set(neighbor_ids)
		ewutils.logMsg("Found neighbors for poi {}: {}".format(poi.id_poi, ewcfg.poi_neighbors[poi.id_poi]))


	for id_poi in ewcfg.landmark_pois:
		ewutils.logMsg("beginning landmark precomputation for " + id_poi)
		poi = ewcfg.id_to_poi.get(id_poi)
		ewmap.landmarks[id_poi] = ewmap.score_map_from(
			coord_start = poi.coord,
			user_data = fake_observer
		)

	ewutils.logMsg("finished landmark precomputation")

	try:
		await client.change_presence(game = discord.Game(name = "EW " + ewcfg.version))
	except:
		ewutils.logMsg("Failed to change_presence!")

	# Look for a Twitch client_id on disk.
	# FIXME debug - temporarily disable Twitch integration
	if False:
		twitch_client_id = ewutils.getTwitchClientId()

	# If no twitch client ID is available, twitch integration will be disabled.
	# FIXME debug - temporarily disable Twitch integration.
	if True:
		twitch_client_id = None
		ewutils.logMsg('Twitch integration disabled.')
	elif twitch_client_id == None or len(twitch_client_id) == 0:
		ewutils.logMsg('No twitch_client_id file found. Twitch integration disabled.')
	else:
		ewutils.logMsg("Enabled Twitch integration.")

	# Channels in the connected discord servers to announce to.
	channels_announcement = []

	# Channels in the connected discord servers to send stock market updates to. Map of server ID to channel.
	channels_stockmarket = {}

	for server in client.servers:
		# Update server data in the database
		ewserver.server_update(server = server)

		# Determine if a Fishing Tourney is active
		ewfish.tourney = ewfish.get_tourney(server = server)

		# store the list of channels in an ewutils field
		ewcfg.update_server_list(server = server)

		# find roles and add them to the database
		ewrolemgr.setupRoles(client = client, id_server = server.id)

		# hides the names of poi roles
		await ewrolemgr.hideRoleNames(client = client, id_server = server.id)

		# Grep around for channels
		ewutils.logMsg("connected to server: {}".format(server.name))
		for channel in server.channels:
			if(channel.type == discord.ChannelType.text):
				if(channel.name == ewcfg.channel_twitch_announcement):
					channels_announcement.append(channel)
					ewutils.logMsg("• found channel for announcements: {}".format(channel.name))

				elif(channel.name == ewcfg.channel_stockexchange):
					channels_stockmarket[server.id] = channel
					ewutils.logMsg("• found channel for stock exchange: {}".format(channel.name))

		# create all the districts in the database
		for poi_object in ewcfg.poi_list:
			poi = poi_object.id_poi
			# call the constructor to create an entry if it doesnt exist yet
			dist = EwDistrict(id_server = server.id, district = poi)
			# change the ownership to the faction that's already in control to initialize topic names
			try:
				# initialize gang bases
				if poi == ewcfg.poi_id_rowdyroughhouse:
					dist.controlling_faction = ewcfg.faction_rowdys
				elif poi == ewcfg.poi_id_copkilltown:
					dist.controlling_faction = ewcfg.faction_killers

				resp_cont = dist.change_ownership(new_owner = dist.controlling_faction, actor = "init", client = client)
				dist.persist()
				await resp_cont.post()

			except:
				ewutils.logMsg('Could not change ownership for {} to "{}".'.format(poi, dist.controlling_faction))

		asyncio.ensure_future(ewdistrict.capture_tick_loop(id_server = server.id))
		asyncio.ensure_future(ewutils.bleed_tick_loop(id_server = server.id))
		if not debug:
			await ewtransport.init_transports(id_server = server.id)
		asyncio.ensure_future(ewslimeoid.slimeoid_tick_loop(id_server = server.id))

	try:
		ewutils.logMsg('Creating message queue directory.')
		os.mkdir(ewcfg.dir_msgqueue)
	except FileExistsError:
		ewutils.logMsg('Message queue directory already exists.')

	ewutils.logMsg('Ready.')

	"""
		Set up for infinite loop to perform periodic tasks.
	"""
	time_now = int(time.time())

	time_last_twitch = time_now
	time_twitch_downed = 0

	# Every three hours we log a message saying the periodic task hook is still active. On startup, we want this to happen within about 60 seconds, and then on the normal 3 hour interval.
	time_last_logged = time_now - ewcfg.update_hookstillactive + 60

	stream_live = None

	ewutils.logMsg('Beginning periodic hook loop.')
	while not ewutils.TERMINATE:
		time_now = int(time.time())

		# Periodic message to log that this stuff is still running.
		if (time_now - time_last_logged) >= ewcfg.update_hookstillactive:
			time_last_logged = time_now

			ewutils.logMsg("Periodic hook still active.")

		# Check to see if a stream is live via the Twitch API.
		# FIXME disabled
		if False:
		#if twitch_client_id != None and (time_now - time_last_twitch) >= ewcfg.update_twitch:
			time_last_twitch = time_now

			try:
				# Twitch API call to see if there are any active streams.
				json_string = ""
				p = subprocess.Popen(
					"curl -H 'Client-ID: {}' -X GET 'https://api.twitch.tv/helix/streams?user_login = rowdyfrickerscopkillers' 2>/dev/null".format(twitch_client_id),
					shell = True,
					stdout = subprocess.PIPE
				)

				for line in p.stdout.readlines():
					json_string += line.decode('utf-8')

				json_parsed = json.loads(json_string)

				# When a stream is up, data is an array of stream information objects.
				data = json_parsed.get('data')
				if data != None:
					data_count = len(data)
					stream_was_live = stream_live
					stream_live = True if data_count > 0 else False

					if stream_was_live == True and stream_live == False:
						time_twitch_downed = time_now

					if stream_was_live == False and stream_live == True and (time_now - time_twitch_downed) > 600:
						ewutils.logMsg("The stream is now live.")

						# The stream has transitioned from offline to online. Make an announcement!
						for channel in channels_announcement:
							await ewutils.send_message(
								client,
								channel,
								"ATTENTION CITIZENS. THE **ROWDY FUCKER** AND THE **COP KILLER** ARE **STREAMING**. BEWARE OF INCREASED KILLER AND ROWDY ACTIVITY.\n\n@everyone\n{}".format(
									"https://www.twitch.tv/rowdyfrickerscopkillers"
								)
							)
			except:
				ewutils.logMsg('Twitch handler hit an exception (continuing): {}'.format(json_string))
				traceback.print_exc(file = sys.stdout)

		# Adjust the exchange rate of slime for the market.
		try:
			for server in client.servers:
				# Load market data from the database.
				market_data = EwMarket(id_server = server.id)

				if market_data.time_lasttick + ewcfg.update_market <= time_now:

					market_response = ""

					for stock in ewcfg.stocks:
						s = EwStock(server.id, stock)
						# we don't update stocks when they were just added
						if s.timestamp != 0:
							s.timestamp = time_now
							market_response = ewmarket.market_tick(s, server.id)
							await ewutils.send_message(client, channels_stockmarket.get(server.id), market_response)

					market_data = EwMarket(id_server = server.id)
					market_data.time_lasttick = time_now

					# Advance the time and potentially change weather.
					market_data.clock += 1

					# Determine if a Fishing Tourney is active
					ewfish.tourney = ewfish.get_tourney(server=server)

					if market_data.clock >= 24 or market_data.clock < 0:
						market_data.clock = 0
						market_data.day += 1

					if market_data.clock == 6:
						# Update the list of available bazaar items by clearing the current list and adding the new items
						market_data.bazaar_wares.clear()

						bazaar_foods = []
						bazaar_cosmetics = []
						bazaar_general_items = []

						for item in ewcfg.vendor_inv.get(ewcfg.vendor_bazaar):
							if item in ewcfg.item_names:
								bazaar_general_items.append(item)

							elif item in ewcfg.food_names:
								bazaar_foods.append(item)

							elif item in ewcfg.cosmetic_names:
								bazaar_cosmetics.append(item)

						market_data.bazaar_wares['generalitem'] = random.choice(bazaar_general_items)

						market_data.bazaar_wares['food1'] = random.choice(bazaar_foods)
						# Don't add repeated foods
						while market_data.bazaar_wares.get('food2') is None or market_data.bazaar_wares.get('food2') == market_data.bazaar_wares['food1']:
							market_data.bazaar_wares['food2'] = random.choice(bazaar_foods)

						market_data.bazaar_wares['cosmetic1'] = random.choice(bazaar_cosmetics)
						# Don't add repeated cosmetics
						while market_data.bazaar_wares.get('cosmetic2') is None or market_data.bazaar_wares.get('cosmetic2') == market_data.bazaar_wares['cosmetic1']:
							market_data.bazaar_wares['cosmetic2'] = random.choice(bazaar_cosmetics)
						while market_data.bazaar_wares.get('cosmetic3') is None or market_data.bazaar_wares.get('cosmetic3') == market_data.bazaar_wares['cosmetic1'] or market_data.bazaar_wares.get('cosmetic3') == market_data.bazaar_wares['cosmetic2']:
							market_data.bazaar_wares['cosmetic3'] = random.choice(bazaar_cosmetics)

					market_data.persist()

					if market_data.clock == 6:
						response = ' The SlimeCorp Stock Exchange is now open for business.'
						await ewutils.send_message(client, channels_stockmarket.get(server.id), response)
					elif market_data.clock == 20:
						response = ' The SlimeCorp Stock Exchange has closed for the night.'
						await ewutils.send_message(client, channels_stockmarket.get(server.id), response)

					market_data = EwMarket(id_server = server.id)

					if random.randrange(30) == 0:
						pattern_count = len(ewcfg.weather_list)

						if pattern_count > 1:
							weather_old = market_data.weather

							# Randomly select a new weather pattern. Try again if we get the same one we currently have.
							while market_data.weather == weather_old:
								pick = random.randrange(len(ewcfg.weather_list))
								market_data.weather = ewcfg.weather_list[pick].name

						# Log message for statistics tracking.
						ewutils.logMsg("The weather changed. It's now {}.".format(market_data.weather))

					# Persist new data.
					market_data.persist()

					# Decay slime totals
					ewutils.decaySlimes(id_server = server.id)

					# Increase hunger for all players below the max.
					ewutils.pushupServerHunger(id_server = server.id)

					# Decrease inebriation for all players above min (0).
					ewutils.pushdownServerInebriation(id_server = server.id)

					# Remove fish offers which have timed out
					ewfish.kill_dead_offers(id_server = server.id)

					await ewdistrict.give_kingpins_slime_and_decay_capture_points(id_server = server.id)

					await ewmap.kick(server.id)

					# Post leaderboards at 6am NLACakaNM time.
					if market_data.clock == 6:
						await ewleaderboard.post_leaderboards(client = client, server = server)

		except:
			ewutils.logMsg('An error occurred in the scheduled slime market update task:')
			traceback.print_exc(file = sys.stdout)

		# Parse files dumped into the msgqueue directory and send messages as needed.
		try:
			for msg_file in os.listdir(ewcfg.dir_msgqueue):
				fname = "{}/{}".format(ewcfg.dir_msgqueue, msg_file)

				msg = ewutils.readMessage(fname)
				os.remove(fname)

				msg_channel_names = []
				msg_channel_names_reverb = []

				if msg.channel != None:
					msg_channel_names.append(msg.channel)

				if msg.poi != None:
					poi = ewcfg.id_to_poi.get(msg.poi)
					if poi != None:
						if poi.channel != None and len(poi.channel) > 0:
							msg_channel_names.append(poi.channel)

						if msg.reverb == True:
							pois_adjacent = ewmap.path_to(poi_start = msg.poi)

							for poi_adjacent in pois_adjacent:
								if poi_adjacent.channel != None and len(poi_adjacent.channel) > 0:
									msg_channel_names_reverb.append(poi_adjacent.channel)

				if len(msg_channel_names) == 0:
					ewutils.logMsg('in file {} message for channel {} (reverb {})\n{}'.format(msg_file, msg.channel, msg.reverb, msg.message))
				else:
					# Send messages to every connected server.
					for server in client.servers:
						for channel in server.channels:
							if channel.name in msg_channel_names:
								await ewutils.send_message(client, channel, "**{}**".format(msg.message))
							elif channel.name in msg_channel_names_reverb:
								await ewutils.send_message(client, channel, "**Something is happening nearby...\n\n{}**".format(msg.message))
		except:
			ewutils.logMsg('An error occurred while trying to process the message queue:')
			traceback.print_exc(file = sys.stdout)

		# Wait a while before running periodic tasks.
		await asyncio.sleep(15)

@client.event
async def on_member_join(member):
	ewutils.logMsg("New member \"{}\" joined. Configuring default roles now.".format(member.display_name))
	await ewrolemgr.updateRoles(client = client, member = member)
	ewplayer.player_update(
		member = member,
		server = member.server
	)

@client.event
async def on_message_delete(message):
	if message != None and message.server != None and message.author.id != client.user.id and message.content.startswith(ewcfg.cmd_prefix):
		ewutils.logMsg("deleted message from {}: {}".format(message.author.display_name, message.content))
		await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, '**I SAW THAT.**'));

@client.event
async def on_message(message):
	time_now = int(time.time())
	ewcfg.set_client(client)

	""" do not interact with our own messages """
	if message.author.id == client.user.id or message.author.bot == True:
		return

	if message.server != None:
		# Note that the user posted a message.
		active_map = active_users_map.get(message.server.id)
		if active_map == None:
			active_map = {}
			active_users_map[message.server.id] = active_map
		active_map[message.author.id] = True

		# Update player information.
		ewplayer.player_update(
			member = message.author,
			server = message.server
		)

	content_tolower = message.content.lower()
	re_awoo = re.compile('.*![a]+[w]+o[o]+.*')

	# update the player's time_last_action which is used for kicking AFK players out of subzones
	if message.server != None:
		try:
			ewutils.execute_sql_query("UPDATE users SET {time_last_action} = %s WHERE id_user = %s AND id_server = %s".format(
				time_last_action = ewcfg.col_time_last_action
			), (
				int(time.time()),
				message.author.id,
				message.server.id
			))
		except:
			ewutils.logMsg('server {}: failed to update time_last_action for {}'.format(message.server.id, message.author.id))

	if message.content.startswith(ewcfg.cmd_prefix) or message.server == None or len(message.author.roles) < 2:
		"""
			Wake up if we need to respond to messages. Could be:
				message starts with !
				direct message (server == None)
				user is new/has no roles (len(roles) < 2)
		"""

		#Ignore users with weird characters in their name
		try:
			message.author.display_name[:3].encode('utf-8').decode('ascii')
		except UnicodeError:
			return await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, "We don't take kindly to moon runes around here."))

		# tokenize the message. the command should be the first word.
		try:
			tokens = shlex.split(message.content)  # it's split with shlex now because shlex regards text within quotes as a single token
		except:
			tokens = message.content.split(' ')  # if splitting via shlex doesnt work (odd number of quotes), use the old splitting method so it doesnt give an exception

		tokens_count = len(tokens)
		cmd = tokens[0].lower() if tokens_count >= 1 else ""

		# remove mentions to us
		mentions = list(filter(lambda user : user.id != client.user.id, message.mentions))
		mentions_count = len(mentions)

		# Create command object
		cmd_obj = ewcmd.EwCmd(
			tokens = tokens,
			message = message,
			client = client,
			mentions = mentions
		)

		"""
			Handle direct messages.
		"""
		if message.server == None:
			# Direct message the player their inventory.
			if ewitem.cmd_is_inventory(cmd):
				return await ewitem.inventory_print(cmd_obj)
			elif cmd == ewcfg.cmd_inspect:
				return await ewitem.item_look(cmd_obj)

			else:
				time_last = last_helped_times.get(message.author.id, 0)

				# Only send the help doc once every thirty seconds. There's no need to spam it.
				if (time_now - time_last) > 30:
					last_helped_times[message.author.id] = time_now
					await ewutils.send_message(client, message.channel, 'Check out the guide for help: https://ew.krakissi.net/guide/')

			# Nothing else to do in a DM.
			return

		# assign the appropriate roles to a user with less than @everyone, faction, location
		if len(message.author.roles) < 3:
			await ewrolemgr.updateRoles(client = client, member = message.author)

		user_data = EwUser(member = message.author)
		if user_data.arrested:
			return

		mutations = user_data.get_mutations()
		# Scold/ignore offline players.
		if message.author.status == discord.Status.offline:

			if ewcfg.mutation_id_chameleonskin not in mutations or cmd not in ewcfg.offline_cmds:

				response = "You cannot participate in the ENDLESS WAR while offline."

				return await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, response))


		if user_data.time_lastoffline > time_now - ewcfg.time_offline:

			if ewcfg.mutation_id_chameleonskin not in mutations or cmd not in ewcfg.offline_cmds:
				response = "You are too paralyzed by ENDLESS WAR's judgemental stare to act."

				return await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, response))


		# Check the main command map for the requested command.
		global cmd_map
		cmd_fn = cmd_map.get(cmd)

		if cmd_fn != None:
			# Execute found command
			return await cmd_fn(cmd_obj)

		# FIXME debug
		# Test item creation
		elif debug == True and cmd == '!createtestitem':
			item_id = ewitem.item_create(
				item_type = 'medal',
				id_user = message.author.id,
				id_server = message.server.id,
				item_props = {
					'medal_name': 'Test Award',
					'medal_desc': '**{medal_name}**: *Awarded to Krak by Krak for testing shit.*'
				}
			)

			ewutils.logMsg('Created item: {}'.format(item_id))
			item = EwItem(id_item = item_id)
			item.item_props['test'] = 'meow'
			item.persist()

			item = EwItem(id_item = item_id)

			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, ewitem.item_look(item)))

		# Creates a poudrin
		elif debug == True and cmd == '!createpoudrin':
			for item in ewcfg.item_list:
				if item.context == "poudrin":
					ewitem.item_create(
						item_type = ewcfg.it_item,
						id_user = message.author.id,
						id_server = message.server.id,
						item_props = {
							'id_item': item.id_item,
							'context': item.context,
							'item_name': item.str_name,
							'item_desc': item.str_desc,
						}
					),
					ewutils.logMsg('Created item: {}'.format(item.id_item))
					item = EwItem(id_item = item.id_item)
					item.persist()
			else:
				pass

			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, "Poudrin created."))

		# Gives the user some slime
		elif debug == True and cmd == '!getslime':
			user_data = EwUser(member = message.author)
			user_initial_level = user_data.slimelevel

			response = "You get 10,000 slime!"

			levelup_response = user_data.change_slimes(n = 10000)

			was_levelup = True if user_initial_level < user_data.slimelevel else False

			if was_levelup:
				response += " {}".format(levelup_response)

			user_data.persist()

			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, response))

		# Deletes all items in your inventory.
		elif debug == True and cmd == '!clearinv':
			user_data = EwUser(member = message.author)
			ewitem.item_destroyall(id_server = message.server.id, id_user = message.author.id)
			response = "You destroy every single item in your inventory."
			user_data.persist()
			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, response))

		elif debug == True and cmd == '!createapple':
			item_id = ewitem.item_create(
				id_user = message.author.id,
				id_server = message.server.id,
				item_type = ewcfg.it_food,
				item_props = {
					'id_food': "direapples",
					'food_name': "Dire Apples",
					'food_desc': "This sure is a illegal Dire Apple!",
					'recover_hunger': 500,
					'str_eat': "You chomp into this illegal Dire Apple.",
					'time_expir': time.time() + ewcfg.farm_food_expir
				}
			)

			ewutils.logMsg('Created item: {}'.format(item_id))
			item = EwItem(id_item = item_id)
			item.item_props['test'] = 'meow'
			item.persist()

			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, "Apple created."))

		# FIXME debug
		# Test item deletion
		elif debug == True and cmd == '!delete':
			items = ewitem.inventory(
				id_user = message.author.id,
				id_server = message.server.id
			)

			for item in items:
				ewitem.item_delete(
					id_item = item.get('id_item')
				)

			await ewutils.send_message(client, message.channel, ewutils.formatMessage(message.author, 'ok'))

		# AWOOOOO
		elif re_awoo.match(cmd):
			return await ewcmd.cmd_howl(cmd_obj)

		# Debug command to override the role of a user
		elif debug == True and cmd == (ewcfg.cmd_prefix + 'setrole'):

			response = ""

			if mentions_count == 0:
				response = 'Set who\'s role?'
			else:
				roles_map = ewutils.getRoleMap(message.server.roles)
				role_target = tokens[1]
				role = roles_map.get(role_target)

				if role != None:
					for user in mentions:
						try:
							await client.replace_roles(user, role)
						except:
							ewutils.logMsg('Failed to replace_roles for user {} with {}.'.format(user.display_name, role.name))

					response = 'Done.'
				else:
					response = 'Unrecognized role.'

			await ewutils.send_message(client, cmd.message.channel, ewutils.formatMessage(message.author, response))

		# didn't match any of the command words.
		else:
			""" couldn't process the command. bail out!! """
			""" bot rule 0: be cute """
			randint = random.randint(1,3)
			msg_mistake = "ENDLESS WAR is growing frustrated."
			if randint == 2:
				msg_mistake = "ENDLESS WAR denies you his favor."
			elif randint == 3:
				msg_mistake = "ENDLESS WAR pays you no mind."

			msg = await ewutils.send_message(client, cmd_obj.message.channel, msg_mistake)
			await asyncio.sleep(2)
			try:
				await client.delete_message(msg)
			except:
				pass

	elif content_tolower.find(ewcfg.cmd_howl) >= 0 or content_tolower.find(ewcfg.cmd_howl_alt1) >= 0 or re_awoo.match(content_tolower):
		""" Howl if !howl is in the message at all. """
		return await ewcmd.cmd_howl(ewcmd.EwCmd(
			message = message,
			client = client
		))


# find our REST API token
token = ewutils.getToken()

if token == None or len(token) == 0:
	ewutils.logMsg('Please place your API token in a file called "token", in the same directory as this script.')
	sys.exit(0)

# connect to discord and run indefinitely
try:
	client.run(token)
finally:
	ewutils.TERMINATE = True
	ewutils.logMsg("main thread terminated.")
