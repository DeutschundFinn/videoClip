import discord
from discord import app_commands
from core.classes import Cog_extension
import os
import google.generativeai as genai
import csv
import pandas as pd

genai.configure(api_key=os.getenv('googleaiKey'))
model = genai.GenerativeModel('gemini-pro')
config = genai.GenerationConfig(temperature=0)

def translateFile(to_lang, from_lang, prompt): #交由Gemini幫忙翻譯的動作
    if from_lang is None:
        response = model.generate_content(f"""Please translate the following content into {to_lang}, automatically detecting the source language. Each line begins with an integer followed by "™" (e.g., "1™"), indicating its order. Please preserve this exact format, including the integers, the "™" symbol, and their positions, ensuring the number of lines remains the same. Provide only the translation without any additional text or explanation:\n\n
                                          {prompt}""", generation_config=config)

    else:
        response = model.generate_content(f"""Please translate the following content into {to_lang}, The source language is {from_lang}. Each line begins with an integer followed by "™" (e.g., "1™"), indicating its order. Please preserve this exact format, including the integers, the "™" symbol, and their positions, ensuring the number of lines remains the same. Provide only the translation without any additional text or explanation:\n\n
                                          {prompt}""", generation_config=config)
    return response.text

class TranslateFile(Cog_extension):
    @app_commands.command(description='翻譯指定訊息的文字檔')
    @app_commands.describe(url='你要進行翻譯的文字檔所在訊息連結', target='你要翻譯成的語言', source='文字檔原本語言')
    async def translate(self, interaction:discord.Interaction, url:str, target:str, source:str=None):
        await interaction.response.send_message("請稍等一下...")
        if not os.path.exists('translate'): #產生存放文字檔的資料夾
            os.makedirs('translate')
        message_id = int(url.split('/')[-1])
        try:
            message = await interaction.channel.fetch_message(message_id) #找到目標訊息
            file = message.attachments[0] 
            outputFile = f"./translate/{file.filename}"
            await file.save(outputFile) #下載文字檔
            frmat = file.filename.split('.')[-1]
            if frmat == 'txt': #檢查如果是txt直接翻譯
                div = []
                with open(outputFile, 'r', encoding='utf8') as txtFile:
                    counter = 1
                    for row in txtFile.read().splitlines():
                        div.append(str(counter)+'™'+row)
                        counter += 1
                    prompt = '\n'.join(div)
                text = translateFile(target, source, prompt)
                result = text.splitlines()
                for i in range(len(result)):
                    result[i] = result[i].split('™')[-1]
                with open(outputFile, 'w', encoding='utf8') as txtFile:
                    txtFile.write('\n'.join(result))
        
            elif frmat == 'csv': #檢查如果是csv把檔案的文字部分翻譯完丟回檔案
                data = []
                div=[]
                with open(outputFile, encoding='utf8') as csvFile:
                    reader = csv.DictReader(csvFile)
                    counter = 1
                    for row in reader:
                        div.append(str(counter)+'™'+row['text'])
                        data.append([row['start'], row['end'], row['text']])
                        counter += 1
                    prompt = '\n'.join(div)
                    text = translateFile(target, source, prompt)
                for i in range(len(data)):
                    data[i][2] = text.splitlines()[i].split('™')[-1]
                cols = ["start", "end", "text"]
                df = pd.DataFrame(data, columns=cols)
                df.to_csv(outputFile, index=False, mode='w', encoding='utf8')
            elif frmat == 'srt': #檢查如果是srt同csv方式處理
                div = []
                with open(outputFile, 'r', encoding='utf8') as srtFile:
                    content = srtFile.read().splitlines()
                    counter = 1
                    for i in range(len(content)):
                        if i%4 == 2: #陣列內部:['順序',  '開始時間-->結束時間', '文字', '', ...]
                            div.append(str(counter)+'™'+content[i])
                            counter +=1
                    prompt = '\n'.join(div)
                    text = translateFile(target, source, prompt)
                    j = 0
                    for i in range(len(content)):
                        if i%4 == 2: #陣列內部:['順序',  '開始時間-->結束時間', '文字', '', ...]
                            content[i] = text.splitlines()[j].split('™')[-1]
                            j+=1
                
                with open(outputFile, 'w', encoding='utf8') as srtFile:
                    srtFile.write('\n'.join(content))
            
            await interaction.followup.send(content=f"這是翻譯完的{frmat}檔案", file=discord.File(outputFile))
            if os.path.exists(outputFile):
                os.remove(outputFile)
            if not os.listdir('./translate'):
                os.rmdir('translate')
        
        except Exception as e:
            print(f"翻譯時發生錯誤: {e}")
            await interaction.followup.send(f"翻譯時發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(TranslateFile(bot))
