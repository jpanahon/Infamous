import datetime
import logging
import random
from io import BytesIO
import discord
from PIL import Image
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


def _splice(s1, s2):
    return s1[:len(s1) // 2] + s2[len(s2) // 2:]


class Fun:
    """Fun commands to play with."""

    def __init__(self, bot):
        self.bot = bot

    # Random Quotes
    @commands.group(
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['random']
    )
    async def quotes(self, ctx):
        """Shows a random quote from the community."""

        quotes = await ctx.bot.db.fetchrow("SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 1")
        embed = discord.Embed(title="Some random quote",
                              color=0xba1c1c,
                              timestamp=datetime.datetime.utcnow()
                              )

        embed.set_image(url=quotes[0])
        await ctx.send(embed=embed)

    @quotes.command()
    async def insert(self, ctx, *, link):
        await ctx.bot.db.execute("INSERT INTO quotes VALUES($1)", link)
        await ctx.message.add_reaction(':FAXcheck:428160543975800833')

    # Questions
    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def question(self, ctx):
        """Asks community provided questions."""

        question = await ctx.bot.db.fetchrow("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
        embed = discord.Embed(title="Random Question",
                              description=question[0],
                              color=0xba1c1c)

        await ctx.send(embed=embed)

    @question.command()
    async def add(self, ctx, *, string):
        """Adds a question to the question pool."""

        await ctx.bot.db.execute("INSERT INTO questions VALUES($1)", string)
        await ctx.author.add_reaction('👌')

    # Ask a Question That Gets Answered by a Randomly Picked User
    @commands.command()
    async def roulette(self, ctx, *, string):
        """Answer a question with a randomly picked user."""

        embed = discord.Embed(title=f'Answer to "{string}"',
                              color=0xba1c1c,
                              timestamp=datetime.datetime.utcnow()
                              )
        roulette = random.choice([x for x in ctx.guild.members if not x.bot])
        embed.set_image(url=roulette.avatar_url_as(
            format='png',
            size=1024)
        )
        embed.description = roulette.display_name
        await ctx.send(embed=embed)

    # Random Gay Couple
    @commands.command(aliases=['homo'])
    @commands.guild_only()
    async def gay(self, ctx):
        """Shows a randomly picked "gay" couple from the server."""

        photo = random.choice(
            ['http://www2.pictures.zimbio.com/gi/Protestors+Take+Part+Group+Kiss+Outside+Pub+y3IUby_-eBVl.jpg',
             'http://favim.com/orig/201109/09/ahhhyeaaaah-boy-couple-gay-boy-love-kiss-gay-love-Favim.com-140725.jpg',
             'http://www.wehoville.com/wp-content/uploads/2014/03/FirstKiss6.png'
             ])

        gay = random.choice(
            [x for x in ctx.guild.members if not x.bot]
        )
        gay2 = random.choice(
            [x for x in ctx.guild.members if not x.bot]
        )
        embed = discord.Embed(title="Random Gay Couple",
                              description=f"<@{gay.id}> and <@{gay2.id}> have a gay/lesbian "
                                          f"relationship with each other.",
                              color=0xba1c1c)

        embed.set_image(url=photo)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def ship(self, ctx, user: discord.Member, member: discord.Member):
        """Puts the names of two members together."""

        ship = _splice(user.name, member.name)

        embed = discord.Embed(color=0xFFC0CB)
        embed.set_author(name="The ship has sailed")
        embed.description = ship

        async with self.bot.session.get(user.avatar_url) as r:
            user_av = await r.read()

        async with self.bot.session.get(member.avatar_url) as r:
            member_av = await r.read()

        async with ctx.typing():
            def pic():
                p1 = (162, 11)
                p2 = (288, 11)
                av1 = Image.open(
                    BytesIO(user_av)) \
                    .resize((64, 64)).convert("RGBA")

                av2 = Image.open(
                    BytesIO(member_av)) \
                    .resize((64, 64)).convert("RGBA")

                i = Image.open("img/shipthing.jpg")
                i.paste(av1, p1)
                i.paste(av2, p2)
                b = BytesIO()
                b.seek(0)
                i.save(b, "png")
                return b.getvalue()

            fp = await self.bot.loop.run_in_executor(None, pic)
            file = discord.File(filename="ship.png", fp=fp)
            embed.set_image(url="attachment://ship.png")
            await ctx.send(embed=embed, file=file)


def setup(bot):
    bot.add_cog(Fun(bot))
