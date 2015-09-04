import urllib2
import tarfile
from PIL import Image
import io
import hashlib
import os.path
import yaml
import argparse
from bs4 import BeautifulSoup as Soup
import glob
import random
from concurrent import futures

parser = argparse.ArgumentParser(description='ImageNet Gatherer')
parser.add_argument('image_folder', type=str, nargs='?', default='images', help='The folder to store the downloaded images')
parser.add_argument('words_file', type=str, nargs='?', default='parent_words.yaml', help='The file from which to load the parent words')

args = parser.parse_args()

image_folder = args.image_folder

def loadCache(cache_name):
	cache = {}
	cache_files = glob.glob("cache/{}__*.dat".format(cache_name))
	for cache_file_name in cache_files:
		with open(cache_file_name, 'r+') as cache_file:
			words = map(lambda l: l.strip(), cache_file.readlines())
			for word in words:
				cache[word] = 0
	return cache

print 'LOADING BAD IMAGE CACHE:'
bad_image_cache = loadCache('bad_image_cache')
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

def downloadImagesForSearchWord(search_word):
	print 'BEGIN SEARCH WORD: {}'.format(search_word)

	bad_image_cache_file = 'cache/bad_image_cache__{}.dat'.format(random.randint(1000, 9999))
	def addToBadImageCache(wordnet_name):
		with open(bad_image_cache_file, 'a+') as cache:
			cache.write("{}\n".format(wordnet_name))

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
					addToBadImageCache(object_name)
					continue
				im = Image.open(io.BytesIO(image_data))
				im.save(output_image_filename, "JPEG")
				print "Saved to {}".format(output_image_filename)
			except Exception as e:
				print "Error retrieving for file {}: {}".format(object_name, e)
				addToBadImageCache(object_name)
				continue
		else:
			print 'Image already exists: {}'.format(object_name)

with futures.ThreadPoolExecutor(max_workers=8) as executor:
	# Build set of futures:
	future_results = {}
	for search_word in search_words:
		# Ignore search words that are known to have bounding box data:
		if search_word in ['n03208556', 'n04019541']:
			print 'WARNING: Skipping search word "{}", as it is known to have bounding box data.'.format(search_word)
			continue

		future = executor.submit(downloadImagesForSearchWord, search_word)
		future_results[future] = search_word

	for future in futures.as_completed(future_results):
		search_word = future_results[future]
		if future.exception() is not None:
			print 'THE SEARCH WORD {} GENERATED AN EXCEPTION: {}'.format(search_word, future.exception())
		else:
			print 'ALL IMAGES FOR SEARCH WORD {} DOWNLOADED.'.format(search_word)
