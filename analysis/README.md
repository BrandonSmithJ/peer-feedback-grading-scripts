# Analysis

#### Discussion on TA Score / Weighted Score analysis

There are a few transformations which student scores go through to obtain the final weighted scores shown in the grading spreadsheet.

The full analysis and following graphs can be created by running analysis.py, but the summary of steps are:
- transform scores to have a mean/stdev in line with TA scores
  - this is done both as a whole and on a per-student basis, with the two averaged to create a more robust score
- transform score to have a similar kurtosis/skewness via a Box-Cox transformation
  - also done both as a whole and per-student basis, then averaged with the previous average to obtain the final score
  - this transformation is still rough, and can be improved (with suggestions in the ks_align function)
  
Running analysis.py will generate a number of graphs, along with various statistics on the TA scores and the student scores. Example output:

```shell
Number of grading TAs: 10

Student Statistics:
Mean & stdev: 27.56 & 7.05
Skewness & kurtosis: -0.29 & -0.58

TA Statistics:
Mean & stdev: 33.65 & 4.27
Skewness & kurtosis: -1.21 & 1.80
R^2: 0.369314959765
-----------------------------

Crowd / TA score differences:
< Redacted for brevity >

=========== Overall =============
('Raw Score', 'difference mean & stdev:\t 6.18 & 4.14')
('Averaged', 'difference mean & stdev:\t 2.83 & 2.43')
('-Individual', 'difference mean & stdev:\t 2.68 & 2.41')
('-Together', 'difference mean & stdev:\t 2.70 & 2.42')
```

As shown, the final weighted score (labeled by 'Averaged') tends to be between 2-3 points off on average, with that number varying per assignment (e.g. for project 1 reflections it's 2.43 & 2.03).

These numbers are also dependent on the TAs, as excluding outliers leads to a better fit. Shown below are graphs outlining the fit of the scores.

### Weighted scores fit (With outliers on the left, without on the right)

![without_outliers_both](https://github.gatech.edu/storage/user/7113/files/28c51888-908a-11e6-8ed0-5a752d47b97c)

Clearly the weighted scores are still extremely noisy, though a definite pattern exists which can be used. The null hypothesis (that student & TA scores are from different distributions) is rejected with pvalue >> .01.

To summarize, these scores offer a rough guideline as to how to score a paper - not at all to be taken as a final value. Future improvements to this score are suggested in analysis.py.


### Weighted scores fit without Box-Cox transformation

![no_ks_align](https://github.gatech.edu/storage/user/7113/files/d865eb50-908a-11e6-964a-06f00efb3406)

As a final note, this graph shows the score fit without performing a Box-Cox transformation. While the pattern still exists, the significance of it is significantly impacted (pvalue << .01) as well as causing poorer outlier prediction.
