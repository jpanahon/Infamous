import asyncio
import random
import discord

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


async def level2(ctx, mon, xp, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        lvl_ = await db.fetchrow("SELECT * FROM profiles WHERE id=$1", user.id)

    lvl_ = {"xp": lvl_[2] + xp, "lvl": lvl_[1]}

    if lvl_["xp"] >= (lvl_["lvl"] * 2000) * 3:
        await ctx.send(f"Congratulations {user.mention} you have leveled up to Level {lvl_['lvl'] + 1} "
                       f"after executing `{ctx.prefix}{ctx.command.name}`")

        async with ctx.db.acquire() as db:
            await db.execute("UPDATE profiles SET level = level + 1, bal = bal + $1, xp = xp + $2 WHERE id=$3",
                             mon, xp, user.id)
    else:
        await ctx.send(f"{user.mention} You have {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}xp left to the next level "
                       f"after executing `{ctx.prefix}{ctx.command.name}`")

        async with ctx.db.acquire() as db:
            await db.execute("UPDATE profiles SET bal = bal + $1, xp = xp + $2 WHERE id=$3",
                             mon, xp, user.id)


async def fetch_user2(ctx, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        info = await db.fetchrow("SELECT * FROM profiles WHERE id=$1", user.id)
    return info


async def fetch_abilities(ctx, user=None):
    if not user:
        user = ctx.author
    p = []

    async with ctx.db.acquire() as db:
        abilities = await db.fetch("SELECT * FROM abilities WHERE id=$1", user.id)

    for i in abilities:
        p.append(i[1])
    return p


def ability_embed(ctx, dict_, ability, current, max_):
    embed = discord.Embed(color=embed_color)
    embed.set_author(name=f"{ability} | ${dict_[ability][0]}")
    embed.description = dict_[ability][2]
    embed.add_field(name="Stats", value=f"**Damage:** {dict_[ability][3]} \n"
                                        f"**Durability:** {dict_[ability][4]}")
    embed.set_image(url=dict_[ability][1])
    embed.set_footer(text=f'Page {current} of {max_} | Use "{ctx.prefix}acquire <ability>" to get this ability')
    return embed


async def ability_level(ctx, xp, dmg, dur, ability, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        lvl_ = await db.fetchrow("SELECT * FROM abilities WHERE id=$1 AND ability=$2", user.id, ability)

    lvl_ = {"lvl": lvl_[2], "xp": lvl_[3] + xp}

    if lvl_["xp"] >= lvl_["lvl"] * 1000:
        await ctx.send(f"Congratulations {user.mention} you have leveled up {ability} to Level {lvl_['lvl'] + 1} "
                       f"after executing `{ctx.prefix}{ctx.command.name}`")

        async with ctx.db.acquire() as db:
            await db.execute(
                "UPDATE abilities SET level = level + 1, damage=damage + $1, "
                "durability=durability + $2, xp = xp + $3 WHERE id=$4 AND ability=$5",
                dmg, dur, xp, user.id, ability)
    else:
        await ctx.send(
            f"{user.mention} You have {lvl_['lvl'] * 2000 - lvl_['xp']}xp left to upgrade your "
            f"{ability} to the next level after executing `{ctx.prefix}{ctx.command.name}`")

        async with ctx.db.acquire() as db:
            await db.execute("UPDATE abilities SET damage=damage + $1, "
                             "durability=durability + $2, xp = xp + $3 WHERE id=$4 AND ability=$5",
                             dmg, dur, xp, user.id, ability)


async def guild_level(ctx, xp, user=None):
    if not user:
        user = ctx.author

    async with ctx.db.acquire() as db:
        lvl_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", user.id)
        lvl_ = await db.fetchrow("SELECT * FROM guilds WHERE guild=$1", lvl_)

    if not lvl_:
        return await ctx.send("You currently aren't apart of a guild; therefore there are no guild rewards.")
    else:
        lvl_ = {"xp": lvl_[3] + xp, "lvl": lvl_[2], "name": lvl_[0]}

    if lvl_["xp"] >= (lvl_["lvl"] * 2000) * 3:
        await ctx.send(f"{lvl_['name']} has leveled up to Level {lvl_['lvl'] + 1}.")

        async with ctx.db.acquire() as db:
            await db.execute("UPDATE guilds SET level = level + 1, xp = xp + $1 WHERE guild=$2",
                             xp, lvl_['name'])
    else:
        await ctx.send(f"**{lvl_['name']}** needs {(lvl_['lvl'] * 2000) * 3 - lvl_['xp']}xp left to the next level.")

        async with ctx.db.acquire() as db:
            await db.execute("UPDATE guilds SET xp = xp + $1 WHERE guild=$2",
                             xp, lvl_['name'])


class MatchEnd(Exception):
    pass


async def reward(ctx, enemy, health):
    if type(enemy) == discord.Member:
        if health <= 0:
            xp = random.randint(250, 500)
            mon = random.randint(250, 500)
            await ctx.send(f"{enemy.mention} wins! They earn {xp}xp and ${mon}")
            await level2(ctx, mon, xp, user=enemy)
            await guild_level(ctx, xp, user=enemy)
            raise MatchEnd  
        
    if health <= 0:
        await ctx.send(f"**{enemy}** wins!")
        raise MatchEnd
        
        
async def turn(ctx, skill1, skill2, health, health2, enemy, user=None):
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
        if msg_ == skill1[1]:
            dmg = random.randint(10, skill1[4] / 2)
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
                    await reward(ctx, enemy, health)
                    
            if health2 <= 0:
                xp = random.randint(250, 500)
                mon = random.randint(250, 500)
                await ctx.send(f"{user.mention} wins! They earn {xp}xp and ${mon}")
                await level2(ctx, mon, xp)
                await guild_level(ctx, xp)
                raise MatchEnd
        else:
            dmg = random.randint(10, skill2[4] / 2)
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
                    await reward(ctx, enemy, health)
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
                    await reward(ctx, enemy, health)
                    
            if health2 <= 0:
                xp = random.randint(250, 500)
                mon = random.randint(250, 500)
                await ctx.send(f"{user.mention} wins! They earn {xp}xp and ${mon}")
                await level2(ctx, mon, xp)
                await guild_level(ctx, xp)
                raise MatchEnd
