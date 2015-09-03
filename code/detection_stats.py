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

	return radius_rel_error < 0.2 and rel_centre_error < 0.1


# Start script:
def str2bool(s):
	return s in ['true', 'True', 't', 'T']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ImageNet Gatherer')
    parser.add_argument('detections_dat', type=str, nargs='?', default='../images/tests/detections.dat', help='File containing image and bounding-box information')
    parser.add_argument('info_dat', type=str, nargs='?', default='info.dat', help='File containing image and bounding-box information')
    parser.add_argument('full_results', type=str2bool, nargs='?', default=True, help='Whether to output results or each image, or just a summary.')

    args = parser.parse_args()

    output_lines = []

    if args.full_results:
    	print 'detections_dat: {}'.format(args.detections_dat)
    	print 'info_dat: {}'.format(args.info_dat)
    	output_lines += ['detections_dat: {}'.format(args.detections_dat)]
    	output_lines += ['info_dat: {}'.format(args.info_dat)]

    detections = readDataFile(args.detections_dat)
    info = readDataFile(args.info_dat)

    total_objects = 0
    total_hit_count = 0
    total_detections = 0

    for key in detections:
    	detected_objs = detections[key]
    	actual_objs = info[key]

    	obj_detection_counts = {}
    	for a in actual_objs:
    		obj_detection_counts[a] = 0

    	num_objects = len(actual_objs) + 0.0
    	total_objects += num_objects
    	total_detections += len(detected_objs) + 0.0

    	num_fp = 0
    	num_tp = 0
    	for d in detected_objs:
    		tp = False
    		for a in actual_objs:
    			if isDetection(d, a):
    				obj_detection_counts[a] += 1
    				num_tp += 1
    				tp = True
    		if not tp:
    			num_fp += 1

    	for a in actual_objs:
    		if obj_detection_counts[a] > 0:
    			total_hit_count += 1

    	num_detected = len(detected_objs) + 0.0
    	if args.full_results:
    		if num_detected > 0:
    			str = "img: {:19}, tp: {:6.2f}, fp: {:6.2f}, tp%: {:4.2f}".format(key, num_tp, num_fp, num_tp / num_detected)
    			print str; output_lines += [str];
    		else:
    			str = "img: {:19}, tp: {:6.2f}, fp: {:6.2f}".format(key, num_tp, num_fp)
    			print str; output_lines += [str];

    recall_str = "recall: Inf"
    if total_objects != 0:
    	recall = total_hit_count / total_objects
    	recall_str = "recall: {:9.5f}".format(recall)


    precision = total_hit_count / total_detections
    precision_str = "precision: {:9.5f}".format(precision)

    if args.full_results:
    	print recall_str; output_lines += [recall_str];
    	print precision_str; output_lines += [precision_str];
    else:
    	str = '{:15}, {}, {}'.format(args.detections_dat, precision_str, recall_str)
    	print str; output_lines += [str];

    results_file_name = '/'.join(args.detections_dat.split('/')[:-1]) + '/results.txt'
    with open(results_file_name, 'w') as dat_file:
    	dat_file.write('{}\n'.format(output_lines[-1]))
    	for line in output_lines:
    		dat_file.write('{}\n'.format(line))
    	dat_file.flush()
