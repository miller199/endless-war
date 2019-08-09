import math

import ewcfg
import ewfish
import ewutils
from ewmarket import EwMarket


async def post_leaderboards(client = None, server = None):
	leaderboard_channel = ewutils.get_channel(server = server, channel_name = ewcfg.channel_leaderboard)

	market = EwMarket(id_server = server.id)
	time = "day {}".format(market.day) 

	await ewutils.send_message(client, leaderboard_channel, "▓▓{} **STATE OF THE CITY:** {} {}▓▓".format(ewcfg.emote_theeye, time, ewcfg.emote_theeye))

	kingpins = make_kingpin_board(server = server, title = ewcfg.leaderboard_kingpins)
	await ewutils.send_message(client, leaderboard_channel, kingpins)
	districts = make_district_control_board(id_server = server.id, title = ewcfg.leaderboard_districts)
	await ewutils.send_message(client, leaderboard_channel, districts)
	topslimes = make_userdata_board(server = server, category = ewcfg.col_slimes, title = ewcfg.leaderboard_slimes)
	await ewutils.send_message(client, leaderboard_channel, topslimes)
	topcoins = make_userdata_board(server = server, category = ewcfg.col_slimecoin, title = ewcfg.leaderboard_slimecoin)
	await ewutils.send_message(client, leaderboard_channel, topcoins)
	topghosts = make_userdata_board(server = server, category = ewcfg.col_slimes, title = ewcfg.leaderboard_ghosts, lowscores = True, rows = 3)
	await ewutils.send_message(client, leaderboard_channel, topghosts)
	topbounty = make_userdata_board(server = server, category = ewcfg.col_bounty, title = ewcfg.leaderboard_bounty, divide_by = ewcfg.slimecoin_exchangerate)
	await ewutils.send_message(client, leaderboard_channel, topbounty)
	topdonated = make_userdata_board(server = server, category = ewcfg.col_poudrin_donations, title = ewcfg.leaderboard_donated)
	await ewutils.send_message(client, leaderboard_channel, topdonated)
	topslimeoids = make_slimeoids_top_board(server = server)
	await ewutils.send_message(client, leaderboard_channel, topslimeoids)
	if ewfish.tourney:
		tourneyresults = make_fishing_top_board(server = server)
		await ewutils.send_message(client, leaderboard_channel, tourneyresults)
		tourney_int = market.day % 28
		if tourney_int == 0:
			tourney_info = "THE WEEKLY FISHING TOURNEY HAS BEGUN!"
		elif tourney_int == 27:
			tourney_info = "THE WEEKLY FISHING TOURNEY BEGINS SOON."
		elif tourney_int == 7:
			tourney_info = "THE WEEKLY FISHING TOURNEY HAS CONCLUDED.\nIF YOU WERE IN THE TOP 3 SPOTS, GO TO THE BASSED PRO SHOP TO **!CLAIM** YOUR PRIZE."
			ewfish.get_tourney_winners(server = server)
		await ewutils.send_message(client, leaderboard_channel, tourney_info)

def make_fishing_top_board(server = None):
	board = "🎣 ▓▓▓▓▓ TOP TOURNEY ENTRIES ▓▓▓▓▓ 🎣\n"

	try:
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		cursor.execute((
			"SELECT pl.display_name, el.id_fish, el.float_size " +
			"FROM tourney_entries AS el " +
			"LEFT JOIN players AS pl ON el.id_user = pl.id_user " +
			"WHERE el.id_server = %s " +
			"ORDER BY el.float_size DESC LIMIT 5"
		), (
			server.id,
		))

		data = cursor.fetchall()
		if data != None:
			for row in data:
				board += "{} `{:_>3} | {}'s {}`\n".format(
					ewcfg.emote_blank,
					row[2],
					row[0].replace("`", ""),
					row[1].replace("`", "")
				)

	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)

	return board

def make_slimeoids_top_board(server = None):
	board = "{mega} ▓▓▓▓▓ TOP SLIMEOIDS (CLOUT) ▓▓▓▓▓ {mega}\n".format(
		mega = "<:megaslime:436877747240042508>"
	)

	try:
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		cursor.execute((
			"SELECT pl.display_name, sl.name, sl.clout " +
			"FROM slimeoids AS sl " +
			"LEFT JOIN players AS pl ON sl.id_user = pl.id_user " +
			"WHERE sl.id_server = %s AND sl.life_state = 2 " +
			"ORDER BY sl.clout DESC LIMIT 3"
		), (
			server.id,
		))

		data = cursor.fetchall()
		if data != None:
			for row in data:
				board += "{} `{:_>3} | {}'s {}`\n".format(
					ewcfg.emote_blank,
					row[2],
					row[0].replace("`",""),
					row[1].replace("`","")
				)
	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)

	return board


def make_userdata_board(server = None, category = "", title = "", lowscores = False, rows = 5, divide_by = 1):
	entries = []
	try:
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		cursor.execute("SELECT {name}, {state}, {faction}, {category} FROM users, players WHERE users.id_server = %s AND users.{id_user} = players.{id_user} ORDER BY {category} {order} LIMIT {limit}".format(
			name = ewcfg.col_display_name,
			state = ewcfg.col_life_state,
			faction = ewcfg.col_faction,
			category = category,
			id_user = ewcfg.col_id_user,
			order = ('DESC' if lowscores == False else 'ASC'),
			limit = rows
		), (
			server.id, 
		))

		i = 0
		row = cursor.fetchone()
		while (row != None) and (i < rows):
			if row[1] == ewcfg.life_state_kingpin or row[1] == ewcfg.life_state_grandfoe or row[1] == ewcfg.life_state_lucky:
				row = cursor.fetchone()
			else:
				entries.append(row)
				row = cursor.fetchone()
				i += 1

	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)

	return format_board(entries = entries, title = title, divide_by = divide_by)

def make_kingpin_board(server = None, title = ""):
	entries = []
	try:
		conn_info = ewutils.databaseConnect()
		conn = conn_info.get('conn')
		cursor = conn.cursor()

		cursor.execute("SELECT {name}, {state}, {faction}, {category} FROM users, players WHERE users.id_server = %s AND {state} = %s AND users.{id_user} = players.{id_user} ORDER BY {category} DESC".format(
			name = ewcfg.col_display_name,
			state = ewcfg.col_life_state,
			faction = ewcfg.col_faction,
			category = ewcfg.col_slimes,
			id_user = ewcfg.col_id_user
		), (
			server.id, 
			ewcfg.life_state_kingpin
		))

		rows = cursor.fetchall()
		for row in rows:
			entries.append(row)

	finally:
		# Clean up the database handles.
		cursor.close()
		ewutils.databaseClose(conn_info)

	return format_board(entries = entries, title = title)


def make_district_control_board(id_server, title):
	entries = []
	districts = ewutils.execute_sql_query(
		"SELECT {district}, {controlling_faction} FROM districts WHERE id_server = %s".format(
			district = ewcfg.col_district,
			controlling_faction = ewcfg.col_controlling_faction
		), (
			id_server,
		)
	)
	rowdy_districts = 0
	killer_districts = 0

	for district in districts:
		if district[1] == ewcfg.faction_rowdys:
			rowdy_districts += 1
		elif district[1] == ewcfg.faction_killers:
			killer_districts += 1

	rowdy_entry = [ewcfg.faction_rowdys.capitalize(), rowdy_districts]
	killer_entry = [ewcfg.faction_killers.capitalize(), killer_districts]

	return format_board(
		entries = [rowdy_entry, killer_entry] if rowdy_districts > killer_districts else [killer_entry, rowdy_entry],
		title = title,
		entry_type = ewcfg.entry_type_districts
	)

"""
	convert leaderboard data into a message ready string 
"""
def format_board(entries = None, title = "", entry_type = "player", divide_by = 1):
	result = ""
	result += board_header(title)

	for entry in entries:
		result += board_entry(entry, entry_type, divide_by)

	return result

def board_header(title):
	emote = None

	bar = " ▓▓▓▓▓"

	if title == ewcfg.leaderboard_slimes:
		emote = ewcfg.emote_slime2
		bar += "▓▓▓ "

	elif title == ewcfg.leaderboard_slimecoin:
		emote = ewcfg.emote_slimecoin
		bar += " "

	elif title == ewcfg.leaderboard_ghosts:
		emote = ewcfg.emote_negaslime
		bar += "▓ "

	elif title == ewcfg.leaderboard_bounty:
		emote = ewcfg.emote_slimegun
		bar += "▓ "

	elif title == ewcfg.leaderboard_kingpins:
		emote = ewcfg.emote_theeye
		bar += " "

	elif title == ewcfg.leaderboard_districts:
		emote = ewcfg.emote_nlacakanm
		bar += " "

	elif title == ewcfg.leaderboard_donated:
		emote = ewcfg.emote_slimecorp
		bar += " "

	return emote + bar + title + bar + emote + "\n"

def board_entry(entry, entry_type, divide_by):
	result = ""

	if entry_type == ewcfg.entry_type_player:
		faction = ewutils.get_faction(life_state = entry[1], faction = entry[2])
		faction_symbol = ewutils.get_faction_symbol(faction, entry[2])

		result = "{} `{:_>15} | {}`\n".format(
			faction_symbol,
			"{:,}".format(entry[3] if divide_by == 1 else int(entry[3] / divide_by)),
			entry[0].replace("`","")
		)

	elif entry_type == ewcfg.entry_type_districts:
		faction = entry[0]
		districts = entry[1]
		faction_symbol = ewutils.get_faction_symbol(faction.lower())

		result = "{} `{:_>15} | {}`\n".format(
			faction_symbol,
			faction,
			districts
		)

	return result
