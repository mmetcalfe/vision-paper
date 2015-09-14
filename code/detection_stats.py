from PIL import Image
import os.path
import argparse
import math
import glob

from train_classifier import loadYamlFile

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
#     return sqrDist(p1, p2) < MAX_BB_CORNER_DISTANCE^2

# # isDetection :: [Int] -> [Int] -> Bool
# def isDetection(obj, actual):
#     c_obj = corners(obj)
#     c_act = corners(actual)
#     return all(map(lambda (c1, c2): isNear(c1, c2), zip(c_obj, c_act)))

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
    img_id = '_'.join(img_name.split('/')[-1].split('_')[0:2]).strip('.jpg').strip('.thumbnail')
    query_str = 'n' + img_id.strip('n') + '.jpg'
    # print img_name, query_str
    if not query_str in bbinfo_cache:
        return (0, [])
    cached_str = bbinfo_cache[query_str]
    values = map(int, cached_str.split(' '))
    return (values[0], values[1:])

# calculateDetectionStats :: String -> Map String [[Int]] -> Bool -> (Double, Double)
def calculateDetectionStats(detections_dat, bbinfo_cache):
    # Process detections file:
    detections = readDataFile(detections_dat)

    total_objects    = 0
    total_detections = 0
    total_hit_count  = 0

    for key in detections:
        detected_objs = detections[key]

        bboxes = loadCachedBB(bbinfo_cache, key)
        img_contains_obj = bboxes[0] != 0
        obj_was_detected = len(detected_objs) != 0

        if img_contains_obj:
            total_objects += 1
        if obj_was_detected:
            total_detections += 1
        if img_contains_obj and obj_was_detected:
            total_hit_count += 1

    precision = recall = None
    if total_objects != 0:
        recall = total_hit_count / float(total_objects)

    if total_detections != 0:
        precision = total_hit_count / float(total_detections)

    # return (total_objects, total_detections)
    # return (precision, recall)
    return {
        'objects' : total_objects,
        'detections' : total_detections,
        'hit_count' : total_hit_count,
    }
    # recall_str = "recall: {:9.5f}".format(recall)
    # precision_str = "precision: {:9.5f}".format(precision)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate detection statistics')
    parser.add_argument('trials_dir', type=str, nargs='?', default='trials', help='File containing image and bounding-box information.')
    parser.add_argument('results_tsv', type=str, nargs='?', default='results.tsv', help='Output file name.')

    args = parser.parse_args()

    trial_files = glob.glob("{}/trial_*.yaml".format(args.trials_dir))

    bbinfo_cache = loadGlobalInfo('positive_info_dwsi')

    # Run calculateStats on each detections file:
    results_table = {}
    for trial_yaml in trial_files:
        # Add trial info to the result:
        trial_data = loadYamlFile(trial_yaml)
        trial_results = {}
        trial_results['number'] = trial_data['dataset']['description']['number']
        trial_results['posFrac'] = trial_data['dataset']['description']['posFrac']
        trial_results['hardNegFrac'] = trial_data['dataset']['description']['hardNegFrac']
        trial_results['featureType'] = trial_data['training']['cascade']['featureType']
        # trial_results['skipFrac'] = trial_data['training']['boost']['skipFrac']

        # Initialise trial totals:
        trial_totals = {}
        trial_totals['objects'] = 0
        trial_totals['detections'] = 0
        trial_totals['hit_count'] = 0

        # Calculate results per test set:
        trial_dir = trial_yaml.strip('.yaml')
        detections_files = glob.glob("{}/*detections.dat".format(trial_dir))
        # detections_files = [trial_dir + '/hard_negative_test_set_detections.dat']
        for det_file in detections_files:
            if det_file == (trial_dir + '/positive_test_set_detections.dat'):
                continue
            test_set_name = det_file.split('/')[-1].rstrip('detections.dat').rstrip('_')
            trial_stats = calculateDetectionStats(det_file, bbinfo_cache)

            for stat in trial_stats:
                trial_results['{}_{}'.format(test_set_name, stat)] = trial_stats[stat]
                trial_totals[stat] += trial_stats[stat]
            # trial_results[test_set_name] = trial_stats

        # Calculate additional stats from totals:
        trial_results['precision'] = trial_results['recall'] = None
        if trial_totals['objects'] != 0:
            trial_results['recall'] = trial_totals['hit_count'] / float(trial_totals['objects'])
        if trial_totals['detections'] != 0:
            trial_results['precision'] = trial_totals['hit_count'] / float(trial_totals['detections'])

        # Add the trial to the results table:
        results_table[trial_yaml] = trial_results

    # trials: [
    #     trial_result: {
    #         trial_name: 'sdfdsf'
    #         skipFrac: 0.66,
    #         posFrac: 0.5,
    #         ...
    #         positive_test_set: {
    #             objects: 32,
    #             detections: 32,
    #             hit_count: 32,
    #         }
    #         neg_test_set: {
    #             ...
    #         }
    #     }
    # ]

    # Save result as tsv:
    # i.e. a row of headers, followed by rows of data.
    with open(args.results_tsv, 'w+') as results_file:
        col_names = sorted(results_table.values()[0].keys())
        header_row = '\t'.join(col_names)

        results_file.write(header_row + '\n')

        for fname, result in results_table.iteritems():
            row_raw = map(lambda n: result[n], col_names)
            row_raw = map(lambda n: '' if n is None else n, row_raw)
            row_str = '\t'.join(map(str, row_raw))
            results_file.write(row_str + '\n')


    # Use matplotlib to plot the data:
    from plot_results import plotResultsTable
    plotResultsTable(results_table)
