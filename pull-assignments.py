from openpyxl.workbook import Workbook
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle, Font, Alignment

from lxml.html import fromstring
from analysis  import get_weighted_scores
from utils     import login, secrets

import datetime
import os
import json
import requests


BASE_URL = 'https://peerfeedback.gatech.edu'
GRADING_TEMPLATE_PATH = 'templates/KBAI PF Grading Template.xltx'

RUBRIC_TEXT_XPATH = '//div[@class="rubricContainerOpen"]//td[@class="rubricNoSelect"]/div'
ASSIGNMENT_NAME_XPATH = '//div[contains(@class, "taskCard")]//h4'
ASSIGNMENT_LINK_XPATH = '//h2/a[contains(.,"Download submitted assignment")]'
ASSIGNMENT_LINKS_XPATH = '//a[contains(@class, "taskButton")]'
RUBRIC_TABLE_XPATH = '//table[contains(@class, "rubricView")]'
STUDENT_NAME_XPATH = '//div[@class="checkbox"]/label/div/a'

USERNAME = secrets()['username'] if secrets() else ''
PASSWORD = secrets()['password'] if secrets() else ''


def populate_spreadsheet(assignment_name, assignments={}):

    print('Populating spreadsheet for %s...' % assignment_name)
    datapath = 'assignments/%s/Data' % (assignment_name)

    with open('%s/rubric.json' % datapath, 'r') as file:
        rubric = json.load(file)

    with open('%s/weights.json' % datapath, 'r') as file:
        weights = json.load(file)

    workbook_path = 'assignments/%s/grades.xlsx' % (assignment_name)
    wb = load_workbook(GRADING_TEMPLATE_PATH)

    wb.template = False
    ws = wb.active

    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1

    center = NamedStyle(name='center')
    center.font = Font(size=12)
    center.alignment = Alignment(horizontal='center', vertical='center')
    wb.add_named_style(center)

    start_row = 8
    end_row = len(assignments) + start_row - 1

    ws['A1'] = 'Generated on %s'   % (datetime.datetime.now())
    ws['B4'] = '=AVERAGE(K%s:K%s)' % (start_row, end_row)
    ws['C4'] = '=MEDIAN(K%s:K%s)'  % (start_row, end_row)
    ws['D4'] = '=STDEV(K%s:K%s)'   % (start_row, end_row)

    for i in range(start_row, end_row + 1):
        for c in ['A', 'B', 'K', 'L', 'M', 'N', 'O']:
            ws['%s%s' % (c, i)].style = center

    for i, r in enumerate(rubric, 3):
        ws.cell(row=7, column=i, value=r)

    current_row = start_row
    for assignment in assignments:
        sum_formula = '=+IF(SUM(C%(cr)s:J%(cr)s)=0,"",SUM(C%(cr)s:J%(cr)s))' % {
            'cr': current_row
        }

        ws.cell(row=current_row, column=1, value=assignment['name'])
        ws.cell(row=current_row, column=2, value=assignment['feedback_id'])
        ws.cell(row=current_row, column=11, value=sum_formula)

        try:
            ws.cell(row=current_row, column=13, value=weights[assignment['name']])
        except KeyError:
            pass

        ws.cell(row=current_row, column=14, value=assignment['feedback_url'])
        ws.cell(row=current_row, column=15, value=assignment['paper_url'])
        ws.cell(row=current_row, column=16, value=' ') # Make sure url is not extended past col

        current_row += 1

    print('Saving grades to %s' % workbook_path)
    if os.path.exists(workbook_path):
        question = input('Do you wish to overwrite %s? (y/n)' % workbook_path)
        if question == 'y':
            wb.save(workbook_path)
        else:
            wb.save("assignments/%s/grades-new.xlsx" % assignment_name)
    else:
        wb.save(workbook_path)


def pull_assignments(session):
    """visits each assigned task, pulls the assignment as feedback_id"""
    resp = session.get(BASE_URL)
    page = resp.text
    tree = fromstring(page)

    assignment_name = tree.xpath(ASSIGNMENT_NAME_XPATH)[0].text.title()

    print('Pulling assignments for %s as %s...' % (assignment_name, USERNAME))

    links = tree.xpath(ASSIGNMENT_LINKS_XPATH)

    if not os.path.exists('assignments/%s/Data' % (assignment_name)):
        os.makedirs('assignments/%s/Data' % (assignment_name))

    tasks = []
    rubric = []

    for link in links:
        st_name = None
        pf_link = link.get('href')
        fb_resp = session.get(BASE_URL + pf_link)
        fb_page = fb_resp.text
        fb_tree = fromstring(fb_page)
        dl_link = fb_tree.xpath(ASSIGNMENT_LINK_XPATH)[0].get('href')
        assert(dl_link)

        if not rubric:
            rubric_table = fb_tree.xpath(RUBRIC_TABLE_XPATH)[-1]
            rubric = [
                r.text.strip()
                for r in fb_tree.xpath(RUBRIC_TEXT_XPATH)]

        for a in fb_tree.xpath(STUDENT_NAME_XPATH):
            if a.text.strip():
                st_name = a.text.strip()
                break

        if st_name is None: assert(0), 'Couldn\'t pull student name'
        tasks.append({
            'name': st_name.lower().strip(),
            'feedback_url': BASE_URL+pf_link,
            'feedback_id': pf_link.split('/')[-1],
            'paper_url': dl_link})

        filepath = 'assignments/%s/Papers/' % assignment_name
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        filename = filepath + st_name.replace(' ', '') + '.pdf'
        resp = session.get(dl_link)
        with open(filename, 'wb') as f:
            f.write(resp.content)

    with open('assignments/%s/Data/assignments.json' % assignment_name, 'w') as file:
        json.dump(tasks, file)

    with open('assignments/%s/Data/rubric.json' % assignment_name, 'w') as file:
        json.dump(rubric, file)

    with open('assignments/%s/Data/weights.json' % assignment_name, 'w') as file:
        # Weighted scores reflect a 'best guess' score for the paper, based
        # on peerfeed back for the student. Still very rough at the moment,
        # and does poorly on outliers
        weights = get_weighted_scores(assignment_name, session)
        json.dump(weights, file)

    populate_spreadsheet(assignment_name, tasks)


def process():
    session = login(USERNAME, PASSWORD)
    pull_assignments(session)

if __name__ == "__main__":
    process()
