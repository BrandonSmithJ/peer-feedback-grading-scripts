## Peer Feedback Grader Scripts

This is a set of scripts to help TAs grading life easier while grading assignments on peer feedback.  Here is a summary of the scripts and their roles:

### Pull Assignments Script

`$ python3 pull-assignments.py`

> Enter credentials in `secrets.yml`, or at the prompt:
![screen shot 2016-10-01 at 3 49 45 pm](https://github.gatech.edu/storage/user/4328/files/c632130e-87ee-11e6-8e3f-3d5ad516e4c2)

This script generates a grades spreadsheet for the current assignment seeded with information from the current tasks assigned to you including:
- rubric titles for the assignment being graded
- student name for each student you're assigned to grade
- weighted estimate grade based on other student grades
- excel formulas calculating mean/median/stdev for overall assignment you're grading
- links to the peer-feedback URL for that assignment
- links to the PDF files for that assignment
- pdf assignments of each student saved to a local data folder, so you can begin grading immediately

> Sample grades spreadsheet
![screen shot 2016-10-12 at 9 36 01 pm](https://github.gatech.edu/storage/user/4328/files/eb6da5b0-90c3-11e6-83f1-b909d030f618)

### Submit Assignments Script

`$ python3 submit-assignments.py`

This script uses the grades you've entered in the grades spreadsheet to seed peer-feedback with the scores for each student.  

**Note:**  Grades are only saved to peer feedback, you must manually submit them.

### Assignment Analysis Script

Provides a full analysis with plots and data for generating an educated guess on a student's score.  This is incorporated into the grades spreadsheet as a reference but the TA must enter their own official grades.  For more detail see the the analysis [readme](analysis/README.md).

### Google Spreadsheet Export Script

Run submit-assignment.py to add your grades.xlsx to the master google spreadsheet, and **partially*** submit on peer-feedback:

```shell
> python submit-assignments.py -h
usage: submit-assignments.py [-h] [--assignment ASSIGNMENT] 
                                  [--name NAME]
                                  [--sheetid SHEETID]

optional arguments:
  -h, --help            show this help message and exit
  --assignment ASSIGNMENT   Which assignment to submit
  --name NAME               TA which program should submit for
  --sheetid SHEETID         Google spreadsheet id program should submit to
```

Alternatively, you can choose to enter the information at the program's prompt. Finally, there will be a confirmation ensuring the information is correct before submitting.

*Partially meaning, the script will populate all scores and comments, but you as the user still need to view each task and click the 'submit' button for the final submission. This is done to ensure any errors are caught before the final submission (on the part of the script _or_ the user). 


### Setup

`pip3 install -r requirements.txt`

### Other Notes

The general output of this script is the following:
- `assignments/<assignment-name>`
- `assignments/<assignment-name>/grades.xslx`
- `assignments/<assignment-name>/Papers/<student-name>.pdf`
- `assignments/<assignment-name>/Data/assignments.json`
- `assignments/<assignment-name>/Data/<full class CSVs for analysis>`
