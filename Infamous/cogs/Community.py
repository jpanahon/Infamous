import asyncio
import datetime
import logging

import aiohttp
import discord
from discord.ext import commands

from .utils.paginator import Pages

logging.basicConfig(level=logging.INFO)


class Community:
    """Community related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def wiki(self, ctx, *, page=None):
        """Fetches a wiki page from the list of available wiki pages"""

        wiki_page = await self.bot.db.fetch("SELECT * FROM wiki WHERE guild_id = $1 ORDER BY views DESC", ctx.guild.id)
        if not page:
            if wiki_page:
                entries = [f"**{r[0]}** is created by **{str(self.bot.get_user(r[8]))}** \n"
                           f"Contributors: {r[9].strip(str(self.bot.get_user(r[8]).name + ' ,'))} \n"
                           f"Views: {r[12]} \n" for r in
                           wiki_page]

                try:
                    p = Pages(ctx, entries=entries, per_page=6)
                    p.embed.set_author(name="List of Wiki Pages")
                    p.embed.add_field(name="Disclaimer", value="You are allowed to create a wiki page about anyone, "
                                                               "and you are allowed to edit your own or other people's "
                                                               "wiki pages. This wiki system is similar to "
                                                               "the one found on [Wikia](http://www.wikia.com/fandom)")
                    await p.paginate()
                except Exception as e:
                    await ctx.send(e)
            else:
                await ctx.send("There are no wiki pages.")

        wiki = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name=$1 AND guild_id=$2", page, ctx.guild.id)

        if wiki:
            if str(wiki['image']).startswith('https:'):
                user = wiki['image']
            else:
                user = self.bot.get_user(int(wiki['image']))

            color = wiki['color']

            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://www.thecolorapi.com/id?format=json&hex={color}') as resp:
                    data = await resp.json()
                    color = data['name']['value']

            embed_color = wiki['color']

            embed = discord.Embed(color=int(embed_color, 16))

            if str(wiki['image']).startswith('https:'):
                user = wiki['image']
                embed.set_author(name=wiki['name'].title(), icon_url=user)
            else:
                embed.set_author(name=wiki['name'].title(),
                                 icon_url=user.avatar_url)

            quote = wiki['quote']

            embed.description = f'*"{quote.strip(" ")}"*'
            embed.add_field(name='Aliases', value=wiki['aliases'])
            embed.add_field(name='About', value=wiki['bio'], inline=False)
            embed.add_field(name='Roles', value=wiki['roles'], inline=False)
            embed.add_field(name='Games', value=wiki['games'], inline=False)
            embed.add_field(name='Favorite Color', value=color, inline=False)
            embed.set_footer(text='Contributors: ' + wiki['contributors'])

            if str(wiki['image']).startswith('https:'):
                user = wiki['image']
                embed.set_thumbnail(url=user)
            else:
                embed.set_thumbnail(url=user.avatar_url)

            await ctx.send(embed=embed)
            await self.bot.db.execute("UPDATE wiki SET views = views + 1 WHERE name=$1", page)

    @wiki.command(name="create")
    async def _create(self, ctx):
        """Creates Wiki Pages"""

        await ctx.send("What is the name of the wiki? This will be used to identify the wiki page.")

        def name(m):
            return m.author == ctx.author and m.channel == ctx.channel

        name_ = await self.bot.wait_for('message', check=name)
        name_ = name_.content
        wiki_page = await self.bot.db.fetchrow("SELECT name FROM wiki WHERE name=$1", name_)
        if wiki_page is None:
            await ctx.send(f"So the wiki page is named {name_}? \n"
                           f"What is a quote from them? This will be automatically given quotations.")

            def quote(m):
                return m.author == ctx.author and m.channel == ctx.channel

            quote_ = await self.bot.wait_for('message', check=quote)
            quote_ = quote_.content.strip('"')

            await ctx.send(f'*"{quote_}"* - {name_} \n'
                           f'What a lovely quote, now what are their aliases?')

            def aliases(m):
                return m.author == ctx.author and m.channel == ctx.channel

            aliases_ = await self.bot.wait_for('message', check=aliases)
            aliases_ = aliases_.content

            await ctx.send(f"So they were called **{aliases_}**? \n"
                           f"Now what information do you have about them?")

            def about(m):
                return m.author == ctx.author and m.channel == ctx.channel

            bio_ = await self.bot.wait_for('message', check=about)
            bio_ = bio_.content

            await ctx.send(f"```css\n{bio_}``` You sure do know something about this person. \n"
                           f"What role(s) do they have on this server?")

            def roles(m):
                return m.author == ctx.author and m.channel == ctx.channel

            roles_ = await self.bot.wait_for('message', check=roles)
            roles_ = roles_.content

            await ctx.send(f"Their role(s) are **{roles_}**? \n"
                           "What games do they play?")

            def games(m):
                return m.author == ctx.author and m.channel == ctx.channel

            games_ = await self.bot.wait_for('message', check=games)
            games_ = games_.content

            await ctx.send(f"They played **{games_}**? \n"
                           f"Now what is their favorite color? Type any color from the RAINBOW")

            def color(m):
                return m.author == ctx.author and m.channel == ctx.channel

            color_ = await self.bot.wait_for('message', check=color)
            color_ = color_.content.capitalize()
            if color_ == "Red":
                await ctx.send("So their favorite color is Red? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "FF0000"
            elif color_ == "Blue":
                await ctx.send("So their favorite color is Blue? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "0000FF"

            elif color_ == "Green":
                await ctx.send("So their favorite color is Green? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "00FF00"

            elif color_ == "Yellow":
                await ctx.send("So their favorite color is Yellow? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "FFFF00"

            elif color_ == "Orange":
                await ctx.send("So their favorite color is Orange? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "FF7F00"

            elif color_ == "Indigo":
                await ctx.send("So their favorite color is Indigo? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "4B0082"

            elif color_ == "Violet":
                await ctx.send("So their favorite color is Violet? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "9400D3"

            elif color_ == "Pink":
                await ctx.send("So their favorite color is Pink? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "FFC0CB"

            elif color_ == "Black":
                await ctx.send("So their favorite color is Black? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "000000"

            elif color_ == "White":
                await ctx.send("So their favorite color is White? \n"
                               "Now what do they look like? You can mention the user or send a link to a image")
                color_ = "FFFFFF"

            def image(m):
                return m.content.startswith("<@") or m.content.endswith((".png", ".jpg")) and m.author == ctx.author

            image_ = await self.bot.wait_for('message', check=image)
            await ctx.send(f"So {image_.content} is what they look like?")

            image = image_.content.strip("<@!")
            image = image.strip(">")
            time = datetime.datetime.now()

            if image_.attachments:
                image = ' '.join(m.url for m in image_.attachments)

            await ctx.send(f"I've successfully created it! Now type **{ctx.prefix} wiki {name_.lower()}** to view it!")
            await self.bot.db.execute(
                "INSERT INTO wiki VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)",
                name_.lower(), quote_, aliases_, bio_, roles_, games_, color_, image,
                ctx.author.id, ctx.author.name, time.strftime("%c"), time.strftime("%c"),
                0, ctx.guild.id)

        else:
            await ctx.send("A wiki page with that name has already been created.")

    @wiki.command(name="edit")
    async def _edit(self, ctx):
        """Edits existing wiki pages."""

        await ctx.send("What page are you going to edit?")

        def page(m):
            return m.author == ctx.author and m.channel == ctx.channel

        page_ = await self.bot.wait_for('message', check=page)
        page_ = page_.content

        wiki = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name=$1 AND guild_id=$2", page_, ctx.guild.id)
        time = datetime.datetime.now()
        if wiki:
            await ctx.send("What field are you going to edit?")

            def field(m):
                return m.content in ['quote', 'aliases', 'bio', 'roles', 'games', 'color', 'image'] and m.author == \
                       ctx.author

            resp = await self.bot.wait_for('message', check=field)
            if resp.content == "quote":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                await self.bot.db.execute("UPDATE wiki SET quote=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the quote for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "aliases":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                await self.bot.db.execute("UPDATE wiki SET aliases=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the aliases for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "bio":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                await self.bot.db.execute("UPDATE wiki SET bio=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the bio for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "roles":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                await self.bot.db.execute("UPDATE wiki SET roles=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the role(s) for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "games":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                await self.bot.db.execute("UPDATE wiki SET games=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the games for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "color":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def content(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                content_ = await self.bot.wait_for('message', check=content)
                content_ = content_.content
                if content_ == "Red":
                    content_ = "FF0000"
                elif content_ == "Blue":
                    content_ = "0000FF"
                elif content_ == "Green":
                    content_ = "00FF00"
                elif content_ == "Yellow":
                    content_ = "FFFF00"
                elif content_ == "Orange":
                    content_ = "FF7F00"
                elif content_ == "Indigo":
                    content_ = "4B0082"
                elif content_ == "Violet":
                    content_ = "9400D3"
                elif content_ == "Pink":
                    content_ = "FFC0CB"
                elif content_ == "Black":
                    content_ = "000000"
                elif content_ == "White":
                    content_ = "FFFFFF"

                await self.bot.db.execute("UPDATE wiki SET color=$1 WHERE name=$2", content_, page_)
                await ctx.send(f"I have set the color for **{page_}** to {content_}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

            if resp.content == "image":
                await ctx.send(f"What is the new content of **{resp.content}**?")

                def image(m):
                    return m.content.startswith("<@") or m.content.endswith(
                        (".png", ".jpg")) and m.author == ctx.author

                content = await self.bot.wait_for('message', check=image)
                content_ = content.content

                image = content_.strip("<@!")
                image = image.strip(">")

                if content.attachments:
                    image = ' '.join(m.url for m in content.attachments)

                await self.bot.db.execute("UPDATE wiki SET image=$1 WHERE name=$2", image, page_)
                await ctx.send(f"I have set the image for **{page_}** to {image}")
                info = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page_)
                await self.bot.db.execute("UPDATE wiki SET last_modified = $1 WHERE name=$2", time.strftime("%c"),
                                          page_)

                if ctx.author.name in info['contributors']:
                    return
                else:
                    await self.bot.db.execute("UPDATE wiki SET contributors = contributors || ', ' || $1 WHERE name=$2",
                                              ctx.author.name, page_)

        else:
            return await ctx.send("This wiki page does not exist.")

    @wiki.command()
    async def delete(self, ctx, *, page):
        """Deletes existing wiki pages"""

        wiki = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name = $1", page)

        if wiki:
            if ctx.author.id == wiki['creator'] or ctx.author.guild_permissions.manage_guild:
                msg = await ctx.send("Are you sure you want to delete this wiki page?")
                emoji = [':BlurpleX:452390303698124800', ':BlurpleCheck:452390337382449153']
                for e in emoji:
                    await msg.add_reaction(e)

                def check(reaction_, user_):
                    return user_ == ctx.author and str(reaction_.emoji) in ['<:BlurpleX:452390303698124800>',
                                                                            '<:BlurpleCheck:452390337382449153>']

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                except asyncio.TimeoutError:
                    await ctx.send(f"I'll take that as a no, {ctx.author.mention}'")
                else:
                    if str(reaction.emoji) == '<:BlurpleCheck:452390337382449153>':
                        await ctx.send(f"Deleted the {page.title()} wiki page from database.")
                        await self.bot.db.execute("DELETE FROM wiki WHERE name= $1", page)
                    else:
                        return await ctx.send("So you changed your mind.")
            else:
                return await ctx.send("You don't own this page.")
        else:
            return await ctx.send("This page doesn't exist.")

    @wiki.command()
    async def info(self, ctx, *, page):
        """Shows information about a wiki page."""

        wiki = await self.bot.db.fetchrow("SELECT * FROM wiki WHERE name=$1", page)

        if str(wiki['image']).startswith('https:'):
            user = wiki['image']
        else:
            user = self.bot.get_user(int(wiki['image']))

        if wiki:
            embed = discord.Embed(color=0xba1c1c)

            if str(wiki['image']).startswith('https:'):
                user = wiki['image']
                embed.set_author(name=wiki['name'].title(), icon_url=user)
            else:
                embed.set_author(name=wiki['name'].title(),
                                 icon_url=user.avatar_url)

            creator = self.bot.get_user(int(wiki['creator']))
            embed.description = "Created By: " + creator.name
            if wiki['contributors'] == creator.name:
                embed.add_field(name="Contributors", value="None")
            else:
                embed.add_field(name="Contributors",
                                value=wiki['contributors'].strip(creator.name + ", "),
                                inline=False)

            embed.add_field(name="Views", value=wiki['views'])
            embed.add_field(name="Last Modified", value=wiki['last_modified'])
            embed.set_footer(text="Created on " + wiki['creation_date'])

            await ctx.send(embed=embed)
        else:
            return await ctx.send("That wiki page does not exist.")

    @commands.command()
    async def trivia(self, ctx):
        """Answer trivia questions."""

        if ctx.author == self.bot.user:
            return

        async with self.bot.session.get("http://jservice.io/api/random?json") as r:
            question = await r.json()
            question = question[0]

        embed = discord.Embed(color=0xba1c1c)
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
            return m.content.lower() == question['answer'].lower() and m.channel == ctx.message.channel

        try:
            right = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The answer was {question['answer']}!")
        else:
            await ctx.send(f"{right.author.mention} is correct! The answer was {question['answer']}!")
            command = self.bot.get_command('trivia')
            await ctx.invoke(command)


def setup(bot):
    bot.add_cog(Community(bot))

