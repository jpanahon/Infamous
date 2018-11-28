import logging

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)


class Settings:
    """Customize my configuration."""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.author.guild_permissions.manage_guild

    @commands.group(name="prefix", invoke_without_command=True)
    async def prefix_(self, ctx):
        """The prefix for this guild."""

        await ctx.send(f"My prefix for {ctx.guild.name} is `{ctx.prefix}`")

    @prefix_.command(name="set")
    async def set_(self, ctx, prefix: str):
        """Change my prefix!"""

        self.bot.prefixes[ctx.guild.id] = prefix
        await ctx.bot.db.execute(
            "UPDATE settings SET prefix=$1 WHERE guild=$2",
            prefix, ctx.guild.id
        )
        await ctx.send(f"Set the prefix to {prefix} for **{ctx.guild.name}**")

    @prefix_.command()
    async def reset(self, ctx):
        """Reset to default prefix"""

        self.bot.prefixes[ctx.guild.id] = None
        await ctx.bot.db.execute("UPDATE settings SET prefix = NULL WHERE guild=$1", ctx.guild.id)
        await ctx.send("The prefix has been reset to default `>`")

    @commands.command()
    async def disable(self, ctx, *, command):
        """Disables a command"""

        try:
            command_ = ctx.bot.get_command(command.lower())
        except discord.Forbidden:
            return await ctx.send("That's not a command.")

        await ctx.bot.db.execute("INSERT INTO disabled VALUES($1, $2)", ctx.guild.id, command_.name)
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

        await ctx.bot.db.execute("DELETE FROM disabled WHERE id=$1 AND command=$2", ctx.guild.id, command_.name)
        await ctx.send("The command has been enabled.")


def setup(bot):
    bot.add_cog(Settings(bot))
