from collections import defaultdict as dd
from utils import fetch_data
import numpy as np

def analyze_spreadsheet(assignment):
    ''' Analyze an assignment's scores after TA grading is completed '''
    from glob import glob
    import matplotlib.pyplot as plt
    import matplotlib.mlab   as mlab

    for folder in glob('./assignments/*/'):
        if assignment.lower() in folder.lower():
            assignment = folder.split('\\')[1]
            break

    data = fetch_data(assignment)

    TAs = sorted(set([d['TA Name (First and Last)'] for d in data]))
    print 'Number of grading TAs:', len(TAs)

    st_score = [v for d in data for k,v in d.iteritems() if v and 'score' in k]
    st_mean  = np.mean(st_score)
    st_stdev = np.std(st_score)
    print 'Student average & stdev: %.2f & %.2f' % (st_mean, st_stdev)

    ta_scores = [d['TA Score'] for d in data]
    if not any(ta_scores):
        print 'Remaining analysis can\'t be completed without TA scores.'
        return
    ta_mean   = np.mean(ta_scores)
    ta_stdev  = np.std(ta_scores)
    print 'TA average & stdev: %.2f & %.2f' % (ta_mean, ta_stdev)

    # Collate the scores each student gave
    st_score = dd(list) 
    st_weight = dd(list)
    for d in data:
        for i in range(1,5):
            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            avg = np.mean([d['student_score_%i' % j] for j in range(1,5) if d['student_score_%i' % j]])
            if score == 0:
                d['student_score_%i' % i] = score = avg
            if uid and score:
                # Add student weights - signed difference from the mean, on average
                st_score[uid].append(score)
                st_weight[uid].append((avg-score))
    
    # Make a copy for future comparison
    raw_data = [dict(d) for d in data]

    # Calculate mean & stdev for each student
    stats = {}
    weights = {}
    for s in st_score:
        stats[s] = (np.mean(st_score[s]), np.std(st_score[s]))
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

                mean, std = stats[uid]
                if std == 0: std = 1    

                ind = (score - mean) / std
                tog = (score - st_mean) / st_stdev
                avg = (ind + tog) / 2.
                
                individual[-1]['student_score_%i' % i] = ind * ta_stdev + ta_mean
                together[-1]['student_score_%i' % i] = tog * ta_stdev + ta_mean 
                averaged[-1]['student_score_%i' % i] = avg * ta_stdev + ta_mean 

    # Sanity check to ensure scores were properly normalized
    for data in [individual, together, averaged]:
        data  = [v for d in data for k,v in d.iteritems() if v and 'score' in k]
        mean  = np.mean(data)
        stdev = np.std(data)
        assert(abs(mean - ta_mean) < 1e3 and abs(stdev - ta_stdev) < 1e3), \
                'Scores improperly normalized'

    safe_diff  = lambda score, data: 0 if not data else score - np.mean(data) 
    difference = lambda data: [safe_diff(d['TA Score'], [d['student_score_%i'%i] 
                                for i in range(1,5) if d['student_score_%i'%i]])
                                for d in data]
    all_data = [('Raw Score', raw_data), ('Averaged', averaged), 
                ('-Individual', individual),('-Together', together)
                ]

    print '-----------------------------\n\nCrowd / TA score differences:'

    # Calculate the difference of crowd-sourced score from individual TA score
    for ta in TAs:
        ta_data = [d['TA Score'] for d in raw_data if d['TA Name (First and Last)'] == ta]

        print '\n-----',ta,'-----'
        print 'Overall mean & stdev:\t\t\t %.2f & %.2f' % (np.mean(ta_data), np.std(ta_data))
        for label, data in all_data:
            ta_data = [d for d in data if d['TA Name (First and Last)'] == ta]
            diff    = difference(ta_data)
            mu, sig = np.mean(np.abs(diff)), np.std(np.abs(diff))
            print label,'difference mean & stdev:\t %.2f & %.2f' % (mu, sig)

            # Plot best fit line for averaged 
            if label == 'Averaged':
                hist, n = np.histogram(diff,50)
                plt.plot(n, mlab.normpdf(n, mu, sig), alpha=.7)

    print '\n=========== Overall ============='

    # Calculate the overall difference of crowd-sourced score from all TA scores
    for label, data in all_data:
        diff = difference(data)
        mu, sig = np.mean(np.abs(diff)), np.std(np.abs(diff))
        print label,'difference mean & stdev:\t %.2f & %.2f' % (mu, sig)

        # Plot best fit line for averaged 
        if label == 'Averaged':
            hist, n = np.histogram(diff,50)
            plt.plot(n, mlab.normpdf(n, mu, sig), '--')

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


def get_weighted_scores(assignment, sess=None, ta_mean=34, ta_stdev=3.75):
    data = fetch_data(assignment, sess)

    st_score = [v for d in data for k,v in d.iteritems() if v and 'score' in k]
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
    
    # Calculate mean & stdev for each student
    stats = {k:(np.mean(v), np.std(v)) for k,v in st_score.iteritems()}

    # Create new scores based on normalized student scores
    averaged = {}
    all_ = []
    for d in data:
        scores = []
        name = d['First Name (Student)'].strip() + ' ' + d['Last Name (Student)'].strip()
        for i in range(1,5):

            uid = d['student_display_id_%i' % i]
            score = d['student_score_%i' % i]
            if uid and score:
                mean, std = stats[uid]
                if std == 0: std = 1    

                ind = (score - mean) / std
                tog = (score - st_mean) / st_stdev
                avg = (ind + tog) / 2.

                scores.append(ind * ta_stdev + ta_mean)
        averaged[name.lower()] = str(round(np.mean(scores),2)) if scores else '0'
    
    return averaged

if __name__ == '__main__':
    analyze_spreadsheet('assignment 1')
