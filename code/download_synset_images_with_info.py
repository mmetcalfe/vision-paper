import urllib2
import tarfile
from PIL import Image
import io
import hashlib
import os.path
import yaml
import argparse
from bs4 import BeautifulSoup as Soup

parser = argparse.ArgumentParser(description='ImageNet Gatherer')
parser.add_argument('image_folder', type=str, nargs='?', default='images', help='The folder to store the downloaded images')
parser.add_argument('info_dat', type=str, nargs='?', default='info.dat', help='The filepath to store the boundingbox information')
parser.add_argument('words_file', type=str, nargs='?', default='parent_words.yaml', help='The file from which to load the parent words')

args = parser.parse_args()

image_folder = args.image_folder

blacklisted_images_sha1_hashes = [
	'10f3f7f79e6528aa9d828316248997568ac0d833'  # flickr 'photo not available' image
]

blacklisted_search_words = [
	'n04118538'  # footballs (non-spherical)
	'n04023962'  # punching bags
]

# file = open('parent_words.yaml', 'r')
file = open(args.words_file, 'r')
parent_words = yaml.load(file)
file.close()

search_words = parent_words[:]

for parent_word in parent_words:
	hyponym_data_url = urllib2.urlopen('http://www.image-net.org/api/text/wordnet.structure.hyponym?wnid={}&full=1'.format(parent_word))
	for child_word in hyponym_data_url.readlines()[1:]:  # ignore first line as its the 'parent word'
		search_words.append(child_word[1:].strip())  # ignore proceeding dash and strip trailing newline

url_map = {}

cached_bbox = {}

output_dat_filename = args.info_dat
with open(output_dat_filename, 'r') as dat_file:
	for line in dat_file.readlines():
		image_path = line.strip().partition(' ')[0]
		cached_bbox[image_path] = True

with open(output_dat_filename, 'a+') as dat_file:
	for search_word in search_words:
		if search_word in blacklisted_search_words:
			print 'Blacklisted search word: {}'.format(search_word)
			continue
		mapping_data_url = urllib2.urlopen('http://www.image-net.org/api/text/imagenet.synset.geturls.getmapping?wnid={}'.format(search_word))
		for map in mapping_data_url.readlines():
			parts = map.strip().partition(' ')
			url_map[parts[0]] = parts[2]

		bounding_boxes_url_data = None
		bounding_boxes_url = 'http://image-net.org/downloads/bbox/bbox/{}.tar.gz'.format(search_word)
		try:
			bounding_boxes_url_data = urllib2.urlopen(bounding_boxes_url)
		except Exception as e:
			print 'Could not open bounding box URL: {}'.format(bounding_boxes_url)
			print 'See: http://www.image-net.org/synset?wnid={}'.format(search_word)
			print e
			continue

		with tarfile.open(fileobj=bounding_boxes_url_data, mode='r|*') as bounding_boxes_file:
			for fileinfo in bounding_boxes_file:
				if fileinfo.isreg():
					bounding_box_file = bounding_boxes_file.extractfile(fileinfo)
					xml = Soup(bounding_box_file)
					objects = xml.findAll('object')
					object_name = xml.annotation.filename.string

					output_image_filename = '{}/{}.jpg'.format(image_folder, object_name)
					if output_image_filename in cached_bbox:
						print 'Image already processed: {}'.format(output_image_filename)
						continue

					try:
						object_url = url_map[object_name]
					except KeyError:
						print 'Mapping did not contain: {}'.format(object_name)
						continue

					if not os.path.exists(output_image_filename):
						try:
							object_data = urllib2.urlopen(object_url)
							image_data = object_data.read()
							sha1hash = hashlib.sha1(image_data).hexdigest()
							if str(sha1hash) in blacklisted_images_sha1_hashes:
								print "Image blacklisted: {}".format(object_name)
								continue
							im = Image.open(io.BytesIO(image_data))
							im.save(output_image_filename, "JPEG")
							print "Saved to {}".format(output_image_filename)
						except Exception as e:
							print "Error retrieving for file {}: {}".format(object_name, e)
							continue
					else:
						print 'Image already exists: {}'.format(object_name)

					bounding_boxes = []
					for obj in objects:
						bbox = obj.bndbox
						bounding_box = {
							'xmin': int(bbox.xmin.string),
							'ymin': int(bbox.ymin.string),
							'xmax': int(bbox.xmax.string),
							'ymax': int(bbox.ymax.string)
						}
						# TODO
						# if bounding_box['xmin'] < 0 or bounding_box['xmax'] > image_width - 1 or bounding_box['ymin'] < 0 or bounding_box['ymax'] > image_height - 1
							# or bounding_box['xmin'] > bounding_box['xmax'] or bounding_box['ymin'] > bounding_box['ymax']:
							# print 'bad'
							# continue
						bounding_boxes.append(bounding_box)

					bbox_output = ['{} {} {} {}'.format(
						bb['xmin'],
						bb['ymin'],
						bb['xmax'] - bb['xmin'],
						bb['ymax'] - bb['ymin']
					) for bb in bounding_boxes]
					output = "{} {} {}".format(output_image_filename, len(bounding_boxes), " ".join(bbox_output))
					print "Writing: {}".format(output)
					dat_file.write("{}\n".format(output))
					dat_file.flush()
					cached_bbox[output_image_filename] = True
