import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault('BILI_COOKIE', 'bili_jct=test')
os.environ.setdefault('BILI_LUCKY_LOG_PATH',
                      os.path.join(tempfile.gettempdir(), 'bili_ui_test.log'))

import bili_ui


def dynamic_item(dynamic_id='100', uid=200, origin_id='', official_type=1):
    item = {
        'id_str': dynamic_id,
        'type': 'DYNAMIC_TYPE_FORWARD' if origin_id else 'DYNAMIC_TYPE_DRAW',
        'visible': True,
        'basic': {
            'comment_id_str': dynamic_id,
            'comment_type': 17 if origin_id else 11,
        },
        'modules': {
            'module_author': {
                'mid': uid,
                'name': '测试账号',
                'face': 'https://example.com/avatar.jpg',
                'pub_ts': int(time.time()),
                'official_verify': {
                    'type': official_type,
                    'desc': '',
                },
            },
            'module_dynamic': {
                'additional': None,
                'desc': {
                    'text': '测试抽奖动态',
                    'rich_text_nodes': [],
                },
                'major': None,
            },
            'module_stat': {
                'forward': {
                    'count': 10
                },
                'comment': {
                    'count': 20
                },
                'like': {
                    'count': 30,
                    'status': False
                },
            },
        },
    }
    if origin_id:
        item['orig'] = {'id_str': origin_id}
    return item


class BiliUiApiTests(unittest.TestCase):

    def setUp(self):
        bili_ui.app.config.update(TESTING=True)
        bili_ui.DETAIL_CACHE.clear()
        self.client = bili_ui.app.test_client()

    def test_config_returns_uid_options(self):
        response = self.client.get('/api/config')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['ok'])
        self.assertIn('article_uids', response.json)

    def test_media_proxy_rejects_non_bilibili_host(self):
        response = self.client.get('/api/media', query_string={
            'url': 'http://127.0.0.1/private.png'
        })

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json['ok'])

    def test_media_proxy_adds_bilibili_referer(self):
        upstream = Mock()
        upstream.headers = {'Content-Type': 'image/jpeg'}
        upstream.iter_content.return_value = [b'image-bytes']
        with patch.object(bili_ui.lucky.rq,
                          'get',
                          return_value=upstream) as request_get:
            response = self.client.get('/api/media', query_string={
                'url': 'https://i0.hdslb.com/bfs/test.jpg'
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'image-bytes')
        self.assertEqual(request_get.call_args.kwargs['headers']['Referer'],
                         'https://www.bilibili.com/')
        upstream.raise_for_status.assert_called_once_with()

    def test_dynamic_media_uses_local_proxy_url(self):
        item = dynamic_item('100')
        item['modules']['module_dynamic']['major'] = {
            'opus': {
                'pics': [{
                    'url': 'http://i0.hdslb.com/bfs/image.jpg',
                    'width': 100,
                    'height': 100,
                }]
            }
        }

        value = bili_ui.serialize_dynamic(item)

        self.assertTrue(value['media'][0]['url'].startswith('/api/media?url='))

    def test_articles_marks_recent_unprocessed_article_eligible(self):
        api_response = Mock()
        api_response.json.return_value = {
            'code': 0,
            'data': {
                'articles': [{
                    'id': 123,
                    'title': '抽奖合集',
                    'summary': '摘要',
                    'publish_time': int(time.time()),
                    'author': {
                        'mid': 456,
                        'name': '作者'
                    },
                    'stats': {},
                }]
            },
        }
        with patch.object(bili_ui.lucky,
                          'req_get',
                          return_value=api_response), patch.object(
                              bili_ui.lucky, 'article_ids', set()):
            response = self.client.get('/api/articles?uid=456')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['items'][0]['eligible'])
        self.assertEqual(response.json['items'][0]['id'], '123')

    def test_article_dynamics_preserves_article_order(self):
        first = bili_ui.serialize_dynamic(dynamic_item('100'))
        second = bili_ui.serialize_dynamic(dynamic_item('200'))
        responses = {
            '100': (first, None),
            '200': (second, None),
        }
        with patch.object(bili_ui.lucky,
                          'parse_article_dynamic_entries',
                          return_value=[{
                              'id': '100',
                              'title': '第一条',
                              'url': 'https://t.bilibili.com/100'
                          }, {
                              'id': '200',
                              'title': '第二条',
                              'url': 'https://t.bilibili.com/200'
                          }]), patch.object(
                              bili_ui,
                              'load_dynamic_safe',
                              side_effect=lambda value, entry: responses[value]):
            response = self.client.get('/api/articles/123/dynamics')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.json['items']],
                         ['100', '200'])
        self.assertEqual(response.json['source_count'], 2)

    def test_ui_keeps_ineligible_dynamic_for_read_only_browsing(self):
        item = dynamic_item('100')
        item['modules']['module_dynamic']['additional'] = {
            'type': 'ADDITIONAL_TYPE_UGC'
        }
        with patch.object(bili_ui, 'get_dynamic_item', return_value=item):
            result, error = bili_ui.load_dynamic_safe('100')

        self.assertIsNone(error)
        self.assertEqual(result['id'], '100')
        self.assertFalse(result['eligible'])

    def test_ui_keeps_lightweight_row_when_detail_request_fails(self):
        source = {
            'id': '100',
            'title': '来自专栏的抽奖标题',
            'url': 'https://t.bilibili.com/100',
        }
        with patch.object(bili_ui,
                          'get_dynamic_item',
                          side_effect=ValueError('详情接口风控')):
            result, error = bili_ui.load_dynamic_safe('100', source)

        self.assertEqual(result['id'], '100')
        self.assertEqual(result['text'], '来自专栏的抽奖标题')
        self.assertIn('详情接口风控', result['detail_error'])
        self.assertIsNotNone(error)

    def test_dynamic_detail_includes_raw_data(self):
        item = dynamic_item('100')
        with patch.object(bili_ui, 'get_dynamic_item', return_value=item):
            response = self.client.get('/api/dynamics/100')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['item']['id'], '100')
        self.assertIn('raw', response.json['item'])

    def test_get_dynamic_item_uses_single_public_request(self):
        response = Mock()
        response.json.return_value = {
            'code': 0,
            'data': {
                'item': dynamic_item('100')
            },
        }
        with patch.object(bili_ui.lucky.rq,
                          'get',
                          return_value=response) as request_get:
            item = bili_ui.get_dynamic_item('100')

        self.assertEqual(item['id_str'], '100')
        self.assertEqual(request_get.call_args.kwargs['headers'],
                         bili_ui.lucky.public_api_headers)
        response.raise_for_status.assert_called_once_with()

    def test_children_endpoint_returns_official_resolved_child(self):
        root = dynamic_item('100')
        child = dynamic_item('200', uid=300, origin_id='100', official_type=1)
        repost = {
            'id_str': '150',
            'user': {
                'mid': 400,
                'name': '转发用户'
            },
            'desc': {},
        }

        def get_item(dynamic_id, force=False):
            return root if str(dynamic_id) == '100' else child

        with patch.object(bili_ui,
                          'get_dynamic_item',
                          side_effect=get_item), patch.object(
                              bili_ui.lucky,
                              'get_repost_items',
                              return_value=[repost]), patch.object(
                                  bili_ui.lucky,
                                  'resolve_son_dynamic_id',
                                  return_value='200'):
            response = self.client.get('/api/dynamics/100/children')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['items'][0]['id'], '200')
        self.assertEqual(response.json['items'][0]['discovered_from']['name'],
                         '转发用户')

    def test_participate_dynamic_runs_follow_repost_comment_in_order(self):
        calls = []
        original_ids = bili_ui.lucky.already_dynamic_id
        bili_ui.lucky.already_dynamic_id = set()
        try:
            with patch.object(bili_ui,
                              'get_dynamic_item',
                              return_value=dynamic_item('100')), patch.object(
                                  bili_ui.lucky,
                                  'get_comment_word'), patch.object(
                                      bili_ui.lucky,
                                      'to_follow',
                                      side_effect=lambda uid: calls.append(
                                          'follow')), patch.object(
                                              bili_ui.lucky,
                                              'to_repost',
                                              side_effect=lambda dynamic_id:
                                              (calls.append('repost')
                                               or 'sent-100')), patch.object(
                                                   bili_ui.lucky,
                                                   'to_comment',
                                                   side_effect=lambda *args:
                                                   (calls.append('comment')
                                                    or '发送成功')):
                result = bili_ui.participate_dynamic('100')
        finally:
            bili_ui.lucky.already_dynamic_id = original_ids

        self.assertEqual(calls, ['follow', 'repost', 'comment'])
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['send_id'], 'sent-100')

    def test_batch_participate_endpoint_returns_mixed_results(self):
        def participate(dynamic_id):
            if dynamic_id == '200':
                raise ValueError('评论失败')
            return {
                'id': dynamic_id,
                'status': 'success',
                'message': '完成',
                'steps': {},
            }

        with patch.object(bili_ui,
                          'participate_dynamic',
                          side_effect=participate):
            response = self.client.post('/api/actions/participate', json={
                'dynamic_ids': ['100', '200']
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['success_count'], 1)
        self.assertEqual(response.json['failed_count'], 1)
        self.assertEqual(response.json['results'][1]['message'], '评论失败')


if __name__ == '__main__':
    unittest.main()
