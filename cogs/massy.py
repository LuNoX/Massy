from .utils import config, checks
from discord.ext import commands
import discord

class Massy:
    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('massy.json', loop=bot.loop)

    @commands.command(name='test', pass_context=True)
    @checks.admin_or_permissions()
    async def test(self, ctx):
        await self.bot.say('this is a test')

def setup(bot):
    bot.add_cog(Massy(bot))