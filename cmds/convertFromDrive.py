import discord
from discord import app_commands
from core.classes import Cog_extension
from typing import Literal
import os
from cmds.convertTxt import transcribe
from cmds.convertCsvOrSrt import writetocsv, generatesrt
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

def download_file_from_google_drive(file_id, destination): #利用爬蟲從Google Drive 下載檔案
    URL = "https://docs.google.com/uc?export=download&confirm=1" #指向分享連結中的檔案

    session = requests.Session() #保留使用者狀態

    response = session.get(URL, params={"id": file_id}, stream=True)  #獲取回應
    token = get_confirm_token(response) #檢查是否產生下載警告

    if token: #當跑出下載警告時傳入確認下載的token
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination) #將回應內容(檔案)下載至電腦

class ConvertFromDrive(Cog_extension):
    @app_commands.command(description='從google雲端硬碟分享連結產生你想要的檔案(使用前請務必打開存取權)')
    @app_commands.describe(url='你要產生檔案的雲端硬碟分享連結', language='音訊的語言', model='轉換時所使用的whisper模型', frmat='需要轉換的檔案(預設是txt檔)')
    async def convert_from_drive(self, 
                                 interaction:discord.Interaction, 
                                 url:str, 
                                 language:str=None, 
                                 model:Literal['tiny', 'base', 'medium', 'large-v1', 'large-v2']='large-v2', 
                                 frmat:Literal['wav', 'txt', 'csv', 'srt']='txt'):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        if not os.path.exists('output'):
            os.makedirs('output')
        file_id = url.split('/')[-2]
        destination = f"./output/{file_id}.wav"
        download_file_from_google_drive(file_id, destination)
        if destination:
            try:
                lang, segments = transcribe(destination, language, model)
                if frmat == 'wav':
                    result = destination
                elif frmat == 'txt':
                    result = f"./output/{file_id}.txt"
                    with open(result, 'w', encoding='utf8') as file:
                        for segment in segments:
                            file.write(segment.text+'\n')
                elif frmat == 'csv':
                    result = writetocsv(segments, file_id)
                elif frmat == 'srt':
                    result = generatesrt(segments, file_id)
            
                await interaction.followup.send(content=f"以下為產生的{frmat}檔案\n語言 {lang}", file=discord.File(result))
                os.remove(destination)

                if os.path.exists(result):
                    os.remove(result)
            
                if not os.listdir('./output'):
                    os.rmdir('output')
            
            except Exception as e:
                print(f"產生文字稿時發生錯誤: {e}")
                await interaction.followup.send(f"產生文字稿時發生錯誤: {e}")
        
        else:
            await interaction.followup.send("轉檔失敗，請檢查輸入的連結")

async def setup(bot:commands.Bot):
    await bot.add_cog(ConvertFromDrive(bot))