import discord
from discord.ext import commands


class Help:
    """Help command"""

    def __init__(self, bot):
        self.bot = bot
        self.icon = bot.user.avatar_url

    def helper(self, ctx):
        """Displays all commands"""

        cmds_ = []
        cogs = ctx.bot.cogs
        for i in cogs:
            cmd_ = ctx.bot.get_cog_commands(i)
            cmd_ = [x for x in cmd_ if not x.hidden]
            for x in list(self.bot.chunk(list(cmd_), 6)):
                embed = discord.Embed(color=self.bot.embed_color)
                embed.set_author(name=f"{i} Commands ({len(cmd_)})", icon_url=self.icon)
                embed.description = ctx.bot.cogs[i].__doc__
                for y in x:
                    embed.add_field(name=y.signature, value=y.help, inline=False)
                cmds_.append(embed)

            for b, a in enumerate(cmds_):
                a.set_footer(
                    text=f'Page {b+1} of {len(cmds_)} | Type "{ctx.prefix}help <command>" for more information'
                )
        return cmds_

    def cog_helper(self, ctx, cog):
        """Displays commands from a cog"""

        name = cog.__class__.__name__
        cmds_ = []
        cmd = [x for x in ctx.bot.get_cog_commands(name) if not x.hidden]
        if not cmd:
            return (discord.Embed(color=self.bot.embed_color,
                                  description=f"{name} commands are hidden.")
                    .set_author(name="ERROR \N{NO ENTRY SIGN}", icon_url=self.icon))

        for i in list(self.bot.chunk(list(cmd), 6)):
            embed = discord.Embed(color=discord.Color.blurple())  # can be any color
            embed.set_author(name=name, icon_url=self.icon)
            embed.description = cog.__doc__
            for x in i:
                embed.add_field(name=x.signature, value=x.help, inline=False)
            cmds_.append(embed)

        for b, a in enumerate(cmds_):
            a.set_footer(text=f"Page {b+1} of {len(cmds_)}")

        return cmds_

    def command_helper(self, command):
        """Displays a command and it's sub commands"""

        try:
            cmd = [x for x in command.commands if not x.hidden]
            cmds_ = []
            for i in list(self.bot.chunk(list(cmd), 6)):
                embed = discord.Embed(color=self.bot.embed_color)
                embed.set_author(name=command.signature, icon_url=self.icon)
                embed.description = command.help
                for x in i:
                    embed.add_field(name=x.signature, value=x.help, inline=False)
                cmds_.append(embed)

            for x, y in enumerate(cmds_):
                y.set_footer(text=f"Page {x+1} of {len(cmds_)}")
            return cmds_
        except AttributeError:
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_author(name=command.signature)
            embed.description = command.help
            return embed

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
                await ctx.paginate(entries=self.cog_helper(ctx, thing))


def setup(bot):
    bot.add_cog(Help(bot))
