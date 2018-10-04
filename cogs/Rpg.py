import random
from io import BytesIO

import aiohttp
from PIL import Image, ImageFont
from discord.ext import commands
import logging
from .utils.paginator import SimplePaginator
from .utils.rpg_tools import *

logging.basicConfig(level=logging.INFO)


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


def equipped():
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

    async def __local_check(self, ctx):
        return ctx.guild is not None

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
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quest(self, ctx):
        """Quests for the brave"""

        class_ = await fetch_user(ctx)

        q = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_quests WHERE class = $1 ORDER BY RANDOM() LIMIT 1",
            class_[1]
        )

        user = self.bot.get_user(q[2])
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"{user.name} sends you on a quest!", icon_url=user.avatar_url)
        embed.description = q[0]
        embed.set_footer(text="Type a number between 1-10")
        await ctx.send(embed=embed)
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
            await add_xp(ctx, xp=xp)
            await lvl(ctx, mon=mon, msg1=f"You completed the quest, leveled up and earned {mon}",
                      msg2=f"You completed the quest and earned {xp}xp")
        else:
            mon = random.randint(1, 100)
            await add_xp(ctx, xp=10)
            await lvl(ctx, mon=mon, msg1=f"You failed to complete the quest, but you leveled up and earned {mon}",
                      msg2=f"You failed to complete the quest and earned 10xp")

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
        item = await item_class(class_=m_.content.lower())
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
        user = await fetch_user(ctx)
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
        user = await fetch_user(ctx)
        s = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_shop WHERE name=$1 AND class = $2",
            item.title(), user[1])

        m = await fetch_mastery(ctx)
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
    @equipped()
    async def duel(self, ctx, user: discord.Member):
        """Duel other players!"""
        u = await fetch_user(ctx, user.id)

        if not u[5]:
            return await ctx.send(f"{user.mention} needs to equip an item ({ctx.prefix}equip <item>)")

        if user.bot:
            return await ctx.send("You can't duel the bot.")

        await ctx.send(f"Do you {user.mention} accept this battle?")

        def accept(m):
            return m.author == user \
                   and m.content.capitalize() in ["Yes", "No"]

        apt = await ctx.bot.wait_for('message', check=accept)
        apt = apt.content

        if apt == "Yes":
            def control(m):
                return m.author == ctx.author and m.content in ["1", "2"]

            def control2(m):
                return m.author == user and m.content in ["1", "2"]

            hp2 = 750
            hp = 750
            w = await fetch_user(ctx)
            w2 = await fetch_user(ctx, user.id)
            weapon = await fetch_item(ctx, w[5], w[1])
            weapon2 = await fetch_item(ctx, w2[5], w[1], user.id)
            msg = await ctx.bot.wait_for('message', check=control)
            msg2 = await ctx.bot.wait_for('message', check=control2)

            await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")

            while hp2 or hp > 0:
                if msg.content == "1":
                    dam = random.randint(1, weapon[2] / 2)
                    hp2 = hp2 - dam
                    await ctx.send(
                        f"{ctx.author.mention}'s attack with **{weapon[0]}** dealt {dam}dmg to {user.mention} "
                        f"\n {user.mention} has {hp2}hp",
                        delete_after=20)
                    await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage", delete_after=20)

                else:
                    dam = random.randint(1, weapon[2] / 2)
                    hp2 = hp2 - dam
                    await ctx.send(
                        f"{ctx.author.mention}'s barrage with **{weapon[0]}** dealt {dam}dmg to {user.mention} "
                        f"\n {user.mention} has {hp2}hp",
                        delete_after=20)
                    await ctx.send(f"{user.mention}, **1:** Attack, **2:** Barrage", delete_after=20)

                if msg2.content == "1":
                    dam = random.randint(1, weapon2[2] / 2)
                    hp = hp - dam
                    await ctx.send(
                        f"{user.mention}'s attack with **{weapon[0]}** dealt {dam}dmg to {ctx.author.mention} "
                        f"\n {ctx.author.mention} has {hp2}hp",
                        delete_after=20)
                    await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage", delete_after=20)

                else:
                    dam = random.randint(1, weapon[2] / 2)
                    hp = hp - dam
                    await ctx.send(
                        f"{user.mention}'s barrage with **{weapon[0]}** dealt {dam}dmg to {ctx.author.mention} "
                        f"\n {ctx.author.mention} has {hp2}hp",
                        delete_after=20)
                    await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage", delete_after=20)

                if hp <= 0:
                    await add_xp(ctx, xp=200, user=user.id)
                    await lvl(ctx, mon=200, user=user.id,
                              msg1=f"{user.mention} won against {ctx.author.mention} using **{weapon2[0]}**,"
                                   f"they leveled up and earned 200$",
                              msg2=f"{user.mention} won against {ctx.author.mention} using **{weapon2[0]}**,"
                                   f"they earned 200xp")
                elif hp2 <= 0:
                    await add_xp(ctx, xp=200)
                    await lvl(ctx, mon=200,
                              msg1=f"{ctx.author.mention} won against {user.mention} using **{weapon[0]}**,"
                                   f"they leveled up and earned 200$",
                              msg2=f"{ctx.author.mention} won against {user.mention} using **{weapon[0]}**,"
                                   f"they earned 200xp")
                else:
                    await ctx.send("It's a tie! Since there are no winners, there is no rewards!")

    @commands.command()
    @registered()
    async def profile(self, ctx, user: discord.Member = None):
        """Your current stats."""

        async with ctx.typing():
            if not user:
                user = ctx.author

            you = await fetch_user(ctx, user.id)
            youm = await fetch_mastery(ctx, user.id)
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
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def master(self, ctx):
        """Increase your mastery level"""

        chance = random.randint(1, 100)

        if chance > 50 < 75:
            await add_mastery_xp(ctx, 50)
            await mastery_lvl(ctx, 100, msg1=f"You have done well and leveled up your mastery and earned 100$",
                              msg2=f"You have done well, but you earned 50xp")
        elif chance < 50:
            await add_mastery_xp(ctx, 10)
            await mastery_lvl(ctx, 10, msg1=f"You have done poorly, but you leveled up and earned 10$",
                              msg2=f"You have done poorly, but you earned 10xp")
        else:
            await add_mastery_xp(ctx, 100)
            await mastery_lvl(ctx, 250, msg1=f"You have done great and leveled up your mastery and earned 250$",
                              msg2=f"You have done great, but you earned 100xp")

    @commands.command()
    @registered()
    async def bal(self, ctx, user: discord.Member = None):
        """Show how much money you or other users have."""
        if not user:
            user = ctx.author

        balance = await fetch_user(ctx, user.id)
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.description = f"You have {balance[3]}$"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    @registered()
    async def daily(self, ctx):
        """Grab your daily rewards."""
        money = random.randint(100, 1000)
        await add_money(ctx, money)

        await ctx.send(f"For your patience, you earned {money}$")

    @commands.command()
    @registered()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        n = random.randint(1, 15)
        n2 = random.randint(1, 15)
        await ctx.send(f"**You:** {n} \n**Dealer:** {n2} \n"
                       "Hit or Stand?")

        def hit(m):
            return m.author == ctx.author and m.content.capitalize() in ["Hit", "Stand"]

        m_ = await ctx.bot.wait_for('message', check=hit)
        m_ = m_.content
        if m_ == "Hit":
            number = random.randint(1, 6)
            number2 = random.randint(1, 6)
            if number + n > number2 + n2:
                await add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {number + n}")
            elif number2 + n2 > number + n:
                await ctx.send(f"You just lost {bet}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {number + n}")
                await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                                         bet, ctx.author.id)
            else:
                await ctx.send("It's a tie! You keep your money.")
        else:
            number2 = random.randint(1, 6)
            if n > number2 + n2:
                await add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {n}")
            elif number2 + n2 > n:
                await ctx.send(f"You just lost {bet}$!"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {n}")
                await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                                         bet, ctx.author.id)
            else:
                await ctx.send("It's a tie! You keep your money.")


def setup(bot):
    bot.add_cog(Rpg(bot))
