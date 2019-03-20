import discord
from discord.ext import commands
import asyncpg
from datetime import datetime


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = "\N{WHITE MEDIUM STAR}"
        self.messages = {}
        self.board = bot.get_channel(537941975706632193)

    async def cog_check(self, ctx):
        if ctx.guild.id != 258801388836880385:
            return False
        return True

    async def fetch(self, channel, message):
        try:
            return self.messages[message]
        except KeyError:
            # Used Danny's trick
            msg = await channel.history(limit=1, before=discord.Object(id=message + 1)).next()
            self.messages[message] = msg
            return msg

    def construct(self, message, stars):
        c = f"From {message.channel.mention}"
        e = discord.Embed(color=message.author.color)
        e.set_author(name=f"{message.author.display_name} | {self.star_emoji} {stars} ",
                     icon_url=message.author.avatar_url,
                     url=message.jump_url)
        if message.content:
            e.description = message.content
        else:
            e.set_image(url=message.attachments[0].url)

        if message.attachments:
            e.set_image(url=message.attachments[0].url)

        e.timestamp = datetime.utcnow()
        e.set_footer(text=f"ID: {message.id}")
        return c, e

    async def star(self, payload):
        if str(payload.emoji) != self.star_emoji:
            return

        if payload.guild_id != 258801388836880385:
            return

        channel = self.bot.get_channel(payload.channel_id)
        msg = await self.fetch(channel, payload.message_id)
        if payload.user_id == msg.author.id:
            return

        async with self.bot.db.acquire() as db:
            try:
                await db.execute("INSERT INTO starboard VALUES($1, $2, $3)", msg.id, None, channel.id)
            except asyncpg.UniqueViolationError:
                pass
            else:
                count = await db.fetchval("SELECT u_id FROM starrers WHERE u_id=$1 AND m_id=$2",
                                          payload.user_id, msg.id)
                if count:
                    return
                else:
                    await db.execute("INSERT INTO starrers VALUES($1, $2)", msg.id, payload.user_id)
                    count = await db.fetchrow("SELECT COUNT(*) FROM starrers WHERE m_id=$1", msg.id)
                    data = await db.fetchval("SELECT b_id FROM starboard WHERE m_id=$1", msg.id)

                    if count[0] < 3:
                        return

                    if not data:
                        c, e = self.construct(msg, count[0])
                        d = await self.board.send(content=c, embed=e)
                        await db.execute("UPDATE starboard SET b_id=$1 WHERE m_id=$2", d.id, msg.id)
                    else:
                        msg = await self.fetch(self.board, data)
                        c, e = self.construct(msg, count)
                        await msg.edit(content=c, embed=e)

    async def unstar(self, payload):
        if str(payload.emoji) != self.star_emoji:
            return

        if payload.guild_id != 258801388836880385:
            return

        channel = self.bot.get_channel(payload.channel_id)
        msg = await self.fetch(channel, payload.message_id)
        data = await self.bot.db.fetchval("SELECT b_id FROM starboard WHERE m_id=$1", msg.id)

        async with self.bot.db.acquire() as db:
            await db.execute("DELETE FROM starrers WHERE u_id=$1 AND m_id=$2", payload.user_id, msg.id)
            count = await db.fetchrow("SELECT COUNT(*) FROM starrers WHERE m_id=$1", msg.id)
            if not data:
                return

            if count[0] < 3:
                await (await self.fetch(self.board, data)).delete()

            elif count == 0:
                await db.execute("DELETE FROM starrers WHERE m_id=$1 AND u_id=$2", msg.id, payload.user_id)
            else:
                c, e = self.construct(msg, count)
                await (await self.fetch(self.board, data)).edit(content=c, embed=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.star(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.unstar(payload)

    @commands.command(name="context")
    async def context_(self, ctx, msg: int):
        async with ctx.db.acquire() as db:
            channel = await db.fetchval("SELECT c_id FROM starboard WHERE m_id=$1", msg)
            if not channel:
                return await ctx.send("Invalid message id/not in the starboard.")

            channel = ctx.bot.get_channel(channel)
            url = await channel.history(limit=1, before=discord.Object(msg + 1)).next()
            await ctx.send(f"Context: {url.jump_url}")


def setup(bot):
    bot.add_cog(Starboard(bot))
