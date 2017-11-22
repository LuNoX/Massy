from .utils import config, checks
from discord.ext import commands
import aiohttp
from PIL import Image
from io import BytesIO
import numpy
import cv2
import argparse


class Massy:
    def __init__(self, bot):
        self.bot = bot
        self.config = config.Config('massy.json', loop=bot.loop)
        self.bot.aiosession = aiohttp.ClientSession(loop=bot.loop)

    # 1. get url                                               X
    # 2. save image from url                                   X
    # 3. do shape recognition
    # 4.a) take the biggest shape
    # b) ask the user for the correct shape
    # 5. do the center of mass calculation for that shape

    @commands.command(name='centerOfMass', aliases=['centerofmass'], pass_context=True)
    async def center_of_mass(self, ctx, url: str, *args):
        parsed_args = self.parse_arguments(args)
        imgbytes = BytesIO(await self.get_image_from_url(url))
        img = Image.open(imgbytes)
        img.show()

    def parse_arguments(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--manual_select', action='store_true', dest='manual_select', default=True)
        parser.add_argument('--lower_bound', type=int, dest='lower_bound', default=0)
        parser.add_argument('--lower_red', type=int, dest='lower_red')
        parser.add_argument('--lower_green', type=int, dest='lower_green')
        parser.add_argument('--lower_blue', type=int, dest='lower_blue')
        parser.add_argument('--upper_bound', type=int, dest='upper_bound', default=0)
        parser.add_argument('--upper_red', type=int, dest='upper_red')
        parser.add_argument('--upper_green', type=int, dest='upper_green')
        parser.add_argument('--upper_blue', type=int, dest='upper_blue')
        parser.add_argument('--contour_colours', '--contour_colors', type=list, dest='contour_colours',
                            default=[(256, 0, 0)])
        parsed_args = parser.parse_args(args)
        return parsed_args

    async def get_image_from_url(self, url):
        async with self.bot.aiosession.get(url) as response:
            img = await response.content.read()
        return img

    @commands.command(name='test', pass_context=True)
    @checks.admin_or_permissions()
    async def test(self, ctx):
        await self.bot.say('this is a test')


def setup(bot):
    bot.add_cog(Massy(bot))
