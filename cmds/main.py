import discord
from discord import app_commands
from core.classes import Cog_extension

class Main(Cog_extension):
    @app_commands.command(description='輸出這機器人的邀請連結')
    async def invite(self, interaction:discord.Interaction):
        await interaction.response.send_message(content='https://discord.com/oauth2/authorize?client_id=1283301891047952424', ephemeral=True)

    @app_commands.command(description='Clear the chatroom.')
    @app_commands.describe(number='The number of messages you want to clear')
    @app_commands.default_permissions(manage_messages=True, manage_channels=True)
    async def purge(self, interaction:discord.Interaction, number:int):
        await interaction.response.send_message("Started deleting")
        await interaction.channel.purge(limit=number+1)
        

async def setup(bot):
    await bot.add_cog(Main(bot))