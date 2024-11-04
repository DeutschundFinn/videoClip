import discord
from discord import app_commands
from core.classes import Cog_extension
from typing import Literal
import os
from cmds.convertTxt import transcribe
from cmds.convertCsvOrSrt import writetocsv, generatesrt
import requests

def get_confirm_token(response:requests.Response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value

    return None


def save_response_content(response:requests.Response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download&confirm=1" #Google drive 要求下載的連結

    session = requests.Session() #保留使用者狀態

    response = session.get(URL, params={"id": file_id}, stream=True)  #獲取回應
    token = get_confirm_token(response)

    if token: #當檔案太大時
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

class ConvertFromDrive(Cog_extension):
    @app_commands.command(description='從google雲端硬碟分享連結產生你想要的檔案(使用前請勿逼打開存取權)')
    @app_commands.describe(url='你要產生檔案的雲端硬碟分享連結', language='音訊的語言', model='轉換時所使用的whisper模型', frmat='需要轉換的檔案(預設是txt檔)')
    async def convert_from_drive(self, 
                                 interaction:discord.Interaction, 
                                 url:str, 
                                 language:str=None, 
                                 model:Literal['tiny', 'base', 'medium', 'large-v1', 'large-v2']='base', 
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
                segments = transcribe(destination, language, model)
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
            
                await interaction.followup.send(content=f"以下為產生的{frmat}檔案", file=discord.File(result))
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

async def setup(bot):
    await bot.add_cog(ConvertFromDrive(bot))