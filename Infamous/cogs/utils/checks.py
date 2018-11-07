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
        elif ctx.author.id in [299879858572492802, 284191082420633601, 311325365735784449]:
            return True
        else:
            raise commands.CheckFailure("You do not have access to this command!")

    return commands.check(predicate)
