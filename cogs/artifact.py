import asyncio
import os
import tempfile

import discord
import pytesseract
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from utils.artifact_parser import extract_stats
from utils.score_calculator import calculate_score

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SLOT_ORDER = ["花", "羽", "時計", "杯", "冠", "不明"]


def detect_slot(text: str) -> str:
    if "砂" in text:
        return "時計"
    if "杯" in text:
        return "杯"
    if "冠" in text:
        return "冠"
    if "HP" in text:
        return "花"
    if "攻撃力" in text:
        return "羽"
    return "不明"


def get_total_rank(score: float) -> str:
    if score >= 220:
        return "SS"
    if score >= 200:
        return "S"
    if score >= 180:
        return "A"
    if score >= 150:
        return "B"
    return "C"


def _ocr_image(image_path: str) -> str:
    with Image.open(image_path) as img:
        return pytesseract.image_to_string(img, lang="jpn")


def _create_collage(artifact_results: list) -> str:
    if not artifact_results:
        raise ValueError("No artifacts to render")

    cols, rows = 3, 2
    canvas = Image.new("RGB", (cols * 300, rows * 340), (40, 40, 40))
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 24)
    except Exception:
        font = ImageFont.load_default()

    for idx, artifact in enumerate(artifact_results):
        try:
            with Image.open(artifact["path"]) as img:
                img.thumbnail((300, 300))
                x = (idx % cols) * 300
                y = (idx // cols) * 340
                canvas.paste(img, (x, y + 40))
                draw.text(
                    (x + 10, y + 5),
                    f"{artifact['slot']} ({artifact['score']:.1f})",
                    fill="white",
                    font=font,
                )
        except Exception as e:
            print(f"collage error: {e}")

    output_path = tempfile.mktemp(suffix=".png")
    canvas.save(output_path)
    return output_path


class ArtifactCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.processing_lock = asyncio.Lock()

    @app_commands.choices(
        mode=[
            app_commands.Choice(name="会心重視 (-cr)", value="cr"),
            app_commands.Choice(name="攻撃重視 (-a)", value="a"),
            app_commands.Choice(name="元素熟知重視 (-e)", value="e"),
            app_commands.Choice(name="元素チャージ重視 (-ch)", value="ch"),
            app_commands.Choice(name="防御重視 (-d)", value="d"),
        ]
    )
    @app_commands.command(name="score", description="聖遺物スコア計算（画像を1〜5枚添付）")
    async def score(
        self,
        interaction: discord.Interaction,
        image1: discord.Attachment,
        image2: discord.Attachment = None,
        image3: discord.Attachment = None,
        image4: discord.Attachment = None,
        image5: discord.Attachment = None,
        mode: app_commands.Choice[str] = None,
    ):
        async with self.processing_lock:
            await interaction.response.defer()
            selected_mode = mode.value if mode else "cr"
            images = [i for i in [image1, image2, image3, image4, image5] if i]
            artifact_results = []
            total_score = 0.0

            for attachment in images:
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        await attachment.save(tmp.name)
                        tmp_path = tmp.name

                    text = await asyncio.to_thread(_ocr_image, tmp_path)
                    stats = extract_stats(text)
                    score_value = calculate_score(stats, selected_mode)
                    slot = detect_slot(text)
                    total_score += score_value

                    artifact_results.append({
                        "slot": slot,
                        "score": score_value,
                        "stats": stats,
                        "path": tmp_path,
                    })
                except Exception as e:
                    print(f"[ERROR] image processing failed: {e}")

            artifact_results.sort(
                key=lambda x: SLOT_ORDER.index(x["slot"]) if x["slot"] in SLOT_ORDER else 999
            )

            embed = discord.Embed(title="⭐ 聖遺物総合評価", color=discord.Color.gold())
            embed.add_field(name="評価モード", value=selected_mode, inline=False)

            for result in artifact_results:
                s = result["stats"]
                embed.add_field(
                    name=f"{result['slot']} ({result['score']:.1f})",
                    value=(
                        f"会心率: {s.get('crit_rate', 0)}%\n"
                        f"会心ダメ: {s.get('crit_dmg', 0)}%\n"
                        f"攻撃%: {s.get('atk_pct', 0)}%\n"
                        f"防御%: {s.get('def_pct', 0)}%\n"
                        f"熟知: {s.get('elemental_mastery', 0)}\n"
                        f"チャージ: {s.get('energy_recharge', 0)}%"
                    ),
                    inline=True,
                )

            embed.add_field(name="総合スコア", value=f"**{total_score:.1f}**", inline=False)
            embed.add_field(name="総合ランク", value=get_total_rank(total_score), inline=False)

            collage_path = await asyncio.to_thread(_create_collage, artifact_results)
            file = discord.File(collage_path, filename="artifacts.png")
            embed.set_image(url="attachment://artifacts.png")

            await interaction.followup.send(embed=embed, file=file)

            for r in artifact_results:
                try:
                    if os.path.exists(r["path"]):
                        os.remove(r["path"])
                except Exception:
                    pass
            try:
                if os.path.exists(collage_path):
                    os.remove(collage_path)
            except Exception:
                pass

    @app_commands.command(name="ping", description="動作確認")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")


async def setup(bot: commands.Bot):
    await bot.add_cog(ArtifactCog(bot))
