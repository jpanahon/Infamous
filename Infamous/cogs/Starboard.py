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

    async def fetch(self, channel, message):
        try:
            return self.messages[message]
        except KeyError:
            # Used Danny's trick
            msg = await channel.history(limit=1, before=discord.Object(id=message+1)).next()
            self.messages[message] = msg
            return msg

    def construct(self, message, stars):
        embed = discord.Embed(color=message.author.color)
        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar_url,
                         url=message.jump_url)
        if message.content:
            embed.description = message.content
        else:
            embed.set_image(url=message.attachments[0].url)

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        embed.timestamp = datetime.utcnow()
        embed.set_footer(text=f"{self.star_emoji} {stars}")
        return embed

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
                        d = await self.board.send(embed=self.construct(msg, count[0]))
                        await db.execute("UPDATE starboard SET b_id=$1 WHERE m_id=$2", d.id, msg.id)
                    else:
                        msg = await self.fetch(self.board, data)
                        await msg.edit(embed=self.construct(msg, count))

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
            if count[0] < 3:
                await (await self.fetch(self.board, data)).delete()

            elif count == 0:
                await db.execute("DELETE FROM starrers WHERE m_id=$1 AND u_id=$2", msg.id, payload.user_id)
            else:
                await (await self.fetch(self.board, data)).edit(embed=self.construct(msg, count))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.star(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.unstar(payload)


def setup(bot):
    bot.add_cog(Starboard(bot))
