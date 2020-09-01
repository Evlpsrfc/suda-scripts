import requests
import datetime
import re
import json

student_id = input('学号：')
password = input('密码：')
time = input('时间（格式为00:00，不填默认为当前时间）：')
date = input('日期（格式为1970-01-01，不填默认为当前日期）：')

# 师生网上事务中心（sswsswzx）
default_sswsswzx2 = "http://myauth.suda.edu.cn/default.aspx?app=sswsswzx2"
login_jsp = "http://aff.suda.edu.cn/_web/fusionportal/login.jsp"
login_sswsswzx2 = "http://myauth.suda.edu.cn/middleware/login?app=sswsswzx2"

# Health information reporting 健康信息填报（jkxxtb）
hir_url = "http://dk.suda.edu.cn/default/work/suda/jkxxtb"
mis_url = f"http://aff.suda.edu.cn/mobile/identityServer?targetUrl={hir_url}/jkxxcj.jsp"
post_url = f"{hir_url}/com.sudytech.portalone.base.db.saveOrUpdate.biz.ext"
query_url = f"{hir_url}/com.sudytech.portalone.base.db.queryBySqlWithoutPagecond.biz.ext"


def _query_today(cookie_jar, tbrq):
    payload = {
        "params": {
            "empcode": student_id,
            "tbrq": tbrq
        },
        "querySqlId": "com.sudytech.work.suda.jkxxtb.jkxxtb.queryToday"
    }
    r = requests.post(
        query_url,
        data=json.dumps(payload),
        headers={
            "content-type": "text/json"
        },
        cookies=cookie_jar
    )
    lst = json.loads(r.text)['list']
    if len(lst):
        return lst[0]["ID"]


def query_data(cookie_jar, time=None, date=None):
    now = str(datetime.datetime.now())
    tbrq = date if date else now[:10]
    tjsj = f'{tbrq} {time if time else now[11:16]}'
    payload = {
        "params": {
            "empcode": student_id
        },
        "querySqlId": "com.sudytech.work.suda.jkxxtb.jkxxtb.queryNear"
    }
    r = requests.post(
        query_url,
        data=json.dumps(payload),
        headers={
            "content-type": "text/json"
        },
        cookies=cookie_jar
    )
    entity = dict()
    for k, v in json.loads(r.text)['list'][0].items():
        if v is not None:
            entity[k.lower()] = v
    entity["id"] = _query_today(cookie_jar, tbrq)
    if entity["id"] is None:
        del entity["id"]
    entity.update({
        "tbrq": tbrq,
        "tjsj": tjsj,
        "__type": "sdo:com.sudytech.work.suda.jkxxtb.jkxxtb.TSudaJkxxtb"
    })
    return json.dumps({'entity': entity})


def parse_token(html):
    login_data = {
        "username": student_id,
        "password": password,
        "source": "cas",
        "_eventId": "submit"
    }
    match = re.search("name=\"execution\" value=\"(.*?)\"", html)
    login_data["execution"] = match[1]
    match = re.search("name=\"lt\" value=\"(.*?)\"", html)
    login_data["lt"] = match[1]
    return login_data


if __name__ == "__main__":
    cookie_jar = dict()
    r = requests.get(default_sswsswzx2)
    # JSESSIONID
    cookie_jar.update(r.cookies)
    r = requests.post(r.url,
                      data=parse_token(r.text),
                      cookies=r.cookies,
                      allow_redirects=False)
    
    if "CAS_TICKET" not in r.cookies:
        print("账号或密码错误")
        exit(1)
    
    # CAS_TICKET, CASTGC
    cookie_jar.update(r.cookies)
    r = requests.get(r.headers['Location'],
                     cookies={
                         "JSESSIONID": cookie_jar["JSESSIONID"],
                         "CAS_TICKET": cookie_jar["CAS_TICKET"]
                     },
                     allow_redirects=False)
    # JSESSIONID, LOGIN_TOKEN
    cookie_jar.update(r.cookies)

    r = requests.get(login_jsp, allow_redirects=False)
    JSESSIONID = r.cookies["JSESSIONID"]
    r = requests.get(login_sswsswzx2, allow_redirects=False)
    r = requests.get(r.headers["Location"],
                     cookies={
                         "JSESSIONID": cookie_jar["JSESSIONID"],
                         "LOGIN_TOKEN": cookie_jar["LOGIN_TOKEN"],
                         "CAS_TICKET": cookie_jar["CAS_TICKET"]
                     },
                     allow_redirects=False)
    r = requests.get(r.headers["Location"],
                     cookies={
                         "CAS_TICKET": cookie_jar["CAS_TICKET"]
                     },
                     allow_redirects=False)
    r = requests.get(r.headers["Location"],
                     cookies={
                         "JSESSIONID": JSESSIONID
                     },
                     allow_redirects=False)
    r = requests.get(mis_url, cookies={"JSESSIONID": JSESSIONID})

    r = requests.post(
        post_url,
        data=query_data(r.cookies, time, date),
        headers={
            "content-type": "text/json"
        },
        cookies=r.cookies
    )
    print(r.text)
