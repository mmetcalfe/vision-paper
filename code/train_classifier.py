import urllib2
import tarfile
from PIL import Image
import io
import os.path
import yaml
import argparse
import subprocess
import glob
import random
import re

class TooFewImagesError(Exception):
	def __init__(self, presentCounts, requiredCounts):
		self.presentCounts = presentCounts
		self.requiredCounts = requiredCounts
	def __str__(self):
		return 'TooFewImagesError: ({} < {})'.format(repr(self.presentCounts), repr(self.requiredCounts))

# loadYamlFile :: String -> IO (Tree String)
def loadYamlFile(fname):
	if not os.path.isfile(fname):
		raise ValueError('Input file \'{}\' does not exist!'.format(fname))
	file = open(fname, 'r')
	data = yaml.load(file)
	file.close()
	return data

# loadGlobalInfo :: String -> Map String String
def loadGlobalInfo():
	global_info = {}
	cache_files = glob.glob("bbinfo/{}__*.dat".format('*'))
	for cache_file_name in cache_files:
		with open(cache_file_name, 'r') as dat_file:
			for line in dat_file.readlines():
				parts = line.strip().partition(' ')
				image_path = parts[0].split('/')[-1]
				details = parts[2]
				global_info[image_path] = details
	return global_info

# requiredImageCounts :: Tree String -> (Int, Int, Int)
def requiredImageCounts(trial_yaml):
	datasetSize = int(trial_yaml['dataset']['description']['number'])
	posFrac = float(trial_yaml['dataset']['description']['posFrac'])
	hardNegFrac = float(trial_yaml['dataset']['description']['hardNegFrac'])
	numPos = int(datasetSize * posFrac)
	numNeg = int(datasetSize * (1 - posFrac) * hardNegFrac)
	numBak = max(0, datasetSize - numPos - numNeg)
	return (numPos, numNeg, numBak)

# sampleTrainingImages :: String -> [String] -> Int -> [String]
def sampleTrainingImages(image_dir, synsets, sample_size):
	image_list = glob.glob("{}/*.jpg".format(image_dir))
	synsetProg = re.compile('.*({})_.*.jpg'.format('|'.join(synsets)))

	# Filter image file lists to match sysnet specifications:
	filtered_image_list = filter(lambda x: synsetProg.match(x), image_list)

	# Truncate file lists to sample the correct number of images:
	image_sample = random.sample(filtered_image_list, min(sample_size, len(filtered_image_list)))
	return image_sample

# preprocessTrial :: Tree String -> String -> IO ()
def preprocessTrial(classifier_yaml, output_dir):
	# Determine required number of images:
	requiredCounts = requiredImageCounts(classifier_yaml)
	numPos, numNeg, numBak = requiredCounts

	pos_img_dir = classifier_yaml['dataset']['directory']['positive']
	bak_img_dir = classifier_yaml['dataset']['directory']['background']
	neg_img_dir = classifier_yaml['dataset']['directory']['negative']
	posSets = classifier_yaml['dataset']['description']['synsets']['pos']
	negSets = classifier_yaml['dataset']['description']['synsets']['neg']

	pos_image_files = sampleTrainingImages(pos_img_dir, posSets, numPos)
	bak_image_files = sampleTrainingImages(bak_img_dir, negSets, numBak)
	neg_image_files = sampleTrainingImages(neg_img_dir, negSets, numNeg)

	# Complain if there aren't enough images:
	there_are_too_few_images = False
	presentCounts = (len(pos_image_files), len(neg_image_files), len(bak_image_files))
	if any(map(lambda (p, r): p < r, zip(presentCounts, requiredCounts))):
		# raise ValueError('Not enough images!')
		raise TooFewImagesError(presentCounts, requiredCounts)

	# Create the output directory:
	if not os.path.isdir(output_dir):
		print '## Creating output directory: {}'.format(output_dir)
		os.makedirs(output_dir)
	else:
		print '## Using existing output directory: {}'.format(output_dir)

	# Load the global info file with bounding boxes for all positive images:
	# global_info_fname = 'info.dat'
	global_info = loadGlobalInfo()

	pos_info_fname = '{}/positive.txt'.format(output_dir)
	neg_info_fname = '{}/negative.txt'.format(output_dir)

	# Note: image paths in the data file have to be relative to the file itself.
	pos_info_fname_depth = len(pos_info_fname.split('/')) - 1
	info_entry_prefix = '../' * pos_info_fname_depth

	def write_img(img, dat_file):
		key = img.split('/')[-1]
		details = global_info[key]
		dat_file.write("{}{} {}".format(info_entry_prefix, img.strip('../'), details))

	# Write pos_image_files and bounding box info to pos_info_fname:
	with open('{}'.format(pos_info_fname), 'w') as dat_file:
		images = sorted(pos_image_files)
		write_img(images[0], dat_file)
		for img in images[1:]:
			# Use the bounding boxes from the global info file:
			dat_file.write("\n")
			write_img(img, dat_file)
		dat_file.flush()

	# Write neg_image_files to neg_info_fname:
	with open('{}'.format(neg_info_fname), 'w') as dat_file:
		images = sorted(bak_image_files + neg_image_files)
		dat_file.write("{}{}".format(info_entry_prefix, images[0].strip('../')))
		for img in images[1:]:
			dat_file.write("\n{}{}".format(info_entry_prefix, img.strip('../')))
		dat_file.flush()

def createSamples(classifier_yaml, output_dir):
	numPos, _, _ = requiredImageCounts(classifier_yaml)

	balls_vec_fname = '{}/balls.vec'.format(output_dir)
	pos_info_fname = '{}/positive.txt'.format(output_dir)

	samplesCommand = [ 'opencv_createsamples'
		, '-info', pos_info_fname
		, '-vec',  balls_vec_fname
		, '-num',  str(numPos)
		]
	cmd_ouptut = subprocess.check_output(samplesCommand, stderr=subprocess.STDOUT, cwd='.')
	with open('{}/output_create_samples.txt'.format(output_dir), 'w') as cmd_output_file:
		cmd_output_file.write(cmd_ouptut)
		cmd_output_file.flush()

# trainClassifier :: Tree String -> String -> IO ()
def trainClassifier(classifier_yaml, output_dir):
	traincascade_data_dir = '{}/data'.format(output_dir)
	if not os.path.isdir(traincascade_data_dir):
		print '## Creating training data directory: {}'.format(traincascade_data_dir)
		os.makedirs(traincascade_data_dir)
	else:
		print '## Using existing training data directory: {}'.format(traincascade_data_dir)

	numPos, numNeg, numBak = requiredImageCounts(classifier_yaml)
	balls_vec_fname = '{}/balls.vec'.format(output_dir)
	neg_info_fname = '{}/negative.txt'.format(output_dir)

	# From the opencv_traincascade documentation:
	#	-numPos <number_of_positive_samples>
	#	-numNeg <number_of_negative_samples>
	#		Number of positive/negative samples used in training for every classifier stage.
	# The key word being 'every'. We need to ensure that we don't ask for so
	# many samples that the last stages don't have enough.
	#
	# We'll use the formula derived on the following page to decide how many
	# samples to use, after solving for numPos:
	# 	http://answers.opencv.org/question/4368/
	# (the formula seems a little off to me - it seems like we should raise
	#  to the power of numStages rather than multiplying? The latter is more
	#  conservative though, so it shouldn't be a problem.)
	skipFrac = float(classifier_yaml['training']['boost']['skipFrac']) # A count of all the skipped samples from vec-file (for all stages).
	skippedSamples = numPos * skipFrac # A count of all the skipped samples from vec-file (for all stages).
	minHitRate = float(classifier_yaml['training']['boost']['minHitRate'])
	numStages = float(classifier_yaml['training']['basic']['numStages'])
	numPosTraining = int((numPos - skippedSamples) / (1 + (1 - minHitRate) * (numStages - 1)))
	# numPosTraining = int((numPos - skippedSamples) / (1 + (1 - minHitRate)**(numStages - 1))) # ??
	numNegTraining = (numNeg + numBak)

	trainingCommand = [ 'opencv_traincascade'
		, '-vec',               balls_vec_fname.split('/')[-1]
		, '-data',              'data'
		, '-bg',                neg_info_fname.split('/')[-1]
		, '-numPos',            str(numPosTraining)
		, '-numNeg',            str(numNegTraining)
		, '-numStages',         classifier_yaml['training']['basic']['numStages']
		, '-featureType',       classifier_yaml['training']['cascade']['featureType']
		, '-minHitRate',        classifier_yaml['training']['boost']['minHitRate']
		, '-maxFalseAlarmRate', classifier_yaml['training']['boost']['maxFalseAlarmRate']
		, '-weightTrimRate',    classifier_yaml['training']['boost']['weightTrimRate']
		, '-maxDepth',          classifier_yaml['training']['boost']['maxDepth']
		, '-maxWeakCount',      classifier_yaml['training']['boost']['maxWeakCount']
		]

	# TODO: Pipe ouptut to file, since this is a long running process.
	cmd_ouptut = subprocess.check_output(trainingCommand, stderr=subprocess.STDOUT, cwd='{}'.format(output_dir))
	with open('{}/output_training.txt'.format(output_dir), 'w') as cmd_output_file:
		cmd_output_file.write(cmd_ouptut)
		cmd_output_file.flush()

# runClassifier :: Tree String -> String -> IO ()
def runClassifier(classifier_yaml, output_dir):
	traincascade_data_dir = '{}/data'.format(output_dir)

	detections_fname = '{}/detections.dat'.format(output_dir)

	results_dir = '{}/results'.format(output_dir)
	results_dir_relative = '{}'.format(results_dir)
	if not os.path.isdir(results_dir_relative):
		print '\n## Creating results directory: {}'.format(results_dir_relative)
		os.makedirs(results_dir_relative)
	else:
		print '\n## Using existing results directory: {}'.format(results_dir_relative)

	runCommand = [ './opencv_runner/build/opencv_runner'
		, traincascade_data_dir + '/cascade.xml'
		, detections_fname
		, classifier_yaml['testing']['inputDir']
		, results_dir
		, 'false' # Do not save result images
		]
	cmd_ouptut = subprocess.check_output(runCommand, stderr=subprocess.STDOUT, cwd='.')
	with open('{}/output_run.txt'.format(output_dir), 'w') as cmd_output_file:
		cmd_output_file.write(cmd_ouptut)
		cmd_output_file.flush()


if __name__ == "__main__":
	random.seed(123454321) # Use deterministic samples.

	# Parse arguments:
	parser = argparse.ArgumentParser(description='Train classifier')
	parser.add_argument('classifier_yaml', type=str, nargs='?', default='../classifiers/classifier.yaml', help='Filename of the YAML file describing the classifier to train.')
	args = parser.parse_args()

	# Read classifier training file:
	classifier_yaml = loadYamlFile(args.classifier_yaml)
	output_dir = args.classifier_yaml.split('.yaml')[0]


	# TODO: Consider having preprocessTrial return a map of trial info:
	preprocessTrial(classifier_yaml, output_dir)

	createSamples(classifier_yaml, output_dir)

	print '\n## Training classifier...'

	trainClassifier(classifier_yaml, output_dir)

	print '\n## Running classifier...'

	runClassifier(classifier_yaml, output_dir)

	# print '\n## Calculating statistics...'
	#
	# global_info_fname = 'info.dat'
	#
	# # Note: Need to use the global data file because
	# #       pos_info_fname doesn't have bounding boxes for the test set.
	# statsCommand = [ 'python', 'detection_stats.py'
	# 	, detections_fname
	# 	, global_info_fname
	# 	]
	# subprocess.call(statsCommand, cwd='.')

	# # subprocess.check_output(['ls'], cwd=base_dir)
