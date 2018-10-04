import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO)


class Settings:
    """Customize my configuration"""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.author.guild_permissions.manage_guild

    @commands.group(aliases=['config', 'set'], invoke_without_command=True)
    async def settings(self, ctx):
        """List of sub commands that can change my config for this server."""
        pass

    @settings.command()
    async def prefix(self, ctx, prefix: str):
        """Change my prefix!"""

        await ctx.bot.db.execute(
            "UPDATE settings SET prefix=$1 WHERE guild=$2",
            prefix, ctx.guild.id
        )
        await ctx.send(f"Set the prefix to {prefix} for **{ctx.guild.name}**")

    @settings.command()
    async def welcome(self, ctx, welcomemsg: str, channel: discord.channel.TextChannel=None):
        if not channel:
            channel = ctx.channel

        """Insert [member] in text to mention user."""

        await ctx.bot.db.execute("UPDATE settings SET welcomemsg = $1 WHERE guild=$2",
                                 welcomemsg, ctx.guild.id)
        await ctx.bot.db.execute("UPDATE settings SET welcomechannel = $1 WHERE guild=$2",
                                 channel.id, ctx.guild.id)

        await ctx.send(f"The welcome message is {welcomemsg} and the channel is {channel.mention}")

    @settings.command()
    async def resetprefix(self, ctx):
        await ctx.bot.db.execute("UPDATE settings SET prefix = NULL WHERE guild=$1", ctx.guild.id)
        await ctx.send("The prefix has been reset to default (*!)")

    @settings.command()
    async def resetwelcome(self, ctx):
        await ctx.bot.db.execute("UPDATE settings SET welcomemsg = NULL WHERE guild=$1", ctx.guild.id)
        await ctx.bot.db.execute("UPDATE settings SET welcomechannel = NULL WHERE guild=$1", ctx.guild.id)
        await ctx.send("I removed the welcome message!")


def setup(bot):
    bot.add_cog(Settings(bot))
