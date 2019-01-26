import discord
from datetime import datetime


class Starboard:
    """(Fame Only)"""

    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction, user):
        if user.guild.id != 258801388836880385:
            return False

        if str(reaction.emoji) == "⭐":
            if user == reaction.message.author:
                return

            if reaction.message.reactions[0].count >= 3:
                channel = self.bot.get_channel(537941975706632193)
                embed = discord.Embed(color=reaction.message.author.color, timestamp=datetime.utcnow())
                if reaction.message.content:
                    embed.description = reaction.message.content
                embed.set_author(name=reaction.message.author.display_name, icon_url=reaction.message.author.avatar_url)
                if reaction.message.attachments:
                    embed.set_image(url=reaction.message.attachments[0].url)

                id_ = await channel.send(content=f"\N{WHITE MEDIUM STAR} 6 {reaction.message.channel.mention}",
                                         embed=embed)
                async with self.bot.db.acquire() as db:
                    await db.execute("INSERT INTO starboard VALUES($1, $2, $3)", id_.id, reaction.message.id,
                                     reaction.message.reactions[0].count)
                    await db.execute("INSERT INTO starrers VALUES($1, $2)", user.id, reaction.message.id)

            elif reaction.message.id in await self.bot.db.fetch("SELECT id FROM starboard"):
                channel = self.bot.get_channel(537941975706632193)
                async with self.bot.db.acquire() as db:
                    msg = await db.fetchrow("SELECT * FROM starboard WHERE id=$1", reaction.message.id)
                    await db.execute("INSERT INTO starrers VALUES($1, $2)", user.id, reaction.message.id)

                msg = await channel.get_message(msg[0])
                await msg.edit(content=f"\N{WHITE MEDIUM STAR} {reaction.message.reactions[0].count} "
                                       f"{reaction.message.channel.mention}")

    async def on_reaction_remove(self, reaction, user):
        if user.guild.id != 258801388836880385:
            return False

        if str(reaction.emoji) == "⭐":
            if user == reaction.message.author:
                return

            if reaction.message.id in await self.bot.db.fetch("SELECT id FROM starboard"):
                channel = self.bot.get_channel(537941975706632193)
                async with self.bot.db.acquire() as db:
                    msg = await db.fetchrow("SELECT * FROM starboard WHERE id=$1", reaction.message.id)
                    await db.execute("DELETE FROM starrers WHERE id=$1 AND message=$2", user.id, reaction.message.id)

                msg = await channel.get_message(msg[0])
                await msg.edit(content=f"\N{WHITE MEDIUM STAR} {reaction.message.reactions[0].count} "
                                       f"{reaction.message.channel.mention}")
            elif reaction.message.reactions[0].count < 3:
                channel = self.bot.get_channel(537941975706632193)
                async with self.bot.db.acquire() as db:
                    msg = await db.fetchrow("SELECT * FROM starboard WHERE id=$1", reaction.message.id)
                    await db.execute("DELETE FROM starrers WHERE message=$1", reaction.message.id)

                msg = await channel.get_message(msg[0])
                await msg.delete()


def setup(bot):
    bot.add_cog(Starboard(bot))

