import discord
from discord.ext import commands
from core.classes import Cog_extension
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
import subprocess
import requests
import os

# youtube影片網址下載為mp3
def download_audio_from_youtube(video_url):
    try:
        output_file_yt = "./output/yt.mp3"

        #-x是提取音訊用的 check=True表示如果yt-dlp命令失敗則會引發錯誤    
        subprocess.run(['yt-dlp', '-x', '--audio-format', 'mp3', video_url, '-o', output_file_yt], check=True) 
        print(f"The audio file has been downloaded as {output_file_yt}")
        return output_file_yt
    
    except Exception as e:
        print(f"An error occurred when downloading audio files: {e}")
        return None
    
# 將音訊網址轉換為wav格式
def convert_audio_to_wav(audio_url):
    try:
        downloaded_file_yt = None  # 初始化變數

        # 如果是YouTube連結就下載音訊
        if "youtube.com" in audio_url or "youtu.be" in audio_url:
            downloaded_file_yt = download_audio_from_youtube(audio_url)

            # 如果下載成功就載入音訊
            if downloaded_file_yt:
                audio = AudioSegment.from_file(downloaded_file_yt)
        
        # 將音訊網址轉換為wav格式
        else:
            r = requests.get(audio_url)  #HTTP GET請求下載音訊
            r.raise_for_status()         #檢查請求是否成功 偵測錯誤

            # 使用BytesIO將下載的內容轉換為類似檔案的東西，然後用pydub讀取音訊
            audio = AudioSegment.from_file(BytesIO(r.content))

        output_file = "./output/output.wav"
        audio.export(output_file, format = "wav")  #導出音檔
        print(f"The audio has successfully saved as {output_file}")

        # 清理下載的音訊檔案
        if downloaded_file_yt and os.path.exists(downloaded_file_yt):
            os.remove(downloaded_file_yt)
        return output_file  

    except Exception as e:
        print(f"Raised exception:{e}")


class VideoClip(Cog_extension):
    @discord.slash_command(description='Convert a Youtube url to text')
    @discord.option('url', input_type=str, description='The youtube url you want to transcribe as text')
    @discord.option('language', input_type=str, description='The language you want to transcribe as. (in english lower letter)', required=False, default=None)
    @discord.option('model', input_type=str, description='The model you want to use for the transcription.', required=False, default='base', choices=['tiny', 'base', 'medium', 'large'])
    async def convert(self, ctx:discord.ApplicationContext, url, language, model):
        print("Processing")  
        await ctx.respond("Please wait for a while.")
        output_file = convert_audio_to_wav(url) 
    
        file_size = os.path.getsize(output_file)       # 偵測檔案大小
        file_size_MB = round(file_size / (1024 * 1024), 1)      # 轉為MB

        try:
            if output_file:
                recognizer = sr.Recognizer()
                with sr.AudioFile(output_file) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2) #處理雜訊
                    audio = recognizer.record(source) #將AudioFile轉換成AudioData供語音辨識器進行辨識
                try:
                    text = recognizer.recognize_whisper(audio, language=language, model=model) #丟給whisper語音模型進行辨識
                    with open('./output/output.txt', 'w', encoding='utf8') as outputFile:
                        outputFile.write(text)
                    await ctx.followup.send(content=f"Here is your recognized text!", file=discord.File('./output/output.txt'))
                    os.remove(output_file)
                    os.remove('./output/output.txt')
                except Exception as e:
                    await ctx.followup.send(e)
            else:
                await ctx.followup.send("Please chack your inserted url")
            
        except Exception as e:
            await ctx.followup.send("The target file is too large")
            await ctx.followup.send(f"The size of the file is {file_size_MB} According to the test the file must be smaller than 25MB")
            print(f"The size of the file is {file_size_MB}")
            print(f"Raised exception:{e}")

            os.remove(output_file)  # 轉檔後刪除 WAV 檔案

def setup(bot):
    bot.add_cog(VideoClip(bot))