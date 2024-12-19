import discord
from discord import app_commands
from core.classes import Cog_extension
from discord.ui import Button, View
from discord.ext import commands

class Main(Cog_extension):
    @app_commands.command(description='輸出這機器人的邀請連結')
    async def invite(self, interaction:discord.Interaction):
        button = Button(style=discord.ButtonStyle.link, label='點擊我以邀請機器人', url='https://discord.com/oauth2/authorize?client_id=1283301891047952424')
        view = View()
        view.add_item(button)
        await interaction.response.send_message(content='以下是邀請連結', view=view)

    @app_commands.command(description='清除聊天室')
    @app_commands.describe(number='你要清除的訊息數')
    @app_commands.default_permissions(manage_messages=True, manage_channels=True)
    async def purge(self, interaction:discord.Interaction, number:int):
        await interaction.response.send_message("開始刪除中...")
        await interaction.channel.purge(limit=number+1)

    @commands.command()  # 使用 commands.command 裝飾器
    async def ping(self, ctx:commands.Context):
        await ctx.send(f"Pong! {round(self.bot.latency*1000)} (ms).")   

async def setup(bot:commands.Bot):
    await bot.add_cog(Main(bot))