from .utils import config, checks
from discord.ext import commands
import aiohttp
from PIL import Image
from io import BytesIO
import numpy
import cv2
import argparse
import math


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

    #so I've got a cv2 image (which is a numbpy array of BGR values. Whats the best way to display it in discord?

    @commands.command(name='centerOfMass', aliases=['centerofmass'], pass_context=True)
    async def center_of_mass(self, ctx, url: str, *args):
        parsed_args = self.parse_arguments(args)
        imagebytes = BytesIO(await self.get_image_from_url(url))
        pil_image = Image.open(imagebytes).convert('RGB')

        # TODO: put this in a separate method
        bounds = self.determine_bounds(parsed_args)
        cv2_image = numpy.array(pil_image)
        # Convert RGB to BGR
        cv2_image = cv2_image[:, :, ::-1].copy()

        shape_mask = cv2.inRange(cv2_image, bounds[0], bounds[1])
        hierarchy, contours, contour_mask = cv2.findContours(shape_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if parsed_args.manual_select is True:
            number_of_colours = len(parsed_args.contour_colours)
            counter = 0
            for i in contours:
                if counter >= number_of_colours:
                    counter = 0
                print(len(i))
                cv2.drawContours(cv2_image, [i], -1, parsed_args.contour_colours[counter][::-1], 2)
                counter += 1
                cv2.imshow('Image', cv2_image)
                # TODO: ask user which shape to use
        else:
            most_complex_contour = (0, contours[0])
            for i in contours:
                if len(i) > most_complex_contour[0]:
                    most_complex_contour = (len(i), i)
            cv2.drawContours(cv2_image, [most_complex_contour[1]], -1, parsed_args.contour_colours[0][::-1], 2)
            contours.remove(most_complex_contour[1])
            for i in contours:
                cv2.drawContours(shape_mask, [i], -1, (0, 0, 0), -1)
        # cv2.imshow('Image', cv2_image) # debug
        # cv2.imshow('Mask', shape_mask)  # debug

        center_of_mass = self.determine_center_of_mass(shape_mask)
        cv2_image = cv2.circle(cv2_image, (center_of_mass[0], center_of_mass[1]), 10, (255, 0, 0)[::-1], 4)
        cv2.imshow('Result', cv2_image)

        # TODO: draw center of mass and display image

        cv2.waitKey(0)

    def parse_arguments(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--manual_select', action='store_true', dest='manual_select', default=False)
        parser.add_argument('--lower_bound', type=int, dest='lower_bound', default=0)
        parser.add_argument('--lower_red', type=int, dest='lower_red')
        parser.add_argument('--lower_green', type=int, dest='lower_green')
        parser.add_argument('--lower_blue', type=int, dest='lower_blue')
        parser.add_argument('--upper_bound', type=int, dest='upper_bound', default=15)
        parser.add_argument('--upper_red', type=int, dest='upper_red')
        parser.add_argument('--upper_green', type=int, dest='upper_green')
        parser.add_argument('--upper_blue', type=int, dest='upper_blue')
        parser.add_argument('--contour_colours', '--contour_colors', type=list, dest='contour_colours',
                            default=[(255, 0, 0)])
        parsed_args = parser.parse_args(args)
        return parsed_args

    async def get_image_from_url(self, url):
        async with self.bot.aiosession.get(url) as response:
            img = await response.content.read()
        return img

    def determine_bounds(self, args):
        if args.lower_red is None:
            lower_red = args.lower_bound
        else:
            lower_red = args.lower_red
        if args.lower_green is None:
            lower_green = args.lower_bound
        else:
            lower_green = args.lower_green
        if args.lower_blue is None:
            lower_blue = args.lower_bound
        else:
            lower_blue = args.lower_blue
        if args.upper_red is None:
            upper_red = args.upper_bound
        else:
            upper_red = args.upper_red
        if args.upper_green is None:
            upper_green = args.upper_bound
        else:
            upper_green = args.upper_green
        if args.upper_blue is None:
            upper_blue = args.upper_bound
        else:
            upper_blue = args.upper_blue
        # CV takes input in BGR instead or RGB
        lower = numpy.array([lower_blue, lower_green, lower_red])
        upper = numpy.array([upper_blue, upper_green, upper_red])
        return [lower, upper]

    def determine_center_of_mass(self, binary_image):
        non_zero = cv2.findNonZero(binary_image)

        center_of_mass_x = 0
        for i in non_zero:
            center_of_mass_x += i[0][0]
        center_of_mass_x = int(math.floor(center_of_mass_x/len(non_zero))) # TODO: catch exception

        center_of_mass_y = 0
        for i in non_zero:
            center_of_mass_y += i[0][1]
        center_of_mass_y = int(math.floor(center_of_mass_y/len(non_zero))) # TODO: catch exception

        print(center_of_mass_x)
        print(center_of_mass_y)

        return (center_of_mass_x, center_of_mass_y)

    @commands.command(name='test', pass_context=True)
    @checks.admin_or_permissions()
    async def test(self, ctx):
        await self.bot.say('this is a test')


def setup(bot):
    bot.add_cog(Massy(bot))
