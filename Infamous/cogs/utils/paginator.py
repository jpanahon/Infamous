# From EvieePy and Rapptz but edited by me
import asyncio
import inspect
import itertools
import re

import discord


async def pager(entries, chunk: int):
    for x in range(0, len(entries), chunk):
        yield entries[x:x + chunk]


class EvieeBed(discord.Embed):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class CannotPaginate(Exception):
    pass


class Pages:
    def __init__(self, ctx, *, entries, per_page=12, show_entry_count=True):
        self.bot = ctx.bot
        self.entries = entries
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author
        self.per_page = per_page
        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1
        self.maximum_pages = pages
        self.maximum_pages = pages
        self.embed = discord.Embed(colour=self.bot.embed_color)
        self.paginating = len(entries) > per_page
        self.show_entry_count = show_entry_count
        self.reaction_emojis = [
            ('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.first_page),
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
            ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', self.last_page),
            ('\N{INPUT SYMBOL FOR NUMBERS}', self.numbered_page),
            ('\N{BLACK SQUARE FOR STOP}', self.stop_pages),
        ]

        if ctx.guild is not None:
            self.permissions = self.channel.permissions_for(ctx.guild.me)
        else:
            self.permissions = self.channel.permissions_for(ctx.bot.user)

        if not self.permissions.embed_links:
            raise CannotPaginate('Bot does not have embed links permission.')

        if not self.permissions.send_messages:
            raise CannotPaginate('Bot cannot send messages.')

        if self.paginating:
            # verify we can actually use the pagination session
            if not self.permissions.add_reactions:
                raise CannotPaginate('Bot does not have add reactions permission.')

            if not self.permissions.read_message_history:
                raise CannotPaginate('Bot does not have Read Message History permission.')

    def get_page(self, page):
        base = (page - 1) * self.per_page
        return self.entries[base:base + self.per_page]

    async def show_page(self, page, *, first=False):
        self.current_page = page
        entries = self.get_page(page)
        p = []
        for index, entry in enumerate(entries, 1 + ((page - 1) * self.per_page)):
            p.append(entry)

        if self.maximum_pages > 1:
            if self.show_entry_count:
                text = f'Page {page} of {self.maximum_pages} ({len(self.entries)} entries)'
            else:
                text = f'Page {page} of {self.maximum_pages}'

            self.embed.set_footer(text=text)

        if not self.paginating:
            self.embed.description = '\n'.join(p)
            return await self.channel.send(embed=self.embed)

        if not first:
            self.embed.description = '\n'.join(p)
            await self.message.edit(embed=self.embed)
            return

        self.embed.description = '\n'.join(p)
        self.message = await self.channel.send(embed=self.embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 1 and reaction in ('\u23ed', '\u23ee'):
                # no |<< or >>| buttons if we only have two pages
                # we can't forbid it if someone ends up using it but remove
                # it from the default set
                continue

            await self.message.add_reaction(reaction)

    async def checked_show_page(self, page):
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self):
        """goes to the first page"""
        await self.show_page(1)

    async def last_page(self):
        """goes to the last page"""
        await self.show_page(self.maximum_pages)

    async def next_page(self):
        """goes to the next page"""
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self):
        """goes to the previous page"""
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self):
        if self.paginating:
            await self.show_page(self.current_page)

    async def numbered_page(self):
        """lets you type a page number to go to"""
        to_delete = []
        pass
        to_delete.append(await self.channel.send('What page do you want to go to?', delete_after=5))

        def message_check(m):
            return m.author == self.author and \
                   self.channel == m.channel and \
                   m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', check=message_check, timeout=30.0)
        except asyncio.TimeoutError:
            to_delete.append(await self.channel.send('Took too long.'))
            await asyncio.sleep(5)
        else:
            page = int(msg.content)
            to_delete.append(msg)
            if page != 0 and page <= self.maximum_pages:
                await self.show_page(page)
            else:
                to_delete.append(await self.channel.send(f'Invalid page given. ({page}/{self.maximum_pages})'))
                await asyncio.sleep(5)

        try:
            await self.channel.delete_messages(to_delete)
        except Exception:
            pass

    async def stop_pages(self):
        """stops the interactive pagination session"""
        try:
            await self.message.clear_reactions()
        except discord.Forbidden:
            await self.message.delete()

        self.paginating = False

    def react_check(self, reaction, user):
        if user is None or user.id != self.author.id:
            return False

        if reaction.message.id != self.message.id:
            return False

        for (emoji, func) in self.reaction_emojis:
            if reaction.emoji == emoji:
                self.match = func
                return True
        return False

    async def paginate(self):
        """Actually paginate the entries and run the interactive loop if necessary."""
        first_page = self.show_page(1, first=True)
        if not self.paginating:
            await first_page
        else:
            self.bot.loop.create_task(first_page)

        while self.paginating:
            if not self.message.guild.me.guild_permissions.manage_messages:
                done, pending = await asyncio.wait([
                    self.bot.wait_for('reaction_add', check=self.react_check, timeout=120.0),
                    self.bot.wait_for('reaction_remove', check=self.react_check, timeout=120.0)
                ], return_when=asyncio.FIRST_COMPLETED)
                try:
                    done.pop().result()
                except asyncio.TimeoutError:
                    self.paginating = False
                    try:
                        await self.message.clear_reactions()
                    except:
                        await self.message.delete()
                    finally:
                        break

                for future in pending:
                    future.cancel()

                await self.match()
            else:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=self.react_check, timeout=120.0)
                except asyncio.TimeoutError:
                    self.paginating = False
                    try:
                        await self.message.clear_reactions()
                    except:
                        await self.message.delete()
                    finally:
                        break

                try:
                    await self.message.remove_reaction(reaction, user)
                except discord.HTTPException:
                    pass

                await self.match()


class SimplePaginator:
    __slots__ = ('entries', 'extras', 'title', 'description', 'colour', 'footer', 'length', 'prepend', 'append',
                 'fmt', 'timeout', 'ordered', 'controls', 'controller', 'pages', 'current', 'previous', 'eof', 'base',
                 'names')

    def __init__(self, **kwargs):
        self.entries = kwargs.get('entries', None)
        self.extras = kwargs.get('extras', None)

        self.title = kwargs.get('title', None)
        self.description = kwargs.get('description', None)
        self.colour = kwargs.get('colour', 0xffd4d4)
        self.footer = kwargs.get('footer', None)

        self.length = kwargs.get('length', 10)
        self.prepend = kwargs.get('prepend', '')
        self.append = kwargs.get('append', '')
        self.fmt = kwargs.get('fmt', '')
        self.timeout = kwargs.get('timeout', 90)
        self.ordered = kwargs.get('ordered', False)

        self.controller = None
        self.pages = []
        self.names = []
        self.base = None

        self.current = 0
        self.previous = 0
        self.eof = 0

        self.controls = {'⏮': 0.0, '◀': -1, '▶': +1,
                         '⏭': None, '🔢': 'selector', '⏹': 'stop'}

    async def indexer(self, ctx, ctrl):
        if ctrl == 'stop':
            ctx.bot.loop.create_task(self.stop_controller(self.base))
        elif ctrl == 'selector':
            ctx.bot.loop.create_task(self.wait_for(ctx))
        elif isinstance(ctrl, int):
            self.current += ctrl
            if self.current > self.eof or self.current < 0:
                self.current -= ctrl
        else:
            self.current = int(ctrl)

    async def reaction_controller(self, ctx):
        bot = ctx.bot
        author = ctx.author

        self.base = await ctx.send(embed=self.pages[0])

        if len(self.pages) == 1:
            await self.base.add_reaction('⏹')
        else:
            for reaction in self.controls:
                try:
                    await self.base.add_reaction(reaction)
                except discord.HTTPException:
                    return

        def check(r, u):
            if str(r) not in self.controls.keys():
                return False
            elif u.id == bot.user.id or r.message.id != self.base.id:
                return False
            elif u.id != author.id:
                return False
            return True

        while True:
            if not ctx.guild.me.guild_permissions.manage_messages:
                done, pending = await asyncio.wait([
                    bot.wait_for('reaction_add', check=check, timeout=self.timeout),
                    bot.wait_for('reaction_remove', check=check, timeout=self.timeout)
                ], return_when=asyncio.FIRST_COMPLETED)

                try:
                    react, user = done.pop().result()
                except asyncio.TimeoutError:
                    return ctx.bot.loop.create_task(self.stop_controller(self.base))

                for future in pending:
                    future.cancel()

                control = self.controls.get(str(react))

            else:
                try:
                    react, user = await bot.wait_for('reaction_add', check=check, timeout=self.timeout)
                except asyncio.TimeoutError:
                    return ctx.bot.loop.create_task(self.stop_controller(self.base))

                control = self.controls.get(str(react))

                try:
                    await self.base.remove_reaction(react, user)
                except discord.HTTPException:
                    pass

            self.previous = self.current
            await self.indexer(ctx, control)

            if self.previous == self.current:
                continue

            try:
                await self.base.edit(embed=self.pages[self.current])
            except KeyError:
                pass

    async def stop_controller(self, message):
        try:
            if not message.guild.me.guild_permissions.manage_messages:
                await message.delete()
            else:
                await message.clear_reactions()
        except discord.HTTPException:
            pass

        try:
            self.controller.cancel()
        except Exception:
            pass

    def formmater(self, chunk):
        return '\n'.join(f'{self.prepend}{self.fmt}{value}{self.fmt[::-1]}{self.append}' for value in chunk)

    def set_pages(self):
        length = len(self.pages)

        for index, embed in enumerate(self.pages):
            embed.set_footer(text=f'Page {index + 1} of {length}')

        for index, name in enumerate(self.names):
            self.names[index] = f'{index + 1} - `{name}`'

    async def del_msg(self, *args):
        for msg in args:
            try:
                await msg.delete()
            except discord.HTTPException:
                return

    async def wait_for(self, ctx):
        def check(m):
            return m.author == ctx.author

        msg = await ctx.send("What page would you like to turn to?")

        while True:
            try:
                resp = await ctx.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await self.del_msg(msg)

            try:
                index = int(resp.content)
            except ValueError:
                await ctx.send('Invalid number, please enter a valid page number.', delete_after=10)
                return await self.del_msg(resp)

            if index > len(self.pages) or index < 1:
                await ctx.send('Invalid number, please enter a valid page number.', delete_after=10)
                return await self.del_msg(resp)
            else:
                await self.del_msg(msg, resp)
                self.previous = self.current
                self.current = index - 1
                try:
                    return await self.base.edit(embed=self.pages[self.current])
                except KeyError:
                    pass

    async def paginate(self, ctx):
        if self.extras:
            self.pages = [p for p in self.extras if isinstance(p, discord.Embed)]

        if self.entries:
            chunks = [c async for c in pager(self.entries, self.length)]

            for index, chunk in enumerate(chunks):
                page = discord.Embed(title=f'{self.title} - {index + 1}/{len(chunks)}', color=self.colour)
                page.description = self.formmater(chunk)

                if self.footer:
                    page.set_footer(text=self.footer)

                self.pages.append(page)

        if not self.pages:
            raise await ctx.send('There must be enough data to create at least 1 page for pagination.')

        self.eof = float(len(self.pages) - 1)
        self.controls['⏭'] = self.eof
        self.controller = ctx.bot.loop.create_task(self.reaction_controller(ctx))


_mention = re.compile(r'<@\!?([0-9]{1,19})>')


def cleanup_prefix(bot, prefix):
    m = _mention.match(prefix)
    if m:
        user = bot.get_user(int(m.group(1)))
        if user:
            return f'@{user.name} '
    return prefix


async def _can_run(cmd, ctx):
    try:
        return await cmd.can_run(ctx)
    except:
        return False


def _command_signature(cmd):
    result = [cmd.qualified_name]
    if cmd.usage:
        result.append(cmd.usage)
        return ' '.join(result)

    params = cmd.clean_params
    if not params:
        return ' '.join(result)

    for name, param in params.items():
        if param.default is not param.empty:
            should_print = param.default if isinstance(param.default, str) else param.default is not None
            if should_print:
                result.append(f'[{name}={param.default!r}]')
            else:
                result.append(f'[{name}]')
        elif param.kind == param.VAR_POSITIONAL:
            result.append(f'[{name}...]')
        else:
            result.append(f'<{name}>')

    return ' '.join(result)


class HelpPaginator(Pages):
    def __init__(self, ctx, entries, *, per_page=4):
        super().__init__(ctx, entries=entries, per_page=per_page)
        self.total = len(entries)

    @classmethod
    async def from_cog(cls, ctx, cog):
        cog_name = cog.__class__.__name__

        entries = sorted(ctx.bot.get_cog_commands(cog_name), key=lambda c: c.name)
        entries = [cmd for cmd in entries if (await _can_run(cmd, ctx)) and not cmd.hidden]

        self = cls(ctx, entries)
        self.title = f'{cog_name} Commands'
        self.description = inspect.getdoc(cog)
        self.prefix = cleanup_prefix(ctx.bot, ctx.prefix)
        return self

    @classmethod
    async def from_command(cls, ctx, command):
        try:
            entries = sorted(command.commands, key=lambda c: c.name)
        except AttributeError:
            entries = []
        else:
            entries = [cmd for cmd in entries if (await _can_run(cmd, ctx)) and not cmd.hidden]

        self = cls(ctx, entries)
        self.title = command.signature

        if command.description:
            self.description = f'{command.description}\n\n{command.help}'
        else:
            self.description = command.help or 'No help given.'

        self.prefix = cleanup_prefix(ctx.bot, ctx.prefix)

        return self

    @classmethod
    async def from_bot(cls, ctx):
        def key(c):
            return c.cog_name or '\u200bMisc'

        entries = sorted(ctx.bot.commands, key=key)
        nested_pages = []
        per_page = 5

        for cog, commands in itertools.groupby(entries, key=key):
            plausible = [cmd for cmd in commands if (await _can_run(cmd, ctx)) and not cmd.hidden]
            if len(plausible) == 0:
                continue

            description = ctx.bot.get_cog(cog)
            if description is None:
                description = discord.Embed.Empty
            else:
                description = inspect.getdoc(description) or discord.Embed.Empty

            nested_pages.extend(
                (cog, description, plausible[i:i + per_page]) for i in range(0, len(plausible), per_page))

        self = cls(ctx, nested_pages, per_page=1)
        self.prefix = cleanup_prefix(ctx.bot, ctx.prefix)

        self.get_page = self.get_bot_page
        self._is_bot = True

        self.total = sum(len(o) for _, _, o in nested_pages)
        return self

    def get_bot_page(self, page):
        cog, description, commands = self.entries[page - 1]
        new_name = {"Rpg2": "Infamous RPG v2", "Imagem": "Image Manipulation"}
        if cog in new_name.keys():
            cog = new_name[cog]

        self.title = f"{cog} Commands"
        self.description = description
        return commands

    async def show_page(self, page, *, first=False):
        self.current_page = page
        entries = self.get_page(page)

        self.embed.clear_fields()
        self.embed.title = self.title
        self.embed.description = self.description
        self.embed.set_footer(text=f'Use the reactions to navigate | '
                                   f'Use "{self.prefix}help command" for info on a command.')

        signature = _command_signature

        for entry in entries:
            self.embed.add_field(name=signature(entry), value=entry.short_doc or "Nothing...", inline=False)

        if self.maximum_pages:
            self.embed.set_author(
                name=f'Infamous | Page {page} of {self.maximum_pages}',
                icon_url=
                "https://cdn.discordapp.com/avatars/429461624341135361/a279705cffe9ef364163f76ec4cd1657.png?size=1024"
            )

        if not self.paginating:
            return await self.channel.send(embed=self.embed)

        if not first:
            await self.message.edit(embed=self.embed)
            return

        self.message = await self.channel.send(embed=self.embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 2 and reaction in ('\u23ed', '\u23ee'):
                continue

            await self.message.add_reaction(reaction)
