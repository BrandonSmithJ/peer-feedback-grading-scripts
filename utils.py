from os.path    import exists
from os         import makedirs
from lxml.html  import fromstring
import getpass
import requests
import csv
import yaml

# Word count libraries
try:                from StringIO import StringIO
except ImportError: from io       import StringIO
from pdf_classes import PDFResourceManagerFixed, CsvConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage   import PDFPage

# Disable verify warnings; can't verify due to peerfeedback ssl certificate issues
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = 'https://peerfeedback.gatech.edu'
COURSES  = {'online': '44'}#, 'oncampus': '40'}

def secrets():
    try:
        with open('secrets.yml', 'r') as file:
            secrets = yaml.load(file)
            return secrets['peer-feedback-credentials']
    except:
        return {}

USERNAME = secrets()['username'] if secrets() else ''
PASSWORD = secrets()['password'] if secrets() else ''


def login():
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

    if 'courses and tasks' not in resp.text.lower():
        raise Exception('Something went wrong; couldn\'t log in')

    return sess


def fetch_data(assignment, sess=None, overwrite=True):
    ''' Parse & clean data '''
    results = []
    for name in COURSES:
        directory = './assignments/%s/Data/' % assignment.title()
        if not exists(directory):
            makedirs(directory)

        if not exists(directory + name + 'data_clean.csv') or overwrite: 
            if not exists(directory + name + '_unprocessed_data.csv') or overwrite:
                if sess is None: sess = login()
                download_spreadsheet(sess, assignment, overwrite)

            with open(directory + name + '_unprocessed_data.csv', encoding='utf8') as f:
                data = [line for line in csv.reader(f)]
            head = data.pop(0)

            # Add fourth student header for the ones which have it
            head += ['student_score_4', 'student_comment_4', 'student_display_id_4']

            # Remove students who did not complete the assignment
            data = [d for d in data if d[4] == 'Yes']

            # Use email as name if the name doesn't exist
            for i,d in enumerate(data):
                if not d[2]:
                    data[i][2] = data[i][1]

            # Rejoin data and quote comments
            quote_idx = [i for i,h in enumerate(head) if 'comment' in h.lower()]
            data = [','.join(head)] + \
                   [','.join([
                        '"%s"' % v.replace('"', '""')
                        if i in quote_idx else v
                        for i, v in enumerate(d)])
                    for d in data]

            with open(directory + name + '_clean.csv', 'w+') as f:
                f.write('\n'.join([''.join([ch for ch in d if ord(ch) < 128]) for d in data]))

        with open(directory + name + '_clean.csv') as f:
            results += [{
                k: int(line[k])
                if line[k] and 'score' in k.lower() else line[k]
                    for k in line}
                for line in csv.DictReader(f)
            ]
    return results


def download_spreadsheet(sess, assignment, overwrite=True):
    ''' Download the full class spreadsheet if not already downloaded '''
    for course in COURSES:
        found = False
        filepath = './assignments/%s/Data/' % assignment.title()
        if not exists(filepath):
            makedirs(filepath)
        filename = filepath + course + '_unprocessed_data.csv'

        # Download the full class csv if it doesn't exist
        if not exists(filename) or overwrite:
            resp = sess.get(BASE_URL + '/course/' + COURSES[course])
            page = resp.text
            tree = fromstring(page)

            assignment_tbl = tree.xpath('//table[@id="assignmentsList"]')[0]
            assignment_ele = assignment_tbl.xpath('.//a')

            assignments = []
            for a in assignment_ele:
                assignments.append(a.text.lower().strip())

                if assignment.lower().strip() in assignments[-1]:
                    cid = a.get('href').split('/')[-1]
                    download_url = BASE_URL+'/data/download/assignment/feedback/'+cid
                    resp = sess.get(download_url)
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    found = True

            if not found:
                raise Exception('"%s" was not found; is the name correct?\n'%assignment +
                                'Available assignments are:\n\t- %s'%'\n\t- '.join(assignments))

def extract(filename, separator=',', threshold=1.5):
    rsrc = PDFResourceManagerFixed()
    outfp = StringIO()

    device = CsvConverter(separator, threshold, rsrc, outfp, codec="ascii")
    with open(filename, 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrc, device)
        for i, page in enumerate(PDFPage.get_pages(fp)):
            # outfp.write("START PAGE %d\n" % i)
            if page is not None:
                interpreter.process_page(page)
            # outfp.write("END PAGE %d\n" % i)
    device.close()
    return outfp.getvalue()


def pdf_word_count(filename):
    ''' Due to extreme variability in pdf fonts / formats there are still a few
        cases in which the extraction fails to parse actual text. The majority 
        of cases will be accurate within a few percent. '''
    def get_count(data):
        words = data.replace('\n', ' ').replace('\t',' ').replace('.', ' ')
        return len([w for w in words.split(' ') if w.strip()])
    return get_count(extract(filename))


    
