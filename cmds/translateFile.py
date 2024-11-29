import discord
from discord import app_commands
from core.classes import Cog_extension
import os
import google.generativeai as genai
import csv
import srt
import pandas as pd

genai.configure(api_key=os.getenv('googleaiKey')) #指定API Key
model = genai.GenerativeModel('gemini-pro') #指定使用的Gemini模型
config = genai.GenerationConfig(temperature=0) #維持翻譯品質所以變異程度設為0

def translateText(to_lang, from_lang, prompt): #交由Gemini幫忙翻譯的動作
    if from_lang is None:
        response = model.generate_content(f"""Please translate the following content into {to_lang}, automatically detecting the source language. Each line begins with an integer followed by "™" (e.g., "1™"), indicating its order. Please preserve this exact format, including the integers, the "™" symbol, and their positions, ensuring the number of lines remains the same. Provide only the translation without any additional text or explanation:\n\n
                                          {prompt}""", generation_config=config)

    else:
        response = model.generate_content(f"""Please translate the following content into {to_lang}, The source language is {from_lang}. Each line begins with an integer followed by "™" (e.g., "1™"), indicating its order. Please preserve this exact format, including the integers, the "™" symbol, and their positions, ensuring the number of lines remains the same. Provide only the translation without any additional text or explanation:\n\n
                                          {prompt}""", generation_config=config)
    return response.text

def translateFile(source:str, destination:str, toLang:str, fromLang:str): #翻譯整個檔案
    frmat = source.split('.')[-1]
    if frmat == 'txt': #檢查如果是txt直接翻譯文字內容
        div = []
        with open(source, 'r', encoding='utf8') as txtFile:
            counter = 1
            for row in txtFile.read().splitlines(): #將每一行加入編號以避免機器人翻譯時漏掉某些段落
                div.append(str(counter)+'™'+row)
                counter += 1
            prompt = '\n'.join(div) 
        text = translateText(toLang, fromLang, prompt) #將文字交給Gemini翻譯
        result = text.splitlines()
        for i in range(len(result)):
            result[i] = result[i].split('™')[-1]
        with open(destination, 'w', encoding='utf8') as txtFile:
            txtFile.write('\n'.join(result))

    elif frmat == 'csv': #檢查如果是csv把檔案的文字部分翻譯完丟回檔案
        data = []
        div=[]
        with open(source, encoding='utf8') as csvFile:
            reader = csv.DictReader(csvFile)
            counter = 1
            for row in reader:
                div.append(str(counter)+'™'+row['text']) #將每一行加入編號以避免機器人翻譯時漏掉某些段落
                data.append([row['start'], row['end'], row['text']])
                counter += 1
            prompt = '\n'.join(div)
            text = translateText(toLang, fromLang, prompt) #將文字交給Gemini翻譯
        for i in range(len(data)):
            data[i][2] = text.splitlines()[i].split('™')[-1]
        cols = ["start", "end", "text"]
        df = pd.DataFrame(data, columns=cols)
        df.to_csv(destination, index=False, mode='w', encoding='utf8')
    elif frmat == 'srt': #檢查如果是srt同csv方式處理
        div = []
        with open(source, 'r', encoding='utf8') as srtFile:
            content = srtFile.read()
            srt_segments = srt.parse(content)
            srt_segments = list(srt_segments)
            for segment in srt_segments:
                div.append(str(segment.index)+'™'+segment.content) #將每一行加入編號以避免機器人翻譯時漏掉某些段落
            
            prompt = '\n'.join(div)
            text = translateText(toLang, fromLang, prompt) #將文字交給Gemini翻譯
            for segment in srt_segments:
                segment.content = text.splitlines()[int(segment.index)-1].split('™')[-1]
        contents = srt.compose(srt_segments)
        with open(destination, 'w', encoding='utf8') as srtFile:
            srtFile.write(contents)

class LanguageSelectionModal(discord.ui.Modal): #接收使用者的輸入
    def __init__(self, sourceFile:str, destination:str, fromLang:str): #傳入原始檔、輸出檔還有來源語言
        self.sourceFile = sourceFile
        self.destination = destination
        self.fromLang = fromLang
        super().__init__(title="請輸入你要翻譯成的語言") #避免覆蓋原始屬性
    language = discord.ui.TextInput(label='語言') #文字輸入框
    async def on_submit(self, interaction:discord.Interaction): #當使用者完成輸入後重新翻譯
        await interaction.response.defer()
        translateFile(self.sourceFile, self.destination, self.language.value, self.fromLang)
        await interaction.edit_original_response(attachments=[discord.File(self.destination)])

class RetranslationView(discord.ui.View): #按鈕
    def __init__(self, sourceFile:str, destination:str, fromLang:str, timeout:float | None=180): #傳入原始檔、輸出檔還有來源語言
        self.sourceFile = sourceFile
        self.destination = destination
        self.fromLang = fromLang
        super().__init__(timeout=timeout) #避免覆蓋原始屬性

    @discord.ui.button(label='重新翻譯這個文字檔', style=discord.ButtonStyle.blurple) #重新翻譯按鈕:當使用者按下後彈出文字輸入框
    async def retranslate(self, interaction:discord.Interaction, button:discord.ui.Button): 
        await interaction.response.send_modal(LanguageSelectionModal(self.sourceFile, self.destination, self.fromLang)) 

    @discord.ui.button(label='退出', style=discord.ButtonStyle.red) #退出按鈕:使用者按下後把按鈕禁用並刪檔
    async def quit(self, interaction:discord.Interaction, button:discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self) #更新原本的按鈕顯示
        if os.path.exists(self.sourceFile): #移除原始檔案
            os.remove(self.sourceFile)
        if os.path.exists(self.destination):
            os.remove(self.destination)
        if not os.listdir('./translate'):
            os.rmdir('translate')
        if not os.listdir('./result'):
            os.rmdir('result')

    async def on_timeout(self): #當超過3分鐘沒收到回應自動刪檔
        for item in self.children:
            item.disabled = True
        
        await self.response.edit(view=self)
        if os.path.exists(self.sourceFile):
            os.remove(self.sourceFile)
        if os.path.exists(self.destination):
            os.remove(self.destination)
        if not os.listdir('./translate'):
            os.rmdir('translate')
        if not os.listdir('./result'):
            os.rmdir('result')            

class TranslateFile(Cog_extension):
    @app_commands.command(description='翻譯指定訊息的文字檔')
    @app_commands.describe(url='你要進行翻譯的文字檔所在訊息連結', target='你要翻譯成的語言', source='文字檔原本語言')
    async def translate(self, interaction:discord.Interaction, url:str, target:str, source:str=None):
        await interaction.response.send_message("請稍等一下...")
        if not os.path.exists('translate'): #產生存放文字檔的資料夾
            os.makedirs('translate')
        if not os.path.exists('result'): #產生存放文字檔的資料夾
            os.makedirs('result')
        message_id = int(url.split('/')[-1])
        try:
            message = await interaction.channel.fetch_message(message_id) #找到目標訊息
            file = message.attachments[0] 
            sourceFile = f"./translate/{file.filename}"
            outputFile = f"./result/{file.filename}"
            await file.save(sourceFile) #下載文字檔
            frmat = file.filename.split('.')[-1]
            translateFile(sourceFile, outputFile, target, source) #翻譯文字檔
            view = RetranslationView(sourceFile, outputFile, source) #新增一群按鈕
            view.response = await interaction.edit_original_response(content=f"這是翻譯完的{frmat}檔案", attachments=[discord.File(outputFile)], view=view)
            #儲存原始訊息
            
        except Exception as e:
            print(f"翻譯時發生錯誤: {e}")
            await interaction.followup.send(f"翻譯時發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(TranslateFile(bot))
