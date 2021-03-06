from PIL import Image
import os.path
import re
import argparse
import glob

# loadGlobalInfo :: String -> Map String String
def loadGlobalInfo(bbinfo_key):
	global_info = {}
	cache_files = glob.glob("bbinfo/{}__*.dat".format(bbinfo_key))
	for cache_file_name in cache_files:
		with open(cache_file_name, 'r') as dat_file:
			for line in dat_file.readlines():
				parts = line.strip().partition(' ')
				image_path = parts[0].split('/')[-1]
				details = parts[2]
				global_info[image_path] = details
	return global_info

def extractObjectWindows(info_key, size, input_folder, output_folder):
	# Read the data file:
	info_cache = loadGlobalInfo(info_key)

	print 'Info len:', len(info_cache)

	# for image_path, details in info.iteritems():
	image_file_list = glob.glob("{}/n*.jpg".format(input_folder))
	for image_path in image_file_list:
		if re.compile('.*n13874073.*').match(image_path):
			print 'Image {} is from a blacklisted synset.'.format(image_path)
			continue

		img_name = image_path.split('/')[-1]
		bbinfo = info_cache[img_name]

		file_name = image_path.rpartition('/')[2].partition('.')[0]
		out_path = '{}/{}.thumbnail.jpg'.format(output_folder, file_name)
		bboxes = [int(x) for x in bbinfo.split(' ')]
		try:
			im = Image.open(image_path)
			num_objects = bboxes[0]
			for i in range(1, 4 * num_objects, 4):
				bbox = bboxes[i:i+4]
				l = bbox[0]
				t = bbox[1]
				r = bbox[2] + bbox[0]
				b = bbox[3] + bbox[1]

				im_width, im_height = im.size
				def clip(val, low, upp):
					return max(low, min(upp, val))
				l = clip(l, 0, im_width-1)
				r = clip(r, 0, im_width-1)
				t = clip(t, 0, im_height-1)
				b = clip(b, 0, im_height-1)

				w = abs(r - l)
				h = abs(b - t)

				# if w < im_width * 0.1 or h < im_height * 0.1:
				# 	print 'Skipping small ellipse: ({}, {}) in ({}, {})'.format(w, h, im_width, im_height)
				# 	continue

				im_crop = im.crop((l, t, r, b))
				im_crop = im_crop.resize(size, Image.ANTIALIAS)
				out_name = '{}_{}.jpg'.format(out_path.strip('.jpg'), i)

				# print '  saving:', out_name
				im_crop.save(out_name, 'jpeg')
		except IOError:
			print "Error opening {}".format(image_path)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='ImageNet Gatherer')
	parser.add_argument('input_folder', type=str, nargs='?', default='samples/positive_test_set', help='Input folder to find images to crop')
	parser.add_argument('output_folder', type=str, nargs='?', default='samples/positive_test_set_cropped', help='Output folder for cropped and resised image windows')
	parser.add_argument('info_key', type=str, nargs='?', default='*', help='File containing image and bounding-box information')
	parser.add_argument('w', type=int, nargs='?', default=24, help='Width of the output window')
	parser.add_argument('h', type=int, nargs='?', default=24, help='Height of the output window')

	args = parser.parse_args()

	size = (args.w, args.h)

	extractObjectWindows(args.info_key, size, args.input_folder, args.output_folder)
