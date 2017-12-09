import discord
from discord.ext import commands
import database as db

class Contests:
    def __init__(self, bot):
        self.bot = bot
        self.bot_logs = self.bot.get_channel(382780308610744331)

    #pylint: disable-msg=too-many-arguments
    def generateEmbed(self, messageAuthor: discord.User, title, description, footerText, image_url="", colour=0x00ff00):
        """Generates a discord embed object off the given parameters

        Arguments:
            messageAuthor {discord.User} -- Allows for the mention and user's logo to be added to the embed
            title {string} -- Title of the embed, the first heading
            description {string} -- The description of this object
            footerText {string} -- The text shown in the footer, usually for commands that operate upon this

        Keyword Arguments:
            colour {hex} -- Used for the bar on the left's colour (default: {0x00ff00} -- green)
            image_url {string} -- The image shown at the bottom of the embed. (default: {""} -- no image)

        Returns:
            [discord.Embed] -- The embed object generated.
        """
        embed = discord.Embed(title="Submission by:", description=messageAuthor.mention, colour=colour)
        embed.add_field(name="Title:", value=title, inline=False)
        embed.add_field(name="Description:", value=description, inline=False)
        embed.set_image(url=image_url)
        embed.set_footer(text=footerText)
        embed.set_thumbnail(url=messageAuthor.avatar_url)
        return embed
    #pylint: enable-msg=too-many-arguments

    @commands.command()
    async def submit(self, ctx, *, args):
        """Submits an item into a contest. c!submit <title> | <description> | [imageURL]. Note the spaces"""
        input_split = tuple(args.split("  |"))
        if len(input_split) != 2 and len(input_split) != 3:
            raise TypeError("Not all arguments passed")
        title, description = input_split[0:2]
        if len(input_split) == 3:
            image_url = input_split[3]
        else:
            image_url = ""
        submissionID = db.generate_id()
        footerText = "Type !allow {} to allow this and !allow {} False to prevent the moving on this to voting queue.".format(submissionID, submissionID)
        embed = self.generateEmbed(ctx.author, title, description, footerText, image_url, 0x00ff00)
        print(db.get_server_channels(ctx.guild.id)[0])
        if ctx.channel.id == db.get_server_channels(ctx.guild.id)[0]:
            channel = ctx.guild.get_channel(db.get_server_channels(ctx.guild.id)[1])
            messageID = await channel.send(embed=embed)
            db.add_submission(submissionID, embed.to_dict(), messageID.id)
            """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.Embed.to_dict"""

    @submit.error
    async def submit_error_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You did not pass all the required arguments, please try again.")
        else:
            await ctx.send("​Submit Warning:\n%s"%str(error))

    @commands.command()
    async def allow(self, ctx, submissionID, allowed="True"):
        """Allows for moderators to approve/reject submissions."""
        #CHECK IF SAME SERVER
        embed = db.get_submission(submissionID)
        if allowed.lower() == "true":
            embed.set_footer(text="Type !vote {} 0 to not like it, type !vote {} 5 to really like it.".format(submissionID, submissionID))
            await ctx.send(embed=embed)
        elif allowed.lower() == "false":
            await ctx.send("​Submssions with submissionID of {} has been rejected.".format(submissionID))
            channel = ctx.guild.get_channel(db.get_server_channels(ctx.guild.id)[1])
            message = await channel.get_message(db.get_server_channels(ctx.message.guild.id)[1])
            embed.colour = 0xff0000
            await message.edit(embed=embed)
            db.del_submission(submissionID)
        else:
            await ctx.send("​A correct value of true/false was not passed ")

    @allow.error
    async def allow_error_handler(self, ctx, error):
        if isinstance(error, LookupError):
            await ctx.send(str(error))
        else:
            await ctx.send("​Warning:\n%s"%str(error))

def setup(bot):
    bot.add_cog(Contests(bot))
