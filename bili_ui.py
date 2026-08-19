import argparse
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import wraps

from flask import Flask, Response, jsonify, request, send_from_directory
from pytz import timezone
from urllib.parse import quote, urlparse

import article_choujiang as lucky


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIST_DIR = os.path.join(BASE_DIR, 'ui', 'dist')
DETAIL_CACHE = {}
PARTICIPATE_LOCK = threading.Lock()

app = Flask(__name__, static_folder=None)

ALLOWED_MEDIA_HOSTS = (
    '.hdslb.com',
    '.biliimg.com',
)


def api_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            lucky.logger.exception(exc)
            return jsonify({
                'ok': False,
                'error': str(exc),
            }), 500

    return wrapper


def require_numeric(value, name):
    value = str(value or '').strip()
    if not value.isdigit():
        raise ValueError(f'{name} 必须是纯数字')
    return value


def proxy_media_url(url):
    if not url:
        return ''
    return f'/api/media?url={quote(str(url), safe="")}'


def format_timestamp(timestamp):
    if not timestamp:
        return ''
    return datetime.fromtimestamp(
        int(timestamp),
        tz=timezone('Asia/Shanghai'),
    ).isoformat()


def get_dynamic_text(item):
    module_dynamic = (item.get('modules') or {}).get('module_dynamic') or {}
    desc = module_dynamic.get('desc') or {}
    if desc.get('text'):
        return desc['text']

    major = module_dynamic.get('major') or {}
    for key in ('opus', 'archive', 'article', 'draw', 'common'):
        content = major.get(key) or {}
        summary = content.get('summary') or {}
        for candidate in (
                summary.get('text'), content.get('title'),
                content.get('desc'), content.get('text')):
            if candidate:
                return candidate
    return ''


def get_dynamic_media(item):
    module_dynamic = (item.get('modules') or {}).get('module_dynamic') or {}
    major = module_dynamic.get('major') or {}
    media = []

    opus = major.get('opus') or {}
    for picture in opus.get('pics') or []:
        if picture.get('url'):
            media.append({
                'type': 'image',
                'url': proxy_media_url(picture['url']),
                'width': picture.get('width'),
                'height': picture.get('height'),
            })

    draw = major.get('draw') or {}
    for picture in draw.get('items') or []:
        if picture.get('src'):
            media.append({
                'type': 'image',
                'url': proxy_media_url(picture['src']),
                'width': picture.get('width'),
                'height': picture.get('height'),
            })

    archive = major.get('archive') or {}
    if archive.get('cover'):
        media.append({
            'type': 'video-cover',
            'url': proxy_media_url(archive['cover']),
            'title': archive.get('title', ''),
            'jump_url': archive.get('jump_url', ''),
        })
    return media


def serialize_stat(module_stat):
    result = {}
    for key in ('forward', 'comment', 'like'):
        value = module_stat.get(key) or {}
        result[key] = value.get('count', 0)
        if key == 'like':
            result['liked'] = bool(value.get('status'))
    return result


def serialize_dynamic(item, include_raw=False):
    modules = item.get('modules') or {}
    author = modules.get('module_author') or {}
    basic = item.get('basic') or {}
    origin = item.get('orig') or {}
    dynamic_id = str(item.get('id_str') or '')

    result = {
        'id': dynamic_id,
        'url': f'https://t.bilibili.com/{dynamic_id}',
        'type': item.get('type', ''),
        'visible': item.get('visible', True),
        'text': get_dynamic_text(item),
        'media': get_dynamic_media(item),
        'origin_id': str(origin.get('id_str') or ''),
        'comment_id': str(basic.get('comment_id_str') or ''),
        'comment_type': basic.get('comment_type'),
        'author': {
            'mid': str(author.get('mid') or ''),
            'name': author.get('name', ''),
            'face': proxy_media_url(author.get('face', '')),
            'official_type': (author.get('official_verify') or {}).get(
                'type', -1),
            'official_desc': (author.get('official_verify') or {}).get(
                'desc', ''),
        },
        'published_at': format_timestamp(author.get('pub_ts')),
        'published_label': author.get('pub_time', ''),
        'stats': serialize_stat(modules.get('module_stat') or {}),
        'eligible': not lucky.should_skip_dynamic(item),
    }
    if include_raw:
        result['raw'] = item
    return result


def get_dynamic_item(dynamic_id, force=False):
    dynamic_id = require_numeric(dynamic_id, '动态 ID')
    if force or dynamic_id not in DETAIL_CACHE:
        response = lucky.rq.get(
            lucky.get_dynamic_detail_url(dynamic_id),
            headers=lucky.public_api_headers,
            proxies=lucky.proxies,
            timeout=8,
        )
        response.raise_for_status()
        result = response.json()
        if result.get('code') != 0:
            raise ValueError(
                f'获取动态详情失败 {dynamic_id}: {result.get("code")} '
                f'{result.get("message", "")}')
        item = (result.get('data') or {}).get('item')
        if not item:
            raise ValueError(f'动态详情缺少 item: {dynamic_id}')
        DETAIL_CACHE[dynamic_id] = item
    return DETAIL_CACHE[dynamic_id]


def serialize_article(article):
    publish_time = int(article.get('publish_time') or article.get('ctime') or 0)
    processed = str(article.get('id')) in lucky.article_ids
    within_window = publish_time >= int(time.time() - 36 * 3600)
    author = article.get('author') or {}
    images = article.get('image_urls') or []
    return {
        'id': str(article.get('id') or ''),
        'url': f'https://www.bilibili.com/read/cv{article.get("id")}',
        'title': article.get('title', ''),
        'summary': article.get('summary', ''),
        'cover': proxy_media_url(article.get('banner_url')
                                 or (images[0] if images else '')),
        'published_at': format_timestamp(publish_time),
        'author': {
            'mid': str(author.get('mid') or ''),
            'name': author.get('name', ''),
            'face': proxy_media_url(author.get('face', '')),
        },
        'stats': article.get('stats') or {},
        'processed': processed,
        'within_window': within_window,
        'eligible': within_window and not processed,
    }


def create_dynamic_fallback(dynamic_id, source_entry, error):
    dynamic_id = str(dynamic_id)
    return {
        'id': dynamic_id,
        'url': (source_entry or {}).get('url')
        or f'https://t.bilibili.com/{dynamic_id}',
        'type': 'DYNAMIC_TYPE_UNKNOWN',
        'visible': True,
        'text': (source_entry or {}).get('title')
        or '动态详情暂时无法获取，点击后可再次加载。',
        'media': [],
        'origin_id': '',
        'comment_id': '',
        'comment_type': None,
        'author': {
            'mid': '',
            'name': '详情待加载',
            'face': '',
            'official_type': -1,
            'official_desc': '',
        },
        'published_at': '',
        'published_label': '',
        'stats': {
            'forward': 0,
            'comment': 0,
            'like': 0,
            'liked': False,
        },
        'eligible': True,
        'detail_error': str(error),
    }


def load_dynamic_safe(dynamic_id, source_entry=None):
    try:
        item = get_dynamic_item(dynamic_id)
        if item.get('type') == 'DYNAMIC_TYPE_ARTICLE':
            return None, None
        return serialize_dynamic(item), None
    except Exception as exc:
        error = {
            'id': str(dynamic_id),
            'error': str(exc),
        }
        return create_dynamic_fallback(dynamic_id, source_entry, exc), error


def participate_dynamic(dynamic_id):
    dynamic_id = require_numeric(dynamic_id, '动态 ID')
    if dynamic_id in lucky.already_dynamic_id:
        return {
            'id': dynamic_id,
            'status': 'already_processed',
            'message': '该动态已经完成过参与操作',
            'steps': {},
        }

    steps = {}
    item = get_dynamic_item(dynamic_id, force=True)
    info = lucky.parse_dynamic_info(item)
    is_repost = bool(info['origin_id'])
    lucky.get_comment_word(dynamic_id, not is_repost)

    lucky.to_follow(info['uid'])
    steps['follow'] = 'completed'

    send_id = lucky.to_repost(dynamic_id)
    if not send_id:
        raise ValueError('转发失败，Bilibili 未返回新动态 ID')
    steps['repost'] = 'completed'

    comment_result = lucky.to_comment(
        info['oid'],
        dynamic_id,
        is_repost,
        info['comment_type'],
    )
    if not comment_result:
        raise ValueError('评论失败，Bilibili 未返回成功结果')
    steps['comment'] = 'completed'

    lucky.already_dynamic_id.add(dynamic_id)
    return {
        'id': dynamic_id,
        'status': 'success',
        'message': '关注、转发、评论均已完成',
        'send_id': str(send_id),
        'steps': steps,
    }


@app.get('/api/config')
@api_endpoint
def config():
    return jsonify({
        'ok': True,
        'article_uids': lucky.article_uid,
        'article_window_hours': 36,
    })


@app.get('/api/media')
@api_endpoint
def media_proxy():
    media_url = str(request.args.get('url') or '').strip()
    parsed = urlparse(media_url)
    hostname = (parsed.hostname or '').lower()
    if (parsed.scheme not in ('http', 'https')
            or not any(hostname.endswith(suffix)
                       for suffix in ALLOWED_MEDIA_HOSTS)):
        return jsonify({
            'ok': False,
            'error': '不允许代理该媒体地址',
        }), 400

    upstream = lucky.rq.get(
        media_url,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/131.0.0.0 Safari/537.36'),
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,'
            'image/*,*/*;q=0.8',
        },
        stream=True,
        timeout=15,
    )
    upstream.raise_for_status()
    return Response(
        upstream.iter_content(chunk_size=64 * 1024),
        content_type=upstream.headers.get('Content-Type',
                                          'application/octet-stream'),
        headers={
            'Cache-Control': 'public, max-age=86400',
        },
    )


@app.get('/api/articles')
@api_endpoint
def articles():
    uid = require_numeric(request.args.get('uid'), 'Article UID')
    page_size = min(max(int(request.args.get('limit', 12)), 1), 30)
    result = lucky.req_get(
        'https://api.bilibili.com/x/space/article'
        f'?mid={uid}&pn=1&ps={page_size}&sort=publish_time').json()
    if result.get('code') != 0:
        raise ValueError(
            f'获取 Article 失败: {result.get("code")} '
            f'{result.get("message", "")}')
    values = [
        serialize_article(value)
        for value in (result.get('data') or {}).get('articles') or []
    ]
    values.sort(key=lambda value: value['published_at'], reverse=True)
    values.sort(key=lambda value: not value['eligible'])
    return jsonify({
        'ok': True,
        'uid': uid,
        'items': values,
    })


@app.get('/api/articles/<article_id>/dynamics')
@api_endpoint
def article_dynamics(article_id):
    article_id = require_numeric(article_id, 'Article ID')
    source_entries = lucky.parse_article_dynamic_entries(article_id)
    source_entries = list({
        entry['id']: entry
        for entry in source_entries
    }.values())
    dynamic_ids = [entry['id'] for entry in source_entries]
    items = []
    errors = []
    worker_count = min(4, max(1, len(dynamic_ids)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(load_dynamic_safe, entry['id'], entry): entry['id']
            for entry in source_entries
        }
        completed = {}
        for future in as_completed(futures):
            dynamic_id = futures[future]
            item, error = future.result()
            if item:
                completed[dynamic_id] = item
            if error:
                errors.append(error)
    for dynamic_id in dynamic_ids:
        if dynamic_id in completed:
            items.append(completed[dynamic_id])
    return jsonify({
        'ok': True,
        'article_id': article_id,
        'source_count': len(dynamic_ids),
        'items': items,
        'errors': errors,
    })


@app.get('/api/dynamics/<dynamic_id>')
@api_endpoint
def dynamic_detail(dynamic_id):
    force = request.args.get('refresh') == '1'
    item = get_dynamic_item(dynamic_id, force=force)
    return jsonify({
        'ok': True,
        'item': serialize_dynamic(item, include_raw=True),
    })


@app.get('/api/dynamics/<dynamic_id>/children')
@api_endpoint
def dynamic_children(dynamic_id):
    selected_item = get_dynamic_item(dynamic_id)
    root_id = str((selected_item.get('orig') or {}).get('id_str')
                  or dynamic_id)
    repost_items = lucky.get_repost_items(root_id, max_pages=3)
    resolved = {}
    sources = {}
    for repost_item in repost_items:
        child_id = lucky.resolve_son_dynamic_id(root_id, repost_item)
        if not child_id or child_id in resolved:
            continue
        try:
            child = get_dynamic_item(child_id)
            author = (child.get('modules') or {}).get('module_author') or {}
            if (author.get('official_verify') or {}).get('type') != 1:
                continue
            resolved[child_id] = serialize_dynamic(child)
            source_user = repost_item.get('user') or {}
            sources[child_id] = {
                'mid': str(source_user.get('mid') or ''),
                'name': source_user.get('name', ''),
                'repost_id': str(repost_item.get('id_str') or ''),
            }
        except Exception as exc:
            lucky.logger.warning(f'预览子动态失败 {child_id}: {exc}')

    values = []
    for child_id, child in resolved.items():
        child['discovered_from'] = sources.get(child_id) or {}
        values.append(child)
    values.sort(key=lambda value: value.get('published_at', ''), reverse=True)
    return jsonify({
        'ok': True,
        'selected_id': str(dynamic_id),
        'root_id': root_id,
        'items': values,
        'scanned_reposts': len(repost_items),
    })


@app.post('/api/actions/participate')
@api_endpoint
def participate_selected_dynamics():
    payload = request.get_json(silent=True) or {}
    dynamic_ids = list(
        dict.fromkeys(str(value).strip()
                      for value in payload.get('dynamic_ids') or []))
    if not dynamic_ids:
        raise ValueError('至少选择一条动态')
    if len(dynamic_ids) > 30:
        raise ValueError('单次最多处理 30 条动态')
    for dynamic_id in dynamic_ids:
        require_numeric(dynamic_id, '动态 ID')

    started_at = time.time()
    results = []
    with PARTICIPATE_LOCK:
        for dynamic_id in dynamic_ids:
            try:
                results.append(participate_dynamic(dynamic_id))
            except Exception as exc:
                lucky.logger.error(f'UI 关转评失败 {dynamic_id}: {exc}')
                results.append({
                    'id': dynamic_id,
                    'status': 'failed',
                    'message': str(exc),
                    'steps': {},
                })

    success_count = sum(result['status'] == 'success' for result in results)
    already_count = sum(result['status'] == 'already_processed'
                        for result in results)
    return jsonify({
        'ok': True,
        'requested_count': len(dynamic_ids),
        'success_count': success_count,
        'already_count': already_count,
        'failed_count': len(dynamic_ids) - success_count - already_count,
        'elapsed_seconds': round(time.time() - started_at, 2),
        'results': results,
    })


@app.get('/')
def index():
    if not os.path.isfile(os.path.join(UI_DIST_DIR, 'index.html')):
        return jsonify({
            'ok': False,
            'error': '前端尚未构建，请先在 ui 目录运行 npm install && npm run build',
        }), 503
    return send_from_directory(UI_DIST_DIR, 'index.html')


@app.get('/<path:path>')
def static_files(path):
    target = os.path.join(UI_DIST_DIR, path)
    if os.path.isfile(target):
        return send_from_directory(UI_DIST_DIR, path)
    return send_from_directory(UI_DIST_DIR, 'index.html')


def main():
    parser = argparse.ArgumentParser(description='Bili Lucky 本地 UI')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=8765, type=int)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()
