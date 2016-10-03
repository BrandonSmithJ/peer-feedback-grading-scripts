## Peer Feedback Grader Scripts

### Setup

`pip3 install -r requirements.txt`

### How it works

Once prompted, enter your TA credentials student assignments will be pulled for you.  A JSON dump is also left in the directory for the create-spreadsheet script.

Run: `python3 pull-assignments.py`

Enter credentials:

![screen shot 2016-10-01 at 3 49 45 pm](https://github.gatech.edu/storage/user/4328/files/c632130e-87ee-11e6-8e3f-3d5ad516e4c2)


Generates the following:
- `assignments/<assignment-name>`
- `assignments/<assignment-name>/<student-feedback-id>.pdf`
- `assignments/<assignment-name>/assignments.json`
- `assignments/<assignment-name>/grades.xslx`

#### Output
```shell
 • peer-feedback-grading-scripts$ ls assignments/Project 1 (Project Reflections)
33609.pdf		33701.pdf		33805.pdf		33933.pdf
33620.pdf		33707.pdf		33823.pdf		33940.pdf
33627.pdf		33729.pdf		33879.pdf		assignments.json
33628.pdf		33744.pdf		33895.pdf		grades.xlsx
33649.pdf		33780.pdf		33908.pdf
33663.pdf		33800.pdf		33925.pdf
```

#### assignments.json output:
```js
[
    {
        "name": "Carlitos Yupertino",
        "feedback_url": "https://peerfeedback.gatech.edu/feedback/1234",
        "feedback_id": "1234"
    },
    //... for each student
]
```

#### Generated `grades.xlsx` spreadsheet

![grades](https://github.gatech.edu/storage/user/4328/files/504d754c-8803-11e6-8f91-6c14c535ac76)

> Note when opening the spreadsheet you may be prompted to repair, just repair and save and it will open regularly after that.
