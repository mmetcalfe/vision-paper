#
# perform_experiments.py
#
#	This script performs the entire data collection process for this project.
#	It generates trials, runs them, collates the data into a convenient format
#	for analysis, then outputs charts ready for a paper.
#

import argparse
import subprocess
import glob
import sys
import os
import re
import random
import math
from concurrent import futures

from train_classifier import loadYamlFile

NUM_THREADS = 6

def loadBbinfo(cache_name):
	cache = {}
	cache_files = glob.glob("bbinfo/{}__*.dat".format(cache_name))
	for cache_file_name in cache_files:
		with open(cache_file_name, 'r+') as cache_file:
			infoLines = map(lambda l: l.strip(), cache_file.readlines())
			for bbinfo in infoLines:
				lst = bbinfo.split(' ')
				cache[lst[0]] = ' '.join(lst[1:])
	return cache

def getEllipseBoundingBox(ellipse):
	rw = float(ellipse['size'][0])
	rh = float(ellipse['size'][1])
	r = float(ellipse['rotate'])
	px = float(ellipse['translate'][0])
	py = float(ellipse['translate'][1])

	# hw = abs(rw*math.sin(r))+abs(rh*math.cos(r))
	# hh = abs(rw*math.cos(r))+abs(rh*math.sin(r))

	def yOfX(x):
		return (x, math.sqrt(rh*rh*(1 - x*x/(rw*rw))))
	def trans(p):
		x, y = p
		tx = x*math.cos(r)-y*math.sin(r)
		ty = x*math.sin(r)+y*math.cos(r)
		return (tx, ty)
	def frange(b, e, n):
		return [b + (float(i)/n) * (e-b) for i in range(0, n+1)]


	numpts = 10
	quadrant_pts = map(yOfX, frange(0, rw, numpts))
	sample_pts = quadrant_pts + map(lambda (x, y): (x, -y), quadrant_pts)
	pts_trans = map(trans, sample_pts)

	# print pts_trans
	hw = max(map(lambda (x, y): abs(x), pts_trans))
	hh = max(map(lambda (x, y): abs(y), pts_trans))

	print (rw, rh), (hw,hh)

	return [int(round(px - hw)), int(round(py - hh)), int(round(hw*2)), int(round(hh*2))]

def findEllipsesInImage(img, bbox_file_name):
	# Inputs: img, bbox_file_name
	print 'IMG: {}'.format(img)
	# Convert the image to PGM using ImageMagick:
	try:
		img_pgm = '{}.pgm'.format(img)
		convert_command = [ 'convert', img, img_pgm ]
		cmd_ouptut = subprocess.check_output(convert_command, stderr=subprocess.STDOUT, cwd='.')
		print '>> {}'.format(' '.join(convert_command))
		print 'output: {}'.format(cmd_ouptut)
	except subprocess.CalledProcessError as e:
		print 'ERROR:'
		print '\te.returncode: {}'.format(e.returncode)
		print '\te.cmd: {}'.format(e.cmd)
		print '\te.output: {}'.format(e.output)
		if re.compile('.*Empty input file.*').match(e.output):
			print 'Deleting bad image: {}'.format(img)
			os.remove(img)
		return

	# Run ELSD on the image to detect ellipses:
	# ELSD is from: http://ubee.enseeiht.fr/vision/ELSD/
	ellipses_file = '{}.ellipses.txt'.format(img_pgm)
	elsd_command = [ 'circle_detector/elsd_1.0/elsd', img_pgm,  ellipses_file]
	cmd_ouptut = subprocess.check_output(elsd_command, stderr=subprocess.STDOUT, cwd='.')
	print cmd_ouptut

	# Convert ouptut from the ellipses.txt file into bounding boxes:
	bounding_boxes = []
	ellipses_yaml = loadYamlFile(ellipses_file)

	if ellipses_yaml is not None:
		for ellipse in ellipses_yaml:
			bb = getEllipseBoundingBox(ellipse)
			bounding_boxes += [bb]

		# Write the bounding boxes to a data file:
		with open(bbox_file_name, 'a+') as bbfile:
			line = '{} {} {}\n'.format(img, len(bounding_boxes), ' '.join(map(lambda bb: ' '.join(map(str, bb)),bounding_boxes)))
			bbfile.write(line)

	# Delete the PGM image and the ellipses.txt file:
	os.remove(img_pgm)
	img_svg = '{}.svg'.format(img_pgm)
	if os.path.exists(img_svg):
		os.remove(img_svg)
	os.remove(ellipses_file)

if __name__ == "__main__":
	random.seed(123454321) # Use deterministic samples.

	# Parse arguments:
	parser = argparse.ArgumentParser(description='Perform experiments')
	parser.add_argument('template_yaml', type=str, nargs='?', default='template.yaml', help='Filename of the YAML file describing the trials to generate.')
	parser.add_argument('output_dir', type=str, nargs='?', default='trials', help='Directory in which to output the generated trials.')
	args = parser.parse_args()

	# print '===== PREPROCESS NEGATIVE IMAGES ====='
	# print '	Create hard negative images by detecting ellipses in negative\n	images, then cropping them to thumbnails.'
	#
	# # bbox_file_name = 'samples/negative_unlabelled_info.dat'
	# neg_image_dir = 'samples/negative_unlabelled'
	# all_neg_images = glob.glob("{}/n*_*.*".format(neg_image_dir))
	# filter_pgm_prog = re.compile('{}/n\d*_\d*\.(pgm|svg)'.format(neg_image_dir))
	# filter_ext_prog = re.compile('{}/n\d*_\d*\.jpg'.format(neg_image_dir))
	# neg_images = filter(lambda x: filter_ext_prog.match(x) and not filter_pgm_prog.match(x), all_neg_images)
	# # for img in neg_images:
	# #	 findEllipsesInImage(img, bbox_file_name)
	#
	# # Load cache:
	# bbinfo_cache = loadBbinfo('negative_unlabelled_info')
	#
	# # Split neg_images into 8 parts:
	# numThreads = 8
	# neg_img_lists = [[] for i in range(numThreads)]
	# for i in range(len(neg_images)):
	# 	k = i % numThreads
	# 	neg_img_lists[k] += [neg_images[i]]
	#
	# def findEllipsesThread(img_list):
	# 	bbfn = 'bbinfo/negative_unlabelled_info__{}.dat'.format(random.randint(1000, 9999))
	# 	for img in img_list:
	# 		if img in bbinfo_cache:
	# 			print 'Skipping cached image: {}.'.format(img)
	# 			continue
	# 		findEllipsesInImage(img, bbfn)
	#
	# # with futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
	# # 	# Build set of futures:
	# # 	future_results = {}
	# # 	for img_list in neg_img_lists:
	# # 		future = executor.submit(findEllipsesThread, img_list)
	# # 		# future_results[future] = img_list
	# #
	# # 	for future in futures.as_completed(future_results):
	# # 		# search_word = future_results[future]
	# # 		if future.exception() is not None:
	# # 			print 'AN EXCEPTION OCCURRED: {}'.format(future.exception())
	# # 		else:
	# # 			print 'ELLIPSES FOR LIST CHUNK COMPLETE.'
	#
	# #
	# # # Use the bounding box data file to save cropped thumbnails of all ellipses:
	# # from extract_object_windows import extractObjectWindows
	# # for info_file in glob.glob('bbinfo/negative_unlabelled_info__*.dat'):
	# # 	print 'Processing info file:', info_file
	# # 	extractObjectWindows(info_file, (24, 24), 'samples/hard_negative')
	# # for info_file in glob.glob('bbinfo/info_dwsi__*.dat'):
	# # 	print 'Processing info file:', info_file
	# # 	extractObjectWindows(info_file, (24, 24), 'samples/hard_negative')
	#

	print '===== GENERATE TRIALS ====='
	from generate_trials import generateTrials
	generateTrials(args.template_yaml, args.output_dir)

	trial_files = glob.glob("{}/*.yaml".format(args.output_dir))

	print '===== PREPROCESS TRIALS ====='
	from train_classifier import preprocessTrial
	from train_classifier import TooFewImagesError

	preprocessing_was_successful = True
	maxImageCountDiff = (0, 0, 0)

	for trial_yaml in trial_files:
		print '    Preprocessing: {}'.format(trial_yaml)
		# Read classifier training file:
		classifier_yaml = loadYamlFile(trial_yaml)
		output_dir = trial_yaml.split('.yaml')[0]

		# Preprocess the trial:
		try:
			preprocessTrial(classifier_yaml, output_dir)
		except TooFewImagesError as e:
			preprocessing_was_successful = False
			print e
			imgCountDiff = map(lambda (p, r): r - p, zip(e.presentCounts, e.requiredCounts))
			maxImageCountDiff = map(lambda (m, c): max(m, c), zip(maxImageCountDiff, imgCountDiff))

	if not preprocessing_was_successful:
		print '\nNOT ENOUGH IMAGES! TRAINING CANCELLED!'
		print 'maxImageCountDiff: {}'.format(maxImageCountDiff)
		sys.exit(1)


	print '===== CREATE SAMPLES ====='
	from train_classifier import createSamples

	for trial_yaml in trial_files:
		print '    Creating samples for: {}'.format(trial_yaml)

		# Read classifier training file:
		classifier_yaml = loadYamlFile(trial_yaml)
		output_dir = trial_yaml.split('.yaml')[0]

		createSamples(classifier_yaml, output_dir)


	print '===== TRAIN CLASSIFIERS ====='
	from train_classifier import trainClassifier

	def doTraining(fname):
		# Read classifier training file:
		classifier_yaml = loadYamlFile(fname)
		output_dir = fname.split('.yaml')[0]
		trainClassifier(classifier_yaml, output_dir)

	with futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
		future_results = dict((executor.submit(doTraining, fname), fname) for fname in trial_files)

		for future in futures.as_completed(future_results):
			fname = future_results[future]
			if future.exception() is not None:
				print '{} generated an exception: {}'.format(fname, future.exception())
			else:
				print '{} completed training successfully'.format(fname)


	# # TODO: Scan output files for possible errors.
	# # (check for bad words: 'cannot', 'error', 'not', 'fail')

	print '===== RUN CLASSIFIERS ====='
	from train_classifier import runClassifier

	# # TODO: Parallelise this code.
	# for trial_yaml in trial_files:
	# 	# Read classifier training file:
	# 	classifier_yaml = loadYamlFile(trial_yaml)
	# 	output_dir = trial_yaml.split('.yaml')[0]
	#
	# 	runClassifier(classifier_yaml, output_dir)

	def doRunning(trial_yaml):
		# Read classifier training file:
		classifier_yaml = loadYamlFile(trial_yaml)
		output_dir = trial_yaml.split('.yaml')[0]
		runClassifier(classifier_yaml, output_dir)

	with futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
		future_results = dict((executor.submit(doRunning, fname), fname) for fname in trial_files)

		for future in futures.as_completed(future_results):
			fname = future_results[future]
			if future.exception() is not None:
				print '{} generated an exception: {}'.format(fname, future.exception())
			else:
				print '{} completed running successfully'.format(fname)


	print '===== COLLECT RESULTS ====='
