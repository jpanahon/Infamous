import asyncio
import logging
import random
import discord
from discord.ext import commands
from .utils import checks
from PIL import Image
from io import BytesIO

logging.basicConfig(level=logging.INFO)


class Original:
    """Fun commands that were made with an original concept."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Annoy
    @commands.command()
    @commands.cooldown(2, 600, commands.BucketType.user)
    @commands.guild_only()
    async def annoy(self, ctx, *, string):
        """Direct Messages a random person, with the message of choice."""

        user = random.choice([x for x in ctx.guild.members if not x.bot])

        try:
            embed = discord.Embed(
                title="Sent in PM",
                description=f'{string}',
                color=0xba1c1c,

            )

            if ctx.message.attachments:
                image = ' '.join(m.url for m in ctx.message.attachments)
                embed.set_image(url=image)
                await user.send(f"{string}\n{image}")

            embed.set_author(name=user, icon_url=user.avatar_url)
            embed.set_footer(
                text=f'Sent by {ctx.author}',
                icon_url=ctx.author.avatar_url
            )
            await ctx.send(embed=embed)
            await user.send(string)
        except discord.Forbidden:
            pass

    # Random Nickname
    @commands.command()
    @commands.cooldown(2, 600, commands.BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx, *, string):
        """Set's the nick of a random person, with nick of choice."""

        user = random.choice([x for x in ctx.guild.members if not x.bot])
        try:
            await user.edit(nick=string)
            embed = discord.Embed(
                title="Changed/Set Nickname",
                description=f"{string}",
                color=0xba1c1c,

            )
            embed.set_author(name=user, icon_url=user.avatar_url)
            embed.set_footer(text=f'Sent by {ctx.author}')
            await ctx.send(embed=embed)
        except discord.Forbidden:
            pass

        await asyncio.sleep(600)
        await user.edit(nick=None)

    @commands.command()
    @commands.guild_only()
    async def guess(self, ctx):
        """Guess who this person is."""

        user1 = [x for x in ctx.guild.members if not x.bot]
        user = random.choice(user1)
        discrim = str(user).split(user.name)
        discrim = ''.join(discrim)

        if not user.avatar:
            user = random.choice(user1)
            discrim = str(user).split(user.name)
            discrim = ''.join(discrim)

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name='Can you guess who this is?')
        embed.description = f'Their discriminant is `{discrim}`'
        embed.set_image(
            url=user.avatar_url_as(format='png', size=1024)
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.content == user.name \
                   or m.content == user.display_name \
                   and m.channel == ctx.message.channel

        try:
            member = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The user was `{user}`")
        else:
            await ctx.send(f'{member.author.mention} is right! This user is `{user}`')
            command = self.bot.get_command('guess')
            await ctx.invoke(command)

    @commands.command()
    async def ask(self, ctx, *, text):
        if not (3 <= len(text) <= 60):
            return await ctx.send("Text must be longer than 3 chars and shorter than 60.")
        payload = {"text": text}
        async with ctx.channel.typing(), ctx.bot.session.post("https://public-api.travitia.xyz/talk", json=payload,
                                                              headers={"authorization": "&KP6Y0%YCx'C?wK4O9q9"}) as req:
            resp = await req.json()
            await ctx.send(f"{ctx.author.mention} {resp['response']}")

    @commands.command()
    @checks.in_fame()
    async def emoji(self, ctx, text=None):
        if not text or not text.startswith("http"):
            if ctx.message.attachments:
                text = ctx.message.attachments[0].url
            else:
                return await ctx.send("Provide an attachment or image url")

        if text:
            async with ctx.bot.session.get(text) as r:
                image = await r.read()

        await ctx.send("What is the name of the emoji?")

        def emoji_name(m):
            if m.author == ctx.author:
                return True
            if len(m.content) < 20:
                return False

        try:
            msg = (await ctx.bot.wait_for('message', check=emoji_name, timeout=20)).content.capitalize()
        except asyncio.TimeoutError:
            await ctx.send("You ran out of time!")
        else:
            channel = ctx.bot.get_channel(270907435999297557)
            react = await channel.send(embed=discord.Embed(color=0xba1c1c)
                                       .set_author(name=f":{msg}:")
                                       .set_image(url=text)
                                       .set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
                                       )

            await react.add_reaction("\N{OK HAND SIGN}")

            def emo(reaction, user):
                if user.bot:
                    return False

                if str(reaction.emoji) == "\N{OK HAND SIGN}":
                    return True

            await ctx.bot.wait_for('reaction_add', check=emo)
            try:
                await react.remove_reaction("\N{OK HAND SIGN}", ctx.bot.user)
            except discord.Forbidden:
                pass

            active = True
            while active:
                react = await channel.get_message(react.id)
                if react.reactions[0].count >= 3:
                    def create():
                        i_ = Image.open(BytesIO(image)).resize((128, 128)).convert("RGBA")
                        b = BytesIO()
                        b.seek(0)
                        i_.save(b, "png")
                        return b.getvalue()

                    fp = await ctx.bot.loop.run_in_executor(None, create)
                    try:
                        await ctx.guild.create_custom_emoji(name=msg, image=fp,
                                                            reason="Automatically added from suggestion")
                        msg = [str(x) for x in ctx.guild.emojis if x.name == msg]
                        await channel.send(f"{msg[0]} has been added!")
                        active = False
                    except discord.Forbidden:
                        await ctx.send("There are no more slots or the file is too big.")
                        active = False


def setup(bot):
    bot.add_cog(Original(bot))
