import discord
from PIL import ImageDraw


async def lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] > lvl_['lvl'] * 100:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET lvl = $1 WHERE id=$2",
            lvl_['lvl'] + 1, user
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


async def mastery_lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] > lvl_['lvl'] * 100:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET lvl = $1 WHERE id=$2",
            lvl_['lvl'] + 1, user
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


async def fetch_mastery(ctx, user=None):
    if not user:
        user = ctx.author.id

    p = await ctx.bot.db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1",
                                  user)

    return p


async def item_class(class_):
    if class_ == "knight":
        return "Sword"

    if class_ == "hunter":
        return "Bow"

    if class_ == "sorcerer":
        return "Staff"

    if class_ == "sentinel":
        return "Crossbow"


def drawtext(x, y, text, font, image):
    draw = ImageDraw.Draw(image)
    draw.text((x + 2, y), text, fill='black', font=font)
    draw.text((x - 2, y), text, fill='black', font=font)
    draw.text((x, y + 2), text, fill='black', font=font)
    draw.text((x, y - 2), text, fill='black', font=font)
    draw.text((x, y), text, fill='white', font=font)
    return draw


def item_embed(item, thumbnail):
    embed = discord.Embed(color=0xba1c1c)
    embed.set_author(name=f"{item[0]} | Price {item[2]}$")
    embed.description = item[7]
    embed.add_field(name="Performance Stats", value=f"**Damage:** {item[3]} \n"
                                                    f"**Defense:** {item[4]}")
    embed.add_field(name="Requirements", value=f"**Class:** {item[5]} \n"
                                               f"**Mastery Level:** {item[6]}", inline=True)
    embed.set_footer(text=f"Type: {item[1]}")
    embed.set_image(url=thumbnail)

    return embed


async def lb_embed(ctx, pfp):
    mast = await ctx.bot.db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1",
                                     pfp[0])
    embed = discord.Embed(color=0xba1c1c)
    member = ctx.guild.get_member(pfp[0])
    embed.set_author(name=member.name)
    embed.description = f"**Level:** {pfp[2]} \n" \
                        f"**Class:** {pfp[1]} \n" \
                        f"**Mastery Level:** {mast[1]}"

    embed.set_thumbnail(url=member.avatar_url)
    return embed


async def fetch_item(ctx, name, class_, user=None, inv=None):
    if not inv:
        inv = "rpg_inventory"

    if not user:
        user = ctx.author.id

    if inv == "rpg_shop":
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_shop WHERE name=$1 AND class=$2", name, class_)
    else:
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2", name, user)

    return item


async def remove_money(ctx, bal, user=None):
    if not user:
        user = ctx.author.id

    await ctx.bot.db.execute("UPDATE rpg_profile SET bal = bal - $1 WHERE id=$2",
                             bal, user)


async def purchase(ctx, item, money, class_, user=None):
    if not user:
        user = ctx.author.id

    i = await fetch_item(ctx, item, class_, user, 'rpg_shop')
    m = await fetch_mastery(ctx, user)
    if i[2] >= money and i[5] == class_ and i[6] == m[1]:
        await ctx.send(f"Do you really want to buy **{i[0]}** \n"
                       f"Price: {i[2]}$, Yes or No?")

        def check(m):
            return m.author == user and m.content in ["Yes", "No"]

        msg = await ctx.bot.wait_for('message', check=check)
        msg = msg.content

        if msg == "Yes":
            await ctx.send(f"{i[0]} has been added to your inventory.")

            await ctx.bot.db.execute(
                "INSERT INTO rpg_inventory VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                i[0], i[1],
                i[2], i[3],
                i[4], i[5],
                i[6], user,
                i[7])
        else:
            await ctx.send(f"Guess you don't want to spend **{i[2]}$**")
    else:
        return await ctx.send(f"Sorry you need {i[2] - money}$ more to purchase! "
                              f"Or.. You don't have the right class or mastery level")


def inventory_embed(ctx, info, thumbnail):
    embed = discord.Embed(color=0xba1c1c)
    embed.set_author(name=f"{ctx.bot.get_user(info[7]).name}'s inventory",
                     icon_url=ctx.bot.get_user(info[7]).avatar_url)
    embed.description = (f"**Name:** {info[0]} \n"
                         f"**Price:** {info[2]} \n"
                         f"**Damage:** {info[3]} \n"
                         f"**Defense:** {info[4]}")
    embed.set_image(url=thumbnail)
    return embed
