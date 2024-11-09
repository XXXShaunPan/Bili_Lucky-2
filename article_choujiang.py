# coding = utf-8
import subprocess
import requests as rq
import random
import time
import copy
import os
import re
from datetime import datetime
from pytz import timezone
from requests.exceptions import *
import execjs
from LogScript import Log
from emailSender import EmailSender

log_ = None
check_follow_ban = False
proxies = {}
context = execjs.compile(open('bili_index_encrypt.js').read())
cookie, article_id, MAILLQQ, MAILLSECRET = [
    os.environ.get(key,'') for key in ["BILI_COOKIE", "article_id", "MAILLQQ", "MAILLSECRET"]
]
csrf = list(filter(lambda x: 'bili_jct' in x,
                   cookie.split('; ')))[0].split('=')[1]

article_uid = [
    '226257459',
    # '3493086911007529'
]

error_num = 0
need_follow_account = []
today = datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
today_filename = datetime.now(
    timezone('Asia/Shanghai')).strftime('%Y-%m-%d=%H')

header = {
    'authority': 'api.vc.bilibili.com',
    'cookie': cookie,
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'content-type': ''
}

header_noCookie = {
    'authority': 'api.vc.bilibili.com',
    'cookie': cookie,
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'content-type': 'application/json'
}

data_follow = {'act': '1', 'fid': '457235238', 're_src': '0', 'csrf': csrf}

data_repost = {
    'uid': '1090970340',
    'dynamic_id': '',
    'content': '~！',
    'extension': '{"emoji_type":1}',
    'at_uids': '',
    'ctrl': '[]',
    'csrf_token': csrf,
    'csrf': csrf
}

new_data_repost = {
    'dyn_req': {
        'content': {
            'contents': []
        },
        'scene': 4,
        'attach_card': None,
        'meta': {
            'app_meta': {
                'from': 'create.dynamic.web',
                'mobi_app': 'web'
            }
        }
    },
    'web_repost_src': {
        'dyn_id_str': '869320467567083529'
    }
}

data_comment = {
    'oid': '976124067840000005',
    'type': '17',
    'message': '~122',
    'plat': '1',
    'ordering': 'heat',
    # 'jsonp': 'jsonp',
    'gaia_source': 'main_web',
    'csrf': csrf,
}

data_thumbsUp = {
    'dyn_id_str': '',
    'up': 1,
    'csrf': csrf,
}


def send_email(title='', content=''):
    if content.endswith('.log'):
        with open(f'{content}', 'r', encoding='utf-8') as f:
            content = f.read()
    with EmailSender(username=MAILLQQ,
                     password=MAILLSECRET,
                     smtpserver='smtp.qq.com',
                     sender='动态Lucky-report') as email:
        email.send([MAILLQQ], title, content)


def save_dynamic(dynamic_id, send_id, filename='bili_lucky_dyid_list.txt'):
    with open(filename, 'a', encoding='utf-8') as f:
        f.writelines(f'{dynamic_id}=={send_id}\n')


# 	rd.lpush("already_dynamic_id-2", dynamic_id)


def get_already_dynamic_id(filename='bili_lucky_dyid_list.txt'):
    # 获取所有已经发送过的存在的动态id
    # return list(map(lambda x: x['dynamic_id'], col_dynamic.find({}, {'_id': 0, 'dynamic_id': 1})))
    with open(filename, 'r', encoding='utf-8') as f:
        all_ids = f.read().split('\n')[-1000:]
        return list(map(lambda x: x.split('==')[0], all_ids))


def get_son_dy_url(x):
    return f'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost_detail?dynamic_id={x}'


def get_word_from_son_dy_url(x):
    return f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail/forward?id={x}"


def create_check_user_info_url(x):
    wts, rid = context.call('mainf', x).values()
    return f"https://api.bilibili.com/x/space/wbi/acc/info?mid={x}&token=&platform=web&web_location=1550101&w_rid={rid}&wts={wts}"


def func(x, y):

    return x if y in x else x + [y]


def process_already_art_id(article_id=0, options='read'):
    if options == 'read':
        with open('bili_lucky_detail/alread_process_article_id.txt', 'r') as f:
            return f.read().split('\n')
    else:
        with open('bili_lucky_detail/alread_process_article_id.txt', 'a') as f:
            f.write(f'\n{article_id}')
        send_email(title='success',
                   content=f'bili_lucky_detail/{article_id}_logger.log')


article_ids = process_already_art_id()
# article_ids = []

def requests_error_reponse(request, response):
    ...


def spider_post(url, data1, data_type):
    # asyncio.sleep(3)
    for _ in range(5):
        time.sleep(3)
        try:
            if data_type == 'json':
                header['content-type'] = 'application/json'
                res = rq.post(url,
                              headers=header,
                              json=data1,
                              proxies=proxies,
                              timeout=5)
            else:
                header['content-type'] = 'application/x-www-form-urlencoded'
                res = rq.post(url,
                              headers=header,
                              data=data1,
                              proxies=proxies,
                              timeout=5)
            return res.json()
        except (RequestException, HTTPError, ConnectionError, ProxyError,
                SSLError, Timeout, ConnectTimeout, ReadTimeout, InvalidSchema,
                InvalidURL, InvalidHeader, InvalidProxyURL,
                ContentDecodingError, RetryError, RequestsWarning) as e:
            log_.error(f'post_{e}')
    raise ValueError('Post请求失败', url)


def req_get(url, need_check_ban=False):
    for _ in range(5):
        try:
            time.sleep(random.randint(1, 4))
            res = rq.get(url,
                         headers=header_noCookie,
                         proxies=proxies,
                         timeout=5)
            if need_check_ban and '风控' in res.json()['message']:
                raise HTTPError(res.json()['message'])
            return res
        except (RequestException, HTTPError, ConnectionError, ProxyError,
                SSLError, Timeout, ConnectTimeout, ReadTimeout, InvalidSchema,
                InvalidURL, InvalidHeader, InvalidProxyURL,
                ContentDecodingError, RetryError, RequestsWarning) as e:
            log_.error(e)
    raise ValueError('GET请求失败', url)


def func_get_random_word():
    return random.choice(['来了', '1', '可以', '在这'])


def parse_article_get_dy(article_id):
    globals().update({
        'log_':
        Log(name=f'{article_id}_logger',
            path=f'bili_lucky_detail/{article_id}_logger.log',
            log_level=None,
            is_write_to_console=None,
            is_write_to_file=True,
            color=None,
            mode=None,
            max_bytes=None,
            backup_count=None,
            encoding=None,
            log_format="%(asctime)s|line:%(lineno)d| %(message)s"
            ),
        'article_id':
        article_id
    })
    log_.info(f'processing article {article_id}')
    if not article_id:
        return []
    res = req_get(f'https://www.bilibili.com/read/cv{article_id}').text
    result = list(
        set(re.findall(r'https://\w+\.?bilibili.com/[opus/]*([0-9]{18})',
                       res)))
    b23_list = re.findall('href="https://b23.tv/(.+?)">', res)
    b23_list = list(set(b23_list))
    #   result = reduce(func,[[]]+result+b23_list)
    b23_list = transform_to_dy_id(b23_list)
    #   return parse_dynamic_order(result)
    return result + b23_list


def parse_dynamic_order(result):
    if order_dy_type(result[2]):
        result.reverse()
    return result


def order_dy_type(dy_id):  # 检查官方与非官方的顺序
    res = req_get(
        f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dy_id}"
    ).json()['data']['card']
    return 'extension' in res.keys()


def transform_to_dy_id(b23_list):  # https://b23.tv/vLj7KNq
    if not b23_list:
        return []
    ids = []
    for url in b23_list:
        try:
            response = req_get("https://b23.tv/" + url)
            url1 = response.history[0].headers['Location']
            id = re.findall(r".*dynamic/([0-9]*)\?.*", url1)
            ids.append(id[0])
        except:
            pass
    return ids


def action():
    article_id = []
    for uid in article_uid:
        articles = req_get(
            f"https://api.bilibili.com/x/space/article?mid={uid}&pn=1&ps=12&sort=publish_time"
        ).json()['data']['articles']
        for i in articles:
            print(i)
            if str(i['id']) not in article_ids and (time.time() -
                                                    i['ctime']) < 36 * 3600:
                article_id.append(str(i['id']))
            else:
                break
    # article_id=articles[1]['id']


#   for i in article_id:
#       result.extend(parse_article_get_dy(i))
    return article_id


def get_comment_word(dy_id, is_origin=0):
    repost_details = req_get(get_word_from_son_dy_url(dy_id)).json()
    repost_details = repost_details['data']['items']
    for repost_detail in repost_details:
        user_type = repost_detail['user']['official']['type']
        if ('//' in repost_detail['desc']['text']
            ) ^ is_origin and user_type != 1:
            word = re.sub(r'\u200b|\u200c|\u200d|\u200b|\u200c', '',
                          repost_detail['desc']['text']).split('//')[0]
            if word != '转发动态' and word != '':
                data_comment['message'] = word
                return
    data_comment['message'] = func_get_random_word()
    # if not is_origin:  # 是为源动态
    #     data_repost['content'] = data_comment['message']
    # else:
    #     data_repost['content'] = word


def get_uid_oid(dy_id):
    try:
        res = req_get(
            f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dy_id}"
        ).json()
        keys = res['data']['card']['desc']

        if 'lottery_id' in res['data']['card'].get(
                'extend_json', '') or res['data']['card'].get(
                    'extension') or "reserve_id" in res['data']['card'][
                        'extend_json'] or res['data']['card']['display'].get(
                            'add_on_card_info'):
            # reserve_id = json.loads(
            #     res['data']['card']['extend_json']).get('reserve_id')
            # if reserve_id:
            #     to_booking_activity(reserve_id, dy_id)
            return 1
        # log_.info(keys)
        if keys.get('origin'):
            log_.info('=========此为子动态=========')
            get_comment_word(keys['origin']['dynamic_id_str'], 1)
            if not parse_origin_dy(keys['origin']):
                return 0
        else:
            log_.info('=========此为源动态=========')
            get_son_lucky_dy(dy_id)
        return keys['uid'], keys['rid'], int(keys['orig_dy_id_str'])
    except Exception as e:
        globals()['error_num'] += 1
        log_.error(e)
        log_.error(f"error line:{e.__traceback__.tb_lineno}")
        return 0


def get_mid_from_son_dy(dy_id):
    res = req_get(f"https://api.bilibili.com/x/v2/reply/subject/description?oid={dy_id}&type=17&web_location=333.1368").json()['data'].get('base')
    if res:
        return res['up_mid']
    return 348933133


def get_son_lucky_dy(dy_id, is_official=False):
    res = req_get(get_son_dy_url(dy_id)).json()['data']['items']
    log_.info('*********子动态开始*********')
    for j in res:
        try:
            # i = json.loads(j['card'])
            # if j['desc']['user_profile']['card']['official_verify']['type'] == 1 and all([key in i['item']['content'] for key in ['关注', '抽']]):
            if j['desc'].get('pre_dy_id_str') != j['desc']['orig_dy_id_str']:
                #       if all([key in i['item']['content'] for key in ['关注','抽']]) and '//' not in i['item']['content']:
                son_dy_id = j['desc']['pre_dy_id_str']
                if son_dy_id not in already_dynamic_id:
                    get_comment_word(son_dy_id)
                    send_id = to_repost(son_dy_id, source='son')
                    if send_id and to_comment(1, son_dy_id, True):
                        to_follow(get_mid_from_son_dy(son_dy_id))
                        already_dynamic_id.append(son_dy_id)
                        log_.info('----完成一个子动态----')
        except Exception as e:
            globals()['error_num'] += 1
            log_.error(e)
            log_.error(f"error line:{e.__traceback__.tb_lineno}")
    log_.info("*********子动态结束*********")


def parse_origin_dy(origin):
    orig_dy_id = origin['dynamic_id_str']
    if orig_dy_id not in already_dynamic_id:
        log_.info("*************原动态处理开始***************")
        send_id = to_repost(orig_dy_id)
        if send_id and to_comment(origin['rid'], orig_dy_id,
                                  False,
                                  origin['type']):
            to_follow(origin['uid'])
            to_thumbsUp(orig_dy_id)
            # if origin['type']!=8:

            already_dynamic_id.append(orig_dy_id)
            log_.info("*************原动态处理完成***************")
        else:
            return 0
    else:
        log_.info("*************原动态已存在***************")
    get_son_lucky_dy(orig_dy_id)
    return 1


def to_booking_activity(reserve_id, dyid):
    url = "https://api.bilibili.com/x/dynamic/feed/reserve/click?csrf=" + csrf
    booking_data = {
        "reserve_id": reserve_id,
        "cur_btn_status": 1,
        "dynamic_id_str": dyid,
        "reserve_total": 1,
        "spmid": ""
    }
    booking_res = spider_post(url, booking_data, 'json')
    return booking_res.get('data', {}).get('toast') or dyid + '预约失败'


def to_follow(uid):
    global check_follow_ban
    try:
        if not check_follow_ban and req_get(create_check_user_info_url(uid), need_check_ban=True).json()['data']['is_followed']:
            log_.info(f'{uid} === 已经关注了')
            return
    except Exception as e:
        check_follow_ban = True
        log_.error(f'check接口被ban')
    data_follow['fid'] = uid
    res = spider_post("https://api.bilibili.com/x/relation/modify",
                      data_follow, 'data')
    # if res['code'] == 0:
    msg = res.get('message', '')
    if '异常' in msg:
        need_follow_account.append(uid)
    log_.info(f"关注 ==== {uid} {msg}")


def add_repost_content_item(text, type=1, biz_id=''):
    return {'raw_text': text, 'type': type, 'biz_id': biz_id}


def to_repost(dynamic_id, source='available'):
    """
    dy_type 是否为子动态 取消了
    """
    res = req_get(
        f'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?timezone_offset=-480&id={dynamic_id}&features=itemOpusStyle'
    ).json()['data']['item']
    user = res['modules']['module_author']

    if user['official_verify']['type'] != 1 and source == 'son':
        return 0
    dy_type = res.get('orig')
    # repost_item = new_data_repost.copy()
    repost_item = copy.deepcopy(new_data_repost)
    repost_item['web_repost_src']['dyn_id_str'] = dynamic_id
    repost_item['dyn_req']['content']['contents'].append(
        add_repost_content_item(f'{data_comment["message"]}' +
                                ('//' if dy_type else '')))
    if dy_type:
        dy_desc = res['modules']['module_dynamic']['desc']['rich_text_nodes']
        repost_item['dyn_req']['content']['contents'].append(
            add_repost_content_item(f'@{user["name"]}:', 2, str(user['mid'])))
        for i in dy_desc:
            item = add_repost_content_item(
                i['orig_text'], (i['type'] == 'RICH_TEXT_NODE_TYPE_AT') + 1,
                str(i.get('rid', '')))
            repost_item['dyn_req']['content']['contents'].append(item)
    # data_repost['content']=tuling.get_response(random.choice(['啦啦啦','嘻嘻嘻','嘿嘿嘿']))
    repost_res = spider_post(
        "https://api.bilibili.com/x/dynamic/feed/create/dyn?csrf=" + csrf,
        repost_item, 'json')
    if repost_res['code'] == 0:
        log_.info(f"转发成功 {repost_res['data']['dyn_id_str']}")
        send_id = repost_res['data']['dyn_id_str']
        save_dynamic(*(dynamic_id, send_id))
        return send_id
    return 0


def to_comment(oid, dy_id, not_origin, type=0):
    # 需要获取动态的oid，才能发送评论
    # get_oid_url="https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id="+dynamic_id
    # oid=spider_get(get_oid_url)['data']['card']['desc']['rid']
    if not not_origin:
        data_comment.update({"oid": oid, 'type': '11'})
    else:
        data_comment.update({"oid": dy_id, 'type': '17'})
    if type == 8:
        data_comment.update({"oid": oid, 'type': '1', 'ordering': 'heat'})
    res = spider_post("https://api.bilibili.com/x/v2/reply/add",
                      data_comment, 'data')
    log_.info('评论' + res['data']['success_toast'])
    return res['data'].get('success_toast', 0)


def to_thumbsUp(dynamic_id):
    data_thumbsUp['dyn_id_str'] = str(dynamic_id)
    res = spider_post(
        "https://api.bilibili.com/x/dynamic/feed/dyn/thumb?csrf=" + csrf,
        data_thumbsUp, 'json')
    log_.info(f"动态-点赞 {res.get('message')}")


def main(dys):
    log_.info(
        "==================================================" +
        datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M') +
        "==================================================")
    if not dys:
        #       log_.info("---开始用户抽奖---")
        #       os.system('python3 follow.py >> users_lucky.log')
        #       log_.info("---结束用户抽奖---")
        return
    global error_num
    for dy_id in dys:
        print()
        log_.info(f'https://t.bilibili.com/{dy_id}', )
        if dy_id in already_dynamic_id:
            log_.info("已有")
            continue
        result = get_uid_oid(dy_id)
        # break
        if result == 1:  # 到官方抽奖了
            log_.info("官方 或 预约 OUT！")
            # get_son_lucky_dy(dy_id, is_official=True)
            #               official_list.append(dy_id)
            #               if len(official_list)>5:
            #                   break
            continue
        if not result:
            log_.error('*#*#*#*#*#*#*#*#*#*原动态处理失败*#*#*#*#*#*#*#*#*#')
            continue
        uid, oid, not_origin = result
        if dy_id not in already_dynamic_id:
            log_.info('-=-=-=-=处理回最初的动态-=-=-=-=')
            get_comment_word(dy_id, not_origin == 0)
            try:
                send_id = to_repost(dy_id)
                if send_id and to_comment(oid, dy_id, not_origin):
                    to_follow(uid)
                    to_thumbsUp(dy_id)
                    # log_.info(uname + "\n\n")
                    already_dynamic_id.append(dy_id)
            except Exception as e:
                globals()['error_num'] += 1
                log_.error(e)
                log_.error(f"error line:{e.__traceback__.tb_lineno}")
    #                   today_list.append(dy_id)
        time.sleep(random.randint(1, 4))
    log_.info('执行结束')
    process_already_art_id(
        article_id, 'write') if error_num < 6 else send_email(
            title='执行失败', content=f'bili_lucky_detail/{article_id}_logger.log')
    error_num = 0
    log_.info(
        "==================================================" +
        datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M') +
        "==================================================")


def pre_man():
    if article_id:
        main(parse_article_get_dy(article_id))
        return
    for art_id in action():
        main(parse_article_get_dy(art_id))


already_dynamic_id = get_already_dynamic_id()
# already_dynamic_id = col_dynamic.find({},{'_id':0,'dynamic_id':1})
if __name__ == '__main__':
    pre_man()
    if need_follow_account:
        with open(f'bili_lucky_detail/need_follow_account.txt', 'a') as f:
            f.write('\n'.join(need_follow_account))
