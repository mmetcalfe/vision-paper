from PIL import Image
import os.path
import re
import argparse
import random
import math
import glob
from progress.bar import Bar

def extractRandomWindows(input_dir, output_dir, out_size):
	# Create the output directory:
	if not os.path.isdir(output_dir):
		print '## Creating output directory: {}'.format(output_dir)
		os.makedirs(output_dir)
	else:
		print '## Using existing output directory: {}'.format(output_dir)

	neg_images = glob.glob("{}/*_*.jpg".format(input_dir))

	bar = Bar('Processing', max=len(neg_images))
	for image_path in neg_images:
		bar.next()
		if not os.path.isfile(image_path):
			print 'The path {} does not exist'.format(image_path)
		else:
			file_name = image_path.rpartition('/')[2].partition('.')[0]
			out_path = '{}/{}.thumbnail.jpg'.format(output_dir, file_name)
			try:
				im = Image.open(image_path)
				im_width, im_height = im.size

				maxWindowSize = min(im_width, im_height)
				minWindowSize = max(out_size, int(0.2 * maxWindowSize))
				window_size = random.randint(minWindowSize, maxWindowSize)

				# Generate a valid sub-image:
				hs = int(math.ceil(window_size * 0.5))
				hsFloor = int(math.floor(window_size * 0.5))
				xMin, xMax = hs, im_width  - hsFloor
				yMin, yMax = hs, im_height - hsFloor
				# print 'maxWindowSize', maxWindowSize
				# print 'minWindowSize', minWindowSize
				# print 'window_size', window_size
				# print xMin, xMax
				# print yMin, yMax
				xc = random.randint(xMin, xMax) if xMin != xMax else xMin
				yc = random.randint(yMin, yMax) if yMin != yMax else yMin

				l = xc - hs
				t = yc - hs
				r = l + window_size
				b = t + window_size

				im_crop = im.crop((l, t, r, b))
				im_crop = im_crop.resize((out_size, out_size), Image.ANTIALIAS)
				im_crop.save(out_path, 'jpeg')
			except IOError:
				print "Error opening {}".format(image_path)
	bar.finish()

if __name__ == "__main__":
	random.seed(0xC0015EED) # Use deterministic samples.

	parser = argparse.ArgumentParser(description='ImageNet Gatherer')
	parser.add_argument('input_dir', type=str, nargs='?', default='samples/background_raw', help='Folder in which to find raw images')
	parser.add_argument('output_dir', type=str, nargs='?', default='samples/background', help='Output folder for cropped and resised image windows')
	parser.add_argument('size', type=int, nargs='?', default=24, help='Width of the output window')

	args = parser.parse_args()

	extractRandomWindows(args.input_dir, args.output_dir, args.size)
