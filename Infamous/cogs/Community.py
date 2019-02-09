import asyncio
import datetime
import logging
import parawrap
import aiohttp
import discord
from discord.ext import commands
from .utils.rpg_tools import yon


logging.basicConfig(level=logging.INFO)


class Wiki:
    def __init__(self, ctx, page, guild):
        self.bot = ctx.bot
        self.page = page
        self.guild = guild
        self.channel = ctx.channel
        self.db = ctx.db
        self.author = ctx.author
        self.input = ctx.input
        self.prefix = ctx.prefix
        self.context = ctx
        self.command = ctx.command
        self.colors = {"Blue": 0x0000FF, "Red": 0xFF0000,
                       "Orange": 0xFF7F00, "Yellow": 0xFFFF00,
                       "Green": 0x00FF00, "Violet": 0x8B00FF,
                       "Indigo": 0x8B00FF, "Black": 0x000000,
                       "White": 0xFFFFFF, "Pink": 0xffb6c1}

        self.fields = {"Image": self._image_check, "Quote": self._quote_check,
                       "About": self._about_check, "Color": self._color_check}

    async def check(self, page):
        async with self.db.acquire() as db:
            info = await db.fetchrow("SELECT * FROM wiki WHERE page=$1 AND guild=$2", page, self.guild.id)
        if not info:
            return False
        return True

    def _image_check(self, m):
        if not m.author or m.author.id != self.author.id:
            return False

        if m.channel != self.channel:
            return False

        if m.mentions:
            self.image = m.mentions[0].avatar_url
            return True

        elif m.content.endswith(('.png', '.jpg')):
            self.image = m.content
            return True
        elif m.attachments:
            return True

        return False

    def _about_check(self, m):
        if not m.author or m.author.id != self.author.id:
            return False
        if m.channel != self.channel:
            return False
        if len(m.content) > 50:
            return True
        return False

    def _quote_check(self, m):
        if not m.author or m.author.id != self.author.id:
            return False
        if m.channel != self.channel:
            return False
        if '"' in m.content:
            return True
        return False

    def _color_check(self, m):
        if not m.author or m.author.id != self.author.id:
            return False
        if m.channel != self.channel:
            return False
        if m.content.capitalize() in self.colors:
            return True
        return False

    def _edit_check(self, m):
        if not m.author or m.author.id != self.author.id:
            return False
        if m.channel != self.channel:
            return False
        if m.content.capitalize() in self.fields:
            return True
        return False

    def constructor(self, name, image, about, quote, color, contributors=None):
        embed = discord.Embed(color=self.colors[color])
        embed.set_author(name=name.capitalize(), icon_url=image)
        embed.set_thumbnail(url=image)
        embed.description = f"*{quote}*"
        embed.add_field(name="Favorite Color", value=color)
        embed.add_field(name="Contributors", value=contributors or 'None')
        embed.add_field(name="About", value='\n'.join(parawrap.wrap(about, 50)))
        return embed

    async def create(self):
        if await self.check(self.page) is False:
            await self.channel.send(f"This wiki will be called `{self.page}` and we don't have a picture of them.  "
                                    f"Can you give us a picture of them? You can mention them, send a link or send an "
                                    f"attachment.")
            try:
                msg = await self.input('message', check=self._image_check, timeout=300)
            except asyncio.TimeoutError:
                return await self.channel.send("You ran out of time.")

            if msg.attachments:
                self.image = msg.attachments[0].url

            await self.channel.send(f"So they look like this? {self.image} \n"
                                    f"Can you tell us about them? In 50 or more characters please.")

            try:
                about = (await self.input('message', check=self._about_check, timeout=300)).content
            except asyncio.TimeoutError:
                self.command.reset_cooldown(self.context)
                return await self.channel.send("You ran out of time.")

            await self.channel.send(f"Is this what you wanted? \n```ini\n{about}``` What is some of the things they "
                                    f"have said? Please encase them in **\" \"**")

            try:
                quote = (await self.input('message', check=self._quote_check, timeout=300)).content
            except asyncio.TimeoutError:
                self.command.reset_cooldown(self.context)
                return await self.channel.send("You ran out of time.")

            await self.channel.send(f"```ini\n{quote}``` Did they really say that? Anyways can you tell us what their "
                                    f"favorite color is? This is so that the page won't be dull. Type a color from "
                                    f"the rainbow.")

            try:
                color = (await self.input('message', check=self._color_check, timeout=300)).content.capitalize()
            except asyncio.TimeoutError:
                self.command.reset_cooldown(self.context)
                return await self.channel.send("You ran out of time.")

            await self.channel.send("Here's what we have so far. Type **Yes** or **No** to confirm and publish.",
                                    embed=self.constructor(self.page, self.image, about, quote, color))

            y = await yon(self.context)
            if y == "Yes":
                await self.channel.send("The wiki page has been created.")
                async with self.db.acquire() as db:
                    await db.execute("INSERT INTO wiki VALUES($1, $2, $3, $4, $5, $6, $7, $8)", self.page,
                                     self.guild.id, self.image, quote, about, color, self.author.id,
                                     datetime.datetime.utcnow())
                self.command.reset_cooldown(self.context)
            else:
                return await self.channel.send("I guess this isn't what you wanted.")
        else:
            return await self.channel.send(f"This page already exists. "
                                           f"You can access it via **{self.prefix}wiki {self.page}**.")

    async def retrieve(self):
        if await self.check(self.page) is True:
            async with self.db.acquire() as db:
                info = await db.fetchrow("SELECT * FROM wiki WHERE page=$1 AND guild=$2", self.page, self.guild.id)
                contributors = await db.fetch("SELECT * FROM contributors WHERE page=$1 AND guild=$2", self.page,
                                              self.guild.id)
            list_ = []
            for user in contributors:
                list_.append(f"**{(self.guild.get_member(user[2])).display_name}**")

            embed = self.constructor(info[0], info[2], info[4], info[3], info[5], '\n'.join(list_))
            embed.set_footer(text="Last Updated at")
            embed.timestamp = info[7]
            await self.channel.send(embed=embed)
        else:
            return await self.channel.send(f"This page does not exist. But you can create it using {self.prefix}wiki "
                                           "create")

    async def edit(self):
        if await self.check(self.page) is True:
            async with self.db.acquire() as db:
                info = await db.fetchrow("SELECT * FROM wiki WHERE page=$1 AND guild=$2", self.page, self.guild.id)
                contributors = await db.fetch("SELECT * FROM contributors WHERE id=$1 AND guild=$2 AND page=$3",
                                              self.author.id, self.guild.id, self.page)

            c = [x[0] for x in contributors]
            await self.channel.send("What field do you want to edit? Image, quote, about and color.")

            try:
                choice = (await self.input('message', check=self._edit_check, timeout=300)).content.capitalize()
            except asyncio.TimeoutError:
                return await self.channel.send("I guess this isn't what you wanted.")

            await self.channel.send(f"What is the new value for the {choice} field?")

            try:
                new = (await self.input('message', check=self.fields[choice], timeout=300)).content
            except asyncio.TimeoutError:
                return await self.channel.send("I guess this isn't what you wanted.")

            if choice == "Color":
                new = new.capitalize()

            await self.channel.send(f"The value for {choice} has been changed to: **{new}**")

            if self.author.id == info[6] or self.author.id in c:
                async with self.db.acquire() as db:
                    await db.execute(f"UPDATE wiki SET {choice.lower()}=$1, edited=$2 WHERE page=$3 AND guild=$4", new,
                                     datetime.datetime.utcnow(), self.page, self.guild.id)
            else:
                async with self.db.acquire() as db:
                    await db.execute(f"UPDATE wiki SET {choice.lower()}=$1, edited=$2 WHERE page=$3 AND guild=$4", new,
                                     datetime.datetime.utcnow(), self.page, self.guild.id)
                    await db.execute("INSERT INTO contributors VALUES($1, $2, $3)", self.page, self.guild.id,
                                     self.author.id)
        else:
            return await self.channel.send(
                f"This page doesn't exist. But you can create it using {self.prefix}wiki "
                "create.")


class Community:
    """Things written by the community of this bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def wiki(self, ctx, *, page):
        """Fetches a wiki page from the list of available wiki pages"""

        w = Wiki(ctx, page.lower(), ctx.guild)
        await w.retrieve()

    @wiki.command(name="create")
    @commands.cooldown(1, float('inf'), commands.BucketType.channel)
    async def _create_(self, ctx, *, name=None):
        """Creates a wiki page"""
        if not name:
            await ctx.send(embed=discord.Embed(title=ctx.command.signature, color=self.bot.embed_color,
                                               description=ctx.command.help))
            ctx.command.reset_cooldown(ctx)
            return

        w = Wiki(ctx, page=name.lower(), guild=ctx.guild)
        await w.create()

    @wiki.command(name="edit")
    async def _edit_(self, ctx, *, name):
        """Edits an already existing page"""
        if not name:
            await ctx.send(embed=discord.Embed(title=ctx.command.signature, color=self.bot.embed_color,
                                               description=ctx.command.help))

        w = Wiki(ctx, name.lower(), ctx.guild)
        await w.edit()

    @wiki.command(name="list")
    async def _list_(self, ctx):
        """Shows all the available wiki pages for the server """

        async with ctx.db.acquire() as db:
            pages = await db.fetch("SELECT * FROM wiki WHERE guild=$1", ctx.guild.id)
            contributors = await db.fetch("SELECT * FROM contributors WHERE guild=$1", ctx.guild.id)
        if pages:
            p = []
            for x, y in enumerate(pages):
                c = '\n'.join([f"**{(ctx.guild.get_member(i[2])).display_name}**" for i in contributors if i[0] ==
                               y[0]])
                p.append(discord.Embed(color=self.bot.embed_color,
                                       description=f"Created by {(ctx.guild.get_member(y[6])).mention}",
                                       timestamp=y[7])
                         .set_author(name=y[0].capitalize())
                         .add_field(name="Contributors", value=c or "None")
                         .set_image(url=y[2])
                         .set_footer(text=f"Page {x+1} of {len(pages)} | Page Last Updated at")
                         )
            await ctx.paginate(entries=p)
        else:
            return await ctx.send(f"There are no wiki pages. You can start creating some by using {ctx.prefix}wiki "
                                  "create")

    @wiki.command(name="global")
    async def global_(self, ctx):
        """Lists all the wiki pages in the database."""
        async with ctx.db.acquire() as db:
            pages = await db.fetch("SELECT * FROM wiki")
            contributors = await db.fetch("SELECT * FROM contributors")
        if pages:
            p = []
            for x, y in enumerate(pages):
                guild = ctx.bot.get_guild(y[1])
                c = '\n'.join([f"**{(guild.get_member(i[2])).display_name}**" for i in contributors if i[2] ==
                               y[0]])
                p.append(discord.Embed(color=self.bot.embed_color,
                                       description=f"Created by {(guild.get_member(y[6])).mention}",
                                       timestamp=y[7])
                         .set_author(name=y[0].capitalize())
                         .add_field(name="Contributors", value=c or "None")
                         .set_image(url=y[2])
                         .add_field(name="Guild", value=guild.name)
                         .set_footer(text=f"Page {x+1} of {len(pages)} | Page Last Updated at")
                         )
            await ctx.paginate(entries=p)
        else:
            return await ctx.send(f"There are no wiki pages. You can start creating some by using {ctx.prefix}wiki "
                                  "create")

    @wiki.command()
    async def view(self, ctx, page: str, guild: str):
        """Views a wiki page from another guild."""

        guild = [x for x in self.bot.guilds if x.name == guild]
        w = Wiki(ctx, page, guild[0])
        await w.retrieve()

    @_create_.error
    async def create_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send("Someone is currently in the process of making a wiki page.")

    @commands.command()
    async def trivia(self, ctx):
        """Answer trivia questions."""

        if ctx.author == self.bot.user:
            return

        async with self.bot.session.get("http://jservice.io/api/random?json") as r:
            question = await r.json()
            question = question[0]

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = 'Trivia Question'
        embed.description = question['question']
        text = question['answer']
        vowels = ('a', 'e', 'i', 'o', 'u')
        for c in text:
            if c in vowels:
                text = text.replace(c, "-")

        embed.set_footer(text=f'Clue: {text}')
        await ctx.send(embed=embed)

        def check(m):
            return m.content.lower() == question['answer'].lower() and m.channel == ctx.channel

        try:
            right = await ctx.input('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The answer was {question['answer']}!")
        else:
            await ctx.send(f"{right.author.mention} is correct! The answer was {question['answer']}!")
            command = self.bot.get_command('trivia')
            await ctx.invoke(command)


def setup(bot):
    bot.add_cog(Community(bot))
