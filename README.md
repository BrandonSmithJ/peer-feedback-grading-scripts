## Peer Feedback Grader Script

This script pulls assignments into a directory called `assignments` with each report stored with the ID of the peerfeedback URL ID.

To run simply run
`python pull-assignments.py`

And then enter your credentials.  A selenium chrome driver will parse the links and pull the files to the assignments directory for you.

> uses python 3