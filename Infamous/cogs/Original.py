import asyncio
import logging
import random
import os
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
    @commands.cooldown(1, 1500, commands.BucketType.user)
    @commands.guild_only()
    async def annoy(self, ctx, user: discord.Member, *, string=None):
        """Annoys a specific person"""
        if not string:
            if ctx.message.attachments:
                string = ctx.message.attachments[0].url
            else:
                return await ctx.send("Provide an attachment or message.")

        if string:
            if ctx.message.attachments:
                string = f"{string} \n{ctx.message.attachments[0].url}"
            else:
                pass

        timer = 1500
        active = True
        while active:
            timer -= 300
            try:
                await user.send(f"Congratulations :tada: You have been chosen by {str(ctx.author)}"
                                f" to be annoyed with this message every five minutes: {string}")
            except discord.Forbidden:
                return await ctx.send("It appears I have been blocked or the user has disabled DMs.")
            await asyncio.sleep(300)

            if timer == 0:
                active = False

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

    # Similar to Chr1s's cleverbot bot conversation except it allows multiple people.
    @commands.command()
    async def chat(self, ctx):
        """Talk to a cleverbot AI"""
        await ctx.send("You are engaged in conversation with the bot. "
                       "Anybody can join the conversation by typing `let me join`. To stop chatting type `stop`")
        active = True
        participants = [ctx.author]
        while active:
            def check(m):
                if m.author.bot:
                    return False
                if m.channel == ctx.channel:
                    return True
            try:
                text = await ctx.bot.wait_for('message', check=check, timeout=20)
            except asyncio.TimeoutError:
                await ctx.send("I guess you don't want to talk to me anymore :cry:")
                active = False
            else:
                if text.content == "stop":
                    await ctx.send("Stopping the conversation.")
                    active = False

                elif text.content.lower() == "let me join":
                    participants.append(text.author)
                elif text.author not in participants:
                    pass
                else:
                    if not (3 <= len(text.content) <= 60):
                        await ctx.send("Text must be longer than 3 chars and shorter than 60.")
                    else:
                        payload = {"text": text.content}
                        async with ctx.channel.typing(), ctx.bot.session.post("https://public-api.travitia.xyz/talk",
                                                                              json=payload,
                                                                              headers={
                                                                                  "authorization":
                                                                                      os.getenv("APIKEY")}) as req:
                            resp = await req.json()
                            await ctx.send(f"{text.author.mention} {resp['response']}")
                                           
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
