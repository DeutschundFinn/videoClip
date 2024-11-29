import discord
from discord import app_commands
from core.classes import Cog_extension
from cmds.convertWav import convert_audio_to_wav
from typing import Literal
import os
from cmds.convertTxt import transcribe
import time
import pandas as pd

def formattedtime(seconds):
    final_time = time.strftime("%H:%M:%S", time.gmtime(float(seconds))) #從檔案開始將每個間隔所表示時間寫成字串
    return f"{final_time},{seconds.split('.')[1]}"

def writetocsv(segments, file_id):
    output_file = f"./output/{file_id}.csv"
    cols = ["start", "end", "text"] #csv每行結構: ["開始時間", "結束時間", "文字"]
    data = []
    for segment in segments:
        start = formattedtime(format(segment.start, ".3f"))
        end = formattedtime(format(segment.end, ".3f"))
        data.append([start, end, segment.text]) 

    df = pd.DataFrame(data, columns=cols) 
    df.to_csv(output_file, index=False) #利用pandas將資料寫入csv檔
    return output_file

def generatesrt(segments, file_id):
    output_file = f"./output/{file_id}.srt"
    count = 0
    
    with open(output_file, 'w', encoding='utf8') as file:
        for segment in segments:
            start = formattedtime(format(segment.start, ".3f"))
            end = formattedtime(format(segment.end, ".3f"))
            count += 1
            txt = f"{count}\n{start} --> {end}\n{segment.text}\n\n" #srt檔案表示法(/表示分行): 順序/開始時間 --> 結束時間/文字
            file.write(txt) #讀取音訊片段並寫入srt
            
    return output_file   

class ConvertCsvOrSrt(Cog_extension):
    @app_commands.command(description='從Youtube網址產生該影片字幕的csv檔案')
    @app_commands.describe(url='你要產生csv檔案的Youtube網址', language='音訊的語言', model='轉換時所使用的whisper模型')
    async def convert_to_csv(self, interaction:discord.Interaction, url:str, language:str=None, model:Literal['tiny', 'base', 'medium', 'large-v1', 'large-v2']='large-v2'):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        file_id = url.split('=')[-1]
        output_file = convert_audio_to_wav(url, file_id)
        if output_file:
            try:
                lang, segments = transcribe(output_file, language, model)
                os.remove(output_file) #轉檔完刪除mp3檔案
                if not os.path.exists('output'): #產生存放文字檔的資料夾
                    os.makedirs('output')

                csv_file = writetocsv(segments, file_id)

                await interaction.followup.send(content=f"以下為轉換的csv檔案:\n語言 {lang}", file=discord.File(csv_file))
                print("成功轉換成文字稿")
                if os.path.exists(csv_file):
                    os.remove(csv_file)
                
                if not os.listdir('./output'):
                    os.rmdir('output')
            
            except Exception as e:
                print(f"產生文字稿時發生錯誤: {e}")
                await interaction.followup.send(f"產生文字稿時發生錯誤: {e}")
        
        else:
            await interaction.followup.send("轉檔失敗，請檢查輸入的連結")
    
    @app_commands.command(description='從Youtube網址產生該影片字幕的srt檔案')
    @app_commands.describe(url='你要產生srt檔案的Youtube網址', language='音訊的語言', model='轉換時所使用的whisper模型')
    async def convert_to_srt(self, interaction:discord.Interaction, url:str, language:str=None, model:Literal['tiny', 'base', 'medium', 'large-v1', 'large-v2']='large-v2'):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        file_id = url.split('=')[-1]
        output_file = convert_audio_to_wav(url, file_id)
        if output_file:
            try:
                lang, segments = transcribe(output_file, language, model)
                os.remove(output_file) #轉檔完刪除mp3檔案
                if not os.path.exists('output'): #產生存放文字檔的資料夾
                    os.makedirs('output')

                srt_file = generatesrt(segments, file_id)

                await interaction.followup.send(content=f"以下為轉換的srt檔案:\n語言 {lang}", file=discord.File(srt_file))
                print("成功轉換成文字稿")

                if os.path.exists(srt_file):
                    os.remove(srt_file)
                
                if not os.listdir('./output'):
                    os.rmdir('output')
            
            except Exception as e:
                print(f"產生文字稿時發生錯誤: {e}")
                await interaction.followup.send(f"產生文字稿時發生錯誤: {e}")
        
        else:
            await interaction.followup.send("轉檔失敗，請檢查輸入的連結")

async def setup(bot):
    await bot.add_cog(ConvertCsvOrSrt(bot))