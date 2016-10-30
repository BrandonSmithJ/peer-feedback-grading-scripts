from os.path    import exists
from os         import makedirs
from lxml.html  import fromstring
import getpass
import requests
import csv
import yaml

# Word count libraries
from cStringIO          import StringIO
from pdfminer.converter import LTChar, TextConverter
from pdfminer.layout    import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage   import PDFPage
from collections        import defaultdict


# Disable verify warnings; can't verify due to peerfeedback ssl certificate issues
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = 'https://peerfeedback.gatech.edu'
COURSES  = {'online': '39', 'oncampus': '40'}

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

    if 'Your courses and tasks' not in resp.text:
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

            with open(directory + name + '_unprocessed_data.csv') as f:
                data = [line for line in csv.reader(f)]
            head = data.pop(0)

            # Add fourth student header for the ones which have it
            head += ['student_score_4', 'student_comment_4', 'student_display_id_4']

            # Remove students who did not complete the assignment
            data = [d for d in data if d[3] == 'Yes']

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
                    download_url = BASE_URL+'/data/download'+a.get('href')
                    resp = sess.get(download_url)
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    found = True

            if not found:
                raise Exception('"%s" was not found; is the name correct?\n'%assignment +
                                'Available assignments are:\n\t- %s'%'\n\t- '.join(assignments))


def pdf_to_csv(filename, separator, threshold):

    class CsvConverter(TextConverter):
        def __init__(self, *args, **kwargs):
            TextConverter.__init__(self, *args, **kwargs)
            self.separator = separator
            self.threshold = threshold

        def end_page(self, i):
            lines = defaultdict(lambda: {})
            for child in self.cur_item._objs:  # <-- changed
                if isinstance(child, LTChar):
                    (_, _, x, y) = child.bbox
                    line = lines[int(-y)]
                    line[x] = child._text.encode(self.codec)  # <-- changed
            for y in sorted(lines.keys()):
                line = lines[y]
                self.line_creator(line)
                self.outfp.write(self.line_creator(line))
                self.outfp.write("\n")

        def line_creator(self, line):
            keys = sorted(line.keys())
            # calculate the average distange between each character on this row
            average_distance = sum([keys[i] - keys[i - 1] for i in range(1, len(keys))]) / len(keys)
            # append the first character to the result
            result = [line[keys[0]]]
            for i in range(1, len(keys)):
                # if the distance between this character and the last character is greater than the average*threshold
                if (keys[i] - keys[i - 1]) > average_distance * self.threshold:
                    # append the separator into that position
                    result.append(self.separator)
                # append the character
                result.append(line[keys[i]])
            printable_line = ''.join(result)
            return printable_line

    # ... the following part of the code is a remix of the
    # convert() function in the pdfminer/tools/pdf2text module
    rsrc = PDFResourceManager()
    outfp = StringIO()
    device = CsvConverter(rsrc, outfp, codec="utf-8", laparams=LAParams())
    # becuase my test documents are utf-8 (note: utf-8 is the default codec)

    fp = open(filename, 'rb')

    interpreter = PDFPageInterpreter(rsrc, device)
    for i, page in enumerate(PDFPage.get_pages(fp)):
        outfp.write("START PAGE %d\n" % i)
        if page is not None:
            # print 'none'
            interpreter.process_page(page)
        outfp.write("END PAGE %d\n" % i)

    device.close()
    fp.close()

    return outfp.getvalue()