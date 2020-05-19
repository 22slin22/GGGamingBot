import discord
import json
import sys

with open("conf.json") as conf_file:
	CONF = json.load(conf_file)

class MyClient(discord.Client):

	def __init__(self):
		super().__init__()
		self.moving_players = set()

	async def on_ready(self):
		print('Logged on as {0}'.format(self.user))
	
	async def on_member_update(self, before, after):
		if before.activity != after.activity:
			print(before, before.activity, after.activity)
			await self.check_move_to_other_game()

	async def on_voice_state_update(self, member, before, after):
		if before.channel != after.channel:
			print("Voice state update")
			if str(member) in self.moving_players:
				self.moving_players.remove(str(member))
			else:
				await self.check_move_to_other_game()

	async def check_move_to_other_game(self):
		for guild in self.guilds:
			if guild.id == CONF["guild_id"]:
				for vc in guild.voice_channels:
					if vc.id not in CONF["channel_blacklist"]:
						activity = self.check_same_activity(vc.members)
						if activity is not None and activity in CONF["games"]:
							# Move all Member of this voice chat into the new category
							print("Members of {0} are all playing {1}".format(vc.name, activity))
							category = self.get_category(guild, CONF["games"][activity])
							if category is not None:
								if vc.category != category:
									availible_vc = None
									for new_vc in category.voice_channels:
										if len(new_vc.members) <= 1 and (new_vc.user_limit == 0 or new_vc.user_limit - len(new_vc.members)) >= len(vc.members):
											availible_vc = new_vc
											break
									if availible_vc is not None:
										members_to_move = [m for m in vc.members if str(m) not in self.moving_players]
										print("Moving them into {0}".format(new_vc.name))
										self.moving_players.update([str(m) for m in members_to_move])
										await self.move_members_to_channel(new_vc, members_to_move)

	def check_same_activity(self, members):
		# Checks if all the memebers have the same activity and returns it, otherwise returns None
		activities = None
		for member in members:
			acts = [a for a in member.activities]
			if len(acts) == 0:
				return None
			else:
				if activities is None:
					activities = [a.name for a in acts if a.type == discord.ActivityType.playing]
				else:
					activities = [a.name for a in acts if a.name in activities]
		if activities is None:
			return None
		if len(activities) == 0:
			return None
		return activities[0]

	def get_category(self, guild, id):
		for category in guild.categories:
			if category.id == id:
				return category
		return None

	async def move_members_to_channel(self, vc, members):
		for member in members:
			await member.move_to(vc)


	async def on_message_edit(self, before, after):
		await self.on_message(after)

	async def on_message(self, message):
		try:
			# Test if the message was sent on a server
			if type(message.author) is discord.Member:
				if not message.content.startswith(".ggg"):
					return
				# Test if author is allowed to edit settings
				member = message.author
				role_ids = [role.id for role in member.roles]
				if not CONF["maintainer_role_id"] in role_ids:
					return

				command = message.content.split(" ")
				if len(command) < 2:
					await message.channel.send("You have to specify a command after .ggg (ch_blacklist, games)")
					return

				if command[1] == "ch_blacklist":
					if len(command) < 3:
						await message.channel.send("You have to specify at least one argument after ch_blacklist (list, add <ch_id>, remove <ch_id>)")
						return

					if command[2] == "list":
						response = "Blacklisted channels:"
						for ch in CONF["channel_blacklist"]:
							response += "\n{0}".format(ch)
						await message.channel.send(response)

					elif command[2] == "add":
						if len(command) < 4:
							await message.channel.send("You have to specify the channel_id of the channel you want to blacklist after 'add'")
							return
						try:
							new_ch_id = int(command[3])
						except ValueError:
							await message.channel.send("channel_id must be of type int. You specified " + command[3])
							return
						CONF["channel_blacklist"].append(new_ch_id)
						with open("conf.json", "w") as conf_file:
							json.dump(CONF, conf_file)
						await message.channel.send("Channel {0} was added to the blacklist".format(command[3]))
						
					elif command[2] == "remove":
						if len(command) < 4:
							await message.channel.send("You have to specify the channel_id of the channel you want to blacklist after 'remove'")
							return
						try:
							ch_id = int(command[3])
						except ValueError:
							await message.channel.send("channel_id must be of type int. You specified " + command[3])
							return
						if ch_id not in CONF["channel_blacklist"]:
							await message.channel.send("{0} is not on the channel_blacklist".format(command[3]))
							return
						CONF["channel_blacklist"].remove(ch_id)
						with open("conf.json", "w") as conf_file:
							json.dump(CONF, conf_file)
						await message.channel.send("Removed {0} from the channel_blacklist".format(command[3]))

					else:
						await message.channel.send("{0} id not a valid command. Use list, add or remove".format(command[2]))
						return

				elif command[1] == "games":
					if len(command) < 3:
						await message.channel.send("Use of .ggg games:\n.ggg games list\n.ggg games add <category_id> <game_name>\n.ggg games remove <game_name>\n.ggg games edit <new_category_id> <game_name>")
						return

					if command[2] == "list":
						response = "Games:"
						for game, cat in CONF["games"].items():
							response += "\n{0}: {1}".format(game, cat)
						await message.channel.send(response)

					elif command[2] == "add":
						if len(command) < 5:
							await message.channel.send("Use of .ggg games:\n.ggg games list\n.ggg games add <category_id> <game_name>\n.ggg games remove <game_name>\n.ggg games edit <new_category_id> <game_name>")
							return
						try:
							cat_id = int(command[3])
						except ValueError:
							await message.channel.send("category_id must be of type int. You specified " + command[4])
							return
						game = ' '.join(command[4:])
						CONF["games"][game] = cat_id
						with open("conf.json", "w") as conf_file:
							json.dump(CONF, conf_file)
						await message.channel.send("{0} was added to the games".format(game))
						
					elif command[2] == "remove":
						if len(command) < 4:
							await message.channel.send("You have to specify the game_name of the channel you want to remove after 'remove'")
							return
						game = ' '.join(command[4:])
						if game not in CONF["games"]:
							await message.channel.send("{0} does not exist".format(game))
							return
						del CONF["games"][game]
						with open("conf.json", "w") as conf_file:
							json.dump(CONF, conf_file)
						await message.channel.send("Removed the game {0}".format(game))

					elif command[2] == "edit":
						if len(command) < 5:
							await message.channel.send("Use of .ggg games:\n.ggg games list\n.ggg games add <category_id> <game_name>\n.ggg games remove <game_name>\n.ggg games edit <new_category_id> <game_name>")
							return
						try:
							cat_id = int(command[3])
						except ValueError:
							await message.channel.send("category_id must be of type int. You specified " + command[4])
							return
						game = ' '.join(command[4:])
						if game not in CONF["games"]:
							await message.channel.send("{0} does not exist".format(game))
							return
						CONF["games"][game] = cat_id
						with open("conf.json", "w") as conf_file:
							json.dump(CONF, conf_file)
						await message.channel.send("{0} was edited".format(game))

					else:
						await message.channel.send("Use of .ggg games:\n.ggg games list\n.ggg games add <category_id> <game_name>\n.ggg games remove <game_name>\n.ggg games edit <new_category_id> <game_name>")
						return

				else:
					await message.channel.send("Use of .ggg:\n.ggg games <args>\n.ggg ch_blacklist <args>")
					return
		except Exception as e:
			await message.channel.send(str(e))



if __name__ == '__main__':
	client = MyClient()
	client.run(CONF["token"])
