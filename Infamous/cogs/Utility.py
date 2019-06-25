import io
import logging
import textwrap
import time
import traceback
from contextlib import redirect_stdout
from datetime import datetime
import discord
import psutil
from discord.ext import commands
from .utils import functions as funct
from dateutil.relativedelta import relativedelta
from .utils import checks

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


class Utility(commands.Cog):
    """Commands that provide information and debugging."""

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
        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = 'Pong! :ping_pong:'
        embed.description = f'That took {ping}ms!'
        await ctx.send(embed=embed)

    # From Rapptz
    @commands.command(pass_context=True, hidden=True, name='eval')
    @checks.is_admin()
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
            original = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            self.bot.previous_error = original
            return

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            original = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
            self.bot.previous_error = original

        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    n = 1000
                    p = []
                    pages = [value[i:i + n] for i in range(0, len(value), n)]
                    for n, x in enumerate(pages):
                        p.append(f"```py\n{x}\n```\nPage {n + 1} of {len(pages)}")
                    await ctx.paginate(entries=p, embed=False)
            else:
                self._last_result = ret
                if "bot.http.token" in body:
                    await ctx.send(f"```py\n" + "*" * 59 + "```")
                else:
                    text = f"{value}{ret}"
                    p = []
                    n = 1000
                    pages = [text[i:i + n] for i in range(0, len(text), n)]
                    for n, x in enumerate(pages):
                        p.append(f"```py\n{x}\n```\nPage {n + 1} of {len(pages)}")
                    await ctx.paginate(entries=p, embed=False)

    # From Rapptz
    @commands.command(hidden=True)
    @checks.is_admin()
    async def sql(self, ctx, *, query: str):
        query = self.cleanup_code(query)
        is_multistatement = query.count(';') > 1
        if is_multistatement:
            # fetch does not support multiple statements
            strategy = ctx.db.execute
        else:
            strategy = ctx.db.fetch

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
            async with ctx.bot.session.post("https://hastebin.com/documents", data=fmt.encode('utf-8')) as post:
                post = await post.json()
                url = f"https://hastebin.com/{post['key']}"

            await ctx.send(f'Too many results... \n{url}')
        else:
            await ctx.send(fmt)

    @commands.group(case_insensitive=True, aliases=['stats'], invoke_without_command=True)
    async def info(self, ctx):
        """Shows information about this bot"""

        uptime = funct.time_(self.bot.launch_time)
        users = sum(1 for _ in self.bot.get_all_members())
        channels = sum(1 for _ in self.bot.get_all_channels())

        author = self.bot.get_user(299879858572492802)

        invite = 'https://discordapp.com/oauth2/authorize?client_id=347205176903335937&scope=bot&permissions=470150359'
        about = ('Infamous is a actively developed bot that gets updated daily.'
                 f' It is written with passion by {author} using the Rewrite branch of the discord.py library.')

        links = (f'**[[Invite Bot]]({invite})** \n'
                 '**[[Fame Discord]](https://discord.gg/NY2MSA3)** \n'
                 '**[[Discord.py]](https://github.com/Rapptz/discord.py/tree/rewrite)** \n'
                 '**[[Support]](https://discord.gg/JyJTh4H)**')

        # From Modelmat
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        ram_usage = self.process.memory_full_info().uss / 1024 ** 2

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.description = 'A multi-purpose bot with image manipulation, wiki pages and it\'s own rpg; originally a ' \
                            'community bot for ★ Fame ★'
        embed.set_thumbnail(
            url=self.bot.user.avatar_url)

        embed.add_field(name='About', value=about, inline=False)

        embed.add_field(name='Statistics 📈',
                        value=(f'**{len(self.bot.guilds)} guilds.**\n'
                               f'**{channels} channels.**\n'
                               f'**{users} users.** \n'
                               f'**{self.bot.lines} lines**'), inline=True)

        embed.add_field(name='Uptime ⏰', value=(f'**{uptime[0]} days.** \n'
                                                f'**{uptime[1]} hours.** \n'
                                                f'**{uptime[2]} minutes.** \n'
                                                f'**{uptime[3]} seconds.**'), inline=True)

        embed.add_field(name='Developer 🕵', value=author)
        embed.add_field(name='Resources 💻', value='`CPU:` {:.2f}% \n`MEM:` {:.2f}'.format(cpu_usage, ram_usage))
        embed.add_field(name='Links 🔗', value=links, inline=True)

        await ctx.send(embed=embed)

    # User Information
    @info.command(aliases=['member'])
    @commands.guild_only()
    async def user(self, ctx, user: discord.Member = None):
        """Shows information about a user."""

        if user is None:
            user = ctx.author

        registered = user.created_at.strftime('%a %b %d %Y at %I:%M %p')
        joined = user.joined_at.strftime('%a %b %d %Y at %I:%M %p')
        days = datetime.strptime(registered, '%a %b %d %Y at %I:%M %p')
        days2 = datetime.strptime(joined, '%a %b %d %Y at %I:%M %p')
        diff1 = relativedelta(days, datetime.utcnow())
        diff2 = relativedelta(days2, datetime.utcnow())
        status = user.status.name
        status = funct.status__(status)

        d_pos = [name for name, has in ctx.guild.default_role.permissions if has]
        pos = ", ".join([name for name, has in user.top_role.permissions if name in d_pos or has])
        perms = pos.replace("_", " ")

        embed = discord.Embed(color=user.colour, timestamp=datetime.utcnow())
        embed.set_author(name=f"Name: {user.name}")
        embed.add_field(name="Nick", value=user.nick, inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name=f"Status {status[1]}", value=status[0], inline=True)
        embed.add_field(name=f"On Mobile", value=user.is_on_mobile())
        activity_ = funct.activity(user.activity)
        if activity_:
            embed.add_field(name=activity_, value=user.activity.name, inline=True)
        else:
            embed.add_field(name='Playing', value='Nothing...', inline=True)

        embed.add_field(name="Roles 📜", value=user.top_role.mention, inline=True)

        embed.add_field(name="Joined at", value=(f'{joined} \n'
                                                 f'That\'s {abs(diff2.years)}y(s), {abs(diff2.months)}m, '
                                                 f'{abs(diff2.days)}d, {abs(diff2.hours)}h, {abs(diff2.minutes)}m and '
                                                 f'{abs(diff2.seconds)}s ago!'), inline=True)

        embed.add_field(name="Registered at", value=(f'{registered} \n'
                                                     f'That\'s {abs(diff1.years)}y(s), {abs(diff1.months)}m, '
                                                     f'{abs(diff1.days)}d, {abs(diff1.hours)}h, {abs(diff1.minutes)}m '
                                                     f'and {abs(diff1.seconds)}s ago!'), inline=True)

        embed.add_field(name="Permissions", value=perms.title())
        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text="User Information")

        await ctx.send(embed=embed)

    # Guild Info
    @info.command(aliases=['guild'])
    @commands.guild_only()
    async def server(self, ctx):
        """Shows information about the current guild."""

        created = ctx.guild.created_at
        created = created.strftime('%a %b %d %Y at %I:%M %p')
        created1 = datetime.strptime(created, '%a %b %d %Y at %I:%M %p')
        created1 = relativedelta(created1, datetime.utcnow())

        channels = len(ctx.guild.channels)
        embed = discord.Embed(color=self.bot.embed_color)

        members = [x for x in ctx.guild.members if not x.bot]
        bots = [x for x in ctx.guild.members if x.bot]

        embed.title = f'{ctx.guild.name} 🏰'
        embed.description = f'Created on {created} \nThat\'s {abs(created1.years)}y(s), {abs(created1.months)}m, ' \
            f'{abs(created1.days)}d, {abs(created1.minutes)}m  and {abs(created1.seconds)}s ago!'

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
        """Looks up a word on the Urban Dictionary.
           *Also shows related definitions if any*"""

        link = '+'.join(string.split())
        async with ctx.bot.session.get("http://api.urbandictionary.com/v0/define?term=" + link) as resp:
            json_data = await resp.json()
            definition = json_data['list']

        if len(definition) > 1:
            p = [funct.ud_embed(i, n + 1, len(definition)) for n, i in enumerate(definition)]
            await ctx.paginate(entries=p)
        else:
            await ctx.send(embed=funct.ud_embed(definition[0], 1, 1))

    @ud.error
    async def ud_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = ctx.command.signature
            embed.description = ctx.command.help
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandInvokeError):
            return await ctx.send("There are no entries found.")

    # User Avatar
    @commands.command(aliases=['av', 'pfp'])
    async def avatar(self, ctx, user: discord.Member = None):
        """Shows the avatar of the mentioned user."""

        if user is None:
            user = ctx.author

        avatar = user.avatar_url_as(static_format='png', size=1024)

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name=f"{user}'s avatar", icon_url=avatar)
        embed.description = f'[[Download Avatar]]({avatar})'

        embed.set_image(url=avatar)

        await ctx.send(embed=embed)

    @commands.command(aliases=['request'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def suggest(self, ctx, *, string=None):
        """Suggest what you want to be implemented into the bot."""

        if not string:
            await ctx.send("Give a suggestion.")
            ctx.command.reset_cooldown(ctx)
            return

        channel = ctx.bot.get_channel(520909751681548307)
        await channel.send(embed=discord.Embed(color=self.bot.embed_color,
                                               description=string)
                           .set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                           .set_footer(text=f"From {ctx.guild.name}")
                           )

        await ctx.send(f"Your suggestion has been sent!")

    @commands.command(aliases=['red', 're'])
    async def reddit(self, ctx, sr: str = None, sort='hot'):
        """Retrieve something from Reddit"""

        if not sr:
            link = f"https://www.reddit.com/r/random.json?sort={sort}"
        else:
            link = f"https://www.reddit.com/r/{sr}/new.json?sort={sort}"

        async with ctx.bot.session.get(link) as resp:
            if resp.status != 200:
                return await ctx.send(f"The subreddit `r/{sr}` does not exist or it's private.", delete_after=20)

            json_data = await resp.json()
            sub = json_data['data']['children']

        p = []
        for i in sub:
            line = i['data']
            if line['over_18'] and ctx.channel.is_nsfw() is False and sub.index(i) == 0:
                return await ctx.send("This is an nsfw subreddit please go to a nsfw channel to view it.",
                                      delete_after=20)

            text = line['selftext'].replace("&amp;#x200B;", "\u200b")
            if text:
                n = 2048
                pages = [text[i:i + n] for i in range(0, len(text), n)]
                for n, x in enumerate(pages):
                    embed = discord.Embed(color=self.bot.embed_color)
                    embed.set_author(name=line['title'] + f' (Page {n + 1} of {len(pages)})')
                    embed.description = x
                    if line['url']:
                        if line['over_18'] and ctx.channel.is_nsfw() is False:
                            embed.set_image(url="https://imgur.com/hPJWFqq.png")
                        embed.set_image(url=line['url'])

                    embed.set_footer(text=f'From r/{line["subreddit"]} | Entry {sub.index(i) + 1} of {len(sub)}')
                    p.append(embed)

            else:
                e = discord.Embed(color=self.bot.embed_color)
                e.set_author(name=line['title'])
                if line['url'].endswith((".png", ".jpg")):
                    e.set_image(url=line['url'])
                else:
                    e.add_field(name='Video', value=line['url'])
                e.set_footer(text=f"From r/{line['subreddit']}")
                p.append(e)
                for n, x in enumerate(p):
                    x.set_footer(text=f'Page {n + 1} of {len(sub)} | From r/{line["subreddit"]}')

        await ctx.paginate(entries=p, embed=True, timeout=300)

    @commands.command(aliases=['ls'])
    async def last_seen(self, ctx, user: discord.Member):
        async with ctx.db.acquire() as db:
            last_seen = await db.fetchval("SELECT lastseen FROM last_seen WHERE id=$1", user.id)

        if last_seen and user.status.name == "offline":
            _time = funct.time_(last_seen)
            await ctx.send(f"{user.display_name or user.name} was last seen **{_time[0]}d**, **{_time[1]}h**, "
                           f"**{_time[2]}m** and **{_time[3]}s**.")
        elif user.status.name != "offline":
            await ctx.send(f"{user.display_name or user.name} is currently **{user.status.name.capitalize()}**")
        else:
            await ctx.send(f"I don't have data from {user.display_name or user.name}")


def setup(bot):
    bot.add_cog(Utility(bot))
