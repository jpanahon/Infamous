import discord
import asyncio
import random
from discord.ext import commands
from .utils import rpg_tools as rpg
from .utils import checks

monologue = """
The year is 2033; technology has become advanced, what was once science fiction
has become a reality. Years of research and experimentation have created superhumans.

In 2029 a rogue scientist by name of Angus Kleric had developed a software that created 
pills to genetically enhance a human; many people have taken the pills and gave themselves 
superpowers, however it caused them to become insane and use their abilities for
committing crime. 

The drug had been discontinued, but new illegal versions of it were made. 
This opted the U.S Government to make their own superhumans; superheroes to combat evil supervillians; 
the term used for the ones who took the Kleric drug.

You can be a superhero or supervillian and interact in the city of Sterben 
where you can take on other superheroes or supervillians.
            """


class Rpg2(commands.Cog, name="Infamous RPG"):
    def __init__(self, bot):
        self.bot = bot
        self.__doc__ = monologue
        self.hp = {"p1": 0, "p2": 0}
        self.user_cache = {}
        self.bot.loop.create_task(self.reset_cache())
        self.method = rpg.RpgMethods(self.user_cache)
        self.abilities = ["Super Strength", "Flight", "Telekinesis",
                          "Super Speed", "Heat Vision", "Freeze Breath",
                          "Sonic Scream", "Electrokinesis"]

        self.shop_items = {"Super Strength": [12000, 'https://imgur.com/vbtnxdi.png',
                                              "Allows you to lift 10x your weight.", 250, 300],

                           "Flight": [15000, 'https://imgur.com/jr8CyIk.png',
                                      "Allows you to fly without an aircraft.", 200, 250],

                           "Telekinesis": [18000, 'https://imgur.com/2UWGYBq.png',
                                           "Control objects with your mind.", 300, 350],

                           "Super Speed": [21000, 'https://imgur.com/bBJujmH.png',
                                           "Run faster than a speeding bullet.", 280, 330],

                           "Heat Vision": [30000, 'https://imgur.com/fV8pIJo.png',
                                           "Destroy things with your vision.", 320, 370],

                           "Freeze Breath": [39000, 'https://imgur.com/ot2zakO.gif',
                                             "Freeze things with your breath.", 350, 400],

                           "Sonic Scream": [41000, 'https://imgur.com/El8Xh9Y.gif',
                                            "Break glass with just your voice.", 400, 450],

                           "Electrokinesis": [44000, 'https://imgur.com/Y8eBb18.png',
                                              "Harness the power of electricity.", 420, 470]}

    async def reset_cache(self):
        try:
            while not self.bot.is_closed():
                await asyncio.sleep(3600)
                self.user_cache.clear()
        except asyncio.CancelledError:
            pass

    async def insert_into_cache(self, ctx):
        async with ctx.db.acquire() as db:
            _info = await db.fetchrow("SELECT * FROM profiles WHERE id=$1", ctx.author.id)
            _abilities = await db.fetch("SELECT * FROM abilities WHERE id=$1", ctx.author.id)
            _guild = await db.fetchrow("SELECT * FROM guilds WHERE guild=$1", _info[5])

        abilities_dict = {}
        for i in _abilities:
            abilities_dict[i[1]] = {"DMG": i[2], "DUR": i[3], "ICON": i[4] or self.shop_items[i[1]][1]}

        self.user_cache[ctx.author.id] = {"Information": {"LVL": _info[1], "XP": _info[2], "BAL": _info[3],
                                                          "MAIN": _info[4]}, "Abilities": abilities_dict}
        if _guild:
            self.user_cache[ctx.author.id]["Guild"] = {"NAME": _guild[0], "LEADER": _guild[1], "LVL": _guild[2],
                                                       "XP": _guild[3], "ICON": _guild[4]}

    async def cog_before_invoke(self, ctx):
        if self.bot.alerts[ctx.guild.id] is True:
            await ctx.send(
                f"This RPG is being actively developed, which means there could be some errors that "
                f"haven't been discovered or I haven't noticed in the code. Please report it via "
                f"`{ctx.prefix}suggest`, you can also join <https://discord.gg/JyJTh4H> to beta test new "
                f"features that are going to be implemented. You can disable these notifications via "
                f"`{ctx.prefix}alerts disable`")

        if ctx.command.qualified_name != 'register':
            if ctx.author.id not in self.user_cache:
                await self.insert_into_cache(ctx)

    @commands.command()
    @checks.unregistered2()
    async def register(self, ctx):
        """Become apart of a world filled with superhumans"""

        await ctx.send(monologue)
        await ctx.send(f"Choose an ability (You will be able to gain more abilities as you acquire more money). \n"
                       f"```prolog\n{', '.join(self.abilities)}.```")

        def check(m):
            if not m.author or m.author.id != ctx.author.id:
                return False

            if m.channel.id != ctx.channel.id:
                return False

            if m.content.title() in self.abilities:
                return True
            return False

        active = True
        while active:
            try:
                msg = (await ctx.input('message', check=check, timeout=60)).content.title()
            except asyncio.TimeoutError:
                return await ctx.send("Registration cancelled.")

            if msg:
                if msg not in self.abilities:
                    await ctx.send(f"{ctx.author.mention} Pick a ability from the list!")
                else:
                    await ctx.send(f"Your main ability is: **{msg}** \n"
                                   f"You can acquire more abilities in the shop and you can master your abilities")

                    async with ctx.db.acquire() as db:
                        await db.execute("INSERT INTO profiles VALUES($1, $2, $3, $4, $5)",
                                         ctx.author.id, 1, 0, 0, msg)
                        await db.execute("INSERT INTO abilities VALUES($1, $2, $3, $4, $5, $6)",
                                         ctx.author.id, msg, 1, 0, self.shop_items[msg][3], self.shop_items[msg][4])

                    await self.insert_into_cache(ctx)
                await ctx.send("You have successfully been registered.")
                active = False

    @commands.command(aliases=['quest', 'adv'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    @checks.registered2()
    async def adventure(self, ctx):
        """Patrol the streets to get rewards."""

        mission_ = ['mission', 'odyssey']
        for i in mission_:
            cmd = self.bot.get_command(i)
            if cmd.is_on_cooldown(ctx):
                await ctx.send(f"You can't use `{ctx.prefix}mission` and `{ctx.prefix}adventure` at the same time.")
                ctx.command.reset_cooldown(ctx)
                return

        await ctx.send("You went on a adventure; you will return in 30 minutes.")
        await asyncio.sleep(1800)
        money = random.randint(20, 100)
        xp = random.randint(20, 100)
        await ctx.send(random.choice([
            f'You stopped a robbery and apprehended a supervillian; you were rewarded with ${money} and {xp}xp.',
            f'You defeated a supervillian and stole their ${money} and {xp}xp.',
            f'You defeated a superhero and stole their ${money} and {xp}xp.',
            f'You saved many civilians from an attack from a supervillian; you earned ${money} and {xp}xp.',
            f'You lured a superhero to your trap and killed them; you earned ${money} and {xp}xp.',
            f'You foiled a supervillian\'s plan to destroy the world; you earned ${money} and {xp}xp.']))

        await self.method.level2(ctx, money, xp)
        await self.method.guild_level(ctx, xp)

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 5400, commands.BucketType.user)
    async def odyssey(self, ctx):
        """Go on a long journey."""

        mission_ = ['mission', 'adventure']
        for i in mission_:
            cmd = self.bot.get_command(i)
            if cmd.is_on_cooldown(ctx):
                await ctx.send(f"You can't use `{ctx.prefix}mission` and `{ctx.prefix}adventure` at the same time.")
                ctx.command.reset_cooldown(ctx)
                return

        responses = ["You have to find the oldest and purebred superhuman in existence who was said to have had "
                     "the gift of immortality; making her ageless. She also possesses the power of super speed and "
                     "is one of the fastest speedsters.",

                     "You went to search for the reincarnation flower which can be used to suppress/remove powers "
                     "that were given by the Kleric drug."
                     ]
        choice = random.choice(responses)
        await ctx.send(choice)
        await asyncio.sleep(5400)
        xp = random.randint(250, 750)
        mon = random.randint(250, 750)
        if choice == responses[0]:
            await ctx.send(f"You found the immortal and she gave you insight about your powers; she gave you "
                           f"{xp}xp and ${mon}")
        else:
            await ctx.send(f"You found the reincarnation flower suppressed the power of Solaris; you were given "
                           f"{xp}xp and ${mon}")

        await self.method.level2(ctx, mon, xp)
        await self.method.guild_level(ctx, xp)

    @commands.command(aliases=['p'])
    @checks.registered2()
    async def profile(self, ctx, user: checks.SuperhumanFinder = None):
        """View the stats of fellow superhumans."""
        if not user:
            user = ctx.author
        else:
            user = await ctx.guild.get_member_named(str(user))

        stats = (await self.method.fetch_user2(ctx, user))['Information']
        abilities = await self.method.fetch_abilities(ctx, user)
        _abilities = [i for i in abilities.keys() if i != stats['MAIN']]

        await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f"Accumulated XP: {stats['XP']}")
                       .set_author(name=f"{user.display_name} | Level {stats['LVL']}")
                       .add_field(name="Info", value=f"**Main Ability:** {stats['MAIN']} \n"
                                                     f"**Balance:** {stats['BAL']}", inline=False)
                       .add_field(name="Other Abilities", value=', '.join(_abilities), inline=False)
                       .add_field(name="Guild", value=self.user_cache[user.id]['Guild']['NAME'] or 'Not recruited',
                                  inline=False)
                       .set_image(url=user.avatar_url)
                       )

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def mission(self, ctx):
        """Participate in an assigned mission."""

        adventure_ = ['adventure', 'odyssey']
        for i in adventure_:
            cmd = self.bot.get_command(i)
            if cmd.is_on_cooldown(ctx):
                await ctx.send(f"You can't use `{ctx.prefix}{ctx.command}` and `{ctx.prefix}{i}` at the same time.")
                ctx.command.reset_cooldown(ctx)
                return

        mission = random.choice([
            "Gather intel about a infamous supervillian gang.",
            "Attack the Scientific and Technological Advanced Research Laboratory.",
            "Defeat the infamous level 70 supervillian Solaris.",
            "Defeat the famous level 75 superhero Chronos.",
            "Save the life of Chronos; who was badly injured in a fight with Solaris.",
            "Save the life of Solaris; who was badly injured in a fight with Chronos.",
            "Stop a Kleric drug deal from happening."
        ])
        await ctx.send(f"**You've been sent to:** {mission} \nYou will return in 1 hour.")
        await asyncio.sleep(3600)
        money = random.randint(100, 250)
        xp = random.randint(100, 250)
        await ctx.send(f"You have been awarded ${money} and {xp}xp for completing the mission.")
        await self.method.level2(ctx, money, xp)
        await self.method.guild_level(ctx, xp)

    @commands.command()
    @checks.registered2()
    async def shop(self, ctx):
        """Acquire new abilities"""

        abilities = await self.method.fetch_abilities(ctx)
        shop = [x for x in self.shop_items if x not in abilities]
        p = [(discord.Embed(color=self.bot.embed_color,
                            description="Welcome to the Infamous RPG shop, react <:info:556320125599350808> to get "
                                        "information on how the reactions work.")

              .set_author(name="Shop Paginator", icon_url=self.bot.user.avatar_url)
              .add_field(name="How do abilities work?", value=f"Abilities are used for commands like **"
                                                              f"{ctx.prefix}duel** and **{ctx.prefix}brawl** "
                                                              f"They can only be acquired in the shop using money.")
              .add_field(name="How do I earn money?", value=f"You can use **{ctx.prefix}adventure, {ctx.prefix},"
                                                            f"mission, {ctx.prefix}odyssey, {ctx.prefix}loot, "
                                                            f"{ctx.prefix}daily, {ctx.prefix}raffle, {ctx.prefix}duel "
                                                            f"and {ctx.prefix} brawl** each giving different amounts.")
              .add_field(name="Note", value="All the abilities you already have don't show up in the shop.")
              .set_footer(text=f"Page 1 of {len(shop)+1} | React 🛒 to get this ability.")
              )]
        if shop:
            for l, i in enumerate(shop):
                p.append(self.method.ability_embed(self.shop_items, i, l + 2, len(shop)+1))

            await rpg.ShopPaginator(ctx, p, self.shop_items, self.user_cache).paginate()
        else:
            await ctx.send("You have acquired every ability in the shop!")

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def loot(self, ctx):
        """Get hourly loot."""

        loot_ = ['adventure', 'mission', 'odyssey']
        for i in loot_:
            cmd = self.bot.get_command(i)
            if cmd.is_on_cooldown(ctx):
                await ctx.send(f"You cannot use `{ctx.prefix}{ctx.command}` and `{ctx.prefix}{i}`")
                ctx.command.reset_cooldown(ctx)
                return

        await ctx.send("You have been given $250 and 250xp")
        await self.method.level2(ctx, 250, 250)
        await self.method.guild_level(ctx, 250)

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 84600, commands.BucketType.user)
    async def daily(self, ctx):
        """Get daily loot."""
        daily_ = ['adventure', 'mission', 'odyssey']
        for i in daily_:
            cmd = self.bot.get_command(i)
            if cmd.is_on_cooldown(ctx):
                await ctx.send(f"You can't use `{ctx.prefix}{ctx.command}` and `{ctx.prefix}{i}` at the same time.")
                ctx.command.reset_cooldown(ctx)
                return
        try:
            await ctx.author.send("You have been given $500 and 500xp")
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention} You have been given $500 and 500xp")

        await self.method.level2(ctx, 500, 500)
        await self.method.guild_level(ctx, 500)

    @daily.error
    async def daily_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = error.retry_after
            cooldown = round(cooldown, 2)
            hours, remainder = divmod(int(cooldown), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            await ctx.send(f"You have to wait {days}d, {hours}h, {minutes}m, {seconds}s.")

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 900, commands.BucketType.user)
    async def master(self, ctx):
        """Upgrade your abilities."""

        abilities = await self.method.fetch_abilities(ctx)
        user = (await self.method.fetch_user2(ctx))
        await ctx.send(f"Choose an ability to master: {', '.join(abilities.keys())}")

        def check(m):
            return m.author == ctx.author and m.content.title() in abilities

        try:
            msg = (await ctx.input('message', check=check, timeout=15)).content.title()
        except asyncio.TimeoutError:
            return await ctx.send("I guess you don't want to pick an ability.")

        if msg not in self.shop_items.keys():
            custom = abilities[msg]
            self.shop_items[msg] = [20000, msg, custom[4], custom[5]]
        if user[3] >= self.shop_items[msg][0] / 4:
            async with ctx.db.acquire() as db:
                await db.execute("UPDATE profiles SET bal = bal - $1 WHERE id = $2",
                                 self.shop_items[msg][0] / 4, ctx.author.id)

            self.user_cache[ctx.author.id]["Information"]["BAL"] -= self.shop_items[msg][0] / 4

            choice = random.choice(["Low", "Middle", "Greater"])
            if choice == "Low":
                xp = random.randint(50, 150)
                await ctx.send(f"You earned {xp}xp and added 50 points to your {msg} stats.")
                await self.method.upgrade_ability(ctx, 50, 50, msg)
            elif choice == "Middle":
                xp = random.randint(150, 300)
                await ctx.send(f"You earned {xp}xp and added 100 points to your {msg} stats.")
                await self.method.upgrade_ability(ctx, xp, 100, 100, msg)
            else:
                xp = random.randint(300, 550)
                await ctx.send(f"You earned {xp}xp and added 150 points to your {msg} stats")
                await self.method.upgrade_ability(ctx, xp, 150, 150, msg)

            if msg not in self.abilities:
                del self.shop_items[msg]
        else:
            return await ctx.send(
                f"{ctx.author.mention} you need ${self.shop_items[msg][0] / 4 - user[3]} more to master.")

    @commands.command()
    @checks.registered2()
    async def active(self, ctx):
        """Shows all the active cooldowns."""

        p = [c.name for c in ctx.cog.get_commands() if c.is_on_cooldown(ctx)]
        await ctx.send(f"**Commands currently on cooldown for {ctx.author.mention}:** {', '.join(p)}")

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def gamble(self, ctx):
        """Risk winning it all or losing it all."""

        await ctx.send("How much are you willing to gamble?")

        user = (await self.method.fetch_user2(ctx))['Information']

        def check(m):
            return m.author == ctx.author and m.content.isdigit()

        active = True
        while active:
            try:
                msg = (await ctx.input('message', check=check, timeout=15)).content
            except asyncio.TimeoutError:
                return await ctx.send("I guess you don't want to risk it.")

            if int(msg) > user['BAL']:
                await ctx.send(f"{ctx.author.mention} you can't gamble what you don't have.")
            else:
                choice = random.choice(["Win", "Lose"])
                async with ctx.db.acquire() as db:
                    if choice == "Win":
                        await ctx.send(f"{ctx.author.mention} got ${msg} richer!")
                        await db.execute("UPDATE profiles SET bal = bal + $1 WHERE id=$2", int(msg), ctx.author.id)
                        self.user_cache[ctx.author.id]["Information"]["BAL"] += int(msg)
                    else:
                        await ctx.send(f"{ctx.author.mention} got ${msg} poorer")
                        await db.execute("UPDATE profiles SET bal = bal - $1 WHERE id=$2", int(msg), ctx.author.id)
                        self.user_cache[ctx.author.id]["Information"]["BAL"] -= int(msg)

                active = False

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 600, commands.BucketType.channel)
    async def duel(self, ctx, user: checks.SuperhumanFinder = None):
        """Battle other players."""
        if not user:
            await ctx.send(f"You need to pick someone.")
            ctx.command.reset_cooldown(ctx)
            return

        user = ctx.guild.get_member_named(str(user))
        abilities1 = await self.method.fetch_abilities(ctx)
        abilities2 = await self.method.fetch_abilities(ctx, user=user)

        if len(abilities1 or abilities2) < 2:
            await ctx.send("One of you don't have two or more abilities")
            ctx.command.reset_cooldown(ctx)
            return

        await ctx.send("Do you accept this challenge? `Yes` or `No`")
        yon = await self.method.yon(ctx, user=user)
        if any(w in yon for w in ["yes", "y"]):
            await ctx.send(f"{ctx.author.mention} Which two abilities do you choose to fight with? \n"
                           f"{', '.join(abilities1.keys())}. (Type your choice like this: Super Speed, Telekinesis)")

            def check(m):
                return m.author == ctx.author and \
                       any(ability in m.content.title() for ability in abilities1) \
                       and ', ' in m.content.title()

            def check2(m):
                return m.author == user and \
                       any(ability in m.content.title() for ability in abilities2) \
                       and ', ' in m.content.title()

            try:
                msg = (await ctx.input('message', check=check, timeout=30)).content.title()
            except asyncio.TimeoutError:
                return await ctx.send(f"{ctx.author.mention}, you ran out of time.")

            await ctx.send(f"{user.mention} Which two abilities do you choose to fight with? \n"
                           f"{', '.join(abilities2.keys())}. (Type your choice like this: Super Speed, Telekinesis)")

            try:
                msg2 = (await ctx.input('message', check=check2, timeout=30)).content.title()
            except asyncio.TimeoutError:
                return await ctx.send(f"{user.mention}, you ran out of time.")

            skill1_ = self.user_cache[ctx.author.id]["Abilities"][(msg.split(', '))[0]]
            skill2_ = self.user_cache[ctx.author.id]["Abilities"][(msg.split(', '))[1]]
            skill1 = self.user_cache[user.id]["Abilities"][(msg2.split(', '))[0]]
            skill2 = self.user_cache[user.id]["Abilities"][(msg2.split(', '))[1]]

            hp = skill1_["DUR"] + skill2_["DUR"]
            hp2 = skill1["DUR"] + skill2["DUR"]
            active = True
            await ctx.send(f"{ctx.author.mention} pick an ability: {msg}")
            try:
                while active:
                    await self.method.turn(ctx, skill1_, skill2_, hp, hp2, user, user=None)
                    await ctx.send(f"{user.mention} pick an ability: {msg2}")
                    await self.method.turn(ctx, skill1, skill2, hp2, hp, ctx.author, user=user)
                    await ctx.send(f"{ctx.author.mention} pick an ability: {msg}")
            except rpg.MatchEnd:
                pass
        else:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("I guess you don't want to duel.")

    @duel.error
    async def duel_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"{ctx.author.mention} there is currently a active duel in {ctx.channel.mention}")

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(error)

    @commands.command()
    async def top(self, ctx):
        """The top players."""

        async with ctx.db.acquire() as db:
            lb = await db.fetch("SELECT * FROM profiles ORDER BY xp DESC")

        p = []
        for place, user in enumerate(lb):
            user_ = ctx.grab(user[0])
            if not user_:
                continue

            p.append((discord.Embed(color=self.bot.embed_color,
                                    description=f"**Level:** {user[1]} \n"
                                    f"**Total XP:** {user[2]} \n"
                                    f"**Guild:** {user[5]}")
                      .set_author(name=f"#{place + 1} {user_.display_name or user_.name}")
                      .set_image(url=user_.avatar_url_as(static_format="png", size=1024))
                      .set_footer(text=f"Page {place + 1} of {len(lb)}")
                      ))

        await ctx.paginate(entries=p)

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 600, commands.BucketType.channel)
    async def drink(self, ctx, user: checks.SuperhumanFinder = None):
        """Last one standing wins!"""

        if not user:
            await ctx.send("Find a reasonable drinking partner")
            ctx.command.reset_cooldown(ctx)
            return

        user = ctx.guild.get_member_named(str(user))
        await ctx.send(f"{user.mention} Do you accept this challenge? \nYes or No?")
        yon = await self.method.yon(ctx, user=user)
        if any(w in yon for w in ["yes", "y"]):
            choice = random.choice([ctx.author, user])
            xp = random.randint(100, 200)
            mon = random.randint(100, 200)
            if choice == ctx.author:
                await ctx.send(f"{ctx.author.mention} wins the drinking contest! They earn {xp}xp and ${mon}")
                await self.method.level2(ctx, mon, xp)
            else:
                await ctx.send(f"{user.mention} wins the drinking contest! They earn {xp}xp and ${mon}")
                await self.method.level2(ctx, mon, xp, user)
            ctx.command.reset_cooldown(ctx)
        else:
            await ctx.send("I guess they don't want to get drunk tonight.")
            ctx.command.reset_cooldown(ctx)
            return

    @drink.error
    async def drink_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"There is currently a drinking competition in {ctx.channel.mention}")

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(error)

    @commands.group(invoke_without_command=True)
    @checks.registered2()
    async def guild(self, ctx):
        """Show your current guild."""

        data = self.user_cache[ctx.author.id]['Guild']
        if not data:
            outcome = f'{ctx.author.mention} You are not in a guild! To join a guild type `{ctx.prefix}guild join`'
        else:
            outcome = f'{ctx.author.mention} you are enlisted in {data}'

        await ctx.send(outcome)

    @guild.command(name="create", aliases=['form'])
    @checks.has_guild()
    @checks.registered2()
    async def _create_(self, ctx, *, name=None):
        """Create your own guild."""

        if not name:
            return await ctx.send("Provide a name!")

        await ctx.send(f"Are you sure you want to create a guild? This will cost $1000")
        user = await self.method.fetch_user2(ctx)
        yon = await self.method.yon(ctx)
        if any(w in yon for w in ["yes", "y"]):
            if user['BAL'] >= 10000:
                await ctx.send(f"You are now the leader and founder of {name}")
                async with ctx.db.acquire() as db:
                    await db.execute("INSERT INTO guilds VALUES($1, $2, $3, $4, $5)",
                                     name, ctx.author.id, 1, 0, )
                    await db.execute("UPDATE profiles SET guild=$1 WHERE id=$2", name, ctx.author.id)
                self.user_cache[ctx.author.id]['Guild'] = {"NAME": name, "LEADER": ctx.author.id, "LVL": 1, "XP": 0}
            else:
                return await ctx.send(f"{ctx.author.mention} You need ${10000 - user[3]} to create a guild!")
        else:
            return await ctx.send("I guess you don't want to create a guild")

    @guild.command()
    @checks.has_guild()
    @checks.registered2()
    async def join(self, ctx, *, name):
        """Join a guild."""

        async with ctx.db.acquire() as db:
            leader = await db.fetchval("SELECT leader FROM guilds WHERE guild=$1", name)
            data = await db.fetchrow("SELECT level, xp, icon FROM guilds WHERE guild=$1", name)

        leader = self.bot.get_user(leader)
        await ctx.send(f"**{leader}** the leader of {name} has been informed of your application.")
        try:
            await leader.send(f"{leader.mention} Do you accept **{ctx.author}** into your guild? \n"
                              f"Yes or No?")
        except discord.Forbidden:
            await ctx.send(f"{leader.mention} Do you accept **{ctx.author}** into your guild? \n"
                           f"Yes or No?")

        def check(m):
            return m.author == leader and m.channel == leader or ctx.channel and m.content.capitalize() in ["Yes", "No"]

        msg = (await ctx.input('message', check=check)).content.capitalize()
        if msg == "Yes":
            async with ctx.db.acquire() as db:
                await db.execute("UPDATE profiles SET guild=$1 WHERE id=$2", name, ctx.author.id)
                self.user_cache[ctx.author.id]['Guild'] = {"NAME": name, "LEADER": leader, "LVL": data[0],
                                                           "XP": data[1], "ICON": data[2]}
            await ctx.send(f"{ctx.author.mention} you have been accepted to join {name}")
        else:
            return await ctx.send(f"{ctx.author.mention} you have been sadly rejected to join {name}")

    @guild.command()
    @checks.registered2()
    @checks.no_guild()
    async def leave(self, ctx):
        """Leave your guild."""
        async with ctx.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", ctx.author.id)

        if not guild_:
            return await ctx.send("You're not in a guild.")
        else:
            await ctx.send(f"Are you sure you want to leave {guild_}? \n"
                           f"Yes or No?")
            yon = await self.method.yon(ctx)
            if any(w in yon for w in ["yes", "y"]):
                async with ctx.db.acquire() as db:
                    await db.execute("UPDATE profiles SET guild = NULL WHERE id=$1", ctx.author.id)
                await ctx.send(f"You have left **{guild_}**")
            else:
                return await ctx.send("I guess you don't want to leave **{guild_}**")

    @guild.command()
    @checks.no_guild()
    @checks.registered2()
    async def transfer(self, ctx, user: discord.Member = None):
        """Transfer leadership of guild."""
        async with ctx.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", ctx.author.id)
            leader_ = await db.fetchval("SELECT leader FROM guilds WHERE name=$1", guild_)

        if not user or user == ctx.author:
            return await ctx.send("You either didn't pick a user, or you picked yourself.")

        if guild_:
            if leader_ == ctx.author.id:
                await ctx.send("Are you sure you want to transfer leadership of **{guild_}** to {user.mention}? \n"
                               "Yes or No?")

                yon = await self.method.yon(ctx)
                if any(w in yon for w in ["yes", "y"]):
                    async with ctx.db.acquire() as db:
                        await db.execute("UPDATE guilds SET leader = $1 WHERE guild=$2", user.id, guild_)

                    for i in self.user_cache:
                        if self.user_cache[i]['Guild']:
                            if self.user_cache[i]['Guild']['NAME'] == self.user_cache[ctx.author.id]['Guild']['NAME']:
                                self.user_cache[i]['Guild']['LEADER'] = user.id

                    await ctx.send(f"Bow down to the new leader of {guild_}, {user.display_name or user.name}")
                else:
                    return await ctx.send("I guess you don't want to transfer leadership.")
            else:
                return await ctx.send(f"You're not the current leader of **{guild_}**")

    @guild.command(name="info")
    @checks.no_guild()
    async def _info_(self, ctx, *, name):
        async with ctx.db.acquire() as db:
            guild_ = await db.fetchrow("SELECT * FROM guilds WHERE guild=$1", name)
            members = await db.fetch("SELECT * FROM profiles WHERE guild=$1", name)

        p = []
        for i in members:
            p.append((ctx.guild.get_member(i[0])).display_name or (ctx.bot.get_user(i)).name)

        leader = ctx.guild.get_member(guild_[1])
        if not leader:
            leader = ctx.bot.get_user(guild_[1])

        await ctx.send(embed=discord.Embed(color=self.bot.embed_color,
                                           description=f"Current Leader: {leader.display_name or leader.name}")
                       .set_author(name=guild_[0])
                       .set_image(url=guild_[4] or "https://imgur.com/Xy8i2UB.png")
                       .add_field(name="Stats", value=f"**Level:** {guild_[2]} \n"
                                                      f"**XP:** {guild_[3]}")
                       .add_field(name="Members", value='\n'.join(p))
                       )

    @guild.command()
    @checks.no_guild()
    @checks.registered2()
    async def icon(self, ctx, *, icon=None):
        if not icon:
            if ctx.message.attachments:
                icon = ctx.message.attachments[0].url
            else:
                return await ctx.send("Provide an attachment or image url.")

        async with ctx.db.acquire() as db:
            guild_ = await db.fetchval("SELECT guild FROM profiles WHERE id=$1", ctx.author.id)
            leader = await db.fetchval("SELECT leader FROM guilds WHERE guild=$1", guild_)
            if leader != ctx.author.id:
                return await ctx.send("You are not the leader of **{guild_}**")
            else:
                await db.execute("UPDATE guilds SET icon = $1 WHERE guild=$2", icon, guild_)
                await ctx.send(f"Changed the icon of **{guild_}** to: {icon}")

    @commands.command()
    @checks.registered2()
    @commands.cooldown(1, 84600, commands.BucketType.user)
    async def raffle(self, ctx):
        await ctx.send("Pick a number between 1-10 to win a prize")

        def check(m):
            if not m.author or m.author.id != ctx.author.id:
                return False

            if m.content.isdigit():
                return True

            return False

        try:
            msg = int((await ctx.input('message', check=check, timeout=20)).content)
        except asyncio.TimeoutError:
            return await ctx.send("I guess you don't want to participate in the raffle.")

        if msg:
            prize = random.choice(["Money", "Master", "Level"])
            if prize == "Money":
                mon = random.randint(100, 500)
                xp = random.randint(100, 500)
                await ctx.send(f"You earned ${mon} and {xp}xp.")
                await self.method.level2(ctx, mon, xp)
            elif prize == "Master":
                ability = random.choice(await self.method.fetch_abilities(ctx))
                await ctx.send(f"{ability} had been upgraded.")
                await self.method.upgrade_ability(ctx, 100, 100, ability)
            else:
                user = await self.method.fetch_user2(ctx)
                await self.method.level2(ctx, (user[1]*2000) * 3, 2000)

    @raffle.error
    async def raffle_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown = error.retry_after
            cooldown = round(cooldown, 2)
            hours, remainder = divmod(int(cooldown), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            await ctx.send(f"You have to wait {days}d, {hours}h, {minutes}m, {seconds}s.")

    @commands.command()
    @checks.registered2()
    async def abilities(self, ctx, user: checks.SuperhumanFinder = None):
        """Shows the abilities you currently have."""
        if not user:
            user = ctx.author
        else:
            user = ctx.guild.get_member_named(str(user))
        p = []
        a = await self.method.fetch_abilities(ctx, user)
        for x, i in enumerate(a):

            p.append(discord.Embed(color=self.bot.embed_color,
                                   description=f"**DMG**: {a[i]['DMG']} \n"
                                               f"**DUR**: {a[i]['DUR']}")
                     .set_author(name=i)
                     .set_image(url=a[i]["ICON"] or self.shop_items[i[1]][1])
                     .set_footer(text=f"Page {x + 1} of {len(a)}")
                     )

        await ctx.paginate(entries=p)

    @commands.command()
    @checks.registered2()
    async def unregister(self, ctx):
        """Delete your account in the self.method."""

        await ctx.send("Are you sure you want to unregister from the RPG? **You will lose all your data** \n"
                       "**Yes** or **No**")

        yon = await self.method.yon(ctx)
        if any(w in yon for w in ["yes", "y"]):
            async with ctx.db.acquire() as db:
                await db.execute("DELETE FROM profiles WHERE id=$1", ctx.author.id)
                await db.execute("DELETE FROM abilities WHERE id=$1", ctx.author.id)

            del self.user_cache[ctx.author.id]

            await ctx.send(f"You have been successfully erased from the RPG database.")
        else:
            return await ctx.send("I guess you don't want to lose your data.")

    @commands.command()
    @checks.registered2()
    async def bootleg(self, ctx):
        """Make custom abilities"""
        user = await self.method.fetch_user2(ctx)

        await ctx.send("Are you sure you want to make a custom ability? It costs $20000")
        yon = await self.method.yon(ctx)
        if any(w in yon for w in ["yes", "y"]):
            if user["BAL"] >= 20000:
                await ctx.send("What is the name of this custom ability")

                def check(m):
                    return m.author == ctx.author and m.content.title()

                try:
                    name = (await ctx.input('message', check=check, timeout=30)).content.title()
                except asyncio.TimeoutError:
                    return await ctx.send("Time ran out...")

                if name in self.shop_items.keys() or name in self.user_cache['Information']['Abilities']:
                    return await ctx.send("You can't create a custom ability already in the shop.")

                await ctx.send(f"So this custom ability is called {name}. "
                               f"What is the icon of the ability? You can post a link or attachment")

                def check3(m):
                    return m.author == ctx.author and m.content.startswith("http") or m.attachments \
                           and m.channel == ctx.channel

                try:
                    icon = await ctx.input('message', check=check3, timeout=30)
                    icon = icon.content or icon.attachments[0].url
                except asyncio.TimeoutError:
                    return await ctx.send("Time ran out...")

                await ctx.send(f"So the ability's icon is this: {icon}")
                await ctx.send(f"{name} has been created.")
                async with ctx.db.acquire() as db:
                    await db.execute("INSERT INTO abilities VALUES($1, $2, $3, $4, $5,)",
                                     ctx.author.id, name, 1000, 1050, icon)
                    await db.execute("UPDATE profiles SET bal = bal - 20000 WHERE id=$1", ctx.author.id)
                    self.user_cache[ctx.author.id]['Abilities'][name] = {"DMG": 1000, "DUR": 1050}
                    self.user_cache[ctx.author.id]['Information']['BAL'] -= 20000
            else:
                return await ctx.send(f"You still need ${20000 - user['BAL']}.")
        else:
            return await ctx.send("I guess you don't want to spend $20000")

    @commands.command()
    @commands.cooldown(1, float('inf'), commands.BucketType.channel)
    async def brawl(self, ctx):
        """Battle randomly generated superhumans"""

        name1 = random.choice([x.display_name for x in ctx.guild.members])
        name2 = random.choice([x.display_name for x in ctx.guild.members if x != name1])
        name = rpg.merge(name1, name2)

        ability1 = random.choice([x for x in self.shop_items])
        ability2 = random.choice([x for x in self.shop_items if x != ability1])
        abilities1 = await self.method.fetch_abilities(ctx)
        level = random.randint(10, 50)

        await ctx.send(f"You will be up against **{name}**, "
                       f"who is **level {level}** with **{ability1}** and **{ability2}** \n"
                       f"What abilities will you choose? (Type your choice like this: Super Speed, Telekinesis) \n"
                       f"`{', '.join(abilities1.keys())}`")

        def check(m):
            if not m.author or m.author.id != ctx.author.id:
                return False

            if m.channel != ctx.channel:
                return False

            if any(ability in m.content.title() for ability in abilities1.keys()) and ', ' in m.content.title():
                return True
            return False

        try:
            msg = (await ctx.input('message', check=check, timeout=60)).content.title()
        except asyncio.TimeoutError:
            return await ctx.send("You ran out of time.")

        skill1_ = self.user_cache[ctx.author.id]['Abilities'][(msg.split(', '))[0]]
        skill2_ = self.user_cache[ctx.author.id]['Abilities'][(msg.split(', '))[1]]

        skill1 = [(self.shop_items[ability1][3] + random.randint(100, 1000)),
                  (self.shop_items[ability1][4] + random.randint(100, 1000))]

        skill2 = [(self.shop_items[ability2][3] + random.randint(100, 1000)),
                  (self.shop_items[ability2][4] + random.randint(100, 1000))]

        self.hp['p1'] = skill1_[5] + skill2_[5]
        self.hp['p2'] = skill1[1] + skill2[1]

        active = True
        await ctx.send(f"{ctx.author.mention} choose an ability: {msg}")
        try:
            while active:
                await self.method.turn(ctx, skill1_, skill2_, self.hp['p1'], self.hp['p2'], name)

                msg_ = random.choice([ability1, ability2])
                if msg_ == ability1:
                    dmg = random.randint(10, round(skill1[0] / 2))
                    if dmg > self.hp['p1'] / 2:
                        chance = random.choice(["Hit", "Miss"])
                        if chance == "Hit":
                            self.hp['p1'] -= dmg
                            await ctx.send(
                                f"**{name}** Your attack using your {msg_} has dealt {dmg}dmg \n"
                                f"{ctx.author.mention} has `{self.hp['p1']}hp`. "
                                f"{ctx.author.mention} pick an ability: {msg} ")
                        else:
                            self.hp['p2'] -= dmg
                            await ctx.send(
                                f"**{name}** missed! Causing {ctx.author.mention} to deal {dmg}dmg \n"
                                f"They now have `{self.hp['p2']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")

                            if self.hp['p2'] <= 0:
                                xp = random.randint(250, 500)
                                mon = random.randint(250, 500)
                                await ctx.send(f"{ctx.author.mention} wins! They earn {xp}xp and ${mon}")
                                await self.method.level2(ctx, mon, xp)
                                await self.method.guild_level(ctx, xp)
                                raise rpg.MatchEnd
                    else:
                        chance = random.choice(["Hit", "Miss"])
                        if chance == "Hit":
                            self.hp['p1'] -= dmg
                            await ctx.send(
                                f"**{name}** Your attack using your {msg_} has dealt {dmg}dmg \n"
                                f"{ctx.author.mention} has `{self.hp['p1']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")
                        else:
                            self.hp['p2'] -= dmg
                            await ctx.send(
                                f"**{name}** missed! Causing {ctx.author.mention} to deal {dmg}dmg \n"
                                f"They now have `{self.hp['p2']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")
                            if self.hp['p2'] <= 0:
                                xp = random.randint(250, 500)
                                mon = random.randint(250, 500)
                                await ctx.send(f"{ctx.author.mention} wins! They earn {xp}xp and ${mon}")
                                await self.method.level2(ctx, mon, xp)
                                await self.method.guild_level(ctx, xp)
                                raise rpg.MatchEnd

                    if self.hp['p1'] <= 0:
                        await ctx.send(f"**{name}** wins!")
                        raise rpg.MatchEnd
                else:
                    dmg = random.randint(10, round(skill2[0] / 2))
                    if dmg > self.hp['p1'] / 2:
                        chance = random.choice(["Hit", "Miss"])
                        if chance == "Hit":
                            self.hp['p1'] -= dmg
                            await ctx.send(
                                f"**{name}** Your attack using your {msg_} has dealt {dmg}dmg \n"
                                f"{ctx.author.mention} has `{self.hp['p1']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")
                        else:
                            self.hp['p2'] -= dmg
                            await ctx.send(
                                f"**{name}** missed! Causing {ctx.author.mention} to deal {dmg}dmg \n"
                                f"They now have `{self.hp['p2']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")

                            if self.hp['p2'] <= 0:
                                xp = random.randint(250, 500)
                                mon = random.randint(250, 500)
                                await ctx.send(f"{ctx.author.mention} wins! They earn {xp}xp and ${mon}")
                                await self.method.level2(ctx, mon, xp)
                                await self.method.guild_level(ctx, xp)
                                raise rpg.MatchEnd
                    else:
                        chance = random.choice(["Hit", "Miss"])
                        if chance == "Hit":
                            self.hp['p1'] -= dmg
                            await ctx.send(
                                f"**{name}** Your attack using your {msg_} has dealt {dmg}dmg \n"
                                f"{ctx.author.mention} has `{self.hp['p1']} hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")
                        else:
                            self.hp['p2'] -= dmg
                            await ctx.send(
                                f"**{name}** missed! Causing {ctx.author.mention} to deal {dmg}dmg \n"
                                f"They now have `{self.hp['p2']}hp.` "
                                f"{ctx.author.mention} pick an ability: {msg}")

                            if self.hp['p2'] <= 0:
                                xp = random.randint(250, 500)
                                mon = random.randint(250, 500)
                                await ctx.send(f"{ctx.author.mention} wins! They earn {xp}xp and ${mon}")
                                await self.method.level2(ctx, mon, xp)
                                await self.method.guild_level(ctx, xp)
                                raise rpg.MatchEnd

                    if self.hp['p1'] <= 0:
                        await ctx.send(f"**{name}** wins!")
                        raise rpg.MatchEnd
        except rpg.MatchEnd:
            ctx.command.reset_cooldown(ctx)

    @brawl.error
    async def brawl_handler(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"There is currently a brawl in {ctx.channel.mention}")


def setup(bot):
    bot.add_cog(Rpg2(bot))
