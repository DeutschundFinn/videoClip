import discord
from discord.ext import commands
from core.classes import Cog_extension

class Main(Cog_extension):
    @discord.slash_command(description='輸出這機器人的邀請連結')
    async def invite(self, ctx:discord.ApplicationContext):
        await ctx.respond(content='https://discord.com/oauth2/authorize?client_id=1283301891047952424', ephemeral=True)

def setup(bot):
    bot.add_cog(Main(bot))