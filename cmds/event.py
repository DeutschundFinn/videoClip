import discord
from discord.ext import commands
from core.classes import Cog_extension
import google.generativeai as genai
import os
from discord.ext import commands

genai.configure(api_key=os.getenv('googleaiKey')) #指定API Key
model = genai.GenerativeModel('gemini-1.5-pro') #指定使用的Gemini模型

class Event(Cog_extension):
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message): #Gemini 聊天機器人的串接
        if self.bot.user in msg.mentions and msg.author!=self.bot.user: #檢測訊息內是否有提到機器人本身
            div = msg.content.split() #將訊息拆分
            for i in range(len(div)):
                if div[i].startswith('<@'): #將有提及到使用者的部分提取出來並換成該使用者的名字 discord mention結構: <@(使用者id)>
                    user:discord.User = await self.bot.fetch_user(div[i][2:-1]) #從mention裡面抓取使用者id並指向該用戶 
                    div[i] = user.name #將用戶名放入該位置
            prompt = ' '.join(div) 
            response = model.generate_content(prompt) #交給Gemini產生文字
            await msg.channel.send(response.text) #送出文字

    @commands.Cog.listener() 
    async def on_command_error(self, ctx:commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(content='Command on cooldown... please wait')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(content="You don't have required permission to use the command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(content="There are some arguments missing to use the command.")
        else:
            await ctx.send(error)  


async def setup(bot:commands.Bot):
    await bot.add_cog(Event(bot))
