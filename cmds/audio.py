import discord
from discord.ext import commands
from core.classes import Cog_extension
import os
import speech_recognition as sr

connections={}

async def once_done(sink:discord.sinks.Sink, user:discord.User, channel:discord.TextChannel, language:str):
    await sink.vc.disconnect()  
    for item in sink.audio_data.items():
        if item[0]==user.id:
            audio:discord.sinks.AudioData = item[1]
    
    with open(f"./output/{user.id}.wav", "wb") as wavfile:
        wavfile.write(audio.file.getbuffer())
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(f"./output/{user.id}.wav") as source:
        recognizer.adjust_for_ambient_noise(source)
        audioData = recognizer.record(source)
        try:
            text = recognizer.recognize_whisper(audio_data=audioData, language=language)
            await channel.send(content=f"Recognized speech:{text}", file=discord.File(audio.file, f"{user.id}.{sink.encoding}"))
        except sr.UnknownValueError:
            await channel.send("I can't understand what you are saying.")
        except sr.RequestError as e:
            await channel.send(f"Could not request from service:{e}")

class Audio(Cog_extension):
    @discord.slash_command(description='convert a video file to text')
    @discord.option('language', type=str, description='the language you want to transcibed to.')
    async def audio_to_text(self, ctx:discord.ApplicationContext, language:str):
        voice = ctx.author.voice
        if not voice:
            return await ctx.respond(content='You are not in a voice channel!', ephemeral=True)
        vc = await voice.channel.connect()

        connections.update({ctx.guild_id:vc})
        
        vc.start_recording(discord.sinks.WaveSink(), once_done, ctx.author, ctx.channel, language)
        await ctx.respond('Started recording!')
    
    @discord.slash_command(description='stops a current recording.')
    async def stop(self, ctx:discord.ApplicationContext):
        if ctx.guild_id in connections:
            vc = connections[ctx.guild_id]
            vc.stop_recording()
            del connections[ctx.guild_id]
            await ctx.respond('Sucessfully stopped a current recording.')
        else:
            await ctx.respond(conetent='I am not currently recording.', ephemeral=True)

def setup(bot):
    bot.add_cog(Audio(bot))