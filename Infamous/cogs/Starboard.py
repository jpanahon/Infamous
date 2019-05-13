import discord
import asyncio
from discord.ext import commands
import asyncpg
from datetime import datetime


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = "\N{WHITE MEDIUM STAR}"
        self.messages = {}
        self.bot.loop.create_task(self.reset_cache())
        self.board = bot.get_channel(537941975706632193)

    async def reset_cache(self):
        """Got it from Danny"""
        try:
            while not self.bot.is_closed():
                self.messages.clear()
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    async def fetch(self, channel, message):
        """Also got this from Danny"""
        try:
            return self.messages[message]
        except KeyError:
            msg = await channel.history(limit=1, before=discord.Object(id=message + 1)).next()
            self.messages[message] = msg
            return msg

    def construct(self, message, stars):
        c = f"{self.star_emoji} {stars} | {message.channel.mention}"
        e = discord.Embed(color=message.author.color)
        e.set_author(name=message.author.display_name,
                     icon_url=message.author.avatar_url)
        if message.content:
            e.description = f"{message.content} \n\n{message.jump_url}"
        else:
            e.description = message.jump_url
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
            query = """INSERT INTO starboard (m_id, c_id) VALUES($1, $2)
                       ON CONFLICT (m_id) DO NOTHING"""

            try:
                await db.execute(query, msg.id, channel.id)
            except asyncpg.UniqueViolationError:
                await self.bot.get_channel(payload.channel_id).send("did not work")
            else:
                count = await db.fetchval("SELECT u_id FROM starrers WHERE u_id=$1 AND m_id=$2",
                                          payload.user_id, msg.id)
                if count:
                    return
                else:
                    await db.execute("INSERT INTO starrers VALUES($1, $2)", msg.id, payload.user_id)
                    count = await db.fetchval("SELECT COUNT(*) FROM starrers WHERE m_id=$1", msg.id)
                    data = await db.fetchval("SELECT b_id FROM starboard WHERE m_id=$1", msg.id)

                    if count < 3:
                        return

                    if not data:
                        c, e = self.construct(msg, count)
                        d = await self.board.send(content=c, embed=e)
                        await db.execute("UPDATE starboard SET b_id=$1 WHERE m_id=$2", d.id, msg.id)
                    else:
                        msg_ = await self.fetch(self.board, data)
                        c, e = self.construct(msg, count)
                        await msg_.edit(content=c, embed=e)

    async def unstar(self, payload):
        if str(payload.emoji) != self.star_emoji:
            return

        if payload.guild_id != 258801388836880385:
            return

        channel = self.bot.get_channel(payload.channel_id)
        msg = await self.fetch(channel, payload.message_id)

        async with self.bot.db.acquire() as db:
            data = await db.fetchval("SELECT b_id FROM starboard WHERE m_id=$1", msg.id)
            if not data:
                return

            await db.execute("DELETE FROM starrers WHERE u_id=$1 AND m_id=$2", payload.user_id, msg.id)
            count = await db.fetchval("SELECT COUNT(*) FROM starrers WHERE m_id=$1", msg.id)

            if count < 3:
                _msg = await self.fetch(self.board, data)
                await _msg.delete()
                await db.execute("UPDATE starboard SET b_id = NULL WHERE b_id=$1", _msg.id)
            elif count == 0:
                await db.execute("DELETE FROM starboard WHERE m_id=$1", msg.id)
            else:
                c, e = self.construct(msg, count)
                _msg = await self.fetch(self.board, data)
                await _msg.edit(content=c, embed=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.star(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.unstar(payload)


def setup(bot):
    bot.add_cog(Starboard(bot))
