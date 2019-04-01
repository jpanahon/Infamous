import asyncio
import random
import discord
from .functions import Paginator

embed_color = 0x740f10


async def lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        lvl_ = await db.fetchrow(
            "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] >= lvl_['level'] * 50:
        await ctx.send(
            msg1
        )
        async with ctx.db.acquire() as db:
            await db.execute(
                "UPDATE rpg_profile SET level = $1 WHERE id=$2",
                lvl_['level'] + 1, user
            )

            await db.execute(
                "UPDATE rpg_profile SET xp = 0 WHERE id=$1",
                user
            )

            await db.execute(
                "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
                mon, user
            )
    else:
        await ctx.send(msg2)


async def mastery_lvl(ctx, mon, skill, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        lvl_ = await db.fetchrow(
            "SELECT * FROM rpg_mastery WHERE id=$1 AND skill=$2", user, skill)

    if lvl_['xp'] >= lvl_['level'] * 50:
        await ctx.send(
            msg1
        )
        async with ctx.db.acquire() as db:
            await db.execute(
                "UPDATE rpg_mastery SET level = $1 WHERE id=$2 AND skill=$3",
                lvl_['level'] + 1, user, skill
            )

            await db.execute(
                "UPDATE rpg_mastery SET xp = 0 WHERE id=$1 AND skill=$2",
                user, skill
            )

            await db.execute(
                "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
                mon, user
            )
    else:
        await ctx.send(msg2)


async def add_xp(ctx, xp, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        await db.execute(
            "UPDATE rpg_profile SET xp = xp + $1 WHERE id = $2",
            xp, user
        )


async def add_mastery_xp(ctx, xp, skill, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        await db.execute(
            "UPDATE rpg_mastery SET xp = xp + $1 WHERE skill = $2 AND id = $3",
            xp, skill, user
        )


async def add_money(ctx, mon, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        await db.execute(
            "UPDATE rpg_profile SET bal = bal + $1 WHERE id = $2",
            mon, user.id
        )


async def fetch_user(ctx, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        p = await db.fetchrow("SELECT * FROM rpg_profile WHERE id=$1",
                              user)
    return p


async def fetch_mastery(ctx, skill, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        p = await db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1 AND skill=$2",
                              user, skill)

    return p


def item_embed(item, thumbnail, current, max_):
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=f"{item[0]} | Price {item[2]}$ | Page {current} of {max_}")
    embed.description = item[6]
    embed.add_field(name="Performance Stats", value=f"**Damage:** {item[3]} \n"
                                                    f"**Defense:** {item[4]}")
    embed.add_field(name="Requirements", value=f"**Required Skill:** {item[5]} Level {item[7]}", inline=True)
    embed.set_image(url=thumbnail)
    embed.set_footer(text=f"Type: {item[1]}")

    return embed


async def lb_embed(ctx, pfp, current, max_):
    embed = discord.Embed(color=embed_color)
    member = ctx.bot.get_user(pfp[0])
    embed.set_author(name=member.name)
    embed.description = f"**Level:** {pfp[2]} \n" \
        f"**Class:** {pfp[1]} \n" \
        f"**Main Skill:** {pfp[5]}"
    duels = await ctx.db.fetchrow("SELECT * FROM rpg_duels WHERE id=$1", member.id)
    if duels:
        embed.add_field(name="Fighting Statistics", value=f"**Wins:** {duels[1]} \n"
                                                          f"**Losses:** {duels[2]}", inline=True)
    else:
        embed.add_field(name="Fighting Statistics", value="User has not participated in duels")
    embed.set_image(url=member.avatar_url_as(format='png', size=1024))
    shared = sum(1 for m in ctx.bot.get_all_members() if m.id == member.id)
    embed.set_footer(text=f"Page {current} of {max_} | Related Servers: {shared}")
    return embed


async def fetch_item(ctx, name, user=None, inv=None):
    if not inv:
        inv = "rpg_inventory"

    if not user:
        user = ctx.author.id

    if inv == "rpg_shop":
        async with ctx.db.acquire() as db:
            item = await db.fetchrow("SELECT * FROM rpg_shop WHERE name=$1", name)
    else:
        async with ctx.db.acquire() as db:
            item = await db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2", name, user)

    return item


async def remove_money(ctx, bal, user=None):
    if not user:
        user = ctx.author.id

    async with ctx.db.acquire() as db:
        await db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                         bal, user)


def inventory_embed(ctx, info, thumbnail, current, max_):
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=f"{ctx.bot.get_user(info[7]).name}'s inventory | Page {current} of {max_}",
                     icon_url=ctx.bot.get_user(info[7]).avatar_url)
    embed.description = (f"**Name:** {info[0]} \n"
                         f"**Price:** {info[2]} \n"
                         f"**Damage:** {info[3]} \n"
                         f"**Defense:** {info[4]} \n"
                         f"**Skill:** {info[5]}")
    embed.set_image(url=thumbnail)
    embed.set_footer(text=f"Type: {info[1]}")
    return embed


async def fetch_skills(ctx, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        skills = await db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)

    p = []
    for i in skills:
        p.append(i[1])

    return p


# Courtesy of MIkusaba
def merge(s1, s2):
    return s1[:len(s1) // 2] + s2[len(s2) // 2:]


async def yon(ctx, user=None):
    if not user:
        user = ctx.author

    def check(m):
        if m.author == user:
            return True
        if any(word in m.content.lower() for word in ["yes", "y", "n", "no"]):
            return True
        return False

    try:
        check_ = (await ctx.input('message', check=check, timeout=30)).content.lower()
        return check_
    except asyncio.TimeoutError:
        pass


async def choose(ctx, choice: list, user=None):
    if not user:
        user = ctx.author

    def check(m):
        return m.author == user and m.content.capitalize() in choice

    try:
        check_ = (await ctx.input('message', check=check, timeout=30)).content.capitalize()
        return check_
    except asyncio.TimeoutError:
        pass


async def lb(ctx, win, loss, user=None):
    if not user:
        user = ctx.author

    data = await ctx.db.fetch("SELECT * FROM rpg_duels WHERE id=$1", user.id)
    if data:
        async with ctx.db.acquire() as db:
            await db.execute("""UPDATE rpg_duels 
                                        SET wins = wins + $1, losses = losses + $2 
                                        WHERE id=$3
                                    """, win, loss, user.id)
    else:
        async with ctx.db.acquire() as db:
            await db.execute("INSERT INTO rpg_duels VALUES($1, $2, $3)", user.id, win, loss)


class MatchEnd(Exception):
    pass


class RpgMethods:
    def __init__(self, cache):
        self.cache = cache

    async def yon(self, ctx, user=None):
        if not user:
            user = ctx.author

        def check(m):
            if m.author == user:
                return True
            if any(word in m.content.lower() for word in ["yes", "y", "n", "no"]):
                return True
            return False

        try:
            check_ = (await ctx.input('message', check=check, timeout=30)).content.lower()
            return check_
        except asyncio.TimeoutError:
            pass

    async def level2(self, ctx, mon, xp, user=None):
        if not user:
            user = ctx.author

        lvl_ = [self.cache[user.id]["Information"]["LVL"], self.cache[user.id]["Information"]["XP"]]
        lvl_ = {"xp": lvl_[1] + xp, "lvl": lvl_[0]}

        if lvl_["xp"] >= (lvl_["lvl"] * 2000) * 3:
            try:
                await user.send(f"Congratulations {user.mention} you have leveled up to Level {lvl_['lvl'] + 1} "
                                f"after executing `{ctx.prefix}{ctx.command.name}`")
            except discord.Forbidden:
                await ctx.send(f"Congratulations {user.mention} you have leveled up to Level {lvl_['lvl'] + 1} "
                               f"after executing `{ctx.prefix}{ctx.command.name}`")

            async with ctx.db.acquire() as db:
                await db.execute("UPDATE profiles SET level = level + 1, bal = bal + $1, xp = xp + $2 WHERE id=$3",
                                 mon, xp, user.id)
                self.cache[user.id]["Information"]["LVL"] += 1
                self.cache[user.id]["Information"]["XP"] += xp
                self.cache[user.id]["Information"]["BAL"] += mon
        else:
            try:
                await user.send(f"{user.mention} You have {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}"
                                f"xp left to the next level after executing `{ctx.prefix}{ctx.command.name}`")
            except discord.Forbidden:
                await ctx.send(f"{user.mention} You have {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}"
                               f"xp left to the next level after executing `{ctx.prefix}{ctx.command.name}`")

            async with ctx.db.acquire() as db:
                await db.execute("UPDATE profiles SET bal = bal + $1, xp = xp + $2 WHERE id=$3",
                                 mon, xp, user.id)
                self.cache[user.id]["Information"]["BAL"] += mon
                self.cache[user.id]["Information"]["XP"] += xp

    async def fetch_user2(self, ctx, user=None):
        if not user:
            user = ctx.author

        return self.cache[user.id]

    async def fetch_abilities(self, ctx, user=None):
        if not user:
            user = ctx.author

        return self.cache[user.id]["Abilities"]

    def ability_embed(self, dict_, ability, current, max_):
        embed = discord.Embed(color=embed_color)
        embed.set_author(name=f"{ability} | ${dict_[ability][0]}")
        embed.description = dict_[ability][2]
        embed.add_field(name="Stats", value=f"**Damage:** {dict_[ability][3]} \n"
                                            f"**Durability:** {dict_[ability][4]}")
        embed.set_image(url=dict_[ability][1])
        embed.set_footer(text=f'Page {current} of {max_} | React 🛒 to get this ability')
        return embed

    async def upgrade_ability(self, ctx, dmg, dur, ability, user=None):
        if not user:
            user = ctx.author

        _ability = self.cache[user.id]["Abilities"][ability]
        _ability["DMG"] += dmg
        _ability["DUR"] += dur
        async with ctx.db.acquire() as db:
            await db.execute("UPDATE abilities SET damage + $1, durability + $2 WHERE ability=$3 AND id=$4", dmg,
                             dur, ability, user.id)

    async def guild_level(self, ctx, xp, user=None):
        if not user:
            user = ctx.author

        lvl_ = self.cache[user.id]["Guild"]
        if not lvl_:
            return await ctx.send("You currently aren't apart of a guild; therefore there are no guild rewards.")
        else:
            lvl_ = {"xp": lvl_["XP"] + xp, "lvl": lvl_["LVL"], "name": lvl_["NAME"]}

        if lvl_["xp"] >= (lvl_["lvl"] * 2000) * 3:
            try:
                await user.send(f"{lvl_['name']} has leveled up to Level {lvl_['lvl'] + 1}.")
            except discord.Forbidden:
                await ctx.send(f"{lvl_['name']} has leveled up to Level {lvl_['lvl'] + 1}.")

            async with ctx.db.acquire() as db:
                await db.execute("UPDATE guilds SET level = level + 1, xp = xp + $1 WHERE guild=$2",
                                 xp, lvl_['name'])

            for i in self.cache:
                if self.cache[i]['Guild']:
                    if self.cache[i]['Guild']['NAME'] == self.cache[ctx.author.id]['Guild']['NAME']:
                        self.cache[i]['Guild']['LVL'] += 1
                        self.cache[i]['Guild']['LVL'] += xp
        else:
            try:
                await user.send(
                    f"**{lvl_['name']}** needs {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}xp left to the next level.")
            except discord.Forbidden:
                await ctx.send(
                    f"**{lvl_['name']}** needs {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}xp left to the next level.")

            async with ctx.db.acquire() as db:
                await db.execute("UPDATE guilds SET xp = xp + $1 WHERE guild=$2",
                                 xp, lvl_['name'])

            for i in self.cache:
                if self.cache[i]['Guild']:
                    if self.cache[i]['Guild']['NAME'] == self.cache[ctx.author.id]['Guild']['NAME']:
                        self.cache[i]['Guild']['LVL'] += xp

    async def reward(self, ctx, enemy, health):
        if type(enemy) == discord.Member:
            if health <= 0:
                xp = random.randint(250, 500)
                mon = random.randint(250, 500)
                await ctx.send(f"{enemy.mention} wins! They earn {xp}xp and ${mon}")
                await self.level2(ctx, mon, xp, user=enemy)
                await self.guild_level(ctx, xp, user=enemy)
                raise MatchEnd

        if health <= 0:
            await ctx.send(f"**{enemy}** wins!")
            raise MatchEnd

    async def turn(self, ctx, skill1, skill2, health, health2, enemy, user=None):
        if not user:
            user = ctx.author

        if type(enemy) == discord.Member:
            enemy = enemy.mention

        def player1(m):
            return m.author == user and m.content.title() in [skill1[1], skill2[1]]

        try:
            msg_ = (await ctx.input('message', check=player1, timeout=30)).content.title()
        except asyncio.TimeoutError:
            await ctx.send(f"{user.mention} has been disqualified. Duel is over!")
            raise MatchEnd
        else:
            if msg_ == skill1:
                dmg = random.randint(10, skill1["DMG"] / 2)
                if dmg > round(health2 / 2):
                    chance = random.choice(["Hit", "Miss"])
                    if chance == "Hit":
                        health2 -= dmg
                        await ctx.send(
                            f"{user.mention} Your attack using your {skill1[1]} has dealt {dmg}dmg \n"
                            f"**{enemy}** has `{health2} health.")
                    else:
                        health -= dmg
                        await ctx.send(
                            f"{user.mention} missed! Causing **{enemy}** to deal {dmg}dmg \n"
                            f"They now have `{health}` health.")
                else:
                    chance = random.choice(["Hit", "Miss"])
                    if chance == "Hit":
                        health2 -= dmg
                        await ctx.send(
                            f"{user.mention} Your attack using your {skill1[1]} has dealt {dmg}dmg \n"
                            f"**{enemy}** has `{health2}` health.")
                    else:
                        health -= dmg
                        await ctx.send(
                            f"{user.mention} missed! Causing **{enemy}** to deal {dmg}dmg \n"
                            f"They now have `{health}` health.")
                        await self.reward(ctx, enemy, health)

                if health2 <= 0:
                    xp = random.randint(250, 500)
                    mon = random.randint(250, 500)
                    await ctx.send(f"{user.mention} wins! They earn {xp}xp and ${mon}")
                    await self.level2(ctx, mon, xp)
                    await self.guild_level(ctx, xp)
                    raise MatchEnd
            else:
                dmg = random.randint(10, skill2["DMG"] / 2)
                if dmg > round(health2 / 2):
                    chance = random.choice(["Hit", "Miss"])
                    if chance == "Hit":
                        health2 -= dmg
                        await ctx.send(
                            f"{user.mention} Your attack using your {skill2[1]} has dealt {dmg}dmg \n"
                            f"**{enemy}** has `{health2}` health.")
                    else:
                        health -= dmg
                        await ctx.send(
                            f"{user.mention} missed! Causing **{enemy}** to deal {dmg}dmg \n"
                            f"They now have `{health}` health.")
                        await self.reward(ctx, enemy, health)
                else:
                    chance = random.choice(["Hit", "Miss"])
                    if chance == "Hit":
                        health2 -= dmg
                        await ctx.send(
                            f"{user.mention} Your attack using your {skill2[1]} has dealt {dmg}dmg \n"
                            f"**{enemy}** has `{health2}` health.")
                    else:
                        health -= dmg
                        await ctx.send(
                            f"{user.mention} missed! Causing **{enemy}** to deal {dmg}dmg \n"
                            f"They now have `{health}` health.")
                        await self.reward(ctx, enemy, health)

                if health2 <= 0:
                    xp = random.randint(250, 500)
                    mon = random.randint(250, 500)
                    await ctx.send(f"{user.mention} wins! They earn {xp}xp and ${mon}")
                    await self.level2(ctx, mon, xp)
                    await self.guild_level(ctx, xp)
                    raise MatchEnd


class ShopPaginator(Paginator):
    def __init__(self, ctx, entries: list, shop_items: dict, cache: dict, embed=True, timeout=120):
        super().__init__(ctx, entries=entries, embed=embed, timeout=timeout)
        self.reactions.append(('<:buy:559703253940568085>', self.buy_item))
        self.shop_items = shop_items
        self.cache = cache

    def find_item(self):
        embed = self.entries[self.current].to_dict()
        name = (embed['author']['name'].split(' | $'))[0]
        item = self.shop_items[name]
        return item, name

    async def info(self):
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name='Instructions')
        embed.description = "This is a reaction paginator; when you react to one of the buttons below " \
                            "the message gets edited. Below you will find what the reactions do."

        embed.add_field(name="First Page <:first_page:556312967797407754>",
                        value="This reaction takes you to the first page.", inline=False)

        embed.add_field(name="Previous Page <:previous_page:556312942966997033>",
                        value="This reaction takes you to the previous page. "
                              "If you use this reaction while in the first page it will take "
                              "you to the last page.", inline=False)

        embed.add_field(name="Next Page <:next_page:556313016832884736>",
                        value="This reaction takes you to the next page. "
                              "If you use this reaction while in the last page it will to take "
                              "you to the first page.", inline=False)

        embed.add_field(name="Last Page <:last_page:556312980665663504>",
                        value="This reaction takes you to the last page.", inline=False)

        embed.add_field(name="Selector <:select:556320090862387211>",
                        value="This reaction allows you to choose what page to go to", inline=False)

        embed.add_field(name="Information <:info:556320125599350808>",
                        value="This reaction takes you to this page.")

        embed.add_field(name="Buy <:buy:559703253940568085>",
                        value="This reaction allows you to buy the ability displayed.")
        await self.msg.edit(embed=embed)

    async def buy_item(self):
        item, name = self.find_item()
        if self.cache[self.user_.id]["Information"]["BAL"] >= item[0]:
            to_delete = await self.channel.send(f"Are you sure you want to buy {name}?")
            _yon = await yon(self.ctx)
            if any(word in _yon for word in ['y', 'yes']):
                async with self.bot.db.acquire() as db:
                    await db.execute("INSERT INTO abilities VALUES($1, $2, $3, $4, $5)", self.user_.id,
                                     name, item[3], item[4], None)
                    await db.execute("UPDATE profiles SET bal = bal - $1 WHERE id=$2", item[0], self.user_.id)

                    self.cache[self.user_.id]["Abilities"][name] = {"DMG": item[2], "DUR": item[3],
                                                                    "ICON": None}
                    self.cache[self.user_.id]['Information']['BAL'] -= item[0]
                await self.channel.send(f"You have acquired {name}!", delete_after=15)
                await to_delete.delete()
            else:
                await self.channel.send("I guess you don't want to buy it.")

        else:
            await self.channel.send(f"You need ${item[0] - self.cache[self.user_.id]['Information']['BAL']} more.",
                                    delete_after=10)
