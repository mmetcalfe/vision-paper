import random
import glob
import os

random.seed(0xBAD5EED) # For repeatability.

### Dry run:
# mitchell-laptop:code mitchell$ python extract_test_set.py.py
# ## Creating test set directory: samples/positive_test_set/
# sample_set_size:  4869 test_set_size:  974
# ## Creating test set directory: samples/hard_negative_test_set/
# sample_set_size:  3523 test_set_size:  705
# ## Creating test set directory: samples/background_test_set/
# sample_set_size:  33875 test_set_size:  6775


sample_fraction = 0.2
sample_dirs = [
    'samples/positive/',
    # 'samples/hard_negative/',
    # 'samples/background/'
    ]

for sample_dir in sample_dirs:

    sample_set = glob.glob("{}/*".format(sample_dir))

    test_set_size = int(round(sample_fraction * len(sample_set)))

    test_set = random.sample(sample_set, test_set_size)

    test_set_dir = '{}_test_set/'.format(sample_dir.rstrip('/'))
    if not os.path.isdir(test_set_dir):
        print '## Creating test set directory: {}'.format(test_set_dir)
        os.makedirs(test_set_dir)
    else:
        print '## Using existing test set directory: {}'.format(test_set_dir)

    print 'sample_set_size: ', len(sample_set), 'test_set_size: ', len(test_set)

    for img in test_set:
        new_path = '{}/{}'.format(test_set_dir, img.lstrip(sample_dir))
        # print img, new_path
        # os.rename(img, new_path)
