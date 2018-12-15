from discord.ext import commands
from .rpg_tools import *


def registered():
    async def predicate(ctx):
        data = await fetch_user(ctx)
        if data is None:
            raise commands.CheckFailure(
                f"You are not registered! Type `{ctx.prefix}register`"
            )
        else:
            return True

    return commands.check(predicate)


def unregistered():
    async def predicate(ctx):
        data = await fetch_user(ctx)
        if data:
            raise commands.CheckFailure(
                f"You are already registered! If you want to edit your class type `{ctx.prefix} class`"
            )
        else:
            return True

    return commands.check(predicate)


def equipped():
    async def predicate(ctx):
        data = (await fetch_user(ctx))[6]
        if data is None:
            raise commands.CheckFailure(
                f"You don't have an item equipped! Type `{ctx.prefix}equip <item>` or `@Infamous#5069 equip <item>`"
            )
        else:
            return True

    return commands.check(predicate)


def is_admin():
    async def predicate(ctx):
        if ctx.author.id not in [299879858572492802, 507490400534265856]:
            raise commands.CheckFailure(f"You do not have permission to use **{ctx.command}**")
        else:
            return True
    return commands.check(predicate)


def rpg_admin():
    async def predicate(ctx):
        if ctx.author.guild_permissions.manage_messages:
            return True
        else:
            raise commands.CheckFailure("You do not have access to this command!")

    return commands.check(predicate)


def in_fame():
    async def predicate(ctx):
        if ctx.guild.id == 258801388836880385:
            return True
        else:
            raise commands.CheckFailure("You must be in the Fame discord server to use this command! \n"
                                        "https://discord.gg/NY2MSA3")
    return commands.check(predicate)


def registered2():
    async def predicate(ctx):
        async with ctx.bot.db.acquire() as db:
            data = await db.fetchrow("SELECT * FROM profiles WHERE id=$1", ctx.author.id)

        if not data:
            raise commands.CheckFailure(
                f"You are not registered! Type `{ctx.prefix}register or @Infamous#5069 register`"
            )
        else:
            return True

    return commands.check(predicate)


def unregistered2():
    async def predicate(ctx):
        async with ctx.bot.db.acquire() as db:
            data = await db.fetchrow("SELECT * FROM profiles WHERE id=$1", ctx.author.id)

        if data:
            raise commands.CheckFailure(
                "You are already registered!"
            )
        else:
            return True

    return commands.check(predicate)


class SuperhumanFinder(commands.Converter):
    async def convert(self, ctx, argument):
        async with ctx.bot.db.acquire() as db:
            argument = await commands.MemberConverter().convert(ctx, argument)
            users = await db.fetchval("SELECT id FROM profiles WHERE id=$1", argument.id)

        if not users:
            raise commands.BadArgument(f"{ctx.author.mention} pick a user registered in the RPG!")
        else:
            return argument


def has_guild():
    async def predicate(ctx):
        async with ctx.bot.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", ctx.author.id)

        if guild_:
            raise commands.CheckFailure(f"{ctx.author.mention} you already enlisted in {guild_}")
        else:
            return True
    return commands.check(predicate)


def no_guild():
    async def predicate(ctx):
        async with ctx.bot.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", ctx.author.id)

        if not guild_:
            raise commands.CheckFailure(f"{ctx.author.mention} you are not in a guild.")
        else:
            return True
    return commands.check(predicate)


class GuildFinder(commands.Converter):
    async def convert(self, ctx, argument):
        async with ctx.bot.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM guilds WHERE id=$1", argument)

        if not guild_:
            raise commands.BadArgument(f"{ctx.author.mention} choose an existing guild.")
        else:
            return guild_


def in_testing():
    async def predicate(ctx):
        if ctx.guild.id != 334164625102995459:
            raise commands.CheckFailure("Sorry this is restricted to https://discord.gg/JyJTh4H, to prevent errors.")
        else:
            return True

    return commands.check(predicate)

