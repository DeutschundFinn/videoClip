import discord
from discord.ext import commands
from core.classes import Cog_extension
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('googleaiKey'))
model = genai.GenerativeModel('gemini-pro')

class Event(Cog_extension):
    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(content='Command on cooldown... please wait')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(content="You don't have required permission to ude the command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(content="There are some arguments missing to use the command.")
        else:
            await ctx.send(error)  
    
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message):
        if self.bot.user in msg.mentions and msg.author!=self.bot.user:
            div = msg.content.split()
            for i in range(len(div)):
                if div[i].startswith('<@'):
                    user:discord.User = await self.bot.fetch_user(div[i][2:-1])
                    div[i] = user.name
            prompt = ' '.join(div)
            response = model.generate_content(prompt)
            await msg.channel.send(response.text)

async def setup(bot):
    await bot.add_cog(Event(bot))