import discord
from discord.ext import commands


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot
        self.icon = bot.user.avatar_url

    def information(self):
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name='Infamous Helper', icon_url=self.icon)
        embed.description = 'Welcome to the Infamous help pages. React :information_source: for information on how ' \
                            'the reactions below work.'
        embed.add_field(name='Syntax', value='When you see **<>** encased around a word, this means it is a '
                                             '**__required__** argument. The bot will tell you if you have missed an '
                                             'argument. \n\nWhen you see **[]** encased around a word this means it '
                                             'is a **__optional__** argument. This means you do not have to put an '
                                             'argument. \n\nWhen you see **[]** with **|** inside the brackets, '
                                             'this means the command has more than one name.')

        embed.add_field(name='Support', value='If you stumble upon a error/have suggestions you can join the support '
                                              'server right [here.](https://discord.gg/JyJTh4H)')
        return embed

    def helper(self, ctx):
        """Displays all commands"""

        cmds_ = [self.information()]
        cogs = ctx.bot.cogs
        for i in cogs:
            cmd_ = ctx.bot.get_cog(i).get_commands()
            cmd_ = [x for x in cmd_ if not x.hidden]
            for x in list(self.bot.chunk(list(cmd_), 6)):
                embed = discord.Embed(color=self.bot.embed_color)
                embed.set_author(name=f"{i} Commands ({len(cmd_)})", icon_url=self.icon)
                embed.description = ctx.bot.cogs[i].__doc__
                for y in x:
                    if y.aliases:
                        embed.add_field(name=f"[{y.name}|{'|'.join(y.aliases)}] {y.signature}", value=y.help,
                                        inline=False)
                    else:
                        embed.add_field(name=f"{y.name} {y.signature}", value=y.help, inline=False)
                cmds_.append(embed)

            for b, a in enumerate(cmds_):
                a.set_footer(
                    text=f'Page {b + 1} of {len(cmds_)} | Type "{ctx.prefix}help <command>" for more information'
                )
        return cmds_

    def cog_helper(self, cog):
        """Displays commands from a cog"""

        name = cog.__class__.__name__
        cmds_ = []
        cmd = [x for x in cog.get_commands() if not x.hidden]
        if not cmd:
            return (discord.Embed(color=self.bot.embed_color,
                                  description=f"{name} commands are hidden.")
                    .set_author(name="ERROR \N{NO ENTRY SIGN}", icon_url=self.icon))

        for i in list(self.bot.chunk(list(cmd), 6)):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_author(name=f"{name} Commands ({len(cmd)})", icon_url=self.icon)
            embed.description = cog.__doc__
            for x in i:
                if x.aliases:
                    embed.add_field(name=f"[{x.name}|{'|'.join(x.aliases)}] {x.signature}", value=x.help, inline=False)
                else:
                    embed.add_field(name=f"{x.name} {x.signature}", value=x.help, inline=False)

            cmds_.append(embed)

        for b, a in enumerate(cmds_):
            a.set_footer(text=f"Page {b + 1} of {len(cmds_)}")

        return cmds_

    def command_helper(self, command):
        """Displays a command and it's sub commands"""

        try:
            cmd = [x for x in command.commands if not x.hidden]
            cmds_ = []
            for i in list(self.bot.chunk(list(cmd), 6)):
                embed = discord.Embed(color=self.bot.embed_color)
                if i.aliases:
                    embed.set_author(name=f"[{command.name}|{'|'.join(command.aliases)}] {command.signature}",
                                     icon_url=self.icon)
                else:
                    embed.set_author(name=f"{command.name} {command.signature}")

                embed.description = command.help
                for x in i:
                    if x.aliases:
                        embed.add_field(name=f"[{x.name}|{'|'.join(x.aliases)}] {x.signature}", value=x.help,
                                        inline=False)
                    else:
                        embed.add_field(name=f"{x.name} {x.signature}", value=x.help, inline=False)
                cmds_.append(embed)

            for x, y in enumerate(cmds_):
                y.set_footer(text=f"Page {x + 1} of {len(cmds_)}")
            return cmds_
        except AttributeError:
            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_author(name=command.signature or command.name)
            embed.description = command.help
            return [embed]

    @commands.command(hidden=True)
    async def help(self, ctx, *, command=None):
        if not command:
            await ctx.paginate(entries=self.helper(ctx))

        if command:
            thing = ctx.bot.get_cog(command) or ctx.bot.get_command(command)
            if not thing:
                return await ctx.send(f'Looks like "{command}" is not a command or category.')
            if isinstance(thing, commands.Command):
                await ctx.paginate(entries=self.command_helper(thing))
            else:
                await ctx.paginate(entries=self.cog_helper(thing))


def setup(bot):
    bot.add_cog(Help(bot))
