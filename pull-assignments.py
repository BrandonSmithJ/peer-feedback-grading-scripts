from selenium import webdriver
from openpyxl.workbook import Workbook
from openpyxl import load_workbook
import datetime
import urllib.request
import os, json


LOGIN_URL = 'https://peerfeedback.gatech.edu/login'
GRADING_TEMPLATE_PATH = "templates/KBAI PF Grading Template.xltx"
driver = webdriver.Chrome('./chromedriver')


def login():
    """prompts user to enter username and password to use"""
    driver.get(LOGIN_URL)

    username = driver.find_element_by_id('username')
    password = driver.find_element_by_id('password')

    user = input("Enter your Peer Feedback email: ")
    pswd = input("Enter your Peer Feedback password: ")

    username.send_keys(user)
    password.send_keys(pswd)

    element = driver.find_element_by_id('_submit')
    element.submit()

    return driver

def populate_spreadsheet(assignment, assignments):

    path = "assignments/%s/assignments.json" % (assignment)

    workbook_path = "assignments/%s/grades.xlsx" % (assignment)
    wb = load_workbook(GRADING_TEMPLATE_PATH)
    wb.template = False
    ws = wb.active
    ws['A1'] = 'Generated on %s' % (datetime.datetime.now())

    start_row = 8
    current_row = start_row
    for assignment in assignments:
        ws.cell(row=current_row, column=1, value=str(assignment['name']))
        ws.cell(row=current_row, column=2, value=str(assignment['feedback_id']))
        current_row += 1

    wb.save(workbook_path)


def pull_assignments():
    """visits each assigned task, pulls the assignment as feedback_id"""
    assignments = []
    links = driver.find_elements_by_xpath("//a[contains(@class, 'taskButton')]")

    assignment_name = driver.find_element_by_xpath("//div[contains(@class, 'taskCard')]//h4").text
    os.makedirs('assignments/%s' % (assignment_name), exist_ok=True)

    for link in links:
        feedback_url = link.get_attribute('href')
        feedback_id = feedback_url.split("feedback/", 1)[1]
        assignments.append(dict(
            feedback_id=feedback_id,
            feedback_url=feedback_url
        ))

    for assignment in assignments:
        driver.get(assignment['feedback_url'])
        download_link = driver.find_element_by_xpath("//h2/a")
        assignment_url = download_link.get_attribute('href')

        # Scrape Student Name
        form = driver.find_element_by_xpath("//form[contains(@id, 'submitStudentSubmissionCommentForm')]")
        student_checkbox = form.find_element_by_class_name("checkbox")
        assignment['name'] = student_checkbox.find_elements_by_tag_name("a")[1].text

        path = "assignments/%s/%s.pdf" % (assignment_name, assignment['feedback_id'])

        urllib.request.urlretrieve(assignment_url, path)

    with open('assignments/%s/assignments.json' % assignment_name, 'w') as file:
        json.dump(assignments, file)

    populate_spreadsheet(assignment_name, assignments)


def process():
    login()
    pull_assignments()
    driver.close()

if __name__ == "__main__":
    process()
