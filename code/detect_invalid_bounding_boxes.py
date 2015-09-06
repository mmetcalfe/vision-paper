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

def detectInvalidBoundingBoxes(sample_dir, bbinfo_key):
	# Read the data file:
	bbinfo_cache = loadGlobalInfo(bbinfo_key)

	img_file_list = glob.glob("{}/*.*".format(sample_dir))

	for img_file in img_file_list:
		img_name = img_file.split('/')[-1]

		bbinfo_str = bbinfo_cache[img_name]
		bboxes = [int(x) for x in bbinfo_str.split(' ')]
		img_width = img_height = 0

		try:
			img = Image.open(img_file)
			img_width, img_height = img.size
		except IOError:
			print "Error opening {}".format(img_file)
			continue

		num_objects = bboxes[0]
		for i in range(1, 4 * num_objects, 4):
			bbox = bboxes[i:i+4]
			l = bbox[0]
			t = bbox[1]
			w = bbox[2]
			h = bbox[3]
			r = l + w
			b = t + h

			if l < 0:
				print "l < 0: {}".format(img_file)
			if t < 0:
				print "t < 0: {}".format(img_file)
			if r >= img_width:
				print "r >= img_width: {}".format(img_file)
				print (t,l,r,b,w,h)
			if b >= img_height:
				print "b >= img_height: {}".format(img_file)
				print (t,l,r,b,w,h)
			if w <= 0:
				print "w <= 0: {}".format(img_file)
			if h <= 0:
				print "h <= 0: {}".format(img_file)

			# def clip(val, low, upp):
			# 	return max(low, min(upp, val))
			# l = clip(l, 0, im_width-1)
			# r = clip(r, 0, im_width-1)
			# t = clip(t, 0, im_height-1)
			# b = clip(b, 0, im_height-1)
			# w = abs(r - l)
			# h = abs(b - t)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='detectInvalidBoundingBoxes')
	parser.add_argument('sample_dir', type=str, nargs='?', default='samples/positive', help='Folder in which to find images')
	parser.add_argument('bbinfo_key', type=str, nargs='?', default='*', help='Key for bounding box cache files')

	args = parser.parse_args()

	detectInvalidBoundingBoxes(args.sample_dir, args.bbinfo_key)
