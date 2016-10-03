from os.path    import exists
from os         import makedirs
from lxml.html  import fromstring
import getpass
import requests
import csv

# Disable verify warnings; can't verify due to peerfeedback ssl certificate issues
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = 'https://peerfeedback.gatech.edu'
COURSES  = {'online': '39', 'oncampus': '40'}


def login(USERNAME='', PASSWORD=''):
    user, pswd = USERNAME, PASSWORD
    if not user: user = input("Enter your email: ")
    if not pswd: pswd = getpass.getpass()

    # Initialize session and variables
    sess = requests.session()
    resp = sess.post(BASE_URL + '/login_check', verify=False)
    data = resp.text

    # Extract csrf token
    idx   = data.index('name="_csrf_token"')
    start = data.index('value="', idx) + 7
    end   = data.index('"', start)
    csrf  = data[start:end]

    # Log in
    resp = sess.post('https://peerfeedback.gatech.edu/login_check',
                     verify=False,
                     data={'_username': user,
                            '_password': pswd,
                            '_csrf_token': csrf,
                            '_submit':'Log in' })

    if 'Your courses and tasks' not in resp.text:
        raise Exception('Something went wrong; couldn\'t log in')

    return sess


def fetch_data(assignment, sess=None):
    ''' Parse & clean data '''
    results = []
    for name in COURSES:
        directory = './assignments/%s/Data/' % assignment.title()
        if not exists(directory):
            makedirs(directory)

        if not exists(directory + name + 'data_clean.csv'):
            if not exists(directory + name + '_unprocessed_data.csv'):
                if sess is None: sess = login()
                download_spreadsheet(sess, assignment)

            with open(directory + name + '_unprocessed_data.csv') as f:
                data = [line for line in csv.reader(f)]
            head = data.pop(0)

            # Add fourth student header for the ones which have it
            head += ['student_score_4', 'student_comment_4', 'student_display_id_4']

            # Remove students who did not complete the assignment
            data = [d for d in data if d[3] == 'Yes']

            # Yan accidently submitted 0
            if assignment == 'assignment 1':
                idx = [i for i,d in enumerate(data) if d[0] == 'jmeanor3']
                if idx:
                    data[idx[0]][4] = '34'

            # Rejoin data and quote comments
            quote_idx = [i for i,h in enumerate(head) if 'comment' in h.lower()]
            data = [','.join(head)] + \
                   [','.join([
                        '"%s"' % v.replace('"', '""')
                        if i in quote_idx else v
                        for i, v in enumerate(d)])
                    for d in data]

            with open(directory + name + '_clean.csv', 'w+') as f:
                f.write('\n'.join(data))

        with open(directory + name + '_clean.csv') as f:
            results += [{
                k: int(v)
                if v and 'score' in k.lower() else v
                    for k, v in line.items()}
                for line in csv.DictReader(f)
            ]
    return results


def download_spreadsheet(sess, assignment):
    ''' Download the full class spreadsheet if not already downloaded '''
    for course in COURSES:
        found = False
        filepath = './assignments/%s/Data/' % assignment.title()
        if not exists(filepath):
            makedirs(filepath)
        filename = filepath + course + '_unprocessed_data.csv'

        # Download the full class csv if it doesn't exist
        if not exists(filename):
            resp = sess.get(BASE_URL + '/course/' + COURSES[course])
            page = resp.text
            tree = fromstring(page)

            assignment_tbl = tree.xpath('//table[@id="assignmentsList"]')[0]
            assignment_ele = assignment_tbl.xpath('.//a')

            assignments = []
            for a in assignment_ele:
                assignments.append(a.text.lower().strip())

                if assignment.lower().strip() in assignments[-1]:
                    download_url = BASE_URL+'/data/download'+a.get('href')
                    resp = sess.get(download_url)
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    found = True

            if not found:
                raise Exception('"%s" was not found; is the name correct?\n'%assignment +
                                'Available assignments are:\n\t- %s'%'\n\t- '.join(assignments))
