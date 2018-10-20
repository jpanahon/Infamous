import random
from discord.ext import commands
import logging
from .utils.paginator import SimplePaginator
from .utils.rpg_tools import *

logging.basicConfig(level=logging.INFO)


class Error(commands.CheckFailure):
    pass


def registered():
    async def predicate(ctx):
        data = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_profile WHERE id=$1",
            ctx.author.id
        )
        if not data:
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
        await ctx.send("Choose a class! (You can pick any it doesn't matter)")

        def class_(m):
            return m.author == ctx.author and m.channel == ctx.channel

        m_ = await ctx.bot.wait_for('message', check=class_)
        await ctx.send("Great! Now choose a skill for your character. (You can add other skills later) \n"
                       "**Marksmanship, Swordsmanship, Necromancy, Clairvoyance, Pyromania, Permafrost, "
                       "Insight, Sorcery, Telekinesis and Swiftness**")

        def skills_(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Marksmanship", "Swordsmanship", "Necromancy",
                    "Clairvoyance", "Pyromania", "Permafrost",
                    "Insight", "Sorcery", "Telekinesis", "Swiftness"]

        s_ = await ctx.bot.wait_for('message', check=skills_)
        skill = s_.content.capitalize()
        await ctx.bot.db.execute("INSERT INTO rpg_profile VALUES($1, $2, $3, $4, $5, $6)",
                                 ctx.author.id, m_.content.capitalize(), 1, 0, 100, skill)

        await ctx.bot.db.execute("INSERT INTO rpg_mastery VALUES($1, $2, $3, $4)",
                                 ctx.author.id, skill, 1, 0)
        await ctx.send(f"You have successfully registered, type {ctx.prefix}help Rpg for commands.")

    @commands.command()
    async def top(self, ctx):
        """The Top Players of the RPG."""
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_profile ORDER BY level ASC"
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

        q = await ctx.bot.db.fetchrow(
            "SELECT * FROM rpg_quests ORDER BY RANDOM() LIMIT 1",
        )

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"You have been sent on a quest!")
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
    @commands.has_permissions(manage_messages=True)
    async def add_quest(self, ctx, *, quest):
        """Adds a quest"""

        await ctx.bot.db.execute("INSERT INTO rpg_quests VALUES($1)", quest.title())
        await ctx.send(f"Added {quest.title()}")

    @admin.command(name="add-item")
    @registered()
    @commands.has_permissions(manage_messages=True)
    async def add_item(self, ctx, name: str, price: int,
                       damage: int, defense: int,
                       description: str):
        """Add's an item to the shop

**Example:** \*!admin add-item 'Example Sword' 10 20 15 'This is an Example'"""
        await ctx.send(
            "What skill is required to purchase this item? \n"
            "**Marksmanship, Swordsmanship, Necromancy, Clairvoyance, Pyromania, Permafrost, "
            "Insight, Sorcery, Telekinesis and Swiftness**"
        )

        def skills_(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Marksmanship", "Swordsmanship", "Necromancy",
                    "Clairvoyance", "Pyromania", "Permafrost",
                    "Insight", "Sorcery", "Telekinesis", "Swiftness"]

        skills = (await ctx.bot.wait_for('message', check=skills_)).content.capitalize()

        await ctx.send(f"What level of **{skills}** is required to buy {name.title()}?")

        def lvl(m):
            return m.author == ctx.author and m.content.isdigit() <= 200

        req = int((await ctx.bot.wait_for('message', check=lvl)).content)

        await ctx.send("What type of item is this? \n"
                       "**Sword, Bow, Spear, Dagger, Staff, Shield, Scroll, Ring, Hammer**")

        def type_(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Sword", "Bow", "Spear", "Dagger",
                    "Staff", "Shield", "Scroll", "Ring", "Hammer"]

        type_ = (await ctx.bot.wait_for('message', check=type_)).content.capitalize()

        await ctx \
            .send(f"**Name:** {name} \n"
                  f"**Type:** {type_} \n"
                  f"**Price:** {price} \n"
                  f"**Damage:** {damage} \n"
                  f"**Defense:** {defense} \n"
                  f"**Skills:** {skills} Level {req} \n"
                  f"**Description:** {description} \n"
                  f"`Do you approve? Yes or No?`")

        def yon(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Yes", "No"]

        y = await ctx.bot.wait_for('message', check=yon)
        if y.content == "Yes":
            await ctx.bot.db.execute(
                "INSERT INTO rpg_shop VALUES($1, $2, $3, $4, $5, $6, $7, $8)",
                name.title(), type_, price, damage, defense, skills, description.title(), req)

            await ctx.send(f"**{name.title()}** has been created!")
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
            t = {"Sword": "https://cdn.discordapp.com/attachments/389275624163770378/502084949420277781/sword.png",
                 "Bow": "https://cdn.discordapp.com/attachments/389275624163770378/502087339854659604/bow.png",
                 "Spear": "https://cdn.discordapp.com/attachments/389275624163770378/502088345661341696/spear.png",
                 "Dagger": "https://cdn.discordapp.com/attachments/389275624163770378/502089390747549696/dagger.png",
                 "Staff": "https://cdn.discordapp.com/attachments/389275624163770378/502088392872558612/staff.png",
                 "Shield": "https://cdn.discordapp.com/attachments/389275624163770378/502083911388626974/shield.png",
                 "Scroll": "https://cdn.discordapp.com/attachments/389275624163770378/502082224900800513/scroll.png",
                 "Ring": "https://cdn.discordapp.com/attachments/389275624163770378/502086417048928266/ring.png",
                 "Hammer": "https://cdn.discordapp.com/attachments/389275624163770378/502084112547315733/hammer.png"
                 }
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
            t = {"Sword": "https://cdn.discordapp.com/attachments/389275624163770378/502084949420277781/sword.png",
                 "Bow": "https://cdn.discordapp.com/attachments/389275624163770378/502087339854659604/bow.png",
                 "Spear": "https://cdn.discordapp.com/attachments/389275624163770378/502088345661341696/spear.png",
                 "Dagger": "https://cdn.discordapp.com/attachments/389275624163770378/502089390747549696/dagger.png",
                 "Staff": "https://cdn.discordapp.com/attachments/389275624163770378/502088392872558612/staff.png",
                 "Shield": "https://cdn.discordapp.com/attachments/389275624163770378/502083911388626974/shield.png",
                 "Scroll": "https://cdn.discordapp.com/attachments/389275624163770378/502082224900800513/scroll.png",
                 "Ring": "https://cdn.discordapp.com/attachments/389275624163770378/502086417048928266/ring.png",
                 "Hammer": "https://cdn.discordapp.com/attachments/389275624163770378/502084112547315733/hammer.png"
                 }

            for i in data:
                p.append(item_embed(i, t[i[1]]))

            await SimplePaginator(extras=p).paginate(ctx)

    @commands.command()
    @registered()
    async def buy(self, ctx, *, item):
        """Buy an item from shop"""
        user = await fetch_user(ctx)
        skills = await fetch_skills(ctx)
        item_ = await fetch_item(ctx, item.title(), user=None, inv='rpg_shop')
        if item_[5] in skills:
            await purchase(ctx, item.title(), user[3], item_[5])

    @commands.command()
    @registered()
    async def equip(self, ctx, *, item):
        """Equip an item to use in battle"""
        u = await fetch_user(ctx)
        i = await fetch_item(ctx, item.title(), u[1])

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
        u = (await fetch_user(ctx, user.id))[5]

        if not u:
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
                    lb = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", user.id)
                    if lb:
                        await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", user.id)
                    else:
                        await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                                 user.id, 1, 0)

                    lb2 = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", ctx.author.id)
                    if lb2:
                        await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", ctx.author.id)
                    else:
                        await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                                 ctx.author.id, 0, 1)
                elif hp2 <= 0:
                    await add_xp(ctx, xp=200)
                    await lvl(ctx, mon=200,
                              msg1=f"{ctx.author.mention} won against {user.mention} using **{weapon[0]}**,"
                                   f"they leveled up and earned 200$",
                              msg2=f"{ctx.author.mention} won against {user.mention} using **{weapon[0]}**,"
                                   f"they earned 200xp")
                    lb = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", ctx.author.id)
                    if lb:
                        await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", ctx.author.id)
                    else:
                        await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                                 ctx.author.id, 1, 0)

                    lb2 = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", user.id)
                    if lb2:
                        await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", user.id)
                    else:
                        await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                                 user.id, 0, 1)
                else:
                    await ctx.send("It's a tie! Since there are no winners, there is no rewards!")

    @commands.command()
    @registered()
    async def profile(self, ctx, user: discord.Member = None):
        """Your current stats."""
        if not user:
            user = ctx.author

        stats = await fetch_user(ctx, user.id)
        embed = discord.Embed(color=0xba1c1c)
        embed.description = f"**Level:** {stats[2]} \n **XP:** {stats[3]}"
        embed.set_author(name=user.name, icon_url=user.avatar_url)
        embed.add_field(name="Statistics", value=f"**Class:** {stats[1]} \n"
                                                 f"**Balance:** {stats[4]} \n"
                                                 f"**Equipped Weapon:** {stats[6]} \n"
                                                 f"**Main Skill:** {stats[5]}", inline=True)

        skills = await ctx.bot.db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)

        p = []
        for i in skills:
            p.append(f"**{i[1]}** - Level {i[2]} \n")

        embed.add_field(name="Skills", value=''.join(p), inline=True)

        iv = await ctx.bot.db.fetch("SELECT * FROM rpg_inventory WHERE owner=$1", user.id)
        if iv:
            inv = []
            for i in iv:
                inv.append(f"{i[0]} \n")

            embed.add_field(name="Inventory", value=''.join(inv), inline=False)
        else:
            embed.add_field(name="Inventory", value="None", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    @registered()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def master(self, ctx):
        """Increase your mastery level"""

        chance = random.randint(1, 100)
        await ctx.send("Which skill do you want to master? **Marksmanship, Swordsmanship, Necromancy, Clairvoyance, "
                       "Pyromania, Permafrost, Insight, Sorcery, Telekinesis, Swiftness**")

        def skills_(m):
            return m.author == ctx.author \
                   and m.content.capitalize() in \
                   ["Marksmanship", "Swordsmanship", "Necromancy",
                    "Clairvoyance", "Pyromania", "Permafrost",
                    "Insight", "Sorcery", "Telekinesis", "Swiftness"]

        skill = (await ctx.bot.wait_for('message', check=skills_)).content.capitalize()

        u = await fetch_mastery(ctx, skill)
        if u:
            pass
        else:
            await ctx.bot.db.execute("INSERT INTO rpg_mastery VALUES($1, $2, $3, $4)",
                                     ctx.author.id, skill, 1, 0)

        if chance > 50 < 75:
            await add_mastery_xp(ctx, 50)
            await mastery_lvl(ctx, 100, skill, msg1=f"You have done well and leveled up your mastery and earned 100$",
                              msg2=f"You have done well, but you earned 50xp")
        elif chance < 50:
            await add_mastery_xp(ctx, 10)
            await mastery_lvl(ctx, 10, skill, msg1=f"You have done poorly, but you leveled up and earned 10$",
                              msg2=f"You have done poorly, but you earned 10xp")
        else:
            await add_mastery_xp(ctx, 100)
            await mastery_lvl(ctx, 250, skill, msg1=f"You have done great and leveled up your mastery and earned 250$",
                              msg2=f"You have done great, but you earned 100xp")

    @commands.command()
    @registered()
    async def bal(self, ctx, user: discord.Member = None):
        """Show how much money you or other users have."""
        if not user:
            user = ctx.author

        balance = (await fetch_user(ctx, user.id))[4]
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.description = f"You have {balance}$"
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

    @commands.command()
    @registered()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def upgrade(self, ctx, *, item):
        """Upgrade the statistics of a weapon."""

        c = (await fetch_user(ctx))[1]
        i = await fetch_item(ctx, item, c)

        await ctx.send(f"Are you sure you want to upgrade **{i[0]}?**  Yes or No?\n"
                       f"Modified Statistics: **Price:** {i[2] * 2}, **Damage:** {i[3] * 2}, **Defense:** {i[4] * 2}")

        def check(m):
            return m.author == ctx.author and m.content.capitalize() in ["Yes", "No"]

        msg = await ctx.bot.wait_for('message', check=check)
        msg = msg.content
        if msg == "Yes":
            if c[3] >= i[2] * 2:
                await ctx.bot.db.execute(
                    "UPDATE rpg_inventory SET price=$1, damage=$2, defense=$3 WHERE name=$4 AND owner=$5",
                    i[2] * 2, i[3] * 2, i[4] * 2, i[0], i[7])
                await ctx.send(f"Upgraded **{item.title()}**'s statistics.")
            else:
                return await ctx.send("You don't have enough to upgrade this item")
        else:
            await ctx.send("I guess you don't want to upgrade your item.")

    @commands.command(aliases=['items', 'inv'])
    @registered()
    async def inventory(self, ctx, user=None):
        if not user:
            user = ctx.author

        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_inventory WHERE owner=$1 ORDER BY price",
            user.id)

        t = {"Sword": "https://cdn.discordapp.com/attachments/389275624163770378/502084949420277781/sword.png",
             "Bow": "https://cdn.discordapp.com/attachments/389275624163770378/502087339854659604/bow.png",
             "Spear": "https://cdn.discordapp.com/attachments/389275624163770378/502088345661341696/spear.png",
             "Dagger": "https://cdn.discordapp.com/attachments/389275624163770378/502089390747549696/dagger.png",
             "Staff": "https://cdn.discordapp.com/attachments/389275624163770378/502088392872558612/staff.png",
             "Shield": "https://cdn.discordapp.com/attachments/389275624163770378/502083911388626974/shield.png",
             "Scroll": "https://cdn.discordapp.com/attachments/389275624163770378/502082224900800513/scroll.png",
             "Ring": "https://cdn.discordapp.com/attachments/389275624163770378/502086417048928266/ring.png",
             "Hammer": "https://cdn.discordapp.com/attachments/389275624163770378/502084112547315733/hammer.png"
             }

        p = []
        for i in data:
            p.append(inventory_embed(ctx, i, t[i[1]]))

        await SimplePaginator(extras=p).paginate(ctx)

    @commands.command()
    @registered()
    async def skills(self, ctx, user: discord.Member=None):
        if not user:
            user = ctx.author

        skills = await ctx.bot.db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)

        p = []
        for i in skills:
            p.append(f"**{i[1]}** - Level {i[2]} \n")

        embed=discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"{user.name}'s skills", icon_url=user.avatar_url)
        embed.description = ''.join(p)
        await ctx.send(embed=embed)

    @commands.command()
    @registered()
    async def drink(self, ctx, user: discord.Member):
        if user.bot or user == ctx.author:
            return await ctx.send("Must not be a bot or yourself.")

        await ctx.send(f"{user.mention} do you accept {ctx.author.mention}'s challenge? \n"
                       f"Yes or No?")

        def check(m):
            return m.author == user and m.content.capitalize() in ["Yes", "No"]

        yon = (await ctx.bot.wait_for('message', check=check)).content

        if yon == "Yes":
            choice = random.choice([ctx.author.name, user.name])
            if choice == ctx.author.name:
                xp = random.randint(10, 100)
                mon = random.randint(10, 100)
                await add_xp(ctx, xp)
                await lvl(ctx, mon,
                          msg1=f"{ctx.author.mention} won the drinking contest, leveled up, and earned {mon}$",
                          msg2=f"{ctx.author.mention} won the drinking contest, and earned {xp}xp")
            else:
                xp = random.randint(10, 100)
                mon = random.randint(10, 100)
                await add_xp(ctx, xp)
                await lvl(ctx, mon,
                          msg1=f"{user.mention} won the drinking contest, leveled up, and earned {mon}$",
                          msg2=f"{user.mention} won the drinking contest, and earned {xp}xp", user=user.id)
        else:
            await ctx.send("I guess they didn't want to get drunk tonight.")

    @commands.command()
    @registered()
    @commands.cooldown(2, 600, commands.BucketType.user)
    async def coinflip(self, ctx, *, choice):
        choice = choice.capitalize()
        if choice not in ["Heads", "Tails"]:
            return await ctx.send(f"Please type `Heads` or `Tails` instead of `{choice}`")

        if choice == "Heads":
            c = random.choice(["Heads", "Tails"])
            if c == "Heads":
                await add_xp(ctx, 100)
                await lvl(ctx, 200,
                          msg1=f"{ctx.author.mention} It was **Heads!** You leveled up and earned 200$",
                          msg2=f"{ctx.author.mention} It was **Heads!** You earned 100xp")
            else:
                await add_xp(ctx, 50)
                await lvl(ctx, 100,
                          msg1=f"{ctx.author.mention} Sorry it was **Tails!** You leveled up and earned 100$",
                          msg2=f"{ctx.author.mention} Sorry it was **Tails!** You earned 50xp")
        elif choice == "Tails":
            c = random.choice(["Tails", "Heads"])
            if c == "Tails":
                await add_xp(ctx, 100)
                await lvl(ctx, 200,
                          msg1=f"{ctx.author.mention} It was **Tails!** You leveled up and earned 200$",
                          msg2=f"{ctx.author.mention} It was **Tails!** You earned 100xp")
            else:
                await add_xp(ctx, 50)
                await lvl(ctx, 100,
                          msg1=f"{ctx.author.mention} Sorry it was **Head!s** You leveled up and earned 100$",
                          msg2=f"{ctx.author.mention} Sorry it was **Heads!** You earned 50xp")


def setup(bot):
    bot.add_cog(Rpg(bot))
