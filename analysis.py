from collections import defaultdict as dd
from utils import fetch_data
from scipy.stats import boxcox, norm
from scipy.special import inv_boxcox
from itertools import groupby
import numpy as np
import warnings
warnings.filterwarnings('ignore') # Comment this out to see warnings

TA_MEAN   = 34    # Change this to be in line with the current assignment
TA_STDEV  = 3.5  # Change this if you think it should be different for the current assignment
TA_LAMBDA = 3.45  # Don't change this unless you know what you're doing -
                  # requires determining the lambda parameter for Box-Cox transformation

ASSIGNMENT = 'project 1' # Which assignment to run the analysis on. Only
                         # pertains to analyze_spreadsheet function
OVERWRITE = True # Only need to set to true for the first run of this script
                 # if you're previously downloaded (an old version of) the data
'''
-------------------------
-- Future Improvements --
-------------------------
- If a student's score is, say, three low scores - but the papers
they graded were terrible, adjusting their average score to
the TA average will skew the bad papers' grades. Need to adjust
their score in relation to the rank/adjusted score, then recalculate
the scores. So a two-pass in other words? Or switch to ranking system,
or perhaps generalizing the two-pass: n-pass until scores stabilize
i.e. a simulated annealing type approach -> energy defined as distance
    of everyone from their respective average score, given the current
    weighted scores

- add in boolean flag to spreadsheet to check if ta score differs by more than a stdev
- confidence metric for each score
- add a 'pressure' away from the average to expand grades to the tails
- better skewness / kurtosis transform

'''

def ensure_matrix(function):
    ''' Ensure all args to a function are a numpy array '''
    def check(*args):
        args = list(args)
        for i in range(len(args)):
            if type(args[i]) is not np.ndarray:
                args[i] = np.array(args[i])
        return function(*args)
    return check


@ensure_matrix
def distribution_stats(data):
    ''' Gather statistics on a data set '''
    mean  = data.mean()             # Mean - first moment
    stdev = data.std()              # Standard deviation - sqrt second moment
    norm  = (data - mean) / stdev   # Normalized data
    skew  = (norm ** 3).mean()      # Fisher Skewness - third moment
    kurt  = (norm ** 4).mean() - 3  # Fisher Kurtosis - fourth moment

    print('Mean & stdev: %.2f & %.2f' % (mean, stdev))
    print('Skewness & kurtosis: %.2f & %.2f' % (skew, kurt))
    return mean, stdev, skew, kurt


@ensure_matrix
def normalize_align(to_align, data):
    ''' Normalize <to_align> by changing mean/std to 0/1,
        then align to <data>'s mean/std '''
    mean, std = to_align.mean(), to_align.std()
    normalized = (to_align - mean) / (std if std else 1)
    return normalized * data.std() + data.mean()


@ensure_matrix
def ks_align(to_align, data):
    ''' Align (somewhat) the skewness and kurtosis of <to_align> to <data>
        Currently uses Box-Cox / inverse to align to a normal distribution
        then align to <data>. Another potential method with similar results
        is the sinh-arcsinh transform, but need to solve for delta & epsilon
    '''
    # Box-Cox transform
    with warnings.catch_warnings(): # randomly (it seems) throws invalid value warnings
        warnings.simplefilter('ignore')
        data[data == 0] = data.mean() # Cannot have 0 score
        _, lambda_ = boxcox(data) #3.926 for assign1, 3.256 proj1
        normal, _  = boxcox(to_align)
        transform  = inv_boxcox(normal, lambda_)
        return normalize_align(transform, data)

    # Sinh-Arcsinh transform
    # Need to solve for the correct delta & epsilon which compose <data>
    # transform = np.sinh( delta * np.arcsinh(to_align) - epsilon)
    # return normalize_align(transform, data)

    # Another suggestion for sinh-arcsinh here: http://stats.stackexchange.com/questions/43482/transformation-to-increase-kurtosis-and-skewness-of-normal-r-v
    #   transform = delta * arcsinh(x) - epsilon
    #   N(transform) * delta * cosh(transform) / (1+x**2) ** .5
    # where N is a normal distribution function. Untested


def get_student_scores(entry):
    ''' Return all student scores in an entry if they are valid (not None/0) '''
    key = 'student_score_%i'
    return [entry[key%i] for i in range(1,5) if entry[key%i]]


def analyze_spreadsheet(assignment):
    ''' Analyze an assignment's scores after TA grading is completed '''
    from glob import glob
    from scipy.stats import ks_2samp
    import matplotlib.pyplot as plt
    import matplotlib.mlab   as mlab

    for folder in glob('./assignments/*/'):
        if assignment.lower() in folder.lower():
            folder = folder.replace('\\','/')
            assignment = folder.split('/')[1]
            break

    data = fetch_data(assignment, overwrite=OVERWRITE)
    exclude =[]
    data = [d for d in data if d['TA Name (First and Last)'] not in exclude and d['TA Score']]
    TAs = sorted(set([d['TA Name (First and Last)'] for d in data]))
    print('Number of grading TAs: %i' % len(TAs))

    st_scores = [d[k] for d in data for k in d if d[k] and 'score' in k]
    print('\nStudent Statistics:')
    st_mean, st_stdev, st_skew, st_kurt = distribution_stats(st_scores)

    ta_scores = [d['TA Score'] for d in data]
    if not any(ta_scores):
        print('Remaining analysis can\'t be completed without TA scores.')
        return

    print('\nTA Statistics:')
    ta_mean, ta_stdev, ta_skew, ta_kurt = distribution_stats(ta_scores)

    indexed_scores = [(i, d[k] if d[k] else ta_mean) for i,d in enumerate(data) for k in ['student_score_%i' % j for j in range(1,5)] if k in d and d[k] is not None]
    idxs, scores   = [ix[0] for ix in indexed_scores], [ix[1] for ix in indexed_scores]
    ks_transform = ks_align(scores, ta_scores)
    ks_transform = zip(idxs, ks_transform)

    idx  = 0
    curr = []
    transformed = []
    for i,score in ks_transform:
        if i == idx:
            curr.append(score)
        else:
            transformed.append(curr)
            curr = [score]
            idx = i
    if curr:
        transformed.append(curr)

    # Collate the scores each student gave
    st_score = dd(list)
    st_weight = dd(list)
    idx = inc = 0
    for d in data:
        scores = get_student_scores(d)
        for i in range(1,5):
            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            avg = np.mean(scores) if scores else ta_mean

            if score == 0:
                d['student_score_%i' % i] = score = avg
            if uid and score:
                # Add student weights - signed difference from the mean, on average
                st_score[uid].append(score)
                st_weight[uid].append((avg-score))
                d['ks_Score_%i'%i] = transformed[idx][i-1]
                if not i-1: inc = 1
        idx += inc
        inc  = 0

    # Make a copy for future comparison
    raw_data = [dict(d) for d in data]

    # Calculate mean & stdev for each student
    stats = {}
    weights = {}
    for s in st_score:
        if st_score[s]:
            ks   = ks_align(st_score[s], ta_scores)
            mean = np.mean(st_score[s])
            std  = np.std(st_score[s])
        else:
            ks   = [None]*len(st_score[s])
            mean = ta_mean
            std  = 1
        stats[s] = (mean, std, dict(zip(st_score[s], ks)))
        weights[s] = np.mean(st_weight[s])

    # Create new scores based on normalized student scores
    individual = [] # Normalize each student by using their three grades
    together   = [] # Normalize scores based on overall student mean & stdev
    averaged   = [] # Normalize based on average of individual and together
    for d in raw_data:
        individual.append(dict(d))
        together.append(dict(d))
        averaged.append(dict(d))

        for i in range(1,5):

            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            if uid and score:
                d['student_weight_%i'%i] = weights[d['student_display_id_%i'%i]]

                mean, std, normed = stats[uid]
                if std == 0: std = 1

                ind = ((score - mean) / std) * ta_stdev + ta_mean
                tog = ((score - st_mean) / st_stdev) * ta_stdev + ta_mean
                avg = (ind + tog) / 2.

                ks_norm = normed[score]
                ks_norm2= d['ks_Score_%i'%i]
                avg = np.mean([avg, ks_norm2, ks_norm if ks_norm else avg])

                individual[-1]['student_score_%i' % i] = ind
                together[-1]['student_score_%i' % i] = tog
                averaged[-1]['student_score_%i' % i] = avg


    D = averaged
    ta_scores = [d for d in D if any(k for k in ['student_score_%i' % j for j in range(1,5)] if k in d and d[k] is not None)]
    scores = [(i, np.mean([d[k] for k in ['student_score_%i' % j for j in range(1,5)] if d[k]])) for i, d in enumerate(ta_scores)]

    ta_scores = [(i,d['TA Score']) for i,d in enumerate(ta_scores)]
    ta_scores = sorted(ta_scores, key=lambda x:x[1])

    idxs = [t for t,_ in scores]
    # scores = [t for _,t in scores]
    scores = ks_align([t for _,t in scores],[t for _,t in ta_scores] )
    scores = np.array(scores)
    scores = ((scores - scores.mean())/scores.std()) * ta_stdev +ta_mean

    i = inc = 0
    for a in averaged:
        for k in ['student_score_%i' % j for j in range(1,5)]:
            if k in a and a[k] is not None:
                a[k] = scores[i]
                inc = 1
        i += inc
        inc = 0

    D = averaged
    ta_scores = [d for d in D if any(k for k in ['student_score_%i' % j for j in range(1,5)] if k in d and d[k] is not None)]
    scores = dict([(i, np.mean([d[k] for k in ['student_score_%i' % j for j in range(1,5)] if d[k]])) for i, d in enumerate(ta_scores)])

    st_scores = get_weighted_scores(assignment)
    st_scores = [st_scores[(d['First Name (Student)'].strip() + ' ' + d['Last Name (Student)'].strip()).lower()] for d in ta_scores]

    ta_scores = [(i,d['TA Score']) for i,d in enumerate(ta_scores)]
    ta_scores = sorted(ta_scores, key=lambda x:x[1])
    # idxs = [t for t,_ in scores]

    # scores = dict(zip(idxs, scores))
    st_scores = [scores[j] for j,_ in ta_scores]
    plt.plot([t for _,t in ta_scores], label='TA Scores')
    plt.plot(st_scores, alpha=.5, label='Weighted Scores')

    x = range(len(st_scores))
    coef = np.polyfit(x, st_scores, 3)
    p = np.poly1d(coef)

    yhat = p(x)
    ybar = np.sum(st_scores)/float(len(st_scores))
    ssreg = np.sum((yhat - ybar)**2)
    sstot = np.sum((st_scores - ybar)**2)
    print('R^2:%s' % ssreg/sstot)
    ks = ks_2samp(st_scores, [t for _,t in ta_scores])
    s  = ks.statistic
    pv = ks.pvalue

    x = np.linspace(0, len(st_scores), 100)
    plt.plot(x, p(x), label='Cubic fit (R^2=%.2f, KS-statistic=%.2f pval=%.2f)'%(ssreg/sstot, s, pv))
    coef = np.polyfit(range(len(st_scores)), st_scores, 1)
    p = np.poly1d(coef)

    plt.plot(x, p(x), 'k--', label='Linear fit')
    plt.legend(loc='lower center', fancybox=True, prop={'size':9})
    plt.title(assignment.title())
    plt.show()


    all_data = [('Raw Score', raw_data), ('Averaged', averaged),
                ('-Individual', individual),('-Together', together)]

    # Sanity check to ensure scores were properly normalized
    for name, data in all_data[1:]:
        data  = [d[k] for d in data for k in d if d[k] and 'score' in k]
        mean  = np.mean(data)
        stdev = np.std(data)
        assert(abs(mean - ta_mean) < 1 and abs(stdev - ta_stdev) < 1), \
                'Scores improperly normalized: %.2f & %.2f for %s' %(mean, stdev, name)

    safe_diff  = lambda score, data: 0 if not data else score - np.mean(data)
    difference = lambda data: [safe_diff(d['TA Score'], [d['student_score_%i'%i]
                                for i in range(1,5) if d['student_score_%i'%i]])
                                for d in data]


    print('-----------------------------\n\nCrowd / TA score differences:')

    # Calculate the difference of crowd-sourced score from individual TA score
    for ta in TAs:
        ta_data = [d['TA Score'] for d in raw_data if d['TA Name (First and Last)'] == ta]

        print('\n-----',ta,'-----')
        print('Overall mean & stdev:\t\t\t %.2f & %.2f' % (np.mean(ta_data), np.std(ta_data)))
        for label, data in all_data:
            ta_data = [d for d in data if d['TA Name (First and Last)'] == ta]
            diff    = difference(ta_data)
            mu, sig = np.mean(np.abs(diff)), np.std(np.abs(diff))
            print(label,'difference mean & stdev:\t %.2f & %.2f' % (mu, sig))

            # Plot best fit line for averaged
            if label == 'Averaged':
                hist, n = np.histogram(diff,50)
                plt.plot(n, mlab.normpdf(n, mu, sig), alpha=.7, label=ta)

    print('\n=========== Overall =============')

    # Calculate the overall difference of crowd-sourced score from all TA scores
    for label, data in all_data:
        diff = difference(data)
        mu, sig = np.mean(np.abs(diff)), np.std(np.abs(diff))
        print(label, 'difference mean & stdev:\t %.2f & %.2f' % (mu, sig))

        # Plot best fit line for averaged
        if label == 'Averaged':
            hist, n = np.histogram(diff,50)
            plt.plot(n, mlab.normpdf(n, mu, sig), '--')
    plt.legend(loc='best', prop={'size':7})
    plt.show()

    # Join all data into one cohesive set
    dataset = []
    for i,d in enumerate(raw_data):

        # All sets need same amount of features
        if not d['student_score_3']:
            continue

        features = []
        for j in range(1,4):
            features.append(d['student_score_%i' % j])
            features.append(len(d['student_comment_%i' % j]))
            features.append(d['student_weight_%i' % j])

            for _,data in all_data[1:]:
                features.append(data[i]['student_score_%i' % j])
        features.append(d['TA Score'])
        dataset.append(features)

    with open('assignments/'+assignment.title()+'/dataset.csv', 'w+') as f:
        for d in dataset:
            f.write(','.join([str(v) for v in d]) + '\n')


def get_weighted_scores(assignment, sess=None, ta_mean=TA_MEAN, ta_stdev=TA_STDEV, lambda_=TA_LAMBDA):

    @ensure_matrix
    def normalize_transform(data):
        mean = data.mean()
        std  = data.std()
        return ((data - mean) / (std if std else 1)) * ta_stdev + ta_mean

    @ensure_matrix
    def bc_transform(data):
        normal, _  = boxcox(data)
        transform  = inv_boxcox(normal, lambda_)
        return normalize_transform(transform)

    def transform_group(score_dict):
        ''' Flatten dict of scores, transform, then regroup '''
        indexed      = [[i, uid, score] for uid in score_dict
                                        for i,score in enumerate(score_dict[uid])]
        idxs, scores = [ix[:2] for ix in indexed], [ix[2] for ix in indexed]
        transformed  = [i+[k] for i,k in zip(idxs, bc_transform(scores))]
        transformed  = {k:[v[2] for v in sorted(list(grp), key=lambda y:y[0])] # Sort by index and keep score
                        for k,grp in groupby(transformed, lambda x:x[1])}      # Group by UID
        return transformed


    data = fetch_data(assignment, sess)

    st_score = [d[k] for d in data for k in d if d[k] and 'score' in k]
    st_mean  = np.mean(st_score)
    st_stdev = np.std(st_score)

    # Collate the scores each student gave
    st_score = dd(list)
    for d in data:
        for i in range(1,5):
            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            if uid and score:
                st_score[uid].append(score)

    # Get kurtosis/skewness tranformed scores
    transformed = transform_group(st_score)

    # Calculate mean & stdev for each student
    stats = {}
    for s in st_score:
        if st_score[s]:
            bc   = bc_transform(st_score[s])
            mean = np.mean(st_score[s])
            std  = np.std(st_score[s])
        else:
            bc   = [None]*len(st_score[s])
            mean = ta_mean
            std  = 1

        bc_ind = dict(zip(st_score[s], bc))
        bc_tog = dict(zip(st_score[s], transformed[s]))
        stats[s] = (mean, std, bc_ind, bc_tog)

    # Create new scores based on normalized student scores
    averaged = {}
    all_ = []
    for d in data:
        scores = []
        name = d['First Name (Student)'].strip() + ' ' + d['Last Name (Student)'].strip()
        for i in range(1, 5):

            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            if uid and score:
                mean, std, bc_ind, bc_tog = stats[uid]
                if std == 0: std = 1

                ind = ((score - mean) / std) * ta_stdev + ta_mean
                tog = ((score - st_mean) / st_stdev) * ta_stdev + ta_mean
                avg = (ind + tog) / 2.

                bc_ind = bc_ind[score] if bc_ind[score] else avg
                bc_tog = bc_tog[score]

                final = np.mean([avg, bc_ind, bc_tog])
                scores.append(final)
        averaged[name.lower().strip()] = np.mean(scores) if scores else ta_mean

    # Final Box-Cox transform
    scores   = [averaged[k] for k in sorted(averaged.keys())]
    transform= bc_transform(scores)
    averaged = {k:round(transform[i],2) for i,k in enumerate(sorted(averaged.keys()))}

    return averaged

if __name__ == '__main__':
    analyze_spreadsheet(ASSIGNMENT)
