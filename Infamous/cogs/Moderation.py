import asyncio
import logging

import discord
from discord.ext import commands
from .utils import checks

logging.basicConfig(level=logging.INFO)


class Moderation:
    """Commands to get your users in place."""

    def __init__(self, bot):
        self.bot = bot

    # Mute
    @commands.command(aliases=['shutup', 'stfu'])
    @commands.has_permissions(manage_messages=True)
    @checks.guild_only()
    async def mute(self, ctx, user: discord.Member, *, string):
        """Mutes mentioned user."""

        muted = discord.utils.get(ctx.guild.roles, name="Muted")

        if user.guild_permissions.manage_messages:
            return await ctx.send("You can't mute another staff member.")

        if muted in user.roles:
            await ctx.send(f"{user.mention} is already muted! \n"
                           f"Type `{ctx.prefix}unmute <@{user.id}>` to unmute them.")
        else:
            await ctx.send(f'{user.mention} has been muted for: {string}')
            await user.add_roles(muted)

        try:
            await user.send(f'You have been muted by `{ctx.author}` for: {string}')
            await ctx.author.send(f'Type `{ctx.prefix}unmute <@{user.id}>` to unmute.')
        except:
            await ctx.author.send(f'Unable to send `{user}` a DM.')
            await ctx.author.send(f'Type `{ctx.prefix}unmute <@{user.id}>` to unmute.')
            pass

    @commands.command(aliases=['am'])
    @commands.has_permissions(manage_messages=True)
    @checks.guild_only()
    async def tempmute(self, ctx, user: discord.Member, time: int, *, reason):
        """Temporarily mutes the mentioned user."""

        hours, remainder = divmod(int(time), 3600)
        minutes, seconds = divmod(remainder, 60)

        muted = discord.utils.get(ctx.guild.roles, name="Muted")

        if user.guild_permissions.manage_messages:
            return await ctx.send("You can't mute another staff member.")

        if muted in user.roles:
            await ctx.send(f'{user.mention} has been temporarily muted for: {reason} \n '
                           f'They will be unmuted in {hours}h, {minutes}m and {seconds}s')

            await user.add_roles(muted)

            try:
                await user.send(f'You have been temporarily muted by `{ctx.author}` for: {reason} \n'
                                f'You may talk again in {hours}h, {minutes}m and {seconds}s')

                await ctx.author.send(f'Type `{ctx.prefix}unmute <@{user.id}>` to unmute.')
            except:
                await ctx.author.send(f'Unable to send `{user}` a DM.')
                await ctx.author.send(f'Type `{ctx.prefix}unmute <@{user.id}>` to unmute.')
                pass

            await asyncio.sleep(time)
            await user.remove_roles(muted)
            await ctx.send(f"{user.mention} has been unmuted after {hours}h, {minutes}m and {seconds}s")

            try:
                await user.send(f'You have been unmuted after {hours}h, {minutes}m and {seconds}s')
            except:
                await ctx.author.send(f'Unable to send `{user}` a DM.')
                pass
        else:
            return await ctx.send("They are already muted.")

    # Unmute
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @checks.guild_only()
    async def unmute(self, ctx, user: discord.Member):
        """Unmutes mentioned user."""

        muted = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted in user.roles:
            await user.remove_roles(muted)
            await ctx.send(f"{user.mention} has been unmuted.")
        else:
            await ctx.send(f"{user.display_name} was not muted.")

        try:
            await user.send(f'You have been unmuted by `{ctx.author}`')
        except:
            await ctx.author.send(f'Unable to DM `{user}`.')
            pass

    # Kick
    @commands.command()
    @commands.has_permissions(kick_members=True)
    @checks.guild_only()
    async def kick(self, ctx, user: discord.Member, *, string):
        """Kicks mentioned user from the guild."""

        notice = (f'You have been kicked from {ctx.guild} for: {string} \n'
                  'You may rejoin using: https://discord.gg/NY2MSA3')
        try:
            await user.send(notice)
        except:
            await ctx.author.send(f'Unable to send `{user}` a DM.')
            pass

        await ctx.guild.kick(user=user, reason=string)
        await ctx.send(f'{user.mention} has been kicked from the server for: {string}')

    # Ban
    @commands.command(aliases=['gtfo'])
    @commands.has_permissions(ban_members=True)
    @checks.guild_only()
    async def ban(self, ctx, user: discord.Member, *, string):
        """Bans the mentioned user from the guild."""

        notice = (f'You have been banned from {ctx.guild} for: {string} \n'
                  f'You may contact {ctx.author.mention} for appeal.')
        try:
            await user.send(notice)
            await ctx.author.send(f"You can unban the user by typing in `f.unban {user.id}`")
        except:
            await ctx.author.send(f'Unable to send `{user}` a DM.')
            await ctx.author.send(f"You can unban the user by typing in `f.unban {user.id}`")
            pass

        await ctx.guild.ban(user=user, reason=f'By: {ctx.author} \nReason: {string}')
        await ctx.send(f'<@{user.id}> has been banned from the server for: {string}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @checks.guild_only()
    async def softban(self, ctx, user: discord.Member, *, reason):
        await ctx.guild.ban(user=user, reason=f'By: {ctx.author} \n Reason: {reason}')

        notice = (f'You have been banned from {ctx.guild} for: {reason} \n'
                  f'You may contact {ctx.author.mention} for appeal.')
        try:
            await user.send(notice)
            await ctx.author.send(f"You can unban the user by typing in `f.unban {user.id}`")
        except:
            await ctx.author.send(f'Unable to send `{user}` a DM.')
            await ctx.author.send(f"You can unban the user by typing in `f.unban {user.id}`")
            pass

        await ctx.guild.unban(user=user, reason="All is forgiven.")
        await ctx.send(f"<@{user.id}> has been banned from the server for: {reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @checks.guild_only()
    async def unban(self, ctx, identification: int):
        """Unbans the mentioned user from the guild."""

        user = await self.bot.get_user_info(identification)
        await ctx.guild.unban(user, reason='All has been forgiven.')

        try:
            await ctx.send(f'`{user}` has been unbanned from the server.')
        except:
            await ctx.send(f'Unable to unban `{user}`')
            pass

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @checks.guild_only()
    async def purge(self, ctx, amount: int):
        """Deletes specified amount of messages."""

        await ctx.channel.purge(limit=amount)
        await ctx.send(f'Deleted {amount} messages.', delete_after=5)

        
def setup(bot):
    bot.add_cog(Moderation(bot))
