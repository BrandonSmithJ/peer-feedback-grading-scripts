from google_spreadsheet import Sheet
from glob import glob
from os.path import exists
from openpyxl import load_workbook
import yaml, argparse

# The sheet id is found at the end of the spread sheet url
# If this is the url, for example:
#
#   https://docs.google.com/spreadsheets/d/1Ed_tyOHhyc-BAPKkcXJRD_R5xZbbb93aPYxNQl8wYbg/edit#gid=0
#
# the id is 1Ed_tyOHhyc-BAPKkcXJRD_R5xZbbb93aPYxNQl8wYbg
SHEET_ID = ''


def get_ta_name():
    try:
        with open('secrets.yml', 'r') as file:
            secrets = yaml.load(file)
            return secrets['spreadsheet-information']['ta-name']
    except:
        return ''


def submit(ta_name, assignment_input, sheet_id):
    ''' Submit all grades in the grades.xlsx file to 
        the google spreadsheet '''
    assignment = None
    assignments= []
    for folder in glob('./assignments/*/'):
        assignments.append(folder.split('\\')[1].split('(')[0])
        if assignment_input.lower() in folder.lower():
            assignment = folder.split('\\')[1]
            break
    if assignment is None:
        raise Exception('"%s" was not found; is the name correct?\n'%assignment_input +
                        'Available assignments are:\n\t- %s'%'\n\t- '.join(assignments))

    filename = './assignments/%s/grades.xlsx' % assignment
    if not exists(filename):
        raise Exception('%s does not exist - have you ran pull-assignments.py?'%filename)

    wb = load_workbook(filename)
    ws = wb.worksheets[0]

    rows = list(ws.iter_rows())[7:]
    idxs = [0,2,3,4,5,6,7,8,9,11]
    data = [[r[i].internal_value if r[i].internal_value is not None else '' 
            for i in idxs] for r in rows if r[0].internal_value]
    data = [[d[0]] + [ta_name] + [d[-1]] + d[1:-1] + [sum([int(v) if v else 0 for v in d[1:-1]])]
            for d in data]
    data = [[str(d) for d in row] for row in data]

    sheet = Sheet(sheet_id)
    sheet.write(data)
    
    
def main():
    parser = argparse.ArgumentParser() 
    parser.add_argument('--assignment', help="Which assignment to submit")
    parser.add_argument('--name', help="TA which program should submit for")
    parser.add_argument('--sheetid', help="Google spreadsheet id program should submit to")
    args = parser.parse_args()

    ta_name = get_ta_name()
    if not ta_name:
        ta_name = args.name if args.name else input('TA Name: ')

    assignment = args.assignment if args.assignment else input('Assigment to submit: ')

    sheet_id = SHEET_ID
    if not SHEET_ID:
        sheet_id = args.sheetid if args.sheetid else input('Google Spreadsheet ID: ')

    resp = input('\nSubmit current grades with vars:\n- Google spreadsheet: '+
                '%s\n- Assignment: %s\n- TA: %s \ny/n?'%(sheet_id, assignment, ta_name))
    if resp != 'y': return
    submit(ta_name, assignment, sheet_id)




if __name__ == '__main__': main()
