import discord
from discord.ext import commands
from discord import app_commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- Google Sheets 設定 ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def login_google_sheets():
    # 優先嘗試從環境變數讀取 (雲端用)
    google_creds_json = os.getenv("GOOGLE_SHEETS_CREDS")
    
    if google_creds_json:
        try:
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            print("✅ 已透過環境變數成功連線至試算表")
            return client.open("⋆.𐙚 ̊.小祈雜貨商ᯓᡣ𐭩").worksheet("職位")
        except Exception as e:
            print(f"❌ 環境變數憑證解析失敗：{e}")

    # 若無環境變數，則嘗試讀取本地檔案 (本地測試用)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0392096505-099bca696737.json", scope)
        client = gspread.authorize(creds)
        print("✅ 已透過本地 JSON 檔案連線")
        return client.open("⋆.𐙚 ̊.小祈雜貨商ᯓᡣ𐭩").worksheet("職位")
    except Exception as e:
        print(f"❌ 找不到本地憑證檔案：{e}")
        return None

# 初始化試算表分頁
sheet = login_google_sheets()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ 斜線指令同步完成")

bot = MyBot()

# --- 統一處理邏輯 ---
async def update_sheet_record(interaction: discord.Interaction, name: str, item_label: str):
    await interaction.response.defer() 
    try:
        header_row = sheet.row_values(2)
        names_col = sheet.col_values(1)

        if item_label not in header_row:
            await interaction.followup.send(f"❌ 試算表找不到項目：`{item_label}`")
            return

        col_idx = header_row.index(item_label) + 1

        if name in names_col:
            row_idx = names_col.index(name) + 1
            sheet.update_cell(row_idx, col_idx, 1)
            status = f"更新了 **{name}** 的記錄"
        else:
            new_row = [""] * len(header_row)
            new_row[0] = name
            new_row[col_idx - 1] = 1
            sheet.append_row(new_row)
            status = f"新增了 **{name}** 的新行"

        await interaction.followup.send(f"✅ **{status}**\n📍 項目：`{item_label}`")
    except Exception as e:
        await interaction.followup.send(f"❌ 錯誤：{e}")

# --- 指令區塊 (代、帶人、陪玩、三戀) ---
# --- 送心員指令 (新增指令) ---
# 對應你圖片中的 B 欄「送心員」
@bot.tree.command(name="送心員", description="登記送心員記錄 (B欄)")
async def send_heart_member(interaction: discord.Interaction, 名字: str):
    # 這裡的 item_label 必須跟試算表 B2 儲存格的文字完全一樣
    # 根據圖片，B2 應該是「送心員」
    await update_sheet_record(interaction, 名字, "送心員")
# --- 代他人指令 (更新版：新增代登選項) ---
@bot.tree.command(name="代", description="登記代他人相關項目 (藍色區塊)")
@app_commands.choices(項目=[
    app_commands.Choice(name="燭火", value="燭火"),
    app_commands.Choice(name="任務", value="任務"),
    app_commands.Choice(name="獻祭", value="獻祭"),
    app_commands.Choice(name="開圖", value="開圖"),
    app_commands.Choice(name="票卷", value="票卷"),
    app_commands.Choice(name="代登", value="代登"),  # 新增選項
])
async def dai_others(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="帶人", description="登記帶人相關項目 (綠色區塊)")
@app_commands.choices(項目=[
    app_commands.Choice(name="帶火", value="帶火"),
    app_commands.Choice(name="帶任", value="帶任"),
    app_commands.Choice(name="帶獻", value="帶獻"),
    app_commands.Choice(name="帶開", value="帶開"),
    app_commands.Choice(name="帶金", value="帶金"),
    app_commands.Choice(name="帶票", value="帶票"),
])
async def carry_others(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="陪玩", description="登記陪玩相關項目 (粉色區塊)")
@app_commands.choices(項目=[
    app_commands.Choice(name="陪玩", value="陪玩"),
    app_commands.Choice(name="陪跑", value="陪跑"),
    app_commands.Choice(name="陪掛", value="陪掛"),
    app_commands.Choice(name="樹洞", value="樹洞"),
])
async def playing_with(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="三戀", description="登記三戀相關項目 (紅色區塊)")
@app_commands.choices(項目=[
    app_commands.Choice(name="虛戀", value="虛戀"),
    app_commands.Choice(name="病戀", value="病戀"),
    app_commands.Choice(name="虐戀", value="虐戀"),
])
async def triple_love(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)
# --- 6. 刪除記錄指令 ---
@bot.tree.command(name="刪除", description="清除特定玩家在某個項目的 1 (例如：名字, 帶火)")
@app_commands.describe(名字="要刪除記錄的人名", 項目名稱="請輸入要清除的完整項目名 (例如：燭火、帶火、陪玩)")
async def delete_record(interaction: discord.Interaction, 名字: str, 項目名稱: str):
    await interaction.response.defer()
    try:
        # 1. 取得標題列與名字列
        header_row = sheet.row_values(2)
        names_col = sheet.col_values(1)

        # 2. 檢查名字是否存在
        if 名字 not in names_col:
            await interaction.followup.send(f"❌ 找不到玩家：`{名字}`，請檢查名字是否正確。")
            return

        # 3. 檢查項目是否存在
        if 項目名稱 not in header_row:
            await interaction.followup.send(f"❌ 試算表標題中找不到項目：`{項目名稱}`")
            return

        # 4. 定位座標
        row_idx = names_col.index(名字) + 1
        col_idx = header_row.index(項目名稱) + 1

        # 5. 清除該格內容 (設為空字串)
        sheet.update_cell(row_idx, col_idx, "")
        
        await interaction.followup.send(f"✅ 已成功清除記錄！\n👤 名字：`{名字}`\n🗑️ 項目：`{項目名稱}`")
        
    except Exception as e:
        await interaction.followup.send(f"❌ 刪除失敗，錯誤原因：{e}")

# 執行
token = os.getenv("DISCORD_TOKEN")
bot.run(token)