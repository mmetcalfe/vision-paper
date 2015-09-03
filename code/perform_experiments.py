#
# perform_experiments.py
#
#    This script performs the entire data collection process for this project.
#    It generates trials, runs them, collates the data into a convenient format
#    for analysis, then outputs charts ready for a paper.
#

import argparse
import subprocess
import glob
import sys
import random
from concurrent import futures

if __name__ == "__main__":
    random.seed(123454321) # Use deterministic samples.

    # Parse arguments:
    parser = argparse.ArgumentParser(description='Perform experiments')
    parser.add_argument('template_yaml', type=str, nargs='?', default='template.yaml', help='Filename of the YAML file describing the trials to generate.')
    parser.add_argument('output_dir', type=str, nargs='?', default='trials', help='Directory in which to output the generated trials.')
    args = parser.parse_args()

    print '===== GENERATE TRIALS ====='
    from generate_trials import generateTrials
    generateTrials(args.template_yaml, args.output_dir)


    print '===== PREPROCESS TRIALS ====='
    from train_classifier import loadYamlFile
    from train_classifier import preprocessTrial
    from train_classifier import TooFewImagesError

    preprocessing_was_successful = True
    maxImageCountDiff = (0, 0, 0)

    trial_files = glob.glob("{}/*.yaml".format(args.output_dir))
    for trial_yaml in trial_files:
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

    # TODO: Use GNU Parallel to run training of classifiers simultaneously.
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_results = dict((executor.submit(doTraining, fname), fname) for fname in trial_files)

        for future in futures.as_completed(future_results):
            fname = future_results[future]
            if future.exception() is not None:
                print '{} generated an exception: {}'.format(fname, future.exception())
            else:
                print '{} completed training successfully'.format(fname)


    # TODO: Scan output files for possible errors.
    # (check for bad words: 'cannot', 'error', 'not', 'fail')

    print '===== RUN CLASSIFIERS ====='
    from train_classifier import runClassifier

    # TODO: Parallelise this code.
    for trial_yaml in trial_files:
        # Read classifier training file:
        classifier_yaml = loadYamlFile(trial_yaml)
        output_dir = trial_yaml.split('.yaml')[0]

        runClassifier(classifier_yaml, output_dir)


    print '===== COLLECT RESULTS ====='
