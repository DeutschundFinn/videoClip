import discord
from discord import app_commands
from core.classes import Cog_extension
import os
from deep_translator import GoogleTranslator
import csv
import pandas as pd

class TranslateFile(Cog_extension):
    @app_commands.command(description='翻譯指定訊息的文字檔')
    @app_commands.describe(url='你要進行翻譯的文字檔所在訊息連結', target='你要翻譯成的語言', source='文字檔原本語言')
    async def translate(self, interaction:discord.Interaction, url:str, target:str, source:str='auto'):
        await interaction.response.send_message("請稍等一下...")
        if not os.path.exists('translate'): #產生存放文字檔的資料夾
            os.makedirs('translate')
        message_id = int(url.split('/')[-1])
        translator = GoogleTranslator(source=source, target=target)
        try:
            message = await interaction.channel.fetch_message(message_id)
            file = message.attachments[0]
            outputFile = f"./translate/{file.filename}"
            await file.save(outputFile)
            frmat = file.filename.split('.')[-1]
            if frmat == 'txt':
                text = translator.translate_file(outputFile)
                with open(outputFile, 'w', encoding='utf8') as txtFile:
                    txtFile.write(text)
            elif frmat == 'csv':
                data = []
                with open(outputFile, encoding='utf8') as csvFile:
                    reader = csv.DictReader(csvFile)
                    for row in reader:
                        data.append([row['start'], row['end'], translator.translate(row['text'])])
                cols = ["start", "end", "text"]
                df = pd.DataFrame(data, columns=cols)
                df.to_csv(outputFile, index=False, mode='w', encoding='utf8')
            elif frmat == 'srt':
                texts = []
                with open(outputFile, 'r', encoding='utf8') as srtFile:
                    texts = srtFile.read().splitlines()
                    for i in range(len(texts)):
                        if i%4 == 2:
                            texts[i] = translator.translate(texts[i])
                
                with open(outputFile, 'w', encoding='utf8') as srtFile:
                    srtFile.write('\n'.join(texts))
            
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