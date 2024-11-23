import discord
from discord import app_commands
from core.classes import Cog_extension
import yt_dlp
from pydub import AudioSegment
import os

# youtube影片網址下載為mp3
def download_audio_from_youtube(video_url, file_id):
    try:
        output_file_yt = f"{file_id}.wav"

        with yt_dlp.YoutubeDL({'extract_audio':True, 'format': 'bestaudio', 'outtmpl':output_file_yt}) as video:
            video.download(video_url)
        print(f"音訊檔案已下載為 {output_file_yt}")
        return output_file_yt
    
    except Exception as e:
        print(f"下載音訊檔案時發生錯誤: {e}")
        return None
    
# 將音訊網址轉換為wav格式
def convert_audio_to_wav(audio_url, file_id):
    try:
        downloaded_file_yt = None  # 初始化變數

        # 下載Youtube音訊
        
        downloaded_file_yt = download_audio_from_youtube(audio_url, file_id)

        # 如果下載成功就載入音訊
        if downloaded_file_yt:
            audio = AudioSegment.from_file(downloaded_file_yt)

        output_file = f"{file_id}.wav"
        audio.export(output_file, format = "wav")  #導出音檔
        print(f"音訊成功轉換並儲存為 {output_file}")

        # 清理下載的音訊檔案
        if downloaded_file_yt and os.path.exists(downloaded_file_yt):
            os.remove(downloaded_file_yt)
        return output_file  

    except Exception as e:
        print(f"轉檔時發生錯誤:{e}")


class ConvertWav(Cog_extension):
    @app_commands.command(description='從Youtube網址下載該影片的WAV音檔')
    @app_commands.describe(url='你要轉成音檔的Youtube網址')
    async def convert_to_wav(self, interaction:discord.Interaction, url:str):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        file_id = url.split('=')[-1]
        output_file = convert_audio_to_wav(url, file_id) 
        
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

async def setup(bot):
    await bot.add_cog(ConvertWav(bot))
