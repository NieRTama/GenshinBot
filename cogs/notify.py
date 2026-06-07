import asyncio
import datetime
import json
import logging
import os
import re

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

log = logging.getLogger(__name__)

WIKI_URL = "https://wikiwiki.jp/genshinwiki/%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%E4%B8%80%E8%A6%A7"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")

NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID", "0"))

DATE_FMT = "%Y/%m/%d %H:%M"
PERIOD_RE = re.compile(
    r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})\s*[~〜]\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})"
)


def _load_events() -> dict:
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_events(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _fetch_events() -> list:
    """wikiwikiから開催中イベント（期間限定）を取得する"""
    try:
        res = requests.get(WIKI_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
        res.encoding = "utf-8"
    except requests.RequestException as e:
        log.error("イベントページ取得失敗: %s", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    # 「開催中イベント（期間限定）」セクションを探す
    target = None
    for tag in soup.find_all(["h2", "h3", "h4", "h5", "span", "div"]):
        text = tag.get_text(strip=True)
        if "開催中イベント" in text and "期間限定" in text:
            target = tag
            break

    # セクション以降にあるテーブルを収集（次の同レベル見出しまで）
    if target:
        tables = []
        for sibling in target.find_next_siblings():
            if sibling.name in ["h2", "h3", "h4", "h5"]:
                break
            if sibling.name == "table":
                tables.append(sibling)
            tables.extend(sibling.find_all("table"))
    else:
        log.warning("「開催中イベント（期間限定）」セクションが見つかりません。全テーブルを検索します。")
        tables = soup.find_all("table")

    events = []
    seen_names = set()

    for table in tables:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            cell_texts = [c.get_text(strip=True) for c in cells]
            row_text = " ".join(cell_texts)

            match = PERIOD_RE.search(row_text)
            if not match:
                continue

            start_str = match.group(1).strip()
            end_str = match.group(2).strip()

            # イベント名: リンクテキストを優先、なければ最長セルテキスト
            name = ""
            for cell in cells:
                link = cell.find("a")
                if link:
                    candidate = link.get_text(strip=True)
                    if candidate and len(candidate) > 1:
                        name = candidate
                        break

            if not name:
                for text in cell_texts:
                    if PERIOD_RE.search(text):
                        continue
                    if len(text) > len(name):
                        name = text

            if not name or name in seen_names:
                continue

            try:
                datetime.datetime.strptime(start_str, DATE_FMT)
                datetime.datetime.strptime(end_str, DATE_FMT)
            except ValueError:
                continue

            seen_names.add(name)
            events.append({"name": name, "start": start_str, "end": end_str})

    log.info("%d 件のイベントを検出: %s", len(events), [e["name"] for e in events])
    return events


class NotifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.event_check.start()
        self.monthly_task.start()

    def cog_unload(self):
        self.event_check.cancel()
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
            events = _load_events()

            if now.weekday() == 0:
                await message.channel.send("週ボスあり。")

            active = [
                ev for ev in events.values()
                if datetime.datetime.strptime(ev["start"], DATE_FMT) <= now
                <= datetime.datetime.strptime(ev["end"], DATE_FMT)
            ]
            for ev in active:
                await message.channel.send(
                    f'イベントあり：**{ev["name"]}**（〜{ev["end"]}）'
                )
        except Exception as e:
            log.error("on_messageエラー: %s", e)

    # -------------------------------------------------------
    # イベント自動チェック（3時間ごと）
    # -------------------------------------------------------
    @tasks.loop(hours=3)
    async def event_check(self):
        if NOTIFY_CHANNEL_ID == 0:
            return

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel is None:
            return

        now = datetime.datetime.now()
        events = _load_events()
        fetched = await asyncio.to_thread(_fetch_events)
        changed = False

        # 期限切れイベントを削除
        expired = [
            name for name, ev in events.items()
            if datetime.datetime.strptime(ev["end"], DATE_FMT) < now
        ]
        for name in expired:
            del events[name]
            changed = True
            log.info("イベント終了・削除: %s", name)

        # 新規イベントを追加・通知
        for ev in fetched:
            name = ev["name"]
            if name in events:
                continue

            events[name] = {
                "name": name,
                "start": ev["start"],
                "end": ev["end"],
                "notified_3days": False,
            }
            changed = True

            embed = discord.Embed(
                title="🎉 新しいイベントが始まりました！",
                color=discord.Color.green(),
            )
            embed.add_field(name="イベント名", value=name, inline=False)
            embed.add_field(name="開催期間", value=f"{ev['start']} 〜 {ev['end']}", inline=False)
            await channel.send(embed=embed)
            log.info("新規イベント通知: %s", name)

        # 終了3日前通知
        for name, ev in events.items():
            if ev.get("notified_3days"):
                continue
            end_dt = datetime.datetime.strptime(ev["end"], DATE_FMT)
            days_left = (end_dt - now).total_seconds() / 86400
            if 0 <= days_left <= 3:
                embed = discord.Embed(
                    title="⏰ イベント終了3日前です",
                    color=discord.Color.orange(),
                )
                embed.add_field(name="イベント名", value=name, inline=False)
                embed.add_field(name="終了日時", value=ev["end"], inline=False)
                await channel.send(embed=embed)
                events[name]["notified_3days"] = True
                changed = True
                log.info("3日前通知: %s", name)

        if changed:
            _save_events(events)

    @event_check.before_loop
    async def before_event_check(self):
        await self.bot.wait_until_ready()

    # -------------------------------------------------------
    # 月次リマインダー（毎日21時）
    # -------------------------------------------------------
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
