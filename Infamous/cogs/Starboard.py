import discord
import asyncpg
from datetime import datetime
from .utils.functions import CustomCTX


class Starboard:
    def __init__(self, ctx, message, user, reaction):
        self.bot = ctx.bot
        self.star = "\U00002b50"
        self.channel = message.channel
        self.msg = message
        self.starboard = ctx.guild.get_channel(537941975706632193)
        self.db = ctx.db
        self.starrer = user
        self.reaction = reaction
        self.server = self.bot.get_guild(258801388836880385)

    async def check(self, msg):
        async with self.db.acquire() as db:
            m = await db.fetchrow("SELECT * FROM starboard WHERE original = $1", msg.id)
        if not m:
            return False
        return True

    async def setup(self):
        if await self.check(self.msg) is False:
            embed = discord.Embed(color=self.msg.author.color)
            embed.set_author(name=self.msg.author.display_name,
                             icon_url=self.msg.author.avatar_url,
                             url=self.msg.jump_url)
            embed.description = self.msg.content
            if self.msg.attachments:
                embed.set_image(url=self.msg.attachments[0].url)
            embed.timestamp = datetime.utcnow()
            msg = await self.starboard.send(content=f"{self.star} 3 {self.channel.mention}", embed=embed)
            async with self.db.acquire() as db:
                await db.execute("INSERT INTO starboard VAlUES($1, $2, $3, $4)", msg.id, self.msg.id, 3,
                                 self.channel.id)
        else:
            async with self.db.acquire() as db:
                thing = await db.fetch("SELECT * FROM starboard WHERE original=$1", self.msg.id)
                await db.execute("UPDATE starboard SET stars=$1 WHERE original=$2", self.reaction.count, self.msg.id)
            edit = await self.starboard.get_message(thing)
            reactions = self.reaction.count
            await edit.edit(content=f"{self.star} {reactions} {self.channel.mention}")

    async def edit_board(self):
        async with self.db.acquire() as db:
            original = await db.fetchrow("SELECT * FROM starboard WHERE id=$1", self.msg.id)
            await db.execute("UPDATE starboard SET stars=stars+1 WHERE id=$1", self.msg.id)
        channel = self.server.get_channel(original[3])
        await self.msg.edit(content=f"{self.star} {original[2]+1} {channel.mention}")

    async def _edit_board(self):
        async with self.db.acquire() as db:
            original = await db.fetchrow("SELECT * FROM starboard WHERE id=$1", self.msg.id)
            await db.execute("UPDATE starboard SET stars=stars-1 WHERE id=$1", self.msg.id)
        channel = self.server.get_channel(original[3])
        await self.msg.edit(content=f"{self.star} {original[2]-1} {channel.mention}")

    async def remover(self):
        if self.reaction.emoji == self.star:
            if self.reaction.count < 3:
                if self.channel.id != self.starboard.id:
                    async with self.db.acquire() as db:
                        await db.execute("UPDATE starboard SET stars=stars-1 WHERE original=$1", self.msg.id)
                        await db.fetchval("SELECT stars FROM starboard WHERE original=$1", self.msg.id)
                        c = await db.fetchval("SELECT id FROM starboard WHERE original=$1", self.msg.id)
                        await db.execute("DELETE FROM starboard WHERE original=$1", self.msg.id)
                    msg = await self.starboard.get_message(c)
                    await msg.delete()
                else:
                    await self._edit_board()

    async def start(self):
        if self.msg.guild.id != self.server.id:
            return

        if self.reaction.emoji == self.star:
            if self.reaction.message.channel.id != self.starboard.id:
                if self.reaction.count >= 3:
                    await self.setup()

            else:
                await self.edit_board()
                async with self.db.acquire() as db:
                    stars = await db.fetchval("SELECT stars FROM starboard WHERE id=$1", self.msg.id)
                if stars < 3:
                    async with self.db.acquire() as db:
                        await db.execute("DELETE FROM starboard WHERE id=$1", self.msg.id)
                    await self.reaction.message.delete()


class Stars:
    """Starboard Only for Fame"""
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction, user):
        ctx = await self.bot.get_context(reaction.message, cls=CustomCTX)
        s = Starboard(ctx, reaction.message, user, reaction)
        await s.start()

    async def on_reaction_remove(self, reaction, user):
        ctx = await self.bot.get_context(reaction.message, cls=CustomCTX)
        s = Starboard(ctx, reaction.message, user, reaction)
        await s.remover()


def setup(bot):
    bot.add_cog(Stars(bot))
