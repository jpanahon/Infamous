import datetime
from functools import partial
from io import BytesIO

from typing import Union
import parawrap
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands


class Imagem(commands.Cog, name="Image Manipulation"):
    """Commands that edit images."""

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

    @commands.command(hidden=True)
    async def scape(self, ctx, *, text):
        """Make ScapeX say anything you want."""

        await ctx.message.delete()

        if len(text) >= 75:
            return await ctx.send("75 characters only.")

        text_ = (83, 45)
        timestamp = (166, 26)
        time_ = datetime.datetime.now()
        time_ = time_.strftime("%-I:%M %p")
        font = ImageFont.truetype("Infamous/fonts/whitney-book.otf", int(16.5))
        font2 = ImageFont.truetype("Infamous/fonts/whitney-light.otf", 11)
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
        """Compare two members using Drake."""

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

    @commands.command(aliases=['brain'])
    async def mind(self, ctx, text1: str, text2: str, text3: str):
        """Mind blown"""

        if len(text1 or text2 or text3) > 50:
            return await ctx.send("50 chars on each!")

        text1_pos = (65, 76)
        text2_pos = (65, 462)
        text3_pos = (65, 869)
        text1_ = parawrap.wrap(text1, 10)
        text2_ = parawrap.wrap(text2, 10)
        text3_ = parawrap.wrap(text3, 10)
        async with ctx.typing():
            def write():
                font = ImageFont.truetype("Infamous/fonts/Arial.ttf", 72)
                image = Image.open("Infamous/img/highermind.jpg")
                draw = ImageDraw.Draw(image)
                draw.text(text1_pos, '\n'.join(text1_), fill='black', font=font)
                draw.text(text2_pos, '\n'.join(text2_), fill='black', font=font)
                draw.text(text3_pos, '\n'.join(text3_), fill='black', font=font)
                b = BytesIO()
                b.seek(0)
                image.save(b, "png")
                return b.getvalue()

        fp = await self.bot.loop.run_in_executor(None, write)
        file = discord.File(filename="mind.png", fp=fp)
        await ctx.send(file=file)

    @commands.command()
    async def gon(self, ctx, text: str, user: discord.Member = None):
        """Replaces a nonagon with a user's avatar and changes the name of it"""
        user = user or ctx.author
        async with self.session.get(user.avatar_url_as(size=512)) as r:
            av = await r.read()

        text_pos = (633, 974)
        font = ImageFont.truetype("Infamous/fonts/Arial.ttf", 48)
        async with ctx.typing():
            def draw_():
                avatar = Image.open(BytesIO(av)).resize((414, 414)).convert("RGBA")
                image = Image.open("Infamous/img/gon.jpg")
                draw = ImageDraw.Draw(image)
                draw.text(text_pos, text + "gon", fill='black', font=font)
                image.paste(avatar, (601, 547))
                b = BytesIO()
                b.seek(0)
                image.save(b, "png")
                return b.getvalue()

        fp = await self.bot.loop.run_in_executor(None, draw_)
        file = discord.File(filename="gon.png", fp=fp)
        await ctx.send(file=file)

    @commands.command()
    async def blurple(self, ctx, user: discord.Member = None):
        """Turns your/other people's avatars blurple"""

        if not user:
            user = ctx.author

        async with self.session.get(user.avatar_url_as(size=1024)) as r_:
            avatar = await r_.read()

        async with ctx.typing():
            def blurplify():
                im = Image.open(BytesIO(avatar))
                im = im.convert('RGBA')
                size = im.size

                colors = [(255, 255, 255), (114, 137, 218), (78, 93, 148)]
                thresholds = [m * 255 / len(colors) for m in range(1, len(colors) + 1)]

                for x in range(size[0]):
                    for y in range(size[1]):
                        r, g, b, a = im.getpixel((x, y))
                        gval = 0.299 * r + 0.587 * g + 0.114 * b

                        for t in list(enumerate(thresholds))[::-1]:
                            lower = thresholds[t[0] - 1] if t[0] - 1 >= 0 else -1
                            if lower < gval <= thresholds[t[0]]:
                                px = colors[list(enumerate(thresholds))[::-1][t[0]][0]]
                                im.putpixel((x, y), (px[0], px[1], px[2], a))

                b = BytesIO()
                b.seek(0)
                im.save(b, "png")
                return b.getvalue()

            fp = await self.bot.loop.run_in_executor(None, blurplify)
            file = discord.File(filename="blurple.png", fp=fp)
            await ctx.send(file=file)


def setup(bot: commands.Bot):
    bot.add_cog(Imagem(bot))
