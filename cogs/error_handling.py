import asyncio
import traceback

import discord
from discord.ext import commands

from custom_classes import KernBot, DisError


class Errors:
    def __init__(self, bot: KernBot):
        self.bot = bot

    async def on_command_error(self, ctx, error: DisError):
        # This prevents any commands already handled locally being run here.
        if hasattr(ctx.command, 'on_error') or \
           hasattr(ctx.cog, f'_{ctx.cog.__class__.__name__}__error'):
            return

        ignored = (commands.NotOwner, commands.CheckFailure,
                   commands.CommandNotFound, discord.Forbidden)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.error(f"Argument `{error.param}` is missing!",
                            "Missing Required Argument(s)")

        elif isinstance(error, asyncio.TimeoutError):
            await ctx.error("The internet is gone?!?!?!?", "Timeout Error")

        elif isinstance(error, self.bot.ResponseError):
            await ctx.error(error, "Response Code > 400:")

        else:
            #add more detailed debug
            await ctx.error("```{}: {}```".format(type(error).__qualname__, error),
                            title=f"Ignoring exception in command *{ctx.command}*:",
                            channel=self.bot.logs)
            print('Ignoring {} in command {}'.format(type(error).__qualname__,
                                                     ctx.command))
            traceback.print_exception(type(error), error, error.__traceback__)

        # if do_send:
        #     print('Ignoring {} in command {}'.format(type(error).__qualname__,
        #                                              ctx.command))

def setup(bot: commands.Bot):
    bot.add_cog(Errors(bot))
