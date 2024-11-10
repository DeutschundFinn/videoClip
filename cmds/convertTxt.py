import discord
from discord import app_commands
from core.classes import Cog_extension
from cmds.convertWav import download_audio_from_youtube
from typing import Literal
from faster_whisper import WhisperModel
import os

def transcribe(audio, lang, mod):
    print(f"正在轉換{audio}") 
    model = WhisperModel(mod, compute_type='int8') #系統限制，一般情況下compute_type可省略
    segments, info = model.transcribe(audio, language=lang, vad_filter=False, vad_parameters=dict(min_silence_duration_ms=100))  #Segments是以每個有100毫秒的無人聲片段所切間隔
    language = info[0]
    print("文字檔語言", language)
    segments = list(segments) #產生各片段所組成的陣列
    return language, segments

class ConvertTxt(Cog_extension):
    @app_commands.command(description='從Youtube網址產生該影片字幕的txt檔案')
    @app_commands.describe(url='你要產生txt文字檔的Youtube網址', language='音訊的語言', model='轉換時所使用的whisper模型')
    async def convert_to_txt(self, interaction:discord.Interaction, url:str, language:str=None, model:Literal['tiny', 'base', 'medium', 'large-v1', 'large-v2']='base'):
        print("正在執行...")  
        await interaction.response.send_message("請稍等一下")
        file_id = url.split('=')[-1]
        output_file = download_audio_from_youtube(url, file_id)
        if output_file:
            try:
                lang, segments = transcribe(output_file, language, model)
                os.remove(output_file) #轉檔完刪除mp3檔案

                if not os.path.exists('output'): #產生存放文字檔的資料夾
                    os.makedirs('output')

                txt_file=f"./output/{file_id}.txt"
                # 寫入文字檔
                with open(txt_file, 'w', encoding='utf8') as outputFile:
                    for segment in segments:
                        outputFile.write(segment.text + '\n')
            
                await interaction.followup.send(content=f"以下為轉換的txt文字檔:\n語言 {lang}", file=discord.File(txt_file))
                print("成功轉換成文字稿")

                if os.path.exists(txt_file):
                    os.remove(txt_file)
                
                if not os.listdir('./output'):
                    os.rmdir('output')

            except Exception as e:
                print(f"產生文字稿時發生錯誤: {e}")
                await interaction.followup.send(f"產生文字稿時發生錯誤: {e}")
        
        else:
            await interaction.followup.send("轉檔失敗，請檢查輸入的連結")

async def setup(bot):
    await bot.add_cog(ConvertTxt(bot))
