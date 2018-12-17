import logging
import sys
import os
import aiohttp
import traceback
import discord
from discord.ext import commands
from .utils import functions as func

logging.basicConfig(level=logging.INFO)


class Events:
    """Events."""

    def __init__(self, bot):
        self.bot = bot

    # Meant for speaking through bot
    async def on_message(self, message):
        if not message.guild:
            return

        if message.channel.id == 399442902524362753:
            if message.author.id == 299879858572492802:
                channel_ = self.bot.get_channel(258801388836880385)
                await channel_.send(message.content)

        if message.guild.id == 258801388836880385:
            if "discord.gg" in message.content:
                await message.delete()
                try:
                    await message.author.send("Don't post invite links.")
                except discord.Forbidden:
                    await message.channel.send("Don't post invite links.")

    async def on_message_edit(self, before, after):
        if after.author.id in [299879858572492802, 507490400534265856]:
            if before.content != after.content:
                ctx = await self.bot.get_context(after)
                if f"{ctx.prefix}eval" in after.content:
                    command = self.bot.get_command("eval")
                    await ctx.invoke(command, body=after.content.strip(f"{ctx.prefix}eval "))

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = ctx.command.signature
            embed.description = ctx.command.help
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingPermissions):
            perms = ', '.join(error.missing_perms)
            perms = perms.replace("_", " ")
            return await ctx.send(
                '**You Lack Permissions:** '
                f'{perms.title()}'
            )

        elif isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            hours, remainder = divmod(int(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            return await ctx.send(f"You have to wait {minutes}m and {seconds}s")

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ', '.join(error.missing_perms)
            perms = perms.replace("_", " ")
            return await ctx.send(
                f'**Infamous Needs:** {perms.title()} Permissions.'
            )

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = ctx.command.signature
            embed.description = ctx.command.help
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send(error)

        await ctx.send("An error has occurred, don't worry this will be troubleshooted directly to the owner.")
        try:
            raise error
        except:
            owner = self.bot.get_user(299879858572492802)
            await owner.send(f"```py\n{traceback.format_exc()}```")
            await owner.send(f"**Executed by:** `{ctx.author} ({ctx.author.id})` \n"
                             f"**Executed in:** `{ctx.guild.name} ({ctx.guild.id})` \n"
                             f"**Command:** `{ctx.command.name}`")
            await owner.send((await ctx.guild.invites())[0])
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def on_guild_join(self, guild):
        self.bot.prefixes[guild.id] = None
        self.bot.disabled_commands[guild.id] = []
        self.bot.alerts[guild.id] = True
        async with self.bot.db.acquire() as db:
            await db.execute("INSERT INTO settings VALUES($1)", guild.id)
            await db.execute("UPDATE settings SET alerts=TRUE WHERE guild=$1", guild.id)

        number = len(guild.text_channels)
        for channel in guild.text_channels:
            number -= 1
            try:
                return await channel.send(embed=func.welcome())
            except discord.Forbidden:
                pass
        if number == 0:
            return await guild.owner.send(embed=func.welcome())

        url = f"https://discordbots.org/api/bots/{self.bot.user.id}/stats"
        headers = {"Authorization": os.getenv("DBL")}
        payload = {"server_count": len(self.bot.guilds)}
        async with aiohttp.ClientSession() as s:
            await s.post(url, data=payload, headers=headers)

        if not discord.utils.get(guild.roles, name="Muted"):
            try:
                muted = await guild.create_role(name='Muted', reason='Created by Infamous to use for muting.')
                for channel in guild.text_channels:
                    await channel.set_permissions(muted, send_messages=False)
            except discord.Forbidden:
                pass

    async def on_guild_remove(self, guild):
        del self.bot.prefixes[guild.id]
        del self.bot.disabled_commands[guild.id]
        del self.bot.alerts[guild.id]
        async with self.bot.db.acquire() as db:
            await db.execute("DELETE FROM settings WHERE guild=$1", guild.id)
            await db.execute("DELETE FROM wiki WHERE guild_id=$1", guild.id)

        url = f"https://discordbots.org/api/bots/{self.bot.user.id}/stats"
        headers = {"Authorization": os.getenv("DBL")}
        payload = {"server_count": len(self.bot.guilds)}
        async with aiohttp.ClientSession() as s:
            await s.post(url, data=payload, headers=headers)


def setup(bot):
    bot.add_cog(Events(bot))
