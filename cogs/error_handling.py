import asyncio
import traceback

import discord
from discord.ext import commands

from custom_classes import KernBot


class Errors:
    def __init__(self, bot: KernBot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        # This prevents any commands already handled locally being run here.
        error = getattr(error, "original", error)
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
            await ctx.error(f"**This error is now known about :thumbsup:**\n```{error}```",
                            type(error).__qualname__)
            await ctx.error("```py\n{}```".format("".join(
                traceback.format_exception(type(error),
                                           error, error.__traceback__))),
                            title=f"{ctx.command}: {type(error).__qualname__}",
                            channel=self.bot.logs)

def setup(bot: commands.Bot):
    bot.add_cog(Errors(bot))
