import asyncio
import io
import json
import logging
import os
import random
import textwrap
import time
import traceback
from contextlib import redirect_stdout
from datetime import datetime

import aiohttp
import discord
import psutil
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from cogs.utils.paginator import HelpPaginator

logging.basicConfig(level=logging.INFO)


# From Rapptz
class Plural:
    def __init__(self, **attr):
        iterator = attr.items()
        self.name, self.value = next(iter(iterator))

    def __str__(self):
        v = self.value
        if v == 0 or v > 1:
            return f'{v} {self.name}s'
        return f'{v} {self.name}'


class TabularData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        """Renders a table in rST format.
        Example:
        +-------+-----+
        | Name  | Age |
        +-------+-----+
        | Alice | 24  |
        |  Bob  | 19  |
        +-------+-----+
        """

        sep = '+'.join('-' * w for w in self._widths)
        sep = f'+{sep}+'

        to_draw = [sep]

        def get_entry(d):
            elem = '|'.join(f'{e:^{self._widths[i]}}' for i, e in enumerate(d))
            return f'|{elem}|'

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return '\n'.join(to_draw)


class Utility:
    """Utility Commands."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.process = psutil.Process()

    # From Rapptz
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    async def ping(self, ctx):
        """Shows the response time of the bot."""

        t_1 = time.perf_counter()
        await ctx.trigger_typing()
        t_2 = time.perf_counter()
        ping = round((t_2 - t_1) * 1000)
        embed = discord.Embed(color=0xba1c1c)
        embed.title = 'Pong! :ping_pong:'
        embed.description = f'That took {ping}ms!'
        await ctx.send(embed=embed)

    # From Rapptz
    @commands.command(pass_context=True, hidden=True, name='eval')
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Executes written code."""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, " ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                if "bot.http.token" in body:
                    await ctx.send(f"```py\n" + "*" * 59 + "```")
                else:
                    await ctx.send(f'```py\n{value}{ret}\n```')

    # From Rapptz
    @commands.command(hidden=True)
    @commands.is_owner()
    async def sql(self, ctx, *, query: str):
        query = self.cleanup_code(query)
        is_multistatement = query.count(';') > 1
        if is_multistatement:
            # fetch does not support multiple statements
            strategy = ctx.bot.db.execute
        else:
            strategy = ctx.bot.db.fetch

        try:
            start = time.perf_counter()
            results = await strategy(query)
            dt = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')

        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(f'`{dt:.2f}ms: {results}`')

        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f'```\n{render}\n```\n*Returned {Plural(row=rows)} in {dt:.2f}ms*'
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode('utf-8'))
            await ctx.send('Too many results...', file=discord.File(fp, 'results.txt'))
        else:
            await ctx.send(fmt)

    @commands.group(case_insensitive=True, aliases=['stats'], invoke_without_command=True)
    async def info(self, ctx):
        """Shows information about this bot"""

        # From Modelmat
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        users = sum(1 for _ in self.bot.get_all_members())
        channels = sum(1 for _ in self.bot.get_all_channels())

        author = self.bot.get_user(299879858572492802)

        invite = 'https://discordapp.com/oauth2/authorize?client_id=347205176903335937&scope=bot&permissions=470150342'
        about = ('Infamous is a actively developed bot that gets updated daily.'
                 f' It is written with passion by {author} using the Rewrite branch of the discord.py library.')

        links = (f'**[[Invite Bot]]({invite})** \n'
                 '**[[Fame Discord]](https://discord.gg/NY2MSA3)** \n'
                 '**[[Discord.py]](https://github.com/Rapptz/discord.py/tree/rewrite)**')

        # From Modelmat
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        ram_usage = self.process.memory_full_info().uss / 1024 ** 2
        
        # From Rapptz
        cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/Rapptz/RoboDanny/commit/%H) %s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')

        try:
            revision = os.popen(cmd).read().strip()
        except OSError:
            revision = 'Could not fetch due to memory error. Sorry.'
            
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.description = 'A Community Bot for ★ Fame ★.'
        embed.set_thumbnail(
            url=self.bot.user.avatar_url)

        embed.add_field(name='About', value=about, inline=False)

        embed.add_field(name='Statistics 📈',
                        value=(f'**{len(self.bot.guilds)} guilds.**\n '
                               f'**{channels} channels.**\n'
                               f'**{users} users.** \n'
                               f'**{self.bot.lines} lines**'), inline=True)

        embed.add_field(name='Uptime ⏰', value=(f'**{days} days.** \n '
                                                f'**{hours} hours.** \n '
                                                f'**{minutes} minutes.** \n '
                                                f'**{seconds} seconds.**'), inline=True)

        embed.add_field(name='Developer 🕵', value=author)
        embed.add_field(name='Resources 💻', value='`CPU:` {:.2f}% \n`RAM:` {:.2f}%'.format(cpu_usage, ram_usage))
        embed.add_field(name='Links 🔗', value=links, inline=True)
        embed.add_field(name='Design', value='`Embed HEX:` ba1c1c')
        embed.add_field(name="Changelogs", value=revision)
        await ctx.send(embed=embed)

    # User Information
    @info.command(aliases=['member'])
    @commands.guild_only()
    async def user(self, ctx, user: discord.Member = None):
        """Shows information about a user."""

        if user is None:
            user = ctx.author

        days = datetime.utcnow() - user.created_at

        days2 = datetime.utcnow() - user.joined_at

        registered = user.created_at.strftime('%a %b %d %Y at %I:%M %p')

        joined = user.joined_at.strftime('%a %b %d %Y at %I:%M %p')

        status = user.status.name

        activity = user.activity

        if status == 'online':
            status = 'Online'
            se = '<:online:435402249448062977> '

        elif status == 'offline':
            status = 'Offline'
            se = '<:offline:435402248282046464>'

        elif status == 'away':
            status = 'Away'
            se = '<:away:435402245144576000> '

        elif status == 'dnd':
            status = 'Do Not Disturb'
            se = '<:dnd:435402246738673675>'

        d_pos = [name for name, has in ctx.guild.default_role.permissions if has]
        pos = ", ".join([name for name, has in user.top_role.permissions if name in d_pos or has])
        perms = pos.replace("_", " ")

        embed = discord.Embed(color=user.colour, timestamp=datetime.utcnow())
        embed.set_author(name=f"Name: {user.name}")
        embed.add_field(name="Nick", value=user.nick, inline=True)
        embed.add_field(name=":id:", value=user.id, inline=True)
        embed.add_field(name=f"Status {se}", value=status, inline=True)

        if activity:
            if activity.type.name == "playing":
                activity_status = "Playing <:controller:444678089415458828>"

            elif activity.type.name == "watching":
                activity_status = "Watching <:YouTube:444677705254961152>"

            elif activity.type.name == "listening":
                activity_status = "Listening <:SpotifyLogo:444677360395223043>"

            elif activity.type.name == "streaming":
                activity_status = "Streaming <:twitchlogo:444676989681532929>"

            embed.add_field(name=f'{activity_status}', value=activity.name, inline=True)
        else:
            embed.add_field(name='Playing', value='Nothing...', inline=True)

        embed.add_field(name="Roles 📜", value=user.top_role.mention, inline=True)

        embed.add_field(name="Joined at", value=(f'{joined} \n'
                                                 f'That\'s {days2.days} days ago!'), inline=True)

        embed.add_field(name="Registered at", value=(f'{registered} \n'
                                                     f'That\'s {days.days} days ago!'), inline=True)

        embed.add_field(name="Permissions", value=perms.title())
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text="User Information")

        await ctx.send(embed=embed)

        # Guild Info

    @info.command(aliases=['guild'])
    @commands.guild_only()
    async def server(self, ctx):
        """Shows information about the guild."""

        created = ctx.guild.created_at
        sincethen = datetime.utcnow() - created
        created = created.strftime('%a %b %d %Y at %I:%M %p')

        channels = len(ctx.guild.channels)
        embed = discord.Embed(color=0xba1c1c)

        members = [x for x in ctx.guild.members if not x.bot]
        bots = [x for x in ctx.guild.members if x.bot]

        embed.title = f'{ctx.guild.name} 🏰'
        embed.description = f'Created on {created} \nThat\'s {sincethen.days} days ago!'

        embed.add_field(name='Owner 🤵', value=ctx.guild.owner.mention, inline=True)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name='Server 🆔', value=ctx.guild.id, inline=True)
        embed.add_field(name='Members :family_mwgb:', value=(
            f"**Users:** {len(members)} \n"
            f"**Bots:** {len(bots)}"
        ), inline=True)

        embed.add_field(name='Channels 📺', value=str(channels), inline=True)
        embed.add_field(name='Roles 📜', value=str(len(ctx.guild.roles)), inline=True)
        await ctx.send(embed=embed)

    # Urban Dictionary
    @commands.command(aliases=['urban'])
    async def ud(self, ctx, *, string):
        """Looks up a word on the Urban Dictionary."""

        link = '+'.join(string.split())
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.urbandictionary.com/v0/define?term=" + link) as resp:
                json_data = await resp.json()
                definition = json_data['list']
                first_def = definition[0]

        embed = discord.Embed(color=0xba1c1c)

        embed.set_author(name=first_def['word'], url=first_def['permalink'])
        embed.description = first_def['definition']
        embed.add_field(name="Example:", value=first_def['example'])
        embed.set_footer(text=f"Written by: {first_def['author']}")

        embed.set_thumbnail(
            url="http://a2.mzstatic.com/us/r30/Purple/v4/dd/ef/75/ddef75c7-d26c-ce82-4e3c-9b07ff0871a5/mzl.yvlduoxl.png"
        )

        await ctx.send(embed=embed)

    # User Avatar
    @commands.command(aliases=['av', 'pfp'])
    async def avatar(self, ctx, user: discord.Member = None):
        """Shows the avatar of the mentioned user."""

        if user is None:
            user = ctx.author

        avatar = user.avatar_url_as(format='png', size=1024)

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"{user}'s avatar", icon_url=avatar)
        embed.description = f'[[Download Avatar]]({avatar})'

        embed.set_image(url=avatar)

        await ctx.send(embed=embed)

    @commands.command(aliases=['request'])
    @commands.cooldown(1, 120, BucketType.user)
    async def suggest(self, ctx, *, string):
        """Suggest what you want to be implemented into the bot."""

        await ctx.message.add_reaction(':checkmark1:434297575663861761')

        accept = random.randint(1, 100)
        deny = 100 - accept
        vortex = self.bot.get_user(299879858572492802)
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.description = string
        embed.add_field(name='Probability', value=(f'**Chances of being accepted:** {accept}% \n'
                                                   f'**Chances of being denied:** {deny}%'), inline=False)
        msg = await vortex.send(embed=embed)

        await msg.add_reaction(':checkmark1:434297575663861761')
        await msg.add_reaction(':xmark:404503695502344203')

        def check(reaction_, user_):
            return user_ == vortex and str(reaction_.emoji) in ['<:checkmark1:434297575663861761>',
                                                                '<:xmark:404503695502344203>']

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check)
        except asyncio.TimeoutError:
            await vortex.send("I'll take that as a no.")
        else:
            if str(reaction.emoji) == '<:checkmark1:434297575663861761>':
                e = discord.Embed(color=0xba1c1c)
                e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
                e.add_field(name='Suggestion', value=string, inline=False)
                e.add_field(name='Status', value='Accepted')

                await vortex.send(embed=e)
                await ctx.author.send(embed=e)
            elif str(reaction.emoji) == '<:xmark:404503695502344203>':
                await vortex.send("Ok... So I won't be getting any new feature?")
                e = discord.Embed(color=0xba1c1c)
                e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
                e.add_field(name='Suggestion', value=string, inline=False)
                e.add_field(name='Status', value='Denied')
                await ctx.author.send(embed=e)

    @commands.command(name="help")
    async def _help(self, ctx, *, command: str = None):
        """Shows help about a command or the bot"""
        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)

                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Looks like "{clean}" is not a command or category.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Utility(bot))
