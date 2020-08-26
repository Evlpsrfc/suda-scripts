import requests
import bs4
from bs4 import BeautifulSoup
import re


base_url = "http://xk.suda.edu.cn/"


def parse_view_state(html):
    soup = BeautifulSoup(html, features="lxml")
    for tag in soup.find_all('input'):
        if tag['name'] == "__VIEWSTATE":
            return tag['value']


def get_icode(html):
    soup = BeautifulSoup(html, features="lxml")
    icode = soup.select('#icode')[0]
    icode_url = base_url + icode['src'].strip('/')
    r_code = requests.get(icode_url, cookies=r.cookies)
    with open('icode.png', 'wb') as f:
        f.write(r_code.content)


def parse_schedule(html):
    soup = BeautifulSoup(html, features="lxml")
    table = soup.select('#Table1')[0]
    course_list = []
    i = 0
    for tr in table.contents:
        if tr == '\n':
            continue
        j = 0
        for td in tr.contents:
            if td == '\n':
                continue
            # rowspan indicates how many "time trunks" the course takes
            rowspan = int(td.get('rowspan', '1'))
            a = td.contents[0]
            if type(a) == bs4.element.Tag:
                course_list.append([
                    # because '上午', '下午', and '晚上' take one column,
                    # and they lies on the 2, 6, 10 row
                    [j - 1 if i in [2, 6, 10] else j, i - 1, rowspan],
                    # escape <br>
                    a.contents[0],
                    a.contents[2],
                    a.contents[4],
                    a.contents[6]
                ])
            j += 1
        i += 1
    course_list.sort()
    courses = []
    for course in course_list:
        course[2] = re.sub('.*第(.*?)周.*', '\g<1>', course[2])
        if len(courses) and all(courses[-1][i] == course[i] for i in  range(1, 5)):
            courses[-1][0][2] += course[0][2]
        else:
            courses.append(course)
    return courses


if __name__ == "__main__":
    student_id = input('学号：')
    password = input('密码：')
    # get code, view state, and cookies
    r = requests.get(base_url)
    view_state = parse_view_state(r.text)
    get_icode(r.text)
    cookies = r.cookies
    # login
    data = {
        'TextBox1': student_id,
        'TextBox2': password,
        'TextBox3': input('验证码：'),
        'Button1': '',
        '__VIEWSTATE': view_state
    }
    r = requests.post(base_url, data=data, cookies=cookies)
    # get name
    name = re.search('xm=(.*?)&', r.text)[1]
    name = requests.utils.quote(name)
    schedule_url = f'{base_url}/xskbcx.aspx?xh={student_id}&xm={name}&gnmkdm=N121603'
    # re-get view_state
    headers = {
        'Referer': schedule_url
    }
    r = requests.get(schedule_url,
                     cookies=cookies,
                     headers=headers)
    view_state = parse_view_state(r.text)
    # get years and selected year
    soup = BeautifulSoup(r.text, features="lxml")
    year_options = soup.select('#xnd')[0]
    year_list = []
    selected_year = None
    for opt in year_options.contents:
        if type(opt) == bs4.element.Tag:
            if opt.get('selected', None):
                selected_year = opt['value']
            year_list.append(opt['value'])
    # get selected term
    term_options = soup.select('#xqd')[0]
    selected_term = None
    for opt in term_options.contents:
        if type(opt) == bs4.element.Tag:
            if opt.get('selected', None):
                selected_term = opt['value']
    # get selected schedule
    # i cannot get this schedule through the post below,
    # and i donnot know why :(
    with open(f'{selected_year}-{selected_term}.txt', 'w') as f:
        f.write(str(parse_schedule(r.text)))
    # get schedules
    data = {
        '__EVENTTARGET': 'xnd',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': view_state
    }
    headers = {
        'Referer': schedule_url
    }
    for year in year_list:
        for term in ['1', '2', '3']:
            if year == selected_year and term == selected_term:
                continue
            data['xnd'] = year
            data['xqd'] = term
            r = requests.post(schedule_url,
                              data=data,
                              cookies=cookies,
                              headers=headers)
            if re.search('您本学期课所选学分小于 0分', r.text) is None:
                with open(f'{year}-{term}.txt', 'w') as f:
                    f.write(str(parse_schedule(r.text)))
