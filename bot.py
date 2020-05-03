import discord
from threading import Lock
from dotenv import load_dotenv
import os

load_dotenv()

GUILD_ID = int(os.getenv("GUILD_ID"))

# A list of server categories ids mapped to games
CATEGORIES = {
	"Counter-Strike: Global Offensive": 689211828517339161,
	"VALORANT" : 					  	699472424361656370,
	"Call of Duty" : 				 	689455527234895965,
	"Tom Clancy's Rainbow Six Siege" : 	689455093887664216,
	"League of Legends" : 				689455277279674374,
	"Overwatch" : 						689455187768901718,
	"Battelfield" : 					689455723255431284,
	"Minecraft" : 						689455808970621047,
	"Fortnite":							689455883134304287,
	"Apex Legends" : 					689455952759619623,
	"Rocket League" : 					690636048346251365,
	"Brawlhalla" : 						690657046059810876,
	"Grand Theft Auto" : 				690920662642065488,
	"Tabletop Simulator" : 				700073633984544779
}

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
			if guild.id == GUILD_ID:
				for vc in guild.voice_channels:
					activity = self.check_same_activity(vc.members)
					if activity is not None and activity in CATEGORIES:
						# Move all Member of this voice chat into the new category
						print("Members of {0} are all playing {1}".format(vc.name, activity))
						category = self.get_category(guild, CATEGORIES[activity])
						if category is not None:
							if vc.category != category:
								availible_vc = None
								for new_vc in category.voice_channels:
									# print(new_vc.user_limit)
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
		activity = None
		for member in members:
			act = member.activity
			if act is None:
				return None
			else:
				if activity is None:
					activity = act.name
				else:
					if act.name != activity:
						return None
		return activity

	def get_category(self, guild, id):
		for category in guild.categories:
			if category.id == id:
				return category
		return None

	async def move_members_to_channel(self, vc, members):
		for member in members:
			await member.move_to(vc)


if __name__ == '__main__':
	client = MyClient()
	client.run(os.getenv("TOKEN"))
