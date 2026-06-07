import datetime
import json
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands, tasks

log = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EVENT_FILE = os.path.join(DATA_DIR, "event.json")

NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))


def _load_event() -> dict:
    if os.path.exists(EVENT_FILE):
        with open(EVENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_event(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


class NotifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.event_data = _load_event()
        self.monthly_task.start()

    def cog_unload(self):
        self.monthly_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if NOTIFY_CHANNEL_ID == 0 or message.channel.id != NOTIFY_CHANNEL_ID:
            return
        if not message.mention_everyone:
            return

        try:
            now = datetime.datetime.now()

            if now.weekday() == 0:
                await message.channel.send("週ボスあり。")

            if self.event_data:
                start = datetime.datetime.strptime(self.event_data["start"], "%Y/%m/%d").date()
                end = datetime.datetime.strptime(self.event_data["end"], "%Y/%m/%d").date()
                if start <= now.date() <= end:
                    await message.channel.send(
                        f'イベントあり（{start} ～ {end} {self.event_data["content"]}）'
                    )
        except Exception as e:
            log.error("on_messageエラー: %s", e)

    @app_commands.command(name="event", description="イベント期間を登録する")
    @app_commands.describe(
        start="開始日 (YYYY/MM/DD)",
        end="終了日 (YYYY/MM/DD)",
        content="イベント内容",
    )
    async def event(self, interaction: discord.Interaction, start: str, end: str, content: str):
        try:
            datetime.datetime.strptime(start, "%Y/%m/%d")
            datetime.datetime.strptime(end, "%Y/%m/%d")
        except ValueError:
            await interaction.response.send_message(
                "日付形式エラー。YYYY/MM/DD 形式で入力してください。", ephemeral=True
            )
            return

        data = {"start": start, "end": end, "content": content}
        _save_event(data)
        self.event_data = data
        await interaction.response.send_message(f"登録完了：{start} ～ {end}", ephemeral=True)

    @tasks.loop(minutes=1)
    async def monthly_task(self):
        if NOTIFY_CHANNEL_ID == 0:
            return

        now = datetime.datetime.now()
        if now.hour != 21 or now.minute != 0:
            return

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel is None:
            return

        try:
            if now.day == 14:
                await channel.send("螺旋の切替が近いです")
            elif now.day == 30:
                await channel.send("シアターの切替が近いです")
            elif now.day == 1:
                await channel.send("チケット交換可能")
        except Exception as e:
            log.error("通知エラー: %s", e)

    @monthly_task.before_loop
    async def before_monthly_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(NotifyCog(bot))
