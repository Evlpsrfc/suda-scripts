import requests
import hashlib
import datetime
import re
import json

student_id = input('学号：')
password = input('密码：')
time = None
# time = "00:00"
date = None
# date = "2049-01-01"


login_data = {
    "IDToken1": student_id,
    "IDToken9": password,
    "IDToken2": hashlib.md5(password.encode("utf8")).hexdigest()
}

auth_url = "http://myauth.suda.edu.cn/default.aspx?app=sswsswzx2"
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


if __name__ == "__main__":
    r = requests.get(auth_url)
    r = requests.post(r.url, data=login_data, allow_redirects=False)
    if 'iPlanetDirectoryPro' not in r.cookies:
        print('Wrong password!')
        exit(1)
    r = requests.get(mis_url, cookies=r.cookies)
    r = requests.post(
        post_url,
        data=query_data(r.cookies, time, date),
        headers={
            "content-type": "text/json"
        },
        cookies=r.cookies
    )
    print(r.text)
