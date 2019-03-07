import datetime
import discord
from discord.ext import commands
import asyncio

embed_color = 0x740f10


def time_(time):
    delta_uptime = datetime.datetime.utcnow() - time
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    return days, hours, minutes, seconds


def status__(status_):
    status = None
    se = None
    if status_ == 'online':
        status = 'Online'
        se = '<:online:435402249448062977> '

    elif status_ == 'offline':
        status = 'Offline'
        se = '<:offline:435402248282046464>'

    elif status_ == 'away':
        status = 'Away'
        se = '<:away:435402245144576000> '

    elif status_ == 'dnd':
        status = 'Do Not Disturb'
        se = '<:dnd:435402246738673675>'

    return status, se


def activity(activity_):
    activity_status = None
    if activity_:
        if activity_.type.name == "playing":
            activity_status = "Playing <:controller:444678089415458828>"

        elif activity_.type.name == "watching":
            activity_status = "Watching <:YouTube:444677705254961152>"

        elif activity_.type.name == "listening":
            activity_status = "Listening <:SpotifyLogo:444677360395223043>"

        elif activity_.type.name == "streaming":
            activity_status = "Streaming <:twitchlogo:444676989681532929>"

        return activity_status


def ud_embed(definition_, current, max_):
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=definition_['word'], url=definition_['permalink'])
    embed.description = ((definition_['definition'])[:2046] + '..') if len(definition_['definition']) > 2048 \
        else definition_['definition']
    embed.add_field(name="Example:",
                    value=((definition_['example'])[:1022] + '..') if len(definition_['example']) > 1024
                    else definition_['example'])
    embed.set_footer(text=f"Written by: {definition_['author']} | Entry {current} of {max_}")

    embed.set_thumbnail(
        url="http://a2.mzstatic.com/us/r30/Purple/v4/dd/ef/75/ddef75c7-d26c-ce82-4e3c-9b07ff0871a5/mzl.yvlduoxl.png"
    )
    return embed


class Paginator:
    def __init__(self, ctx, entries: list, embed=True, timeout=120):
        self.bot = ctx.bot
        self.ctx = ctx
        self.entries = entries
        self.embed = embed
        self.max_pages = len(entries)
        self.msg = ctx.message
        self.paginating = True
        self.user_ = ctx.author
        self.channel = ctx.channel
        self.current = 0
        self.timeout = timeout
        self.reactions = [('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.first_page),
                          ('\N{BLACK LEFT-POINTING TRIANGLE}', self.backward),
                          ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.forward),
                          ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.last_page),
                          ('\N{INPUT SYMBOL FOR NUMBERS}', self.selector),
                          ('\N{BLACK SQUARE FOR STOP}', self.stop),
                          ('\N{INFORMATION SOURCE}', self.info)]

    async def setup(self):
        if self.embed is False:
            try:
                self.msg = await self.channel.send(self.entries[0])
            except AttributeError:
                await self.channel.send(self.entries)
        else:
            try:
                self.msg = await self.channel.send(embed=self.entries[0])
            except (AttributeError, TypeError):
                await self.channel.send(embed=self.entries)

        if len(self.entries) == 1:
            return

        for (r, _) in self.reactions:
            await self.msg.add_reaction(r)

    async def alter(self, page: int):
        try:
            await self.msg.edit(embed=self.entries[page])
        except (AttributeError, TypeError):
            await self.msg.edit(content=self.entries[page])

    async def first_page(self):
        self.current = 0
        await self.alter(self.current)

    async def backward(self):
        if self.current == 0:
            self.current = self.max_pages-1
            await self.alter(self.current)
        else:
            self.current -= 1
            await self.alter(self.current)

    async def forward(self):
        if self.current == self.max_pages-1:
            self.current = 0
            await self.alter(self.current)
        else:
            self.current += 1
            await self.alter(self.current)

    async def last_page(self):
        self.current = self.max_pages-1
        await self.alter(self.current)

    async def selector(self):
        def check(m):
            if m.author == self.user_:
                return True
            if m.id == self.msg.id:
                return True
            if int(m.content) > 1 <= self.max_pages - 1:
                return True
            return False

        delete = await self.channel.send(f"Which page do you want to turn to? **1-{self.max_pages}?**")
        try:
            number = int((await self.bot.wait_for('message', check=check, timeout=60)).content)
        except asyncio.TimeoutError:
            return await self.channel.send("You ran out of time.")
        else:
            self.current = number - 1
            await self.alter(self.current)
            await delete.delete()

    async def stop(self):
        try:
            await self.msg.clear_reactions()
        except discord.Forbidden:
            await self.msg.delete()
        finally:
            pass

        self.paginating = False

    async def info(self):
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name='Instructions')
        embed.description = "This is a reaction paginator; when you react to one of the buttons below " \
                            "the message gets edited. Below you will find what the reactions do."

        embed.add_field(name="First Page ⏮", value="This reaction takes you to the first page.", inline=False)
        embed.add_field(name="Previous Page ◀", value="This reaction takes you to the previous page. "
                                                      "If you use this reaction while in the first page it will take "
                                                      "you to the last page.", inline=False)
        embed.add_field(name="Next Page ▶", value="This reaction takes you to the next page. "
                                                  "If you use this reaction while in the last page it will to take "
                                                  "you to the first page.", inline=False)
        embed.add_field(name="Last Page ⏭", value="This reaction takes you to the last page", inline=False)
        embed.add_field(name="Selector 🔢", value="This reaction allows you to choose what page to go to", inline=False)
        embed.add_field(name="Information ℹ", value="This reaction takes you to this page.")
        await self.msg.edit(embed=embed)

    def _check(self, reaction, user):
        if user.id != self.user_.id:
            return False

        if reaction.message.id != self.msg.id:
            return False

        for (emoji, func) in self.reactions:
            if reaction.emoji == emoji:
                self.execute = func
                return True
        return False

    async def paginate(self):
        perms = self.ctx.me.guild_permissions.manage_messages
        await self.setup()
        while self.paginating:
            if perms:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=self._check, timeout=self.timeout)
                except asyncio.TimeoutError:
                    return await self.stop()

                try:
                    await self.msg.remove_reaction(reaction, user)
                except discord.HTTPException:
                    pass

                await self.execute()
            else:
                done, pending = await asyncio.wait(
                    [self.bot.wait_for('reaction_add', check=self._check, timeout=self.timeout),
                     self.bot.wait_for('reaction_remove', check=self._check, timeout=self.timeout)],
                    return_when=asyncio.FIRST_COMPLETED)
                try:
                    done.pop().result()
                except asyncio.TimeoutError:
                    return await self.stop()

                for future in pending:
                    future.cancel()
                await self.execute()


class Awareness(commands.Context):
    async def paginate(self, entries: list, embed=True, timeout=120):
        p = Paginator(self, entries=entries, embed=embed, timeout=timeout)
        return await p.paginate()

    @property
    def db(self):
        return self.bot.db

    def grab(self, member):
        return self.guild.get_member(member) or self.bot.get_user(member)

    @property
    def input(self):
        return self.bot.wait_for
