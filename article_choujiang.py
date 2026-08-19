# coding = utf-8
import requests as rq
import random
import time
import copy
import hashlib
import json
import os
import re
from datetime import datetime
from urllib.parse import urlencode, urlparse
from pytz import timezone
from requests.exceptions import *
import execjs
from LogScript import Log
# from emailSender import EmailSender

log_ = None
check_follow_ban = False
proxies = {}
context = execjs.compile(open('bili_index_encrypt.js').read())
cookie, article_id, MAILLQQ, MAILLSECRET = [
    os.environ.get(key, '')
    for key in ["BILI_COOKIE", "article_id", "MAILLQQ", "MAILLSECRET"]
]
cookie = "buvid3=02F7ABD8-6183-074E-2C66-0056F21B199604491infoc; b_nut=1785305304; _uuid=2644BC98-DEDA-1333-9489-538F71EF77B304686infoc; buvid_fp=fcee54640d51e0b6a74d300f77e1d32c; buvid4=96824C3F-36FD-6831-5963-8859B1AE099373681-024092407-+Hkhi4zOncNE1bIJxACXLw%3D%3D; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; rpdid=|(JlR)mlY|lu0J'u~)lJ|lR|k; home_feed_column=5; browser_resolution=1720-966; hit-dyn-v2=1; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODcwNjg1MTIsImlhdCI6MTc4NjgwOTI1MiwicGx0IjotMX0.8VPywlKYp4GTvTszjCQ0TXRXmyKAA9I1rk5g7n0qES4; bili_ticket_expires=1787068452; theme-switch-show=SHOWED; PVID=1; LIVE_BUVID=AUTO4817868093847535; ogv_device_support_dolby=0; ogv_device_support_hdr=1; SESSDATA=90c6ef9e%2C1802489167%2C75467%2A82CjCAUXuvCXaHQpXqLH3ilS8kgpV4dtrNgLXVeRYgSAwfyMnptrT_inqINnpQpGihlEcSVmZ0eHRWQXJiaXpiWklhdjdmcTRnYTFfZ3JjZzNTUnJ4V1psRTNKM25iUjc1eVB1TFZZcEthQ0xFWEJWX0pLbHE4RUZLV1V1TWEwRElXaGZJQjNkaWhnIIEC; bili_jct=486c5c2fce09c5ec00033f1e33e0ea52; DedeUserID=1090970340; DedeUserID__ckMd5=aae500216002dd45; sid=50m358r3; CURRENT_QUALITY=80; bp_t_offset_1090970340=1237424453579702272; CURRENT_FNVAL=2000; b_lsid=7DA25F74_1A0137AB478"
csrf = list(filter(lambda x: 'bili_jct' in x,
                   cookie.split('; ')))[0].split('=')[1]

article_uid = [
    '226257459',
    '100680137',
    # '3493086911007529'
]

error_num = 0
need_follow_account = []
son_dynamic_cache = {}
_wbi_mixin_key = None
today = datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
today_filename = datetime.now(
    timezone('Asia/Shanghai')).strftime('%Y-%m-%d=%H')

header = {
    'authority': 'api.vc.bilibili.com',
    'cookie': cookie,
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'content-type': ''
}

header_noCookie = {
    'authority': 'api.vc.bilibili.com',
    'cookie': cookie,
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'content-type': 'application/json'
}

public_api_headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json,text/plain,*/*',
}

WBI_MIXIN_KEY_ENC_TAB = (
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
)

SPACE_FEED_FEATURES = (
    'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,'
    'forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,'
    'ugcDelete,onlyfansQaCard,avatarAutoTheme,sunflowerStyle,cardsEnhance,'
    'eva3CardOpus,eva3CardVideo,eva3CardComment,eva3CardUser')

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
today = datetime.now().strftime('%Y-%m-%d:%H')
logger = Log(name=f'{today}_logger',
             path=os.environ.get('BILI_LUCKY_LOG_PATH',
                                 f'bili_lucky_detail/{today}_logger.log'),
             log_level=None,
             is_write_to_console=None,
             is_write_to_file=True,
             color=None,
             mode=None,
             max_bytes=None,
             backup_count=None,
             encoding=None,
             log_format="%(asctime)s|line:%(lineno)d| %(message)s")


def send_email(title='', content=''):
    if content.endswith('.log'):
        with open(f'{content}', 'r', encoding='utf-8') as f:
            content = f.read()
    print(title)
    print(content)
    # with EmailSender(username=MAILLQQ,
    #                  password=MAILLSECRET,
    #                  smtpserver='smtp.qq.com',
    #                  sender='动态Lucky-report') as email:
    #     email.send([MAILLQQ], title, content)


def save_dynamic(dynamic_id, send_id, filename='bili_lucky_dyid_list.txt'):
    with open(filename, 'a', encoding='utf-8') as f:
        f.writelines(f'{dynamic_id}=={send_id}\n')


# 	rd.lpush("already_dynamic_id-2", dynamic_id)


def get_already_dynamic_id(filename='bili_lucky_dyid_list.txt'):
    # 获取所有已经发送过的存在的动态id
    # return list(map(lambda x: x['dynamic_id'], col_dynamic.find({}, {'_id': 0, 'dynamic_id': 1})))
    with open(filename, 'r', encoding='utf-8') as f:
        return {
            line.split('==', 1)[0]
            for line in f.read().splitlines() if line
        }


def get_word_from_son_dy_url(dynamic_id, offset=''):
    params = urlencode({
        'id': dynamic_id,
        'offset': offset,
        'web_location': '333.1368',
    })
    return (
        'https://api.bilibili.com/x/polymer/web-dynamic/v1/detail/forward?' +
        params)


def get_dynamic_detail_url(dynamic_id):
    return ("https://api.bilibili.com/x/polymer/web-dynamic/v1/detail"
            f"?timezone_offset=-480&id={dynamic_id}&features=itemOpusStyle")


def get_wbi_mixin_key():
    global _wbi_mixin_key
    if _wbi_mixin_key:
        return _wbi_mixin_key

    result = req_get('https://api.bilibili.com/x/web-interface/nav').json()
    if result.get('code') != 0:
        raise ValueError(
            f'获取 WBI 配置失败: {result.get("code")} {result.get("message", "")}')
    wbi_img = result.get('data', {}).get('wbi_img') or {}
    img_key = os.path.splitext(
        os.path.basename(urlparse(wbi_img.get('img_url', '')).path))[0]
    sub_key = os.path.splitext(
        os.path.basename(urlparse(wbi_img.get('sub_url', '')).path))[0]
    raw_key = img_key + sub_key
    if len(raw_key) < 64:
        raise ValueError('WBI 配置缺少 img_key 或 sub_key')

    _wbi_mixin_key = ''.join(raw_key[index]
                             for index in WBI_MIXIN_KEY_ENC_TAB)[:32]
    return _wbi_mixin_key


def create_wbi_url(url, params, wts=None):
    signed_params = dict(params)
    signed_params['wts'] = int(wts or time.time())
    signed_params = {
        key: ''.join(char for char in str(value) if char not in "!'()*")
        for key, value in signed_params.items()
    }
    query = urlencode(sorted(signed_params.items()))
    signed_params['w_rid'] = hashlib.md5(
        (query + get_wbi_mixin_key()).encode('utf-8')).hexdigest()
    return f'{url}?{urlencode(signed_params)}'


def create_check_user_info_url(x):
    wts, rid = context.call('mainf', x).values()
    return f"https://api.bilibili.com/x/space/wbi/acc/info?mid={x}&token=&platform=web&web_location=1550101&w_rid={rid}&wts={wts}"


def process_already_art_id(article_id=0, options='read'):
    if options == 'read':
        with open('bili_lucky_detail/alread_process_article_id.txt', 'r') as f:
            return set(filter(None, f.read().splitlines()))
    elif article_id:
        with open('bili_lucky_detail/alread_process_article_id.txt', 'a') as f:
            f.write(f'\n{article_id}')


article_ids = process_already_art_id()


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
            res.raise_for_status()
            return res.json()
        except (RequestException, ValueError) as e:
            logger.error(f'post_{e}')
    raise ValueError('Post请求失败', url)


def req_get(url, need_check_ban=False, request_headers=None):
    for _ in range(5):
        try:
            time.sleep(random.randint(1, 4))
            res = rq.get(url,
                         headers=request_headers or header_noCookie,
                         proxies=proxies,
                         timeout=5)
            res.raise_for_status()
            if need_check_ban:
                message = res.json().get('message', '')
                if '风控' in message:
                    raise HTTPError(message)
            return res
        except (RequestException, ValueError) as e:
            logger.error(e)
    raise ValueError('GET请求失败', url)


def func_get_random_word():
    return random.choice(['来了', '1', '可以', '在这'])


def decode_article_html(content):
    content = re.sub(
        r'\\u([0-9a-fA-F]{4})',
        lambda match: chr(int(match.group(1), 16)),
        content,
    )
    return content.replace(r'\/', '/')


def extract_article_dynamic_ids(content):
    content = decode_article_html(content)
    dynamic_ids = list(
        dict.fromkeys(
            re.findall(r'https://\w+\.?bilibili.com/[opus/]*([0-9]{18,})',
                       content)))
    short_links = list(
        dict.fromkeys(re.findall(r'https://b23.tv/([^"?\\\s]+)', content)))
    return dynamic_ids + transform_to_dy_id(short_links)


def extract_opus_dynamic_entries(opus_data):
    entries = []
    seen_ids = set()
    paragraphs = ((opus_data.get('content') or {}).get('paragraphs') or [])
    for paragraph in paragraphs:
        nodes = ((paragraph.get('text') or {}).get('nodes') or [])
        for node in nodes:
            link = node.get('link') or {}
            link_url = link.get('link') or ''
            match = re.search(
                r'https://\w+\.?bilibili.com/[opus/]*([0-9]{18,})',
                link_url,
            )
            if not match:
                continue
            dynamic_id = match.group(1)
            if dynamic_id in seen_ids:
                continue
            seen_ids.add(dynamic_id)
            entries.append({
                'id': dynamic_id,
                'title': link.get('show_text') or '',
                'url': link_url,
            })
    return entries


def fetch_article_api_data(article_id, max_attempts=10):
    url = f'https://api.bilibili.com/x/article/view?id={article_id}'
    public_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json,text/plain,*/*',
    }
    for attempt in range(max_attempts):
        try:
            response = rq.get(url,
                              headers=public_headers,
                              proxies=proxies,
                              timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                return result.get('data') or {}
            logger.warning(f'获取 Article 结构化正文失败 {article_id}: '
                           f'{result.get("code")} {result.get("message", "")}')
        except (RequestException, ValueError) as e:
            logger.warning(f'获取 Article 结构化正文失败 {article_id}: {e}')
        if attempt + 1 < max_attempts:
            time.sleep(0.8 * (attempt + 1))
    return {}


def fetch_article_html(article_id, max_attempts=5):
    public_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    last_content = ''
    for attempt in range(max_attempts):
        url = (f'https://www.bilibili.com/read/cv{article_id}'
               f'?_={int(time.time() * 1000)}-{attempt}')
        try:
            response = rq.get(url,
                              headers=public_headers,
                              proxies=proxies,
                              timeout=10)
            response.raise_for_status()
            last_content = response.text
            if extract_article_dynamic_ids(last_content):
                return last_content
        except RequestException as e:
            logger.warning(f'获取 Article HTML 失败 {article_id}: {e}')
        if attempt + 1 < max_attempts:
            time.sleep(0.5 * (attempt + 1))
    return last_content


def parse_article_dynamic_entries(article_id):
    logger.info(f'processing article {article_id}')
    if not article_id:
        return []

    article_data = fetch_article_api_data(article_id)
    opus_data = article_data.get('opus') or {}
    if opus_data:
        entries = extract_opus_dynamic_entries(opus_data)
        if entries:
            return entries

        dynamic_ids = extract_article_dynamic_ids(
            json.dumps(opus_data, ensure_ascii=False))
        if dynamic_ids:
            return [{
                'id': dynamic_id,
                'title': '',
                'url': f'https://t.bilibili.com/{dynamic_id}',
            } for dynamic_id in dynamic_ids]

    dynamic_ids = extract_article_dynamic_ids(fetch_article_html(article_id))
    if not dynamic_ids:
        logger.warning(f'Article 未解析到动态链接: {article_id}')
    return [{
        'id': dynamic_id,
        'title': '',
        'url': f'https://t.bilibili.com/{dynamic_id}',
    } for dynamic_id in dynamic_ids]


def parse_article_get_dy(article_id):
    return [entry['id'] for entry in parse_article_dynamic_entries(article_id)]


def parse_dynamic_order(result):
    if order_dy_type(result[2]):
        result.reverse()
    return result


def order_dy_type(dy_id):  # 检查官方与非官方的顺序
    return should_skip_dynamic(get_dynamic_detail(dy_id))


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
            if str(i['id']) not in article_ids and (
                    time.time() -
                    i['ctime']) < 36 * 3600 and '【官方抽奖' not in i['title']:
                article_id.append(str(i['id']))
    # article_id=articles[1]['id']


#   for i in article_id:
#       result.extend(parse_article_get_dy(i))
    return article_id


def get_repost_items(dy_id, max_pages=1):
    items = []
    offset = ''
    for _ in range(max_pages):
        result = req_get(get_word_from_son_dy_url(dy_id, offset)).json()
        if result.get('code') != 0:
            logger.warning(f'获取转发列表失败 {dy_id}: {result.get("code")} '
                           f'{result.get("message", "")}')
            break

        data = result.get('data') or {}
        items.extend(data.get('items') or [])
        next_offset = str(data.get('offset') or '')
        if not data.get(
                'has_more') or not next_offset or next_offset == offset:
            break
        offset = next_offset
    return items


def normalize_dynamic_text(text):
    return re.sub(r'\s|\u200b|\u200c|\u200d', '', text or '')


def extract_pre_dynamic_reference(repost_item):
    desc = repost_item.get('desc') or {}
    nodes = desc.get('rich_text_nodes') or []
    separator_seen = False
    for node in nodes:
        node_text = node.get('orig_text') or node.get('text') or ''
        if '//' in node_text:
            separator_seen = True
            continue
        if (separator_seen and node.get('type') == 'RICH_TEXT_NODE_TYPE_AT'
                and node.get('rid')):
            reference_text = (desc.get('text') or '').split('//', 1)[-1]
            reference_text = reference_text.split(':', 1)[-1]
            return str(node['rid']), reference_text
    return '', ''


def find_official_child_dynamic(root_dynamic_id,
                                official_uid,
                                reference_text='',
                                max_pages=5):
    root_dynamic_id = str(root_dynamic_id)
    official_uid = str(official_uid)
    reference = normalize_dynamic_text(reference_text)
    cache_key = (root_dynamic_id, official_uid, reference[:80])
    if cache_key in son_dynamic_cache:
        return son_dynamic_cache[cache_key]

    offset = ''
    fallback_dynamic_id = ''
    api_url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
    for _ in range(max_pages):
        params = {
            'offset':
            offset,
            'host_mid':
            official_uid,
            'timezone_offset':
            -480,
            'platform':
            'web',
            'features':
            SPACE_FEED_FEATURES,
            'web_location':
            '333.1387',
            'dm_img_list':
            '[]',
            'dm_img_str': ('V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ'),
            'dm_cover_img_str':
            ('QU5HTEUgKEFwcGxlLCBBTkdMRSBNZXRhbCBSZW5kZXJlcjogQXBwbGUg'
             'TTEgUHJvLCBVbnNwZWNpZmllZCBWZXJzaW9uKUdvb2dsZSBJbmMuIChB'
             'cHBsZS'),
            'dm_img_inter':
            '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}',
            'x-bili-device-req-json':
            json.dumps(
                {
                    'platform': 'web',
                    'device': 'pc',
                    'spmid': '333.1387'
                },
                separators=(',', ':'),
            ),
        }
        result = req_get(create_wbi_url(api_url, params)).json()
        if result.get('code') != 0:
            raise ValueError(f'获取用户动态失败 {official_uid}: {result.get("code")} '
                             f'{result.get("message", "")}')

        data = result.get('data') or {}
        for item in data.get('items') or []:
            author = (item.get('modules') or {}).get('module_author') or {}
            origin_id = str((item.get('orig') or {}).get('id_str') or '')
            if (str(author.get('mid')) != official_uid
                    or author.get('official_verify', {}).get('type') != 1
                    or origin_id != root_dynamic_id):
                continue

            child_dynamic_id = str(item.get('id_str') or '')
            if not child_dynamic_id:
                continue
            if not fallback_dynamic_id:
                fallback_dynamic_id = child_dynamic_id
            if not reference:
                son_dynamic_cache[cache_key] = child_dynamic_id
                return child_dynamic_id

            desc = ((item.get('modules') or {}).get('module_dynamic')
                    or {}).get('desc') or {}
            candidate = normalize_dynamic_text(desc.get('text'))
            if candidate and (candidate[:40] in reference
                              or reference[:40] in candidate):
                son_dynamic_cache[cache_key] = child_dynamic_id
                return child_dynamic_id

        next_offset = str(data.get('offset') or '')
        if not data.get(
                'has_more') or not next_offset or next_offset == offset:
            break
        offset = next_offset

    son_dynamic_cache[cache_key] = fallback_dynamic_id
    return fallback_dynamic_id


def resolve_son_dynamic_id(root_dynamic_id, repost_item):
    desc = repost_item.get('desc') or {}
    pre_dynamic_id = str(desc.get('pre_dy_id_str') or '')
    origin_id = str(desc.get('orig_dy_id_str') or '')
    if pre_dynamic_id and pre_dynamic_id != origin_id:
        return pre_dynamic_id

    official_uid, reference_text = extract_pre_dynamic_reference(repost_item)
    if not official_uid:
        return ''
    return find_official_child_dynamic(root_dynamic_id, official_uid,
                                       reference_text)


def get_dynamic_detail(dy_id):
    result = req_get(get_dynamic_detail_url(dy_id),
                     request_headers=public_api_headers).json()
    if result.get('code') != 0:
        raise ValueError(
            f'获取动态详情失败 {dy_id}: {result.get("code")} {result.get("message", "")}'
        )
    item = result.get('data', {}).get('item')
    if not item:
        raise ValueError(f'动态详情缺少 item: {dy_id}')
    return item


def parse_dynamic_info(item):
    modules = item.get('modules') or {}
    author = modules.get('module_author') or {}
    basic = item.get('basic') or {}
    origin = item.get('orig') or {}

    uid = author.get('mid')
    oid = basic.get('comment_id_str') or basic.get('rid_str')
    comment_type = basic.get('comment_type')
    if uid is None or not oid or not comment_type:
        raise ValueError(
            f'动态字段不完整: id={item.get("id_str")}, uid={uid}, oid={oid}, '
            f'comment_type={comment_type}')

    return {
        'dynamic_id': str(item.get('id_str') or ''),
        'uid': uid,
        'oid': str(oid),
        'comment_type': int(comment_type),
        'origin_id': str(origin.get('id_str') or ''),
    }


def should_skip_dynamic(item):
    module_dynamic = (item.get('modules') or {}).get('module_dynamic') or {}
    if module_dynamic.get('additional'):
        return True

    raw_item = json.dumps(item, ensure_ascii=False)
    skip_markers = (
        # 'lottery_id',
        # 'reserve_id',
        # 'create.big_plus',
        # 'ADDITIONAL_TYPE_RESERVE',
        'RICH_TEXT_NODE_TYPE_LOTTERY', )
    return any(marker in raw_item for marker in skip_markers)


def get_comment_word(dy_id, is_origin=0):
    try:
        repost_details = get_repost_items(dy_id)
    except Exception as e:
        logger.warning(f'获取评论参考失败 {dy_id}: {e}')
        repost_details = []
    random.shuffle(repost_details)
    for repost_detail in repost_details:
        user_type = repost_detail.get('user', {}).get('official',
                                                      {}).get('type', -1)
        text = repost_detail.get('desc', {}).get('text', '')
        if ('//' in text) ^ is_origin and user_type != 1:
            word = re.sub(r'\u200b|\u200c|\u200d|\u200b|\u200c', '',
                          text).split('//')[0]
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
        item = get_dynamic_detail(dy_id)
        if should_skip_dynamic(item):
            return 1

        dynamic_info = parse_dynamic_info(item)
        origin_id = dynamic_info['origin_id']
        if origin_id:
            logger.info('=========此为子动态=========')
            get_comment_word(origin_id, 1)
            if not parse_origin_dy(origin_id):
                return 0
        else:
            logger.info('=========此为源动态=========')
            get_son_lucky_dy(dy_id)
        return (dynamic_info['uid'], dynamic_info['oid'], bool(origin_id),
                dynamic_info['comment_type'])
    except Exception as e:
        globals()['error_num'] += 1
        logger.error(e)
        logger.error(f"error line:{e.__traceback__.tb_lineno}")
        return 0


def get_mid_from_son_dy(dy_id):
    res = req_get(
        f"https://api.bilibili.com/x/v2/reply/subject/description?oid={dy_id}&type=17&web_location=333.1368"
    ).json()['data'].get('base')
    if res:
        return res['up_mid']
    return 348933133


def get_son_lucky_dy(dy_id, is_official=False):
    logger.info('*********子动态开始*********')
    try:
        res = get_repost_items(dy_id, max_pages=3)
    except Exception as e:
        globals()['error_num'] += 1
        logger.error(f'获取子动态失败 {dy_id}: {e}')
        logger.info("*********子动态结束*********")
        return
    discovered_son_ids = set()
    for j in res:
        try:
            son_dy_id = resolve_son_dynamic_id(dy_id, j)
            if (not son_dy_id or son_dy_id == str(dy_id)
                    or son_dy_id in discovered_son_ids):
                continue
            discovered_son_ids.add(son_dy_id)
            logger.info(f'恢复子动态 {son_dy_id}')
            if son_dy_id in already_dynamic_id:
                continue

            get_comment_word(son_dy_id)
            send_id = to_repost(son_dy_id, source='son')
            if send_id and to_comment(1, son_dy_id, True):
                to_follow(get_mid_from_son_dy(son_dy_id))
                already_dynamic_id.add(son_dy_id)
                logger.info('----完成一个子动态----')
        except Exception as e:
            globals()['error_num'] += 1
            logger.error(e)
            logger.error(f"error line:{e.__traceback__.tb_lineno}")
    logger.info("*********子动态结束*********")


def parse_origin_dy(orig_dy_id):
    origin_item = get_dynamic_detail(orig_dy_id)
    if should_skip_dynamic(origin_item):
        logger.info("*************原动态为官方或预约，跳过***************")
        return 1
    origin_info = parse_dynamic_info(origin_item)
    if orig_dy_id not in already_dynamic_id:
        logger.info("*************原动态处理开始***************")
        send_id = to_repost(orig_dy_id)
        if send_id and to_comment(origin_info['oid'], orig_dy_id, False,
                                  origin_info['comment_type']):
            to_follow(origin_info['uid'])
            to_thumbsUp(orig_dy_id)
            already_dynamic_id.add(orig_dy_id)
            logger.info("*************原动态处理完成***************")
        else:
            return 0
    else:
        logger.info("*************原动态已存在***************")
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
        if not check_follow_ban and req_get(
                create_check_user_info_url(uid),
                need_check_ban=True).json()['data']['is_followed']:
            logger.info(f'{uid} === 已经关注了')
            return
    except Exception as e:
        check_follow_ban = True
        logger.error(f'check接口被ban')
    data_follow['fid'] = uid
    res = spider_post("https://api.bilibili.com/x/relation/modify",
                      data_follow, 'data')
    # if res['code'] == 0:
    msg = res.get('message', '')
    if '异常' in msg:
        need_follow_account.append(str(uid))
    logger.info(f"关注 ==== {uid} {msg}")


def add_repost_content_item(text, type=1, biz_id=''):
    return {'raw_text': text, 'type': type, 'biz_id': biz_id}


def to_repost(dynamic_id, source='available'):
    """
    dy_type 是否为子动态 取消了
    """
    res = get_dynamic_detail(dynamic_id)
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
        dy_desc = (res['modules']['module_dynamic'].get('desc')
                   or {}).get('rich_text_nodes') or []
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
        logger.info(f"转发成功 {repost_res['data']['dyn_id_str']}")
        send_id = repost_res['data']['dyn_id_str']
        save_dynamic(*(dynamic_id, send_id))
        return send_id
    return 0


def to_comment(oid, dy_id, is_repost, comment_type=11):
    # 需要获取动态的oid，才能发送评论
    if not is_repost:
        data_comment.update({"oid": oid, 'type': str(comment_type)})
    else:
        data_comment.update({"oid": dy_id, 'type': '17'})
    res = spider_post("https://api.bilibili.com/x/v2/reply/add", data_comment,
                      'data')
    logger.info('评论' + res['data']['success_toast'])
    return res['data'].get('success_toast', 0)


def to_thumbsUp(dynamic_id):
    data_thumbsUp['dyn_id_str'] = str(dynamic_id)
    res = spider_post(
        "https://api.bilibili.com/x/dynamic/feed/dyn/thumb?csrf=" + csrf,
        data_thumbsUp, 'json')
    logger.info(f"动态-点赞 {res.get('message')}")


def main(dys, processed_article_id=None):
    logger.info(
        "==================================================" +
        datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M') +
        "==================================================")
    if not dys:
        #       logger.info("---开始用户抽奖---")
        #       os.system('python3 follow.py >> users_lucky.log')
        #       logger.info("---结束用户抽奖---")
        return
    global error_num
    for dy_id in dys:
        print()
        logger.info(f'https://t.bilibili.com/{dy_id}', )
        if dy_id in already_dynamic_id:
            logger.info("已有")
            continue
        result = get_uid_oid(dy_id)
        # break
        if result == 1:  # 到官方抽奖了
            logger.info("官方 或 预约 OUT！")
            # get_son_lucky_dy(dy_id, is_official=True)
            #               official_list.append(dy_id)
            #               if len(official_list)>5:
            #                   break
            continue
        if not result:
            logger.error('*#*#*#*#*#*#*#*#*#*原动态处理失败*#*#*#*#*#*#*#*#*#')
            continue
        uid, oid, is_repost, comment_type = result
        if dy_id not in already_dynamic_id:
            logger.info('-=-=-=-=处理回最初的动态-=-=-=-=')
            get_comment_word(dy_id, not is_repost)
            try:
                send_id = to_repost(dy_id)
                if send_id and to_comment(oid, dy_id, is_repost, comment_type):
                    to_follow(uid)
                    to_thumbsUp(dy_id)
                    # logger.info(uname + "\n\n")
                    already_dynamic_id.add(dy_id)
            except Exception as e:
                globals()['error_num'] += 1
                logger.error(e)
                logger.error(f"error line:{e.__traceback__.tb_lineno}")
    #                   today_list.append(dy_id)
        time.sleep(random.randint(1, 4))
    logger.info('执行结束')
    if error_num < 6:
        if processed_article_id:
            process_already_art_id(processed_article_id, 'write')
    else:
        logger.error(f'执行失败，错误数量为{error_num}')
    error_num = 0
    logger.info(
        "==================================================" +
        datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M') +
        "==================================================")


def pre_man():
    if article_id:
        main(parse_article_get_dy(article_id), article_id)
        return
    for art_id in action():
        main(parse_article_get_dy(art_id), art_id)


def check_is_win():
    check_list = []
    replys = req_get(
        f"https://api.bilibili.com/x/msgfeed/reply?platform=web&build=0&mobi_app=web"
    ).json()['data']['items']
    for reply in replys:
        logger.info(
            f"{('reply: ',reply['user']['nickname'], reply['item']['source_content'])}"
        )
        if reply['reply_time'] >= time.time() - 3600 * 36:
            check_list.append(('reply: ', reply['user']['nickname'],
                               reply['item']['source_content']))
    ats = req_get(f"https://api.bilibili.com/x/msgfeed/at?build=0&mobi_app=web"
                  ).json()['data']['items']
    for at in ats:
        logger.info(
            f"{('at: ',at['user']['nickname'], at['item']['source_content'])}")
        if at['at_time'] >= time.time() - 3600 * 36:
            check_list.append(
                ('at: ', at['user']['nickname'], at['item']['source_content']))
    return check_list


already_dynamic_id = get_already_dynamic_id()
# already_dynamic_id = col_dynamic.find({},{'_id':0,'dynamic_id':1})
if __name__ == '__main__':
    pre_man()
    if need_follow_account:
        with open(f'bili_lucky_detail/need_follow_account.txt', 'a') as f:
            f.write('\n'.join(need_follow_account))
    check_list = check_is_win()
    send_email(title='success',
               content=f'bili_lucky_detail/{today}_logger.log')
    if check_list:
        send_email(title='中奖啦！！！', content=f'{check_list}')
