import discord


async def lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] >= lvl_['level'] * 50:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET level = $1 WHERE id=$2",
            lvl_['level'] + 1, user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET xp = 0 WHERE id=$1",
            user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
            mon, user
        )
    else:
        await ctx.send(msg2)


async def mastery_lvl(ctx, mon, skill, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_mastery WHERE id=$1 AND skill=$2", user, skill)

    if lvl_['xp'] >= lvl_['level'] * 50:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_mastery SET level = $1 WHERE id=$2 AND skill=$3",
            lvl_['level'] + 1, user, skill
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_mastery SET xp = 0 WHERE id=$1 AND skill=$2",
            user, skill
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
            mon, user
        )
    else:
        await ctx.send(msg2)


async def add_xp(ctx, xp, user=None):
    if not user:
        user = ctx.author.id

    await ctx.bot.db.execute(
        "UPDATE rpg_profile SET xp = xp + $1 WHERE id = $2",
        xp, user
    )


async def add_mastery_xp(ctx, xp, user=None):
    if not user:
        user = ctx.author.id

    await ctx.bot.db.execute(
        "UPDATE rpg_mastery SET xp = xp + $1 WHERE id = $2",
        xp, user
    )


async def add_money(ctx, mon, user=None):
    if not user:
        user = ctx.author

    await ctx.bot.db.execute(
        "UPDATE rpg_profile SET bal = bal + $1 WHERE id = $2",
        mon, user.id
    )


async def fetch_user(ctx, user=None):
    if not user:
        user = ctx.author.id

    p = await ctx.bot.db.fetchrow("SELECT * FROM rpg_profile WHERE id=$1",
                                  user)
    return p


async def fetch_mastery(ctx, skill, user=None):
    if not user:
        user = ctx.author.id

    p = await ctx.bot.db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1 AND skill=$2",
                                  user, skill)

    return p


def item_embed(item, thumbnail):
    embed = discord.Embed(color=0xba1c1c)
    embed.set_author(name=f"{item[0]} | Price {item[2]}$")
    embed.description = item[6]
    embed.add_field(name="Performance Stats", value=f"**Damage:** {item[3]} \n"
                                                    f"**Defense:** {item[4]}")
    embed.add_field(name="Requirements", value=f"**Required Skill:** {item[5]} Level {item[7]}", inline=True)
    embed.set_footer(text=f"Type: {item[1]}")
    embed.set_image(url=thumbnail)

    return embed


async def lb_embed(ctx, pfp):
    embed = discord.Embed(color=0xba1c1c)
    member = ctx.bot.get_user(pfp[0])
    embed.set_author(name=member.name)
    embed.description = f"**Level:** {pfp[2]} \n" \
                        f"**Class:** {pfp[1]} \n" \
                        f"**Main Skill:** {pfp[5]}"
    duels = await ctx.bot.db.fetchrow("SELECT * FROM rpg_duels WHERE id=$1", member.id)
    if duels:
        embed.add_field(name="Fighting Statistics", value=f"**Wins:** {duels[1]} \n"
                                                          f"**Losses:** {duels[2]}", inline=True)
    else:
        embed.add_field(name="Fighting Statistics", value="User has not participated in duels")
    embed.set_image(url=member.avatar_url_as(format='png', size=1024))
    return embed


async def fetch_item(ctx, name, user=None, inv=None):
    if not inv:
        inv = "rpg_inventory"

    if not user:
        user = ctx.author.id

    if inv == "rpg_shop":
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_shop WHERE name=$1", name)
    else:
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2", name, user)

    return item


async def remove_money(ctx, bal, user=None):
    if not user:
        user = ctx.author.id

    await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                             bal, user)


def inventory_embed(ctx, info, thumbnail):
    embed = discord.Embed(color=0xba1c1c)
    embed.set_author(name=f"{ctx.bot.get_user(info[7]).name}'s inventory",
                     icon_url=ctx.bot.get_user(info[7]).avatar_url)
    embed.description = (f"**Name:** {info[0]} \n"
                         f"**Price:** {info[2]} \n"
                         f"**Damage:** {info[3]} \n"
                         f"**Defense:** {info[4]} \n"
                         f"**Skill:** {info[5]}")
    embed.set_image(url=thumbnail)
    return embed


async def fetch_skills(ctx, user=None):
    if not user:
        user = ctx.author

    skills = await ctx.bot.db.fetch("SELECT * FROM rpg_mastery WHERE id=$1", user.id)

    p = []
    for i in skills:
        p.append(i[1])

    return p


# Courtesy of MIkusaba
def merge(s1, s2):
    return s1[:len(s1) // 2] + s2[len(s2) // 2:]
