import logging
import random

import discord
from discord.ext import commands

from .utils.paginator import SimplePaginator as paginator
from .utils import rpg_tools as rpg

logging.basicConfig(level=logging.INFO)


def registered():
    async def predicate(ctx):
        data = await rpg.fetch_user(ctx)
        if data is None:
            raise commands.CheckFailure(
                "You are not registered! Type `*!register` or `@Infamous#5069 register`"
            )
        else:
            return True

    return commands.check(predicate)


def unregistered():
    async def predicate(ctx):
        data = await rpg.fetch_user(ctx)
        if data:
            raise commands.CheckFailure(
                "You are already registered! If you want to edit your class type `*!class` or `@Infamous#5069 class`"
            )
        else:
            return True

    return commands.check(predicate)


def equipped():
    async def predicate(ctx):
        data = (await rpg.fetch_user(ctx))[6]
        if data is None:
            raise commands.CheckFailure(
                "You don't have an item equipped! Type `*!equip` or `@Infamous#5069 equip`"
            )
        else:
            return True

    return commands.check(predicate)


class Rpg:
    """Infamous RPG commands."""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return ctx.guild is not None

    @commands.command()
    @unregistered()
    async def register(self, ctx):
        """Register for the rpg."""
        await ctx.send("Choose a class! (You can type any class it doesn't matter)")

        def class_(m):
            return m.author == ctx.author and m.channel == ctx.channel

        m_ = await ctx.bot.wait_for('message', check=class_)
        await ctx.send("Great! Now choose a skill for your character. (You can add other skills later) \n"
                       "**Marksmanship, Swordsmanship, Necromancy, Clairvoyance, Pyromania, Permafrost, "
                       "Insight, Sorcery, Telekinesis and Swiftness**")

        skills = ["Marksmanship", "Swordsmanship", "Necromancy", "Clairvoyance", "Pyromania", "Permafrost",
                  "Insight", "Sorcery", "Telekinesis", "Swiftness"]

        skill = await rpg.choose(ctx, skills)
        await ctx.bot.db.execute("INSERT INTO rpg_profile VALUES($1, $2, $3, $4, $5, $6)",
                                 ctx.author.id, m_.content.capitalize(), 1, 0, 100, skill)

        await ctx.bot.db.execute("INSERT INTO rpg_mastery VALUES($1, $2, $3, $4)",
                                 ctx.author.id, skill, 1, 0)
        await ctx.send(f"You have successfully registered, type {ctx.prefix}guide for help.")

    @commands.command()
    async def top(self, ctx):
        """The Top Players of the RPG."""
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_profile ORDER BY level DESC"
        )

        p = []
        number = 0
        for i in data:
            number = number + 1
            p.append(await rpg.lb_embed(ctx, i, number, len(data)))

        await paginator(extras=p).paginate(ctx)

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
            await rpg.add_xp(ctx, xp=xp)
            await rpg.lvl(ctx, mon=mon, msg1=f"You completed the quest, leveled up and earned {mon}",
                          msg2=f"You completed the quest and earned {xp}xp")
        else:
            mon = random.randint(1, 100)
            await rpg.add_xp(ctx, xp=10)
            await rpg.lvl(ctx, mon=mon, msg1=f"You failed to complete the quest, but you leveled up and earned {mon}",
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
        """Add's an item to the shop.

        **Example:** \*!admin add-item 'Example Sword' 10 20 15 'This is an Example'
        """
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

        def levl(m):
            return m.author == ctx.author and m.content.isdigit() <= 200

        req = int((await ctx.bot.wait_for('message', check=levl)).content)

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

        y = await rpg.yon(ctx)
        if y == "Yes":
            await ctx.bot.db.execute(
                "INSERT INTO rpg_shop VALUES($1, $2, $3, $4, $5, $6, $7, $8)",
                name.title(), type_, price, damage, defense, skills, description.title(), req)

            await ctx.send(f"**{name.title()}** has been created!")
        else:
            await ctx.send("Cancelled")

    @commands.group(case_insensitive=True, invoke_without_command=True)
    @registered()
    async def shop(self, ctx):
        """Items that are available"""
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_shop ORDER BY price DESC"
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
            number = 0
            for i in data:
                number += 1
                p.append(rpg.item_embed(i, t[i[1]], number, len(data)))

            await paginator(extras=p).paginate(ctx)

    @shop.command()
    @registered()
    async def recommend(self, ctx):
        """Items you can buy."""
        user = await rpg.fetch_user(ctx)
        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_shop ORDER BY price BETWEEN 0 AND $1 DESC",
            user[4]
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

            number = 0
            for i in data:
                number += 1
                p.append(rpg.item_embed(i, t[i[1]], number, len(data)))

            await paginator(extras=p).paginate(ctx)

    @commands.command()
    @registered()
    async def buy(self, ctx, *, item):
        """Buy an item from shop"""
        user = await rpg.fetch_user(ctx)
        skills = await rpg.fetch_skills(ctx)
        i = await rpg.fetch_item(ctx, item.title(), None, 'rpg_shop')
        if i[5] in skills:
            skill = i[5]
        else:
            return await ctx.send("You don't have the right skill")

        mast = (await rpg.fetch_mastery(ctx, skill=i[5], user=ctx.author.id))[2]
        inv = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                        item.title(), ctx.author.id)
        if inv:
            return await ctx.send("You already have this item!")

        if user[4] >= i[2]:
            if i[5] == skill and mast >= i[7]:
                await ctx.send(f"Do you really want to buy **{i[0]}** \n"
                               f"Price: {i[2]}$, Yes or No?")
                msg = await rpg.yon(ctx)
                if msg == "Yes":
                    await ctx.send(f"{i[0]} has been added to your inventory.")

                    await ctx.bot.db.execute(
                        "INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                        i[0], i[1], i[2], i[3], i[4], i[5], i[6], user[0], 0
                    )
                else:
                    await ctx.send(f"Guess you don't want to spend **{i[2]}$**")
            else:
                return await ctx.send("You don't have the right skill or skill level.")
        else:
            return await ctx.send(f"Sorry you need {i[2] - user[2]}$ more to purchase!")

    @commands.command()
    @registered()
    async def equip(self, ctx, *, item):
        """Equip an item to use in battle"""
        i = await rpg.fetch_item(ctx, item.title())
        if i:
            await ctx.send(f"**{i[0]}** has been equipped and can be used for battle.")
            await ctx.bot.db \
                .execute("UPDATE rpg_profile SET equipped = $1 WHERE id=$2",
                         i[0], ctx.author.id)
        else:
            await ctx.send("You don't have this item.")

    @commands.command()
    @registered()
    @equipped()
    async def duel(self, ctx, player2: discord.Member):
        """Duel other players!"""
        u = await rpg.fetch_user(ctx, player2.id)

        if u[6] is None:
            return await ctx.send(f"{player2.mention} needs to equip an item ({ctx.prefix}equip <item>)")

        if player2.bot or player2 == ctx.author:
            return await ctx.send("You can't duel a bot or yourself.")

        await ctx.send(f"Do you {player2.mention} accept this battle? Yes or No?")

        apt = await rpg.yon(ctx, user=player2)
        if apt == "Yes":
            hp2 = {"hp": 1000}
            hp = {"hp": 1000}
            await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage")
            active = True
            while active:
                w = await rpg.fetch_user(ctx)
                w2 = await rpg.fetch_user(ctx, player2.id)
                weapon = await rpg.fetch_item(ctx, w[6])
                weapon2 = await rpg.fetch_item(ctx, w2[6], player2.id)

                def control(m):
                    return m.author == ctx.author and m.content in ["1", "2"]

                msg = await ctx.bot.wait_for('message', check=control, timeout=10)

                if msg.content == "1":
                    dam = random.randint(1, abs(weapon[3] - weapon2[4] / 5))
                    hp2['hp'] -= dam
                    await ctx.send(
                        f"{ctx.author.mention}'s attack with **{weapon[0]}** dealt {dam}dmg to {player2.mention} "
                        f"\n{player2.mention} has {hp2['hp']}hp",
                        delete_after=20)
                    await ctx.send(f"{player2.mention}, **1:** Attack, **2:** Barrage", delete_after=20)
                    if hp2['hp'] <= 0:
                        active = False

                else:
                    dam = random.randint(10, abs(weapon[3] - weapon2[4] / 5))
                    hp2['hp'] -= dam
                    await ctx.send(
                        f"{ctx.author.mention}'s barrage with **{weapon[0]}** dealt {dam}dmg to {player2.mention} "
                        f"\n{player2.mention} has {hp2['hp']}hp",
                        delete_after=20)
                    await ctx.send(f"{player2.mention}, **1:** Attack, **2:** Barrage", delete_after=20)
                    if hp2['hp'] <= 0:
                        active = False

                def control2(m):
                    return m.author == player2 and m.content in ["1", "2"]

                msg2 = await ctx.bot.wait_for('message', check=control2, timeout=10)

                if msg2.content == "1":
                    dam = random.randint(1, abs(weapon2[3] - weapon[4] / 5))
                    hp['hp'] -= dam
                    await ctx.send(
                        f"{player2.mention}'s attack with **{weapon2[0]}** dealt {dam}dmg to {ctx.author.mention} "
                        f"\n{ctx.author.mention} has {hp['hp']}hp",
                        delete_after=20)
                    await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage", delete_after=20)
                    if hp['hp'] <= 0:
                        active = False
                else:
                    dam = random.randint(10, abs(weapon2[3] - weapon[4] / 5))
                    hp['hp'] -= dam
                    await ctx.send(
                        f"{player2.mention}'s barrage with **{weapon2[0]}** dealt {dam}dmg to {ctx.author.mention} "
                        f"\n{ctx.author.mention} has {hp['hp']}hp",
                        delete_after=20)
                    await ctx.send(f"{ctx.author.mention}, **1:** Attack, **2:** Barrage", delete_after=20)
                    if hp['hp'] <= 0:
                        active = False

            if hp['hp'] <= 0:
                await rpg.add_xp(ctx, xp=200, user=player2.id)
                await rpg.lvl(ctx, mon=200, user=player2.id,
                              msg1=f"{player2.mention} won against {ctx.author.mention} using **{weapon2[0]}**, "
                                   f"they leveled up and earned 200$",
                              msg2=f"{player2.mention} won against {ctx.author.mention} using **{weapon2[0]}**, "
                                   f"they earned 200xp")
                lb = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", player2.id)
                if lb:
                    await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", player2.id)
                else:
                    await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                             player2.id, 1, 0)

                lb2 = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", ctx.author.id)
                if lb2:
                    await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", ctx.author.id)
                else:
                    await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                             ctx.author.id, 0, 1)
            elif hp2['hp'] <= 0:
                await rpg.add_xp(ctx, xp=200)
                await rpg.lvl(ctx, mon=200,
                              msg1=f"{ctx.author.mention} won against {player2.mention} using **{weapon[0]}**, "
                                   f"they leveled up and earned 200$",
                              msg2=f"{ctx.author.mention} won against {player2.mention} using **{weapon[0]}**, "
                                   f"they earned 200xp")
                lb = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", ctx.author.id)
                if lb:
                    await ctx.bot.db.execute("UPDATE rpg_duels SET wins = wins + 1 WHERE id=$1", ctx.author.id)
                else:
                    await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                             ctx.author.id, 1, 0)

                lb2 = await ctx.bot.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", player2.id)
                if lb2:
                    await ctx.bot.db.execute("UPDATE rpg_duels SET losses = losses + 1 WHERE id=$1", player2.id)
                else:
                    await ctx.bot.db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)",
                                             player2.id, 0, 1)
            else:
                return await ctx.send("It's a tie! Since there are no winners, there is no rewards!")
        else:
            return await ctx.send("I guess you don't want to duel")

    @commands.command()
    @registered()
    async def profile(self, ctx, user: discord.Member = None):
        """Your current statistics."""
        if not user:
            user = ctx.author

        stats = await rpg.fetch_user(ctx, user.id)
        if stats:
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
        else:
            return await ctx.send("This user isn't registered.")

    @commands.command()
    @registered()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def master(self, ctx):
        """Increase your mastery level of a skill"""

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

        u = await rpg.fetch_mastery(ctx, skill)
        if u:
            pass
        else:
            await ctx.bot.db.execute("INSERT INTO rpg_mastery VALUES($1, $2, $3, $4)",
                                     ctx.author.id, skill, 1, 0)

        if chance > 50 < 75:
            await rpg.add_mastery_xp(ctx, 50)
            await rpg.mastery_lvl(ctx, 100, skill,
                                  msg1=f"You have done well and leveled up your mastery and earned 100$",
                                  msg2=f"You have done well, but you earned 50xp")
        elif chance < 50:
            await rpg.add_mastery_xp(ctx, 10)
            await rpg.mastery_lvl(ctx, 10, skill,
                                  msg1=f"You have done poorly, but you leveled up and earned 10$",
                                  msg2=f"You have done poorly, but you earned 10xp")
        else:
            await rpg.add_mastery_xp(ctx, 100)
            await rpg.mastery_lvl(ctx, 250, skill,
                                  msg1=f"You have done great and leveled up your mastery and earned 250$",
                                  msg2=f"You have done great, but you earned 100xp")

    @commands.command()
    @registered()
    async def bal(self, ctx, user: discord.Member = None):
        """Show how much money you or other users have."""
        if not user:
            user = ctx.author

        balance = (await rpg.fetch_user(ctx, user.id))[4]
        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.description = f"You have {balance}$"
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    @registered()
    async def daily(self, ctx):
        """Grab your daily rewards.

        **Items are randomly chosen based on skills that were randomly chosen**
        """

        try:
            money = random.randint(100, 1000)
            await rpg.add_money(ctx, money)

            skills = await rpg.fetch_skills(ctx)
            skills = random.choice(skills)
            items = await ctx.bot.db.fetch("SELECT * FROM rpg_inventory WHERE owner=$1", ctx.author.id)
            p = []
            for i in items:
                p.append(i[0])
            item = await ctx.bot.db.fetchrow(
                "SELECT * FROM rpg_shop WHERE skill=$1 AND level < 3 ORDER BY RANDOM() LIMIT 1",
                skills)
            if item[0] in p:
                skills_ = await rpg.fetch_skills(ctx)
                skills_ = random.choice(skills_)
                item_ = await ctx.bot.db.fetchrow(
                    "SELECT * FROM rpg_shop WHERE skill=$1, level < 3 AND name != $1 ORDER BY RANDOM() LIMIT 1",
                    skills_)

                await ctx.bot.db.execute(
                    "INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                    item_[0], item_[1], item_[2], item_[3], item_[4], item_[5], item_[6], ctx.author.id, 0
                )

                await ctx.send(f"For your patience, you earned {money}$ and **{item_[0]}**")
            else:
                await ctx.bot.db.execute(
                    "INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                    item[0], item[1], item[2], item[3], item[4], item[5], item[6], ctx.author.id, 0
                )

                await ctx.send(f"For your patience, you earned {money}$ and **{item[0]}**")
        except Exception as e:
            print(e)
            money = random.randint(100, 1000)
            await ctx.send(f"There was no item for you but you still earned {money}$")
            await rpg.add_money(ctx, money)

    @commands.command()
    @registered()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int = None):
        """Play blackjack

        **If there is no bet it takes money out of your balance**
        """

        if not bet:
            user = (await rpg.fetch_user(ctx))[4]
            bet = random.randint(100, user)

        n = random.randint(1, 15)
        n2 = random.randint(1, 15)
        await ctx.send(f"**You:** {n} \n**Dealer:** {n2} \n"
                       "Hit or Stand?")

        def hit(m):
            return m.author == ctx.author and m.content.capitalize() in ["Hit", "Stand"]

        m_ = await ctx.bot.wait_for('message', check=hit)
        m_ = m_.content
        if m_ == "Hit":
            number = random.randint(1, 15)
            number2 = random.randint(1, 15)
            if number + n > number2 + n2:
                await rpg.add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {number + n}")
            elif number2 + n2 > number + n < 21:
                await ctx.send(f"You just lost {bet}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {number + n}")
                await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                                         bet, ctx.author.id)
            elif number2 + n2 > 21:
                await rpg.add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {number + n}")
            elif number + n > 21:
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
                await rpg.add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {n}")
            elif number2 + n2 > n < 21:
                await ctx.send(f"You just lost {bet}$!"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {n}")
                await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                                         bet, ctx.author.id)
            elif number2 + n2 > 21:
                await rpg.add_money(ctx, bet * 2)
                await ctx.send(f"You win! You earn {bet * 2}$! \n"
                               f"**Dealer:** {number2 + n2} \n"
                               f"**You:** {n}")
            else:
                await ctx.send("It's a tie! You keep your money.")

    @commands.command()
    @registered()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def upgrade(self, ctx, *, item):
        """Upgrade the statistics of a weapon."""

        c = await rpg.fetch_user(ctx)
        i = await rpg.fetch_item(ctx, item.title())

        if i:
            await ctx.send(f"Are you sure you want to upgrade **{i[0]}?**  Yes or No?\n"
                           f"Modified Statistics: **Price:** {i[2] * 2}, **Damage:** {i[3] * 2}, "
                           f"**Defense:** {i[4] * 2}")

            msg = await rpg.yon(ctx)
            if msg == "Yes":
                if c[4] >= i[2] * 2:
                    await ctx.bot.db.execute(
                        "UPDATE rpg_inventory SET price=$1, damage=$2, defense=$3, upgrades = upgrades + 1 "
                        "WHERE name=$4 AND owner=$5",
                        i[2] * 2, i[3] * 2, i[4] * 2, i[0], i[7])
                    await ctx.send(f"Upgraded **{item.title()}**'s statistics.")
                    await rpg.remove_money(ctx, i[2] * 2)
                else:
                    return await ctx.send("You don't have enough to upgrade this item")
            else:
                await ctx.send("I guess you don't want to upgrade your item.")
        else:
            return await ctx.send("You don't have this item.")

    @commands.command(aliases=['items', 'inv'])
    @registered()
    async def inventory(self, ctx, user: discord.Member = None):
        """Shows inventory of a player."""
        if not user:
            user = ctx.author

        data = await ctx.bot.db.fetch(
            "SELECT * FROM rpg_inventory WHERE owner=$1 ORDER BY price DESC",
            user.id)
        if data:
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
            number = 0
            for i in data:
                number += 1
                p.append(rpg.inventory_embed(ctx, i, t[i[1]], number, len(data)))

            await paginator(extras=p).paginate(ctx)
        else:
            return await ctx.send("This person does not have any items.")

    @commands.command()
    @registered()
    async def skills(self, ctx, user: discord.Member = None):
        """Shows skill level of a player"""
        if not user:
            user = ctx.author

        skills = await ctx.bot.db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)

        p = []
        for i in skills:
            p.append(f"**{i[1]}** - Level {i[2]} \n")

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"{user.name}'s skills", icon_url=user.avatar_url)
        embed.description = ''.join(p)
        await ctx.send(embed=embed)

    @commands.command()
    @registered()
    async def drink(self, ctx, user: discord.Member):
        """Challenge other players in a drinking contest"""

        if user.bot or user == ctx.author:
            return await ctx.send("Must not be a bot or yourself.")

        await ctx.send(f"{user.mention} do you accept {ctx.author.mention}'s challenge? \n"
                       f"Yes or No?")

        yon = await rpg.yon(ctx, user)
        if yon == "Yes":
            choice = random.choice([ctx.author.name, user.name])
            if choice == ctx.author.name:
                xp = random.randint(10, 100)
                mon = random.randint(10, 100)
                await rpg.add_xp(ctx, xp)
                await rpg.lvl(ctx, mon,
                              msg1=f"{ctx.author.mention} won the drinking contest, leveled up, and earned {mon}$",
                              msg2=f"{ctx.author.mention} won the drinking contest, and earned {xp}xp")
            else:
                xp = random.randint(10, 100)
                mon = random.randint(10, 100)
                await rpg.add_xp(ctx, xp)
                await rpg.lvl(ctx, mon,
                              msg1=f"{user.mention} won the drinking contest, leveled up, and earned {mon}$",
                              msg2=f"{user.mention} won the drinking contest, and earned {xp}xp", user=user.id)
        else:
            await ctx.send("I guess they didn't want to get drunk tonight.")

    @commands.command()
    @registered()
    @commands.cooldown(2, 600, commands.BucketType.user)
    async def coinflip(self, ctx, *, choice=None):
        """Heads or Tails?

        **Randomly picks if no choice is provided.**
        """
        if not choice:
            choice = random.choice(["Heads", "Tails"])

        choice = choice.capitalize()
        if choice not in ["Heads", "Tails"]:
            return await ctx.send(f"Please type `Heads` or `Tails` instead of `{choice}`")

        if choice == "Heads":
            c = random.choice(["Heads", "Tails"])
            if c == "Heads":
                await rpg.add_xp(ctx, 100)
                await rpg.lvl(ctx, 200,
                              msg1=f"{ctx.author.mention} It was **Heads!** You leveled up and earned 200$",
                              msg2=f"{ctx.author.mention} It was **Heads!** You earned 100xp")
            else:
                await rpg.add_xp(ctx, 50)
                await rpg.lvl(ctx, 100,
                              msg1=f"{ctx.author.mention} Sorry it was **Tails!** You leveled up and earned 100$",
                              msg2=f"{ctx.author.mention} Sorry it was **Tails!** You earned 50xp")
        elif choice == "Tails":
            c = random.choice(["Tails", "Heads"])
            if c == "Tails":
                await rpg.add_xp(ctx, 100)
                await rpg.lvl(ctx, 200,
                              msg1=f"{ctx.author.mention} It was **Tails!** You leveled up and earned 200$",
                              msg2=f"{ctx.author.mention} It was **Tails!** You earned 100xp")
            else:
                await rpg.add_xp(ctx, 50)
                await rpg.lvl(ctx, 100,
                              msg1=f"{ctx.author.mention} Sorry it was **Head!s** You leveled up and earned 100$",
                              msg2=f"{ctx.author.mention} Sorry it was **Heads!** You earned 50xp")

    @commands.command()
    @registered()
    async def item(self, ctx, *, choice):
        """Show information about an item in the shop"""

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

        item = await rpg.fetch_item(ctx, choice.title(), None, 'rpg_shop')
        number = 0
        if item:
            number += 1
            await ctx.send(embed=rpg.item_embed(item, t[item[1]], number, len(item)))
        else:
            return await ctx.send(f"There is no item named **{choice.title()}**")

    @commands.command()
    async def guide(self, ctx):
        """Shows how to play the RPG"""
        embed = discord.Embed(color=0xba1c1c)
        embed.description = \
            "Welcome to the Infamous RPG where you can become the most powerful warrior there ever was. You can go on" \
            " quests to earn money and forge a weapon to finish those who challenge you."

        embed.add_field(
            name="Leveling/Acquiring Money",
            value=f"{ctx.prefix}quest \n"
                  f"{ctx.prefix}coinflip \n"
                  f"{ctx.prefix}duel \n"
                  f"{ctx.prefix}drink \n"
                  f"{ctx.prefix}blackjack \n"
                  f"{ctx.prefix}daily \n"
                  f"{ctx.prefix}sell")

        embed.add_field(
            name="Achieving/Modifying Items",
            value=f"{ctx.prefix}shop \n"
                  f"{ctx.prefix}buy \n"
                  f"{ctx.prefix}upgrade \n"
                  f"{ctx.prefix}merge \n"
                  f"{ctx.prefix}daily \n"
                  f"{ctx.prefix}rename")

        embed.add_field(
            name="Player Statistics",
            value=f"{ctx.prefix}profile \n"
                  f"{ctx.prefix}bal \n"
                  f"{ctx.prefix}top \n"
                  f"{ctx.prefix}inv \n"
                  f"{ctx.prefix}skills")

        embed.add_field(
            name="Administrator",
            value=f"{ctx.prefix}admin add-quest \n"
                  f"{ctx.prefix}admin add-item")

        embed.add_field(name="\u200b", value=f"**More info on each command can be found in {ctx.prefix}help Rpg**")

        embed.set_author(name="Instructions", icon_url=(await ctx.bot.application_info()).owner.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @registered()
    async def merge(self, ctx, item1: str, item2: str):
        """Merge items together.

        **Example:** *!merge 'Item One' 'Item Two'
        """

        i1 = await rpg.fetch_item(ctx, item1.title())
        i2 = await rpg.fetch_item(ctx, item2.title())
        if item1.title() == item2.title() or item2.title() == item1.title():
            return await ctx.send("You can't merge the same item together.")

        if i1 and i2:
            await ctx.send(f"Are you sure you want to merge **{i1[0]}** and **{i2[0]}** together? \n"
                           f"**Modified Statistics:** Price: {i1[2] + i2[2]}, Damage: {i1[3] + i2[3]}, Defense: "
                           f"{i1[4] + i2[4]}. `Yes` or `No`?")

            yon = await rpg.yon(ctx)
            if yon == "Yes":
                await ctx.send(f"**{rpg.merge(item1.title(), item2.title()).title()}** has been created!")
                await ctx.bot.db.execute("DELETE FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                         item1.title(), ctx.author.id)
                await ctx.bot.db.execute("DELETE FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                         item2.title(), ctx.author.id)
                await ctx.bot.db.execute("INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                                         rpg.merge(item1.title(), item2.title()).title(), i1[1], i1[2] + i2[2],
                                         i1[3] + i2[3], i1[4] + i2[4], i1[5], rpg.merge(i1[6], i2[6]).title(),
                                         ctx.author.id, 0
                                         )
                await rpg.remove_money(ctx, i1[2] + i2[2])
            else:
                return await ctx.send("I guess you don't want to merge your items.")
        else:
            return await ctx.send("You must not have one of the items, or you misspelled one of the names.")

    @commands.command()
    @registered()
    async def sell(self, ctx, *, item):
        """Sell your items for cash"""

        item_ = await rpg.fetch_item(ctx, item)
        if item_:
            await ctx.send(f"Are you sure you want to sell {item[0]}? \n"
                           f"`Yes` or `No`")

            yon = await rpg.yon(ctx)
            if yon == "Yes":
                await ctx.send(f"You have received **{item_[2]}$** for selling **{item_[0]}**")
                await rpg.add_money(ctx, item_[2])
                await ctx.bot.db.execute("DELETE FROM rpg_inventory WHERE name=$1 AND owner=$2",
                                         item_[0], ctx.author.id)
            else:
                return await ctx.send(f"I guess you don't want to sell {item.title()}")
        else:
            return await ctx.send("You don't have that item")

    @commands.command()
    @registered()
    async def rename(self, ctx, item: str, name: str):
        """Renames an item"""
        i = await rpg.fetch_item(ctx, item.title())
        if i:
            await ctx.send(f"Are you sure you want to rename **{item.title()}** to {name.title()}? It will cost"
                           f"**{i[2]}$** \n `Yes` or `No`")

            yon = await rpg.yon(ctx)
            if yon == "Yes":
                await ctx.send(f"Renamed {item.title()} to {name.title()}")
                await ctx.bot.db.execute("UPDATE rpg_inventory SET name=$1 WHERE name=$2 AND owner=$3", name.title(),
                                         item.title(), ctx.author.id)
                await rpg.remove_money(ctx, i[2])
            else:
                return await ctx.send(f"I guess you don't want to rename **{item.title()}**.")
        else:
            return await ctx.send(f"You don't have **{item.title()}**")

    @commands.command(name="class")
    @registered()
    async def _class(self, ctx, *, _class):
        await ctx.bot.db.execute("UPDATE rpg_profile SET class = $1 WHERE id=$2", _class.capitalize(), ctx.author.id)
        await ctx.send(f"Set class to **{_class.capitalize()}**")

    @commands.command()
    @registered()
    async def next(self, ctx, user: discord.Member=None):
        if not user:
            user = ctx.author

        u = await rpg.fetch_user(ctx, user=user.id)

        skills = await ctx.bot.db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)
        p = []
        for i in skills:
            p.append(f"**{i[1]}:** {i[2] * 50 - i[3]}xp to **Level {i[2] + 1}**")

        embed = discord.Embed(color=0xba1c1c)
        embed.set_author(name=f"{user.name}'s requirements to level up.", icon_url=user.avatar_url)
        embed.description = f"**{u[2] * 50 - u[3]}xp** to **Level {u[2] + 1}**"
        embed.add_field(name="Skills", value='\n'.join(p))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Rpg(bot))
