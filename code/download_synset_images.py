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
parser.add_argument('words_file', type=str, nargs='?', default='parent_words.yaml', help='The file from which to load the parent words')

args = parser.parse_args()

image_folder = args.image_folder


bad_image_cache_file = 'bad_image_cache.dat'
bad_image_cache = {}
if os.path.exists(bad_image_cache_file):
	print 'LOADING BAD IMAGE CACHE:'
	with open(bad_image_cache_file, 'r+') as cache:
		words = map(lambda l: l.strip(), cache.readlines())
		for word in words:
			bad_image_cache[word] = 0
		print '  size: {}'.format(len(bad_image_cache))


blacklisted_images_sha1_hashes = [
	'10f3f7f79e6528aa9d828316248997568ac0d833'  # flickr 'photo not available' image
]

# file = open('parent_words.yaml', 'r')
file = open(args.words_file, 'r')
parent_words = yaml.load(file)
file.close()

search_words = parent_words[:]

print 'DOWNLOADING PARENT WORD HYPONYMS:'
for parent_word in parent_words:
	print '  {}'.format(parent_word)
	hyponym_data_url = urllib2.urlopen('http://www.image-net.org/api/text/wordnet.structure.hyponym?wnid={}&full=1'.format(parent_word))
	for child_word in hyponym_data_url.readlines()[1:]:  # ignore first line as its the 'parent word'
		search_words.append(child_word[1:].strip())  # ignore proceeding dash and strip trailing newline

url_map = {}

for search_word in search_words:
	print 'BEGIN SEARCH WORD: {}'.format(search_word)

	mapping_data_url = urllib2.urlopen('http://www.image-net.org/api/text/imagenet.synset.geturls.getmapping?wnid={}'.format(search_word))
	for map in mapping_data_url.readlines():
		parts = map.strip().partition(' ')
		object_name = parts[0]
		object_url = parts[2]

		output_image_filename = '{}/{}.jpg'.format(image_folder, object_name)

		if object_name in bad_image_cache:
			print "Skipping cached bad image {}.".format(object_name)
			continue

		if not os.path.exists(output_image_filename):
			try:
				print object_url
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
				with open(bad_image_cache_file, 'a+') as cache:
					cache.write("{}\n".format(object_name))
				continue
		else:
			print 'Image already exists: {}'.format(object_name)
