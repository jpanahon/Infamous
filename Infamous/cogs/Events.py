import logging
import sys
import traceback
import discord
from discord.ext import commands

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
                if "eval" in after.content:
                    command = self.bot.get_command("eval")
                    ctx = await self.bot.get_context(after)
                    await ctx.invoke(command, body=after.content.strip(f"{ctx.prefix}eval"))

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
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingPermissions):
            perms = ', '.join(error.missing_perms)
            perms = perms.replace("_", " ")
            return await ctx.send(
                '**You Lack Permissions:** '
                f'{perms.title()}'
            )

        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name == "daily":
                cooldown = error.retry_after
                cooldown = round(cooldown, 2)
                hours, remainder = divmod(int(cooldown), 3600)
                minutes, seconds = divmod(remainder, 60)
                days, hours = divmod(hours, 24)
                await ctx.send(f"You have to wait {days}d, {hours}h, {minutes}m, {seconds}s.")
            elif ctx.command.name == "duel":
                await ctx.send(f"There is currently a match going on in {ctx.channel.mention}")
            else:
                seconds = error.retry_after
                seconds = round(seconds, 2)
                hours, remainder = divmod(int(seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"You have to wait {minutes}m and {seconds}s")

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ', '.join(error.missing_perms)
            perms = perms.replace("_", " ")
            return await ctx.send(
                f'**Infamous Needs:** {perms.title()} Permissions.'
            )

        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(
                f'You cannot execute **{ctx.command}** in a Private Message.'
            )

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = ctx.command.signature
            embed.description = ctx.command.help
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(error)

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def on_typing(self, channel, user, when):
        if user.id == 299879858572492802:
            if channel.id == 399442902524362753:
                channel_ = self.bot.get_channel(258801388836880385)
                await channel_.trigger_typing()
        else:
            pass

    async def on_guild_join(self, guild):
        self.bot.prefixes[guild.id] = None
        await self.bot.db.execute("INSERT INTO settings VALUES($1)", guild.id)

    async def on_guild_remove(self, guild):
        del self.bot.prefixes[guild.id]
        await self.bot.db.execute("DELETE FROM settings WHERE guild=$1", guild.id)


def setup(bot):
    bot.add_cog(Events(bot))
