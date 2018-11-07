import datetime
from functools import partial
from io import BytesIO

from typing import Union

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands


class Imagem:
    """Like Photoshop, but easier."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)

    async def get_avatar(self, user: Union[discord.User, discord.Member]) -> bytes:
        avatar_url = user.avatar_url_as(format="png")

        async with self.session.get(avatar_url) as response:
            avatar_bytes = await response.read()

        return avatar_bytes

    @staticmethod
    def processing(avatar_bytes: bytes, colour: tuple) -> BytesIO:
        with Image.open(BytesIO(avatar_bytes)) as im:
            with Image.new("RGB", im.size, colour) as background:
                rgb_avatar = im.convert("RGB")
                with Image.new("L", im.size, 0) as mask:
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([(0, 0), im.size], fill=255)
                    background.paste(rgb_avatar, (0, 0), mask=mask)

                final_buffer = BytesIO()
                background.save(final_buffer, "png")

        final_buffer.seek(0)

        return final_buffer

    @commands.command()
    async def circle(self, ctx, *, member: discord.Member = None):
        """Display the user's avatar on their colour."""

        member = member or ctx.author

        async with ctx.typing():
            if isinstance(member, discord.Member):
                member_colour = member.colour.to_rgb()
            else:
                member_colour = (0, 0, 0)

            avatar_bytes = await self.get_avatar(member)
            fn = partial(self.processing, avatar_bytes, member_colour)
            final_buffer = await self.bot.loop.run_in_executor(None, fn)
            file = discord.File(filename="circle.png", fp=final_buffer)
            await ctx.send(file=file)

    @commands.command()
    async def scape(self, ctx, *, text):
        """Make ScapeX say anything you want."""

        await ctx.message.delete()

        if len(text) >= 75:
            return await ctx.send("75 characters only.")

        text_ = (83, 45)
        timestamp = (166, 26)
        time_ = datetime.datetime.now()
        time_ = time_.strftime("%-I:%M %p")
        font = ImageFont.truetype("fonts/whitney-book.otf", int(16.5))
        font2 = ImageFont.truetype("fonts/whitney-light.otf", 11)
        async with ctx.typing():
            def write():
                i = Image.open("Infamous/img/scapexcutout.png")
                draw = ImageDraw.Draw(i)
                draw.text(text_, text, fill='white', font=font)
                draw.text(timestamp, f"Today at {time_}", fill=(111, 115, 120), font=font2)
                b = BytesIO()
                b.seek(0)
                i.save(b, "png")
                return b.getvalue()

            fp = await self.bot.loop.run_in_executor(None, write)
            file = discord.File(filename="scape.png", fp=fp)
            await ctx.send(file=file)

    @commands.command()
    async def drake(self, ctx, user1: discord.Member, user2: discord.Member):
        async with self.session.get(user1.avatar_url_as(format="png", size=512)) as r:
            av1 = await r.read()

        async with self.session.get(user2.avatar_url_as(format="png", size=512)) as r:
            av2 = await r.read()

        async with ctx.typing():
            def draw():
                user1_av = Image.open(BytesIO(av1)).resize((371, 369)).convert("RGBA")
                user2_av = Image.open(BytesIO(av2)).resize((371, 349)).convert("RGBA")

                image = Image.open("Infamous/img/drake.jpg")
                image.paste(user1_av, (346, 0))
                image.paste(user2_av, (346, 368))
                b = BytesIO()
                b.seek(0)
                image.save(b, "png")
                return b.getvalue()

        fp = await self.bot.loop.run_in_executor(None, draw)
        file = discord.File(filename="drake.png", fp=fp)
        await ctx.send(file=file)


def setup(bot: commands.Bot):
    bot.add_cog(Imagem(bot))

