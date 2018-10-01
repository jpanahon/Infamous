import asyncio
import logging
import random

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

logging.basicConfig(level=logging.INFO)


class Original:
    """Original Commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)

    # Annoy
    @commands.command()
    @commands.cooldown(2, 600, BucketType.user)
    @commands.guild_only()
    async def annoy(self, ctx, *, string):
        """Direct Messages a random person, with the message of choice."""

        user = random.choice([x for x in ctx.guild.members if not x.bot])

        try:
            embed = discord.Embed(
                title="Sent in PM",
                description=f'{string}',
                color=0xba1c1c,

            )

            if ctx.message.attachments:
                image = ' '.join(m.url for m in ctx.message.attachments)
                embed.set_image(url=image)
                await user.send(f"{string}\n{image}")

            embed.set_author(name=user, icon_url=user.avatar_url)
            embed.set_footer(
                text=f'Sent by {ctx.author}',
                icon_url=ctx.author.avatar_url
            )
            await ctx.send(embed=embed)
            await user.send(string)
        except discord.Forbidden:
            pass

    # Random Nickname
    @commands.command()
    @commands.cooldown(2, 600, BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx, *, string):
        """Set's the nick of a random person, with nick of choice."""

        user = random.choice([x for x in ctx.guild.members if not x.bot])
        try:
            await user.edit(nick=string)
            embed = discord.Embed(
                title="Changed/Set Nickname",
                description=f"{string}",
                color=0xba1c1c,

            )
            embed.set_author(name=user, icon_url=user.avatar_url)
            embed.set_footer(text=f'Sent by {ctx.author}')
            await ctx.send(embed=embed)
        except discord.Forbidden:
            pass

        await asyncio.sleep(600)
        await user.edit(nick=None)

    @commands.command()
    @commands.guild_only()
    async def guess(self, ctx):
        """Guess who this person is."""

        user1 = [x for x in ctx.guild.members if not x.bot]
        user = random.choice(user1)
        discrim = str(user).split(user.name)
        discrim = ''.join(discrim)

        if not user.avatar:
            user = random.choice(user1)
            discrim = str(user).split(user.name)
            discrim = ''.join(discrim)

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name='Can you guess who this is?')
        embed.description = f'Their discriminant is `{discrim}`'
        embed.set_image(
            url=user.avatar_url_as(format='png', size=1024)
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.content == user.name \
                   or m.content == user.display_name \
                   and m.channel == ctx.message.channel

        try:
            member = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The user was `{user}`")
        else:
            await ctx.send(f'{member.author.mention} is right! This user is `{user}`')
            command = self.bot.get_command('guess')
            await ctx.invoke(command)


def setup(bot):
    bot.add_cog(Original(bot))
