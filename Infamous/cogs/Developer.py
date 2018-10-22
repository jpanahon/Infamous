import copy
import datetime
import inspect
import logging
import os
import random

import aiohttp
import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


class Developer:
    """Developer Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension_name: str):
        """Loads a cog."""

        try:
            self.bot.load_extension(f'cogs.{extension_name.capitalize()}')
        except (AttributeError, ImportError):
            await ctx.message.add_reaction(':BlurpleX:452390303698124800')
            return
        await ctx.message.add_reaction(':BlurpleCheck:452390337382449153')
        await ctx.message.delete()

    @commands.command(aliases=['r'], hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, module):
        """Reloads a cog."""

        try:
            self.bot.unload_extension(f'cogs.{module.capitalize()}')
            self.bot.load_extension(f'cogs.{module.capitalize()}')
        except Exception:
            await ctx.message.add_reaction(':BlurpleX:452390303698124800')
        else:
            await ctx.message.add_reaction(':BlurpleCheck:452390337382449153')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, module):
        """Unloads a cog."""

        try:
            self.bot.unload_extension(f'cogs.{module.capitalize()}')
        except Exception:
            await ctx.message.add_reaction(':BlurpleX:452390303698124800')
        else:
            await ctx.message.add_reaction(':BlurpleCheck:452390337382449153')
            await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def quit(self, ctx):
        """Closes the bot."""

        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar_url)
        embed.description = f'Well that was a good {days}d {hours}h {minutes}m {seconds}s of activity.'
        await ctx.send(embed=embed)
        await self.bot.db.close()
        await self.bot.logout()

    @commands.command(aliases=['rs'], hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restart all cogs."""

        for cog in self.bot.cogs:
            try:
                self.bot.unload_extension(f'cogs.{cog}')
                self.bot.load_extension(f'cogs.{cog}')
            except Exception as e:
                print(f'**`ERROR:`** {type(e).__name__} - {e}')

        await ctx.message.add_reaction(':BlurpleCheck:452390337382449153')

    @commands.group(case_insensitive=True, invoke_without_command=True, hidden=True)
    async def find(self, ctx, discrim: str):
        """Find people with the same discriminator."""

        if len(discrim) > 5 or len(discrim) < 4:
            return await ctx.send('There must be 4 digits.')

        if "#" in discrim:
            discrim = discrim.strip("#")

        if discrim.isalpha():
            return await ctx.send('They must be numbers.')

        user = [str(x.name) for x in ctx.guild.members if x.discriminator == f'{discrim}']
        users = ' \n'.join(user)

        if len(user) >= 20:
            users = ', '.join(user)

        if not users:
            users = None

        embed = discord.Embed(color=0xba1c1c)
        embed.title = f'List of users with the #{str(discrim)} discriminator'
        embed.description = f'`{users}`'
        embed.set_footer(text=f'{len(user)} users found')
        await ctx.send(embed=embed)

    @find.command()
    async def user(self, ctx, id: int):
        """Shows who the user id belongs to."""

        if len(str(id)) < 17:
            return await ctx.send('That is not a user id.')

        try:
            user = ctx.guild.get_member(id)
            embed = discord.Embed(color=0xba1c1c)
            embed.set_author(name=user)
            embed.title = 'Discord ID'
            embed.description = id
            embed.set_thumbnail(url=user.avatar_url)
            embed.add_field(name='Created at', value=user.created_at.strftime('%a %b %m %Y at %I:%M %p %Z'),
                            inline=False)

            await ctx.send(embed=embed)
        except:
            user = await self.bot.get_user_info(id)
            embed = discord.Embed(color=0xba1c1c)
            embed.set_author(name=user)
            embed.title = 'Discord ID'
            embed.description = id
            embed.set_thumbnail(url=user.avatar_url)
            embed.add_field(name='Created at', value=user.created_at.strftime('%a %b %m %Y at %I:%M %p %Z'),
                            inline=False)
            await ctx.send(embed=embed)
            pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def say(self, ctx, *, text):
        """Make the bot say anything."""

        await ctx.send(text)

    @commands.command(hidden=True)
    async def loop(self, ctx, time: int, command: str):
        """Executes a command for x times."""

        for x in range(time):
            x = self.bot.get_command(command)
            await ctx.invoke(x)

    @commands.group(case_insensitive=True, invoke_without_command=True, hidden=True)
    @commands.is_owner()
    async def imitate(self, ctx, user: discord.Member, *, text):
        """Use webhooks to imitate a user."""
        await ctx.message.delete()
        url = 'https://discordapp.com/api/webhooks/432064261120851979/' \
              '6Ems0Op4A2rEGSG5b0lGjVd1n1qxcYLvFJUxdweUKs3dNGDD8BKn6LgpFsAWnLkWtUb7'

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            await webhook.send(text, username=str(user.display_name), avatar_url=user.avatar_url)

    @imitate.command(hidden=True)
    @commands.is_owner()
    async def random(self, ctx, *, text):
        """Imitate a random person."""

        await ctx.message.delete()
        user = random.choice([x for x in ctx.guild.members if not x.bot])
        url = 'https://discordapp.com/api/webhooks/432064261120851979/' \
              '6Ems0Op4A2rEGSG5b0lGjVd1n1qxcYLvFJUxdweUKs3dNGDD8BKn6LgpFsAWnLkWtUb7'

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            await webhook.send(text, username=user.display_name, avatar_url=user.avatar_url)

    @imitate.command()
    @commands.is_owner()
    async def custom(self, ctx, user: int, *, text):
        """Imitate a person outside the server"""

        await ctx.message.delete()
        user = await self.bot.get_user_info(user)
        url = 'https://discordapp.com/api/webhooks/432064261120851979/' \
              '6Ems0Op4A2rEGSG5b0lGjVd1n1qxcYLvFJUxdweUKs3dNGDD8BKn6LgpFsAWnLkWtUb7'

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            await webhook.send(text, username=user.display_name, avatar_url=user.avatar_url)

    @commands.command(hidden=True)
    async def clear(self, ctx, *, amount: int):
        """Deletes bot messages."""

        async for m in ctx.channel.history(limit=amount + 1):
            if m.author.id == self.bot.user.id:
                await m.delete()

        await ctx.send(f"Cleared `{amount}` messages!", delete_after=5)

    # Originally from Rapptz
    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Shows source code for each command """

        source_url = 'https://github.com/OneEyedKnight/Infamous'
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        if not obj.callback.__module__.startswith('discord'):
            location = os.path.relpath(src.co_filename).replace('\\', '/')
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'

        final_url = f'{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'

        await ctx.send(final_url)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sudo(self, ctx, member: discord.Member, *, command):
        fake_msg = copy.copy(ctx.message)
        fake_msg._update(ctx.message.channel, dict(content=ctx.prefix + command))
        fake_msg.author = member
        new_ctx = await ctx.bot.get_context(fake_msg)
        await ctx.bot.invoke(new_ctx)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def test(self, ctx):
        for i in self.bot.commands:
            try:
                await ctx.invoke(i)
            except:
                pass


def setup(bot):
    bot.add_cog(Developer(bot))
