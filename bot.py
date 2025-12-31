import discord
from discord.ext import commands
from discord import app_commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- 設定區 ---
STAFF_ROLE_ID = 1439344370456199409  # 員工身分組 ID
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# --- Google Sheets 連線函式 ---
def login_google_sheets():
    # 優先嘗試環境變數 (雲端部署用)
    google_creds_json = os.getenv("GOOGLE_SHEETS_CREDS")
    if google_creds_json:
        try:
            creds_dict = json.loads(google_creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
            client = gspread.authorize(creds)
            print("✅ 已透過環境變數連線至試算表")
            return client.open("⋆.𐙚 ̊.小祈雜貨商ᯓᡣ𐭩").worksheet("職位")
        except Exception as e:
            print(f"❌ 環境變數憑證解析失敗：{e}")

    # 嘗試讀取本地檔案 (本地測試用)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0392096505-099bca696737.json", SCOPE)
        client = gspread.authorize(creds)
        print("✅ 已透過本地 JSON 檔案連線")
        return client.open("⋆.𐙚 ̊.小祈雜貨商ᯓᡣ𐭩").worksheet("職位")
    except Exception as e:
        print(f"❌ 找不到憑證檔案或連線失敗：{e}")
        return None

sheet = login_google_sheets()

# --- 權限檢查器 ---
def is_staff_or_admin():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        has_role = any(role.id == STAFF_ROLE_ID for role in interaction.user.roles)
        if not has_role:
            raise app_commands.MissingAnyRole([STAFF_ROLE_ID])
        return True
    return app_commands.check(predicate)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ 斜線指令同步完成")

bot = MyBot()

# --- 統一寫入邏輯 ---
async def update_sheet_record(interaction: discord.Interaction, name: str, item_label: str):
    if not sheet:
        await interaction.response.send_message("❌ 機器人目前未連線至試算表。", ephemeral=True)
        return
        
    await interaction.response.defer() 
    try:
        header_row = sheet.row_values(2) # 標題在第二行
        names_col = sheet.col_values(1)   # 名字在第一欄

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
        await interaction.followup.send(f"❌ 執行錯誤：{e}")

# --- 指令區塊 ---

@bot.tree.command(name="送心員", description="登記送心員記錄")
@is_staff_or_admin()
async def send_heart_member(interaction: discord.Interaction, 名字: str):
    await update_sheet_record(interaction, 名字, "送心員")

@bot.tree.command(name="代", description="登記代他人項目 (藍色區塊)")
@is_staff_or_admin()
@app_commands.choices(項目=[
    app_commands.Choice(name="燭火", value="燭火"),
    app_commands.Choice(name="任務", value="任務"),
    app_commands.Choice(name="獻祭", value="獻祭"),
    app_commands.Choice(name="金人", value="金人"),
    app_commands.Choice(name="開圖", value="開圖"),
    app_commands.Choice(name="票卷", value="票卷"),
    app_commands.Choice(name="試煉", value="試煉"),
    app_commands.Choice(name="先祖", value="先祖"),
    app_commands.Choice(name="掛火", value="掛火"),
    app_commands.Choice(name="紅石", value="紅石"),
    app_commands.Choice(name="季節節點", value="季節節點"),
    app_commands.Choice(name="代登", value="代登"),
])
async def dai_others(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="帶人", description="登記帶人項目 (綠色區塊)")
@is_staff_or_admin()
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

@bot.tree.command(name="陪玩", description="登記陪玩項目 (粉色區塊)")
@is_staff_or_admin()
@app_commands.choices(項目=[
    app_commands.Choice(name="陪玩", value="陪玩"),
    app_commands.Choice(name="陪跑", value="陪跑"),
    app_commands.Choice(name="陪掛", value="陪掛"),
    app_commands.Choice(name="樹洞", value="樹洞"),
])
async def playing_with(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="三戀", description="登記三戀項目 (紅色區塊)")
@is_staff_or_admin()
@app_commands.choices(項目=[
    app_commands.Choice(name="虛戀", value="虛戀"),
    app_commands.Choice(name="病戀", value="病戀"),
    app_commands.Choice(name="虐戀", value="虐戀"),
])
async def triple_love(interaction: discord.Interaction, 名字: str, 項目: str):
    await update_sheet_record(interaction, 名字, 項目)

@bot.tree.command(name="刪除", description="清除記錄，若該行全空則自動刪除行")
@is_staff_or_admin()
async def delete_record(interaction: discord.Interaction, 名字: str, 項目名稱: str):
    if not sheet: return
    await interaction.response.defer()
    try:
        header_row = sheet.row_values(2)
        names_col = sheet.col_values(1)

        if 名字 not in names_col or 項目名稱 not in header_row:
            await interaction.followup.send(f"❌ 找不到玩家 `{名字}` 或項目 `{項目名稱}`")
            return

        row_idx = names_col.index(名字) + 1
        col_idx = header_row.index(項目名稱) + 1
        
        # 清除儲存格
        sheet.update_cell(row_idx, col_idx, "")
        
        # 檢查該行是否還有其他 1 (跳過第一格名字)
        current_row = sheet.row_values(row_idx)
        has_data = any(val.strip() != "" for val in current_row[1:])
        
        msg = f"✅ 已清除 **{名字}** 的 **{項目名稱}** 記錄。"
        if not has_data:
            sheet.delete_rows(row_idx)
            msg += "\n♻️ 該行已無其他資料，自動刪除行。"
            
        await interaction.followup.send(msg)
    except Exception as e:
        await interaction.followup.send(f"❌ 刪除失敗：{e}")

# --- 錯誤處理 ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message("❌ 你不具備員工身分組，無法登記資料！", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ 需要管理者權限才能執行此操作。", ephemeral=True)
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"⚠️ 系統錯誤：{error}", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
