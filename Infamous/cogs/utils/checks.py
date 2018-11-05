from discord.ext import commands
from .rpg_tools import *


def registered():
    async def predicate(ctx):
        data = await fetch_user(ctx)
        if data is None:
            raise commands.CheckFailure(
                "You are not registered! Type `*!register` or `@Infamous#5069 register`"
            )
        else:
            return True

    return commands.check(predicate)


def unregistered():
    async def predicate(ctx):
        data = await fetch_user(ctx)
        if data:
            raise commands.CheckFailure(
                "You are already registered! If you want to edit your class type `*!class` or `@Infamous#5069 class`"
            )
        else:
            return True

    return commands.check(predicate)


def equipped():
    async def predicate(ctx):
        data = (await fetch_user(ctx))[6]
        if data is None:
            raise commands.CheckFailure(
                "You don't have an item equipped! Type `*!equip <item>` or `@Infamous#5069 equip <item>`"
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

