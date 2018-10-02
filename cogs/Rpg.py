import asyncio
import random
from io import BytesIO

import aiohttp
import discord
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.paginator import SimplePaginator
from cogs.utils.rpg_tools import *


class Error(commands.CheckFailure):
    pass


def registered():
    async def predicate(ctx):
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_profile WHERE id=$1",
            ctx.author.id
        )
        if data is None:
            raise Error(f"Looks like you're not registered, type {ctx.prefix}register.")
        return True

    return commands.check(predicate)


def unregistered():
    async def predicate(ctx):
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_profile WHERE id=$1",
            ctx.author.id
        )
        return not bool(data)

    return commands.check(predicate)


def eweapon():
    async def predicate(ctx):
        data = await ctx.bot.db.fetch(
            "SELECT equip FROM rpg_profile WHERE id=$1",
            ctx.author.id
        )

        if data is None:
            raise Error(f"You need to have an item equipped `{ctx.prefix}equip <item>`")

        return True

    return commands.check(predicate)


class Rpg:
    """Rpg related commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @unregistered()
    async def register(self, ctx):
        """Register for the rpg."""
        await ctx.send("Choose a class: **Knight, Hunter, Sorcerer and Sentinel**")

        def class_(m):
            return m.author == ctx.author \
                   and m.content.lower() in \
                   ["knight", "hunter", "sorcerer", "sentinel"]

        m_ = await ctx.bot.wait_for('message', check=class_)
        await ctx.bot.db.execute("INSERT INTO rpg_profile VALUES($1, $2, $3, $4, $5)",
                                 ctx.author.id, m_.content.capitalize(), 1, 100, 0)

        await ctx.bot.db.execute("INSERT INTO rpg_mastery VALUES($1, $2, $3)",
                                 ctx.author.id, 1, 0)
        await ctx.send(f"You have successfully registered, type {ctx.prefix}help Rpg for commands.")

    @commands.command()
    async def top(self, ctx):
        """The Top Players of the RPG."""
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_profile ORDER BY lvl"
        )

        p = []
        for i in data:
            p.append(await lb_embed(ctx, i))

        await SimplePaginator(extras=p).paginate(ctx)

    @commands.command()
    @registered()
    @commands.cooldown(1, 600, BucketType.user)
    async def quest(self, ctx):
        """Quests for the brave"""

        class_ = await fetch(ctx, user=ctx.author.id)

        q = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_quests WHERE class = $1 ORDER BY RANDOM() LIMIT 1",
            class_[1]
        )

        await ctx.send(f"**Quest:** {q[0]} \n"
                       f"**Class:** {q[1]} \n"
                       f"**Creator:** {ctx.bot.get_user(q[2]).display_name} \n"
                       f"`Pick a number between 1-10`")

        ans = random.randint(1, 10)

        def message(m):
            return m.author == ctx.author and m.content.isdigit()

        message_ = await ctx.bot.wait_for(
            'message',
            check=message,
            timeout=15
        )
        if message_.content == ans:
            xp = random.randint(1, 50)
            mon = random.randint(1, 100)
            await add_xp(ctx, xp=xp, user=ctx.author.id)
            await level(ctx, xp=xp, mon=mon, user=ctx.author.id)
        else:
            mon = random.randint(1, 100)
            await add_xp(ctx, xp=10, user=ctx.author.id)
            await level(ctx, xp=10, mon=mon, user=ctx.author.id)

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def admin(self, ctx):
        """Group of admin commands for RPG"""
        cmd = ctx.bot.get_command("help")
        await ctx.invoke(cmd, command="admin")

    @admin.command(name="add-quest")
    @registered()
    @commands.has_any_role("Peacemakers ☮", "Test Puppets")
    async def add_quest(self, ctx, *, quest):
        """Adds a quest"""
        await ctx.send("What class is this quest for? \n"
                       "**Knight, Hunter, Sorcerer and Sentinel**")

        def class_(m):
            return m.author == ctx.author \
                   and m.content.lower() in \
                   ["knight", "hunter", "sorcerer", "sentinel"]

        m_ = await ctx.bot.wait_for('message', check=class_)
        await ctx.send(f"**{quest.title()}** is a quest for **{m_.content.capitalize()}s**")
        await ctx.bot.db.execute("INSERT INTO rpg_quests VALUES($1, $2, $3)",
                                 quest.title(), m_.content.capitalize(), ctx.author.id)

    @admin.command(name="add-item")
    @commands.has_any_role("Peacemakers ☮", "Test Puppets")
    async def add_item(self, ctx, name: str, price: int,
                       damage: int, defense: int,
                       mastery: int, description: str):
        """Add's an item"""
        await ctx.send(
            "What class is this item for? \n"
            "**Knight, Hunter, Sorcerer and Sentinel**"
        )

        def class_(m):
            return m.author == ctx.author \
                   and m.content.lower() in \
                   ["knight", "hunter", "sorcerer", "sentinel"]

        m_ = await ctx.bot.wait_for('message', check=class_)
        item = await item_(class_=m_.content.lower())
        await ctx \
            .send(f"**Name:** {name} \n"
                  f"**Type:** {item} \n"
                  f"**Price:** {price} \n"
                  f"**Damage:** {damage} \n"
                  f"**Defense:** {defense} \n"
                  f"**Class:** {m_.content.capitalize()} \n"
                  f"**Mastery Level:** {mastery} \n"
                  f"**Description:** {description.title()} \n"
                  f"`Do you approve? Yes or No?`")

        def yon(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Yes", "No"]

        y = await ctx.bot.wait_for('message', check=yon)
        if y.content == "Yes":
            await ctx.bot.db.execute(
                "INSERT INTO rpg_shop VALUES($1, $2, $3, $4, $5, $6, $7, $8)",
                name.title(), item, price, damage, defense, m_.content.capitalize(), mastery, description.title())

            await ctx.send(f"{name.title()} has been created for class {m_.content.capitalize()}")
        else:
            await ctx.send("Cancelled")

    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def shop(self, ctx):
        """Items that are available"""
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_shop ORDER BY price"
        )

        if data:
            p = []
            t = {"Sword": "http://orig05.deviantart.net/092b/f/2010/302/e/3/ice_sword_by_myrdah-d31rxrg.jpg",
                 "Bow": "http://orig14.deviantart.net/e9ae/f/2015/073/1/f/bows"
                        "___9___________2015__by_rittik_designs-d8lp1ay.jpg",
                 "Staff": "http://cliparts.co/cliparts/Aib/jyM/AibjyMkeT.png",
                 "Crossbow": "http://img4.wikia.nocookie.net/__cb20130711033127/runescape/"
                             "images/2/20/Off-hand_Ascension_crossbow_detail.png"}

            for i in data:
                p.append(item_embed(i, t[i[1]]))

            await SimplePaginator(extras=p).paginate(ctx)

    @shop.command()
    @registered()
    async def recommend(self, ctx):
        """Items you can buy."""
        user = await fetch(ctx, user=ctx.author.id)
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_shop WHERE class = $1 ORDER BY price BETWEEN 0 AND $2",
            user[1], user[3]
        )

        if data:
            p = []
            t = {"Sword": "http://orig05.deviantart.net/092b/f/2010/302/e/3/ice_sword_by_myrdah-d31rxrg.jpg",
                 "Bow": "http://orig14.deviantart.net/e9ae/f/2015/073/1/f/bows"
                        "___9___________2015__by_rittik_designs-d8lp1ay.jpg",
                 "Staff": "http://cliparts.co/cliparts/Aib/jyM/AibjyMkeT.png",
                 "Crossbow": "http://img4.wikia.nocookie.net/__cb20130711033127/runescape/"
                             "images/2/20/Off-hand_Ascension_crossbow_detail.png"}

            for i in data:
                p.append(item_embed(i, t[i[1]]))

            await SimplePaginator(extras=p).paginate(ctx)

    @commands.command()
    @registered()
    async def buy(self, ctx, *, item):
        """Buy an item from shop"""
        user = await fetch(ctx, user=ctx.author.id)
        s = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_shop WHERE name=$1 AND class = $2",
            item.title(), user[1])

        m = await fetchm(ctx, user=ctx.author.id)
        if s:
            if user[3] >= s[2] and m[1] >= s[6]:
                await ctx.send(f"Are you sure you want to buy **{item}**? \n"
                               f"`Yes or No`")

                def yon(m_):
                    return m_.author == ctx.author \
                           and m_.content.capitalize() in \
                           ["Yes", "No"]

                y = await ctx.bot.wait_for('message', check=yon)
                if y.content == "Yes":
                    await ctx.bot.db.execute(
                        "INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                        s[0], s[1],
                        s[2], s[3],
                        s[4], s[5],
                        s[6], ctx.author.id,
                        s[7])

                    await ctx.bot.db.execute(
                        "UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                        s[2], ctx.author.id
                    )
                    await ctx.send(f"You have successfully bought {item.title()}")
                else:
                    await ctx.send("Cancelled")
            else:
                await ctx.send(
                    "Looks like you don't have enough money or have the right mastery level."
                )
        else:
            await ctx.send("Looks like you don't have the right class.")

    @commands.command()
    @registered()
    async def equip(self, ctx, *, item):
        """Equip an item to use in battle"""
        i = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                      item.title(), ctx.author.id)

        if i:
            await ctx.send(f"**{i[0]}** has been equipped and can be used for battle.")
            await ctx.bot.db \
                .execute("UPDATE rpg_profile SET equip = $1 WHERE id=$2",
                         i[0], ctx.author.id)
        else:
            await ctx.send("You don't have this item.")

    @commands.command()
    @registered()
    @eweapon()
    @commands.cooldown(1, 300, BucketType.channel)
    async def duel(self, ctx, user: discord.Member):
        """Duel other players"""
        if user == ctx.author:
            return await ctx.send("Don't even try.")

        equip = await ctx.bot.db.fetchrow("SELECT * FROM rpg_profile WHERE id=$1", user.id)

        if equip[5] is None:
            return await ctx.send(f"{user.mention} needs to equip an item to participate.")

        await ctx.send(f"Do you accept this challenge **{user.display_name}** `Yes or No`")

        def yon(m):
            return m.author == user \
                   and m.content.capitalize() in \
                   ["Yes", "No"]

        try:
            y = await ctx.bot.wait_for('message', check=yon, timeout=15)
        except asyncio.TimeoutError:
            await ctx.send("You ran out of time")
        else:
            if y.content == "Yes":
                hp1 = 750
                hp2 = 750
                p1w = await fetch(ctx, user=ctx.author.id)
                p2w = await fetch(ctx, user=user.id)
                p1w = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                                p1w[5], ctx.author.id)
                p2w = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                                p2w[5], user.id)

                ult = {"Knight": "Bloodbath",
                       "Hunter": "Death From Above",
                       "Sorcerer": "Dark Magic",
                       "Sentinel": "Heartbreaker"}

                ultd1 = await fetchm(ctx, user=ctx.author.id)
                ultd2 = await fetchm(ctx, user=user.id)

                await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage", delete_after=20)
                while hp1 or hp2 > 0:
                    def move(m):
                        return m.author == ctx.author \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move)
                    if m_.content == "1":
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s attack with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    else:
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s barrage with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    def move1(m):
                        return m.author == user \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move1)
                    if m_.content == "1":
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s attack with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    else:
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s barrage with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    def move2(m):
                        return m.author == ctx.author \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move2)
                    if m_.content == "1":
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s attack with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    else:
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s barrage with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    def move3(m):
                        return m.author == user \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move3)
                    if m_.content == "1":
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s attack with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    else:
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s barrage with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    def move4(m):
                        return m.author == ctx.author \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move4)
                    if m_.content == "1":
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s attack with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    else:
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s barrage with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage")

                    def move5(m):
                        return m.author == user \
                               and m.content in ["1", "2"]

                    m_ = await ctx.bot.wait_for('message', check=move5)
                    if m_.content == "1":
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s attack with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage, **3:** {ult[p1w[5]]}")

                    else:
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s barrage with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage, **3:** {ult[p1w[5]]}")

                    def ult1(m):
                        return m.author == ctx.author \
                               and m.content in ["1", "2", "3"]

                    m_ = await ctx.bot.wait_for("message", check=ult1)
                    if m_.content == "1":
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s attack with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage, **3:** {ult[p2w[5]]}")

                    if m_.content == "2":
                        dam = random.randint(1, p1w[2] / 2)
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s barrage with **{p1w[0]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp",
                            delete_after=20)
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage, **3:** {ult[p2w[5]]}")

                    if m_.content == "3":
                        dam = 100 * ultd1[1]
                        hp2 = hp2 - dam
                        await ctx.send(
                            f"{ctx.author.mention}'s **{ult[p1w[5]]}** dealt {dam}dmg to {user.mention} "
                            f"\n {user.mention} has {hp2}hp"
                        )
                        await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage, **3:** {ult[p2w[5]]}")

                    def ult2(m):
                        return m.author == user \
                               and m.content in ["1", "2", "3"]

                    m_ = await ctx.bot.wait_for('message', check=ult2)
                    if m_.content == "1":
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s attack with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    if m_.content == "2":
                        dam = random.randint(1, p2w[2] / 2)
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s barrage with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    if m_.content == "3":
                        dam = 100 * ultd2[1]
                        hp1 = hp1 - dam
                        await ctx.send(
                            f"{user.mention}'s barrage with **{p2w[0]}** dealt {dam}dmg to {ctx.author.mention} "
                            f"\n {ctx.author.mention} has {hp1}hp",
                            delete_after=20)
                        await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

                    if hp2 <= 0:
                        await ctx.send(f"{ctx.author.mention} won the battle.")
                        await add_xp(ctx, xp=500, user=ctx.author.id)
                        await level(ctx, mon=150, xp=500, user=ctx.author.id)
                        break

                    if hp1 <= 0:
                        await ctx.send(f"{user.mention} won the battle.")
                        await add_xp(ctx, xp=500, user=user.id)
                        break

    @commands.command()
    @registered()
    async def profile(self, ctx, user: discord.Member = None):
        async with ctx.typing():
            if not user:
                user = ctx.author

            you = await fetch(ctx, user.id)
            youm = await fetchm(ctx, user.id)
            async with aiohttp.ClientSession() as s:
                async with s.get(user.avatar_url_as(format="png", size=512)) as r:
                    pfp = await r.read()

            font = ImageFont.truetype("fonts/gothic.ttf", 18)

            def text():
                image = Image.open("img/rpgp.png")
                profile = Image.open(BytesIO(pfp))
                profile = profile.resize((188, 188))
                # Class
                drawtext(278, 49, text=you[1], font=font, image=image)

                # Level
                drawtext(280, 91, text=str(you[2]), font=font, image=image)

                # Experience Points
                drawtext(385, 134, text=str(you[4]), font=font, image=image)

                # Mastery Level
                drawtext(352, 178, text=str(youm[1]), font=font, image=image)

                # Equipped
                drawtext(388, 221, text=str(you[5]), font=font, image=image)
                
                image.paste(profile, (15, 50))
                b = BytesIO()
                b.seek(0)
                image.save(b, "png")
                return b.getvalue()

            fp = await ctx.bot.loop.run_in_executor(None, text)
            file = discord.File(filename="profile.png", fp=fp)
            await ctx.send(file=file)

    @commands.command()
    @registered()
    @commands.cooldown(1, 1800, BucketType.user)
    async def master(self, ctx):
        chance = random.randint(1, 100)

        if chance > 50 < 75:
            await add_xpm(ctx, 50, ctx.author.id)
            await levelm(ctx, 100, 50, ctx.author.id)
        elif chance < 50:
            await add_xpm(ctx, 10, ctx.author.id)
            await levelm(ctx, 25, 10, ctx.author.id)
        else:
            await add_xpm(ctx, 100, ctx.author.id)
            await levelm(ctx, 25, 10, ctx.author.id)

    @commands.command()
    @registered()
    async def bal(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author

        balance = await fetch(ctx, user.id)
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.description = f"You have {balance[3]}$"
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Rpg(bot))
