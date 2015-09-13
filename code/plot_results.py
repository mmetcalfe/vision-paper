import numpy as np
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
    ind_labels = sorted(ind_parts.keys())

    N = len(ind_parts.keys())
    ind = np.arange(N)  # the x locations for the groups
    width = 0.2         # the width of the bars

    series_cols = ['#fc8d59', '#ffffbf', '#91bfdb']

    fig, ax = plt.subplots()

    def autolabel(rects):
        # attach some text labels
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x()+rect.get_width()/2., height + width*0.1, '%d'%int(height),
                    ha='center', va='bottom')

    series_x_offset = 0
    series_num = 0
    for key in series_parts:
        series = series_parts[key]
        trials = filter(lambda t:
            float(t['number'])==3000 and
            float(t['skipFrac'])==0.1
            , series)
        sorted_trials = sorted(trials, key=lambda x: float(x['hardNegFrac']))
        values = map(itemgetter('recall'), sorted_trials)
        # TODO: Handle missing values!
        values = map(lambda v: 0 if v is None else v, values)
        print values
        series_rects = ax.bar(ind + series_x_offset, values, width, color=series_cols[series_num])
        series_x_offset += width
        series_num += 1
        autolabel(series_rects)

    # add some text for labels, title and axes ticks
    ax.set_title('Precision by feature type')
    ax.set_ylabel('Precision (%)')
    ax.set_xticks(ind+width)
    ax.set_xticklabels(ind_labels)


    # ax.legend( (rects1[0], rects2[0]), ('Men', 'Women') )

    # plt.show()
    plt.savefig('results_fig.pdf', bbox_inches='tight')
