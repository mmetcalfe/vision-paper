import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from operator import itemgetter

# results_table: [
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

def isHAAR(trial):
    return trial['featureType'] == 'HAAR'
def isHOG(trial):
    return trial['featureType'] == 'HOG'
def isLBP(trial):
    return trial['featureType'] == 'LBP'

def partitionOn(key, results):
    parts = {}
    for r in results:
        v = r[key]
        if v in parts:
            parts[v] += [r]
        else:
            parts[v] = [r]
    return parts

def plotResultsTable(results_table):

    font = {
    # 'family' : 'normal',
            # 'weight' : 'bold',
            'size'   : 22}

    matplotlib.rc('font', **font)
    matplotlib.rc('text', usetex=True)

    from matplotlib.font_manager import FontProperties
    smallFontP = FontProperties()
    smallFontP.set_size('small')

    # Varied the following:
    #   - number      (3)
    #   - hardNegFrac (2)
    #   - featureType (3)
    #   - skipFrac    (2)

    # haar_results = filter(isHAAR, results_table.values())
    # hog_results = filter(isHOG, results_table.values())
    # lbp_results = filter(isLBP, results_table.values())
    # parts = partitionOn('skipFrac', lbp_results)

    # womenMeans = (25, 32, 34, 20, 25)
    # womenStd =   (3, 5, 2, 3, 3)
    # rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)

    series_parts = partitionOn('featureType', results_table.values())

    ind_parts = partitionOn('hardNegFrac', results_table.values())
    ind_labels = map(lambda s: '{:2d}'.format(int(round(100*float(s)))), sorted(ind_parts.keys()))

    N = len(ind_parts.keys())
    ind = np.arange(N)  # the x locations for the groups
    width = 0.4         # the width of the bars

    series_cols = ['#fc8d59', '#ffffbf', '#91bfdb']

    for value_key in ['precision', 'recall']:
        fig, ax = plt.subplots()

        plt.rc('text', usetex=True)
        plt.rc('font', family='serif')

        def autolabel(rects):
            # attach some text labels
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x()+rect.get_width()/2., height + width*0.025, '{:.1f}'.format(float(height)),
                        ha='center', va='bottom',
                        fontsize=7)
                        # fontsize=13)

        series_x_offset = 0
        # series_x_offset = -width*0.5
        series_num = 0
        part_rects_dict = {}
        for part_key in sorted(series_parts.keys()):
            series = series_parts[part_key]
            trials = series
            # trials = filter(lambda t:
            #     float(t['number'])==1000 and
            #     # float(t['skipFrac'])==0.1
            #     , series)
            sorted_trials = sorted(trials, key=lambda x: float(x['hardNegFrac']))
            values = map(itemgetter(value_key), sorted_trials)
            values = map(lambda v: 0 if v is None else v, values) # TODO: Handle missing values!
            values = map(lambda v: 100*v, values) # convert to percentages
            print values
            series_rects = ax.bar(ind + series_x_offset, values, width, color=series_cols[series_num])
            series_x_offset += width
            series_num += 1
            autolabel(series_rects)
            part_rects_dict[part_key] = series_rects

        # add some text for labels, title and axes ticks
        # ax.set_title('Precision by feature type')
        ax.set_ylabel('{} (\%)'.format(value_key.capitalize()))
        ax.set_xlabel('Hard Neg. \%')
        ax.set_xticks(ind+width)
        ax.set_xticklabels(ind_labels)

        sorted_part_keys = sorted(part_rects_dict.keys())

        # # Shrink current axis's height by 10% on the bottom
        # box = ax.get_position()
        # shrinkf = 0.8
        # ax.set_position([box.x0, box.y0,# + box.height * (1.0-shrinkf),
        #                  box.width, box.height * shrinkf])

        ax.legend([part_rects_dict[key] for key in sorted_part_keys]
        , sorted_part_keys
        , ncol=3
        , prop=smallFontP
        , loc='upper center'
        , bbox_to_anchor=(0.5, 1.15))
        #           fancybox=True)

        # plt.show()
        plt.savefig('results_fig_{}.pdf'.format(value_key), bbox_inches='tight')
