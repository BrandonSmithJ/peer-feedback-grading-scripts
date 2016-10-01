from selenium import webdriver
import urllib.request


LOGIN_URL = 'https://peerfeedback.gatech.edu/login'


def login(driver):
    """prompts user to enter username and password to use"""
    # import pdb;pdb.set_trace()
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

def parse_assignments(driver):
    assignments = []
    links = driver.find_elements_by_xpath("//a[contains(@class, 'taskButton')]")

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
        filename = "assignments/%s.pdf" % (assignment['feedback_id'])
        urllib.request.urlretrieve(assignment_url, filename)

    return assignments

def process(driver):
    login(driver)
    assignments = parse_assignments(driver)
    populate_spreadsheet(driver)


if __name__ == "__main__":
    driver = webdriver.Chrome('./chromedriver')
    # driver = webdriver.PhantomJS('./phantomjs')
    process(driver)
    driver.close()
