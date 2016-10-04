from google_spreadsheet import Sheet
from glob import glob
from os.path import exists
from openpyxl import load_workbook

SHEET_ID   = '1Ed_tyOHhyc-BAPKkcXJRD_R5xZbbb93aPYxNQl8wYbg'
ASSIGNMENT = 'project 1'
TA_NAME = ''

def submit():
    ''' Submit all grades in the grades.xlsx file to 
        the google spreadsheet '''
    assignment = None
    for folder in glob('./assignments/*/'):
        if ASSIGNMENT.lower() in folder.lower():
            assignment = folder.split('\\')[1]
            break
    if assignment is None:
        raise Exception('Assignment %s not found in the assignments folder.' % ASSIGNMENT)

    filename = './assignments/%s/grades.xlsx' % assignment
    if not exists(filename):
        raise Exception('%s does not exist - have you ran pull-assignments.py?'%filename)

    wb = load_workbook(filename)
    ws = wb.worksheets[0]

    rows = list(ws.iter_rows())[7:]
    idxs = [0,2,3,4,5,6,7,8,9,11]
    data = [[r[i].internal_value if r[i].internal_value is not None else '' 
            for i in idxs] for r in rows if r[0].internal_value]
    data = [[d[0]] + [TA_NAME] + [d[-1]] + d[1:-1] + [sum([int(v) if v else 0 for v in d[1:-1]])]
            for d in data]
    data = [[str(d) for d in row] for row in data]

    sheet = Sheet(SHEET_ID)
    sheet.write(data)
    
    
def main():
    assert(TA_NAME), 'Need to enter your TA Name in this script'
    resp = input('Submit current grades with:\nGoogle spreadsheet:'+
                     ' %s\nAssignment: %s\nTA: %s \ny/n?'%(SHEET_ID, ASSIGNMENT, TA_NAME))
    if resp != 'y': return
    submit()




if __name__ == '__main__': main()
