from discord.ext import commands

class Cog_extension(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot