import discord
from discord import app_commands
from core.classes import Cog_extension
import os
import google.generativeai as genai
import csv
import pandas as pd

genai.configure(api_key=os.getenv('googleaiKey'))
model = genai.GenerativeModel('gemini-pro')

def translateFile(to_lang, from_lang, prompt): #交由Gemini幫忙翻譯的動作
    if from_lang is None:
        response = model.generate_content(f"Please translate the following text into {to_lang}, while preserving the line breaks:\n\n{prompt}\n\nPlease only return the translated text, with the original line breaks intact, and without any additional explanations or comments.")
    else:
        response = model.generate_content(f"Please translate the following text from {from_lang} into {to_lang}, while preserving the line breaks:\n\n{prompt}\n\nPlease only return the translated text, with the original line breaks intact, and without any additional explanations or comments.")
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
                with open(outputFile, 'r', encoding='utf8') as txtFile:
                    prompt = txtFile.read()
                text = translateFile(target, source, prompt)
                with open(outputFile, 'w', encoding='utf8') as txtFile:
                    txtFile.write('\n'.join(text.split('\\n')))
            elif frmat == 'csv': #檢查如果是csv把檔案的文字部分翻譯完丟回檔案
                data = []
                div=[]
                with open(outputFile, encoding='utf8') as csvFile:
                    reader = csv.DictReader(csvFile)
                    for row in reader:
                        div.append(row['text'])
                        data.append([row['start'], row['end'], row['text']])
                    prompt = '\n'.join(div)
                    text = translateFile(target, source, prompt)
                for i in range(len(data)):
                    data[i][2] = text.splitlines()[i]
                cols = ["start", "end", "text"]
                df = pd.DataFrame(data, columns=cols)
                df.to_csv(outputFile, index=False, mode='w', encoding='utf8')
            elif frmat == 'srt': #檢查如果是srt同csv方式處理
                texts = []
                div = []
                with open(outputFile, 'r', encoding='utf8') as srtFile:
                    texts = srtFile.read().splitlines()
                    for i in range(len(texts)):
                        if i%4 == 2: #陣列內部:['順序',  '開始時間-->結束時間', '文字', '', ...]
                            div.append(texts[i])
                    prompt = '\n'.join(div)
                    text = translateFile(target, source, prompt)
                    j = 0
                    for i in range(len(texts)):
                        if i%4 == 2: #陣列內部:['順序',  '開始時間-->結束時間', '文字', '', ...]
                            texts[i] = text.splitlines()[j]
                            j+=1
                
                with open(outputFile, 'w', encoding='utf8') as srtFile:
                    srtFile.write('\n'.join(texts))
            else:
                if os.path.exists(outputFile):
                    os.remove(outputFile)
                if not os.listdir('./translate'):
                    os.rmdir('translate')
                await interaction.followup.send(f"目前不支援目前檔案格式{frmat}")
                return 
            
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
