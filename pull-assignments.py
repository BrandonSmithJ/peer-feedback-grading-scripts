from openpyxl.workbook import Workbook
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle, Font, Alignment

from lxml.html import fromstring 
from analysis  import get_weighted_scores 
from utils     import login 

import datetime
import os
import json
import requests


USERNAME    = ''            # if left blank, script will prompt you for it
PASSWORD    = ''            # if left blank, script will prompt you for it
DOWNLOAD    = False          # whether to download papers locally or not
SHOW_WEIGHT = True          # whether or not to have the 'weighted scores' column displayed
                            # Weighted scores reflect a 'best guess' score for the paper, based
                            # on peerfeed back for the student. Still very rough at the moment,
                            # and does poorly on outliers

BASE_URL = 'https://peerfeedback.gatech.edu'
GRADING_TEMPLATE_PATH = "templates/KBAI PF Grading Template2.xltx"


def populate_spreadsheet(assignment, assignments={}, weights={}):

    print("Populating spreadsheet...")
    path = "assignments/%s/assignments.json" % (assignment)

    workbook_path = "assignments/%s/grades.xlsx" % (assignment)
    wb = load_workbook(GRADING_TEMPLATE_PATH)

    wb.template = False
    ws = wb.active
    ws.page_setup.fitToHeight = 1
    ws.page_setup.fitToWidth = 1

    center = NamedStyle(name="center")
    center.font = Font(size=12)
    center.alignment = Alignment(horizontal="center", vertical="center")
    wb.add_named_style(center)

    start_row = 8
    end_row = len(assignments) + start_row - 1

    ws['A1'] = 'Generated on %s' % (datetime.datetime.now())
    ws['B4'] = '=AVERAGE(K%s:K%s)' % (start_row, end_row)
    ws['C4'] = '=MEDIAN(K%s:K%s)' % (start_row, end_row)
    ws['D4'] = '=STDEV(K%s:K%s)' % (start_row, end_row)

    for i in range(start_row, end_row + 1):
        for c in ['A', 'B', 'K', 'L', 'M', 'N', 'O']:
            ws['%s%s' % (c,i)].style = center

    current_row = start_row
    for assignment in assignments:
        ws.cell(row=current_row, column=1, value=assignment['name'])
        ws.cell(row=current_row, column=2, value=assignment['feedback_id'])
        ws.cell(row=current_row, column=11, value='=+IF(SUM(C%s:J%s)=0,"",SUM(C%s:J%s))' % (
            current_row, current_row, current_row, current_row)
        )
        ws.cell(row=current_row, column=13, value=weights[assignment['name']] 
                                                  if SHOW_WEIGHT else '')
        ws.cell(row=current_row, column=14, value=assignment['feedback_url'])
        ws.cell(row=current_row, column=15, value=assignment['paper_url'])
        ws.cell(row=current_row, column=16, value=' ') # Make sure url is not extended past col

        current_row += 1

    wb.save(workbook_path)


def pull_assignments(sess):
    """visits each assigned task, pulls the assignment as feedback_id"""
    print("Pulling assignments...")
    resp = sess.get(BASE_URL)
    page = resp.text
    tree = fromstring(page)

    assignment_name = tree.xpath("//div[contains(@class, 'taskCard')]//h4")[0].text.title()
    links = tree.xpath("//a[contains(@class, 'taskButton')]")
    if not os.path.exists('assignments/%s/Data' % (assignment_name)):
        os.makedirs('assignments/%s/Data' % (assignment_name))

    tasks = []
    for link in links:
        pf_link = link.get('href')
        fb_resp = sess.get(BASE_URL + pf_link)
        fb_page = fb_resp.text
        fb_tree = fromstring(fb_page)
        dl_link = fb_tree.xpath('//h2/a[contains(.,"Download submitted assignment")]')[0].get('href')
        assert(dl_link)
        st_name = None
        for a in fb_tree.xpath('//div[@class="checkbox"]/label/div/a'):
            if a.text.strip():
                st_name = a.text.strip()
                break
        if st_name is None: assert(0), 'Couldn\'t pull student name'
        tasks.append({  'name': st_name.lower().strip(),
                        'feedback_url': BASE_URL+pf_link, 
                        'feedback_id' : pf_link.split('/')[-1],
                        'paper_url'   : dl_link})

        if DOWNLOAD:
            filepath = 'assignments/%s/Papers/' % assignment_name
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            filename = filepath + st_name.replace(' ','') + '.pdf'
            resp = sess.get(dl_link)
            with open(filename, 'wb') as f:
                f.write(resp.content)

    with open('assignments/%s/Data/assignments.json' % assignment_name, 'w') as file:
        json.dump(tasks, file)

    weights = {}
    if SHOW_WEIGHT:
        weights = get_weighted_scores(assignment_name, sess)

    populate_spreadsheet(assignment_name, tasks, weights)


def process():
    sess = login(USERNAME, PASSWORD)
    pull_assignments(sess)

if __name__ == "__main__":
    process()
