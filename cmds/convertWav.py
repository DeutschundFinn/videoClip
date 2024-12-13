import discord
from discord import app_commands
from core.classes import Cog_extension
import yt_dlp
from pydub import AudioSegment
import os
import requests
from discord.ext import commands

def get_confirm_token(response:requests.Response): #確認是否會遇到下載警告
    for key, value in response.cookies.items(): #當有下載警告時獲取確認token
        if key.startswith("download_warning"):
            return value

    return None

def save_response_content(response:requests.Response, destination): #下載檔案
    CHUNK_SIZE = 32768 #區塊大小(單位為bytes)

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE): #此處將大檔案分割成一堆小區塊進行下載
            if chunk:  
                f.write(chunk)

def get_file_id(url:str):
    if 'youtube.com' in url or 'youtu.be' in url:
        return url.split('=')[-1]
    elif 'drive.google.com' in url:
        return url.split('/')[-2]

# youtube影片網址下載為mp3
def download_audio(video_url, file_id):
    try:
        output_file = f"{file_id}.mp3"

        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            with yt_dlp.YoutubeDL({'extract_audio':True, 'format': 'bestaudio', 'outtmpl':output_file}) as video:
                video.download(video_url)

        elif 'drive.google.com' in video_url:
            URL = "https://docs.google.com/uc?export=download&confirm=1" #指向分享連結中的檔案

            session = requests.Session() #保留使用者狀態

            response = session.get(URL, params={"id": file_id}, stream=True)  #獲取回應
            token = get_confirm_token(response) #檢查是否產生下載警告

            if token: #當跑出下載警告時傳入確認下載的token
                params = {"id": file_id, "confirm": token}
                response = session.get(URL, params=params, stream=True)

            save_response_content(response, output_file) #將回應內容(檔案)下載至電腦
        print(f"音訊檔案已下載為 {output_file}")
        return output_file
    
    except Exception as e:
        print(f"下載音訊檔案時發生錯誤: {e}")
        return None
    
# 將音訊網址轉換為wav格式
def convert_url_to_wav(audio_url, file_id):
    try:
        downloaded_file = None  # 初始化變數

        # 下載Youtube音訊
        
        downloaded_file = download_audio(audio_url, file_id)

        # 如果下載成功就載入音訊
        if downloaded_file:
            audio = AudioSegment.from_file(downloaded_file)

        output_file = f"{file_id}.wav"
        audio.export(output_file, format = "wav")  #導出音檔
        print(f"音訊成功轉換並儲存為 {output_file}")

        # 清理下載的音訊檔案
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        return output_file  

    except Exception as e:
        print(f"轉檔時發生錯誤:{e}")


class ConvertWav(Cog_extension):
    @app_commands.command(description='從Youtube網址下載該影片的WAV音檔')
    @app_commands.describe(url='你要轉成音檔的Youtube網址')
    async def convert_to_wav(self, interaction:discord.Interaction, url:str):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        file_id = get_file_id(url)
        output_file = convert_url_to_wav(url, file_id) 
        
        file_size = os.path.getsize(output_file)                # 偵測檔案大小
        file_size_MB = round(file_size / (1024 * 1024), 1)      # 轉為MB

        try:
            if output_file:
                await interaction.followup.send(file=discord.File(output_file))
                await interaction.followup.send("好了啦")
                print("完成執行")

                os.remove(output_file)  # 轉檔後刪除 WAV 檔案  
            else:
                await interaction.followup.send("轉檔失敗 請檢查輸入的連結")
                
        except Exception as e:
            await interaction.followup.send("檔案太大 目前太窮沒辦法升級discord 所以沒辦法回傳")
            await interaction.followup.send(f"此檔案大小為{file_size_MB}MB 根據測試應該小於25MB才能回傳")
            print(f"此檔案大小為{file_size_MB}MB")
            print(f"發生錯誤:{e}")

            os.remove(output_file)  # 轉檔後刪除 WAV 檔案

async def setup(bot:commands.Bot):
    await bot.add_cog(ConvertWav(bot))
