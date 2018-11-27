import datetime
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

    # Concept inspired by Rapptz
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild.id != 258801388836880385:
            return

        if reaction.emoji == '\N{WHITE MEDIUM STAR}' and reaction.count >= 3:
            msg = await self.bot.db.fetchrow(
                "SELECT * FROM starboard WHERE id=$1",
                reaction.message.id)

            if msg:
                users = []
                async for m in reaction.users:
                    users.append(m.name)

                await self.bot.db.execute(
                    "UPDATE starboard SET reactions = reactions + 1 WHERE id=$1",
                    reaction.message.id)

                await self.bot.db.execute(
                    "UPDATE starboard SET starred_by = starred_by || ', ' || $1 WHERE id=$2",
                    ', '.join(users), reaction.message.id)

                channel = self.bot.get_channel(419365646917435392)
                message = await channel.get_message(msg['bot_message'])
                await message.edit(content=f"**\N{WHITE MEDIUM STAR} {msg['reactions']}** <#{msg['channel']}>")
            else:
                await self.bot.db.execute(
                    "INSERT INTO starboard VALUES($1, $2, $3, $4)",
                    reaction.message.id, reaction.count, reaction.message.channel.id, user.name)

                embed = discord.Embed(color=0xba1c1c)
                embed.set_author(name=reaction.message.author,
                                 icon_url=reaction.message.author.avatar_url)

                embed.description = reaction.message.content
                embed.timestamp = datetime.datetime.utcnow()

                if reaction.message.attachments:
                    attachment = reaction.message.attachments[0].url
                    embed.set_image(url=attachment)

                channel = self.bot.get_channel(419365646917435392)
                bot_msg = await channel.send(f"**\N{WHITE MEDIUM STAR} {reaction.count} "
                                             f"<#{reaction.message.channel}>**", embed=embed)

                await self.bot.execute(
                    "UPDATE starboard SET bot_message = $1 WHERE id=$2",
                    bot_msg.id, reaction.message.id)

        if reaction.emoji != '\N{WHITE MEDIUM STAR}':
            pass

    async def on_reaction_remove(self, reaction, user):
        if reaction.emoji == '\N{WHITE MEDIUM STAR}':
            msg = await self.bot.db.fetchrow(
                "SELECT * FROM starboard WHERE id=$1",
                reaction.message.id)
            if msg:
                await self.bot.db.execute(
                    "UPDATE starboard SET reactions = reactions - 1 WHERE id=$1",
                    reaction.message.id)

                await self.bot.db.execute(
                    "UPDATE starboard SET reactions = $1 WHERE id=$2",
                    reaction.count, reaction.message.id)

                channel = self.bot.get_channel(419365646917435392)
                message = await channel.get_message(msg['bot_message'])
                await message.edit(content=f"**\N{WHITE MEDIUM STAR} {msg['reactions']} <#{msg['channel']}>**")

        if reaction.emoji == '\N{WHITE MEDIUM STAR}' and reaction.count < 3:
            msg = await self.bot.db.fetchrow(
                "SELECT * FROM starboard WHERE id=$1",
                reaction.message.id)

            if msg:
                channel = self.bot.get_channel(419365646917435392)
                message = await channel.get_message(msg['bot_message'])
                await message.delete()
                await self.bot.db.execute("DELETE FROM starboard WHERE id=$1",
                                          reaction.message.id)

        if reaction.emoji != '\N{WHITE MEDIUM STAR}':
            pass

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, commands.CommandInvokeError):
            if ctx.command.name == 'ud':
                await ctx.send(
                    f'There are no results found on Urban Dictionary.'
                )

            elif ctx.command.name == 'wiki':
                await ctx.send(
                    f"That page does not exist, you can create it using **{ctx.prefix}wiki create**"
                )

            else:
                await ctx.send(f"**Error:** {str(error.original).title()}")

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=0xba1c1c)
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
            embed = discord.Embed(color=0xba1c1c)
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
