import logging

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


class Settings:
    """Commands that changes the configuration of the bot for each server."""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            raise commands.CheckFailure("You don't have the `Manage Server` permission.")
        else:
            return True

    @commands.group(name="prefix", invoke_without_command=True)
    async def prefix_(self, ctx):
        """The prefix for this guild."""

        await ctx.send(f"My prefix for {ctx.guild.name} is `{ctx.prefix}`")

    @prefix_.command(name="set")
    async def set_(self, ctx, prefix: str):
        """Change my prefix!"""

        self.bot.prefixes[ctx.guild.id] = prefix

        async with ctx.bot.db.acquire() as db:
            await db.execute("UPDATE settings SET prefix=$1 WHERE guild=$2", prefix, ctx.guild.id)

        await ctx.send(f"Set the prefix to {prefix} for **{ctx.guild.name}**")

    @prefix_.command()
    async def reset(self, ctx):
        """Reset to default prefix"""

        self.bot.prefixes[ctx.guild.id] = None

        async with ctx.bot.db.acquire() as db:
            await db.execute("UPDATE settings SET prefix = NULL WHERE guild=$1", ctx.guild.id)

        await ctx.send("The prefix has been reset to default `>`")

    @commands.command()
    async def disable(self, ctx, *, command):
        """Disables a command"""

        try:
            command_ = ctx.bot.get_command(command.lower())
        except discord.Forbidden:
            return await ctx.send("That's not a command.")

        async with ctx.bot.db.acquire() as db:
            data = await db.fetchval("SELECT disabled FROM settings WHERE guild=$1", ctx.guild.id)

            if data is not None:
                await db.execute("UPDATE settings SET disabled = disabled || ', ' || $1 WHERE guild=$2",
                                 command_.name, ctx.guild.id)
            else:
                await db.execute("UPDATE settings SET disabled = $1 WHERE guild=$2", command_.name, ctx.guild.id)

        if ctx.guild.id not in self.bot.disabled_commands:
            self.bot.disabled_commands[ctx.guild.id] = [command]
        else:
            self.bot.disabled_commands[ctx.guild.id].append(command)

        await ctx.send("The command has been disabled.")

    @commands.command()
    async def enable(self, ctx, *, command):
        """Enables a command"""

        try:
            command_ = ctx.bot.get_command(command.lower())
        except discord.Forbidden:
            return await ctx.send("That's not a command.")

        if self.bot.disabled_commands[ctx.guild.id] is not None:
            self.bot.disabled_commands[ctx.guild.id].remove(command_.name)
        elif ctx.guild.id not in self.bot.disabled_commands:
            await ctx.send("There are no disabled commands.")
        else:
            self.bot.disabled_commands[ctx.guild.id] = None

        async with ctx.bot.db.acquire() as db:
            await db.execute("UPDATE settings SET disabled = $1 WHERE guild=$2",
                             ', '.join(self.bot.disabled_commands[ctx.guild.id]), ctx.guild.id)

        await ctx.send("The command has been enabled.")

    @commands.command()
    async def disabled(self, ctx):
        await ctx.send(
            f"Commands disabled for **{ctx.guild.name}**: {', '.join(self.bot.disabled_commands[ctx.guild.id])}")


def setup(bot):
    bot.add_cog(Settings(bot))
