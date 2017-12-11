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
    # 3. do shape recognition                                  X
    # 4.a) take the biggest shape                              X
    #   b) ask the user for the correct shape
    # 5. do the center of mass calculation for that shape      X
    # 6. display center of mass                                X

    @commands.command(name='centerOfMass', aliases=['centerofmass'], pass_context=True)
    async def center_of_mass(self, ctx, url: str, *args):
        # Parse args
        parsed_args = self.parse_arguments(args)
        parsed_args.contour_colours = self.convert_contour_colours_into_list_of_tuples(parsed_args.contour_colours)

        # Fetch image
        async with self.bot.aiosession.get(url) as response:
            img_from_url = await response.content.read()
        pil_image = Image.open(BytesIO(img_from_url)).convert('RGB')

        # Convert PIL to CV2
        cv2_image = numpy.array(pil_image)
        cv2_image = cv2_image[:, :, ::-1].copy()  # Convert RGB to BGR

        # Turn image into binary image
        # TODO: allow different values for the different colours (instead of them all having to be the same)
        # TODO: fix those weird contours probably cause by the same issue
        lower_bound = numpy.array(parsed_args.lower_bound[::-1])
        upper_bound = numpy.array(parsed_args.upper_bound[::-1])
        shape_mask = cv2.inRange(cv2_image, lower_bound, upper_bound)
        if parsed_args.inverse is True:
            shape_mask = cv2.bitwise_not(shape_mask)

        # Determine shape contours
        hierarchy, contours, contour_mask = cv2.findContours(shape_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Determine correct shape and remove everything else
        # TODO: implement manual select fully, not functional at the moment
        if parsed_args.manual_select is True:
            number_of_colours = len(parsed_args.contour_colours)
            counter = 0
            for i in contours:
                if counter >= number_of_colours:
                    counter = 0
                cv2.drawContours(cv2_image, [i], -1, parsed_args.contour_colours[counter][::-1], 2)
                counter += 1
                cv2.imshow('Image', cv2_image)
                # TODO: ask user which shape to use
        else:
            # Determine the most complex contour
            most_complex_contour = (0, contours[0])
            for index, i in enumerate(contours):
                if len(i) > most_complex_contour[0]:
                    most_complex_contour = (len(i), i, index)
            # Draw the contour on the image for user reference
            cv2.drawContours(cv2_image, most_complex_contour[1], -1, parsed_args.contour_colours[0][::-1], 2)
            # Remove everything from the shape_mask except the shape inside the most complex contour
            contours.pop(most_complex_contour[2])
            for i in contours:
                cv2.drawContours(shape_mask, [i], -1, (0, 0, 0), -1)

        center_of_mass = self.determine_center_of_mass(shape_mask)
        # Draw center of mass
        # TODO: use appropriate colour
        cv2_image = cv2.circle(cv2_image, (center_of_mass[0], center_of_mass[1]), 10, (255, 0, 0)[::-1], -1)
        cv2_image = cv2.circle(cv2_image, (center_of_mass[0], center_of_mass[1]), 30, (0, 0, 0)[::-1], 20)

        image_ready_to_be_sent = self.convert_cv2_image_to_byte_image_png(cv2_image)

        # Send image
        # TODO: (optional) include the original name in new file name
        await self.bot.send_file(ctx.message.channel, image_ready_to_be_sent, filename="Center of Mass.png",
                                 content='I have calculated the center of mass to be at ({0}|{1}).'.format(
                                     center_of_mass[0],
                                     center_of_mass[1]), )

    def parse_arguments(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--manual_select', action='store_true', dest='manual_select', default=False)
        parser.add_argument('--inverse', action='store_true', dest='inverse', default=False)
        parser.add_argument('--lower_bound', nargs="+", type=int, dest='lower_bound', default=[0, 0, 0])
        parser.add_argument('--upper_bound', nargs="+", type=int, dest='upper_bound', default=[15, 15, 15])
        parser.add_argument('--contour_colours', '--contour_colors', nargs="+", type=int, dest='contour_colours',
                            default=[255, 0, 0])
        parsed_args = parser.parse_args(args)
        return parsed_args

    async def get_image_from_url(self, url):
        async with self.bot.aiosession.get(url) as response:
            img = await response.content.read()
        return img

    def convert_contour_colours_into_list_of_tuples(self, contour_colours):
        # Make the list a multiple of 3 long
        offset = 3-len(contour_colours)%3
        for i in range(offset):
            contour_colours.append(0)
        # Generate the tuples and add them to the list
        list_of_tuples = []
        for i in range(int(len(contour_colours)/3)):
            colour = (contour_colours[3*i], contour_colours[3*i+1], contour_colours[3*i+2])
            list_of_tuples.append(colour)
        return list_of_tuples

    def determine_center_of_mass(self, binary_image):
        # Get all the area segments of the shape
        non_zero = cv2.findNonZero(binary_image)
        # Calculate x-component
        center_of_mass_x = 0
        for i in non_zero:
            center_of_mass_x += int(i[0][0])
        center_of_mass_x = int(math.floor(center_of_mass_x) / len(non_zero))  # TODO: catch exception
        # Calculate y-component
        center_of_mass_y = 0
        for i in non_zero:
            center_of_mass_y += int(i[0][1])
        center_of_mass_y = int(math.floor(center_of_mass_y) / len(non_zero))  # TODO: catch exception
        center_of_mass = (center_of_mass_x, center_of_mass_y)
        return center_of_mass

    def convert_cv2_image_to_byte_image_png(self, cv2_image):
        # Convert colour space
        image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        # Save image as jpeg
        byte_image = BytesIO()
        pil_image = Image.fromarray(image)
        pil_image.save(byte_image, format='jpeg')
        # Jump to beginning of image
        byte_image.seek(0)
        return byte_image

    @commands.command(name='test', pass_context=True)
    @checks.admin_or_permissions()
    async def test(self, ctx):
        await self.bot.say('this is a test')


def setup(bot):
    bot.add_cog(Massy(bot))
