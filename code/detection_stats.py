from PIL import Image
import os.path
import argparse
import math

# MAX_BB_CORNER_DISTANCE = 50

# From: http://stackoverflow.com/a/312464
# chunks :: [Int] -> [[Int]]
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

# Read a bounding box data file:
# readDataFile :: String -> Map String [[Int]]
def readDataFile(file_name):
	data = {}
	with open(file_name, 'r') as dat_file:
		for line in dat_file.readlines():
			parts = line.strip().partition(' ')
			image_path = parts[0]
			image_name = image_path.split('/')[-1]
			num, unused_, objs_str = parts[2].partition(' ')

			objs = []
			if int(num) > 0:
				objs = list(chunks(map(int, objs_str.split(' ')), 4))

			objs = map(tuple, objs)

			data[image_name] = objs
	return data

# corners :: [Int] -> [(Int, Int)]
def corners(obj):
	x = obj[0]
	y = obj[1]
	w = obj[2]
	h = obj[3]
	return [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]

# sqrDist :: (Int, Int) -> (Int, Int) -> Float
def sqrDist(p1, p2):
	return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

# # isNear :: (Int, Int) -> Int -> (Int, Int) -> Bool
# def isNear(p1, p2):
# 	return sqrDist(p1, p2) < MAX_BB_CORNER_DISTANCE^2

# # isDetection :: [Int] -> [Int] -> Bool
# def isDetection(obj, actual):
# 	c_obj = corners(obj)
# 	c_act = corners(actual)
# 	return all(map(lambda (c1, c2): isNear(c1, c2), zip(c_obj, c_act)))

# isDetection :: [Int] -> [Int] -> Bool
def isDetection(obj, actual):
	obj_radius = (obj[2] + obj[3]) / 2
	act_radius = (actual[2] + actual[3]) / 2

	radius_diff = abs(obj_radius - act_radius)
	radius_rel_error = radius_diff / act_radius

	obj_centre = (obj[0], obj[1])
	act_centre = (actual[0], actual[1])

	centre_error = math.sqrt(sqrDist(obj_centre, act_centre))
	rel_centre_error = centre_error / act_radius

    # TODO: Document the criteria for a valid detection.
	return radius_rel_error < 0.2 and rel_centre_error < 0.1


# Start script:
def str2bool(s):
	return s in ['true', 'True', 't', 'T']

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

def loadCachedBB(bbinfo_cache, img_name):
    if not img_name in bbinfo_cache:
        return None
    cached_str = bbinfo_cache[img_name]


# calculateDetectionStats :: String -> Map String [[Int]] -> Bool -> (Double, Double)
def calculateDetectionStats(detections_dat, bbinfo_cache):
    # Process detections file:
    detections = readDataFile(detections_dat)

    total_objects = 0
    total_hit_count = 0
    total_detections = 0

    for key in detections:
        detected_objs = detections[key]

        obj_detection_counts = {}
        for a in actual_objs:
            obj_detection_counts[a] = 0

        num_objects = len(actual_objs) + 0.0
        total_objects += num_objects
        total_detections += len(detected_objs) + 0.0
        total_hit_count += 1

    recall_str = "recall: Inf"
    if total_objects != 0:
        recall = total_hit_count / total_objects
        recall_str = "recall: {:9.5f}".format(recall)

    precision = total_hit_count / total_detections
    precision_str = "precision: {:9.5f}".format(precision)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate detection statistics')
    parser.add_argument('trials_dir', type=str, nargs='?', default='trials', help='File containing image and bounding-box information')

    args = parser.parse_args()

	trial_files = glob.glob("{}/trial_*.yaml".format(args.trials_dir))

    bbinfo_cache = loadGlobalInfo('*')

    # Run calculateStats on each detections file:
    for trial_yaml in trial_files:
        trial_dir = trial_yaml.strip('.yaml')
        detections_files = glob.glob("{}/*detections.dat".format(trial_dir))

        trial_results = {}
        for det_file in detections_files:
            trial_stats = calculateDetectionStats(det_file, bbinfo_cache)
            trial_results[det_file] = trial_stats

        calculateDetectionStats()

    # Save result as csv:
    # i.e. a row of headers, followed by rows of data.

    # Use matplotlib to plot the data:
