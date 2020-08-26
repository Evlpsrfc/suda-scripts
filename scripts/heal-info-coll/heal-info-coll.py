import requests
import hashlib
import datetime
import re
import json

student_id = input('学号：')
password = input('密码：')
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


def query_data(cookie_jar):
    payload = {
        "params": {
            "empcode": student_id,
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
    entity.update({
        "tbrq": str(datetime.datetime.now())[:10],
        # "tbrq": "2020-08-26",
        "tjsj": str(datetime.datetime.now())[:16],
        # "tjsj": "2020-08-26 00:00"
        "__type": "sdo:com.sudytech.work.suda.jkxxtb.jkxxtb.TSudaJkxxtb"
    })
    # print(entity)
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
        data=query_data(r.cookies),
        headers={
            "content-type": "text/json"
        },
        cookies=r.cookies
    )
    print(r.text)
