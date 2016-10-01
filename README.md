## Peer Feedback Grader Script

### Setup

`pip install -r requirements.txt`

### pull assignments

Once prompted, enter your TA credentials.  A selenium chrome driver will pull the files to the assignments directory for you.  Pulls any current assignments students have submitted.  A JSON dump is also left in the directory for the create-spreadsheet script.

Run: `python3 pull-assignments.py`

Generates the following:
- `assignments/<assignment-name>`
- `assignments/<assignment-name>/<assignment-id>.pdf`
- `assignments/<assignment-name>/assignments.json`
- `assignments/<assignment-name>/grades.xslx`

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

![grades-output-example](https://github.gatech.edu/storage/user/4328/files/0118cd62-87ec-11e6-9b26-2d29166918dc)

> Note when opening the spreadsheet you may be prompted to repair, just repair and save and it will open regularly after that.