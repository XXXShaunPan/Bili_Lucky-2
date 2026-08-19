import os
import tempfile
import unittest
from contextlib import ExitStack
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock, patch


os.environ.setdefault('BILI_COOKIE', 'bili_jct=test')
os.environ.setdefault('article_id', '')
os.environ.setdefault('MAILLQQ', '')
os.environ.setdefault('MAILLSECRET', '')
os.environ.setdefault('BILI_LUCKY_LOG_PATH',
                      os.path.join(tempfile.gettempdir(),
                                   'bili_lucky_test.log'))

import article_choujiang as article


def make_dynamic_item(*,
                      dynamic_id='1236363031907139590',
                      uid=3546377799862777,
                      oid='405460500',
                      comment_type=11,
                      origin_id='',
                      additional=None):
    item = {
        'id_str': dynamic_id,
        'type': 'DYNAMIC_TYPE_FORWARD' if origin_id else 'DYNAMIC_TYPE_DRAW',
        'basic': {
            'comment_id_str': oid,
            'comment_type': comment_type,
        },
        'modules': {
            'module_author': {
                'mid': uid,
                'name': 'tester',
                'official_verify': {
                    'type': 1
                },
            },
            'module_dynamic': {
                'additional': additional,
                'desc': {
                    'rich_text_nodes': []
                },
            },
        },
    }
    if origin_id:
        item['orig'] = {'id_str': origin_id}
    return item


def make_new_repost_item():
    official_text = (
        '#互动抽奖# 科睿新品来啦！看着很帅啊，艾湃电竞品牌也来为阿睿打call！'
        '【关注】@KOORUI科睿官方UP +@Apexgaming艾湃电竞，【转发+评论】本条动态')
    return {
        'id_str': '1237743724314755079',
        'user': {
            'mid': 1593972,
            'name': 'チェシャ猫·Nyanya',
        },
        'desc': {
            'text': f'[doge] //@Apexgaming艾湃电竞:{official_text}',
            'rich_text_nodes': [
                {
                    'orig_text': '[doge]',
                    'type': 'RICH_TEXT_NODE_TYPE_EMOJI'
                },
                {
                    'orig_text': ' //',
                    'type': 'RICH_TEXT_NODE_TYPE_TEXT'
                },
                {
                    'orig_text': '@Apexgaming艾湃电竞',
                    'rid': '242136088',
                    'type': 'RICH_TEXT_NODE_TYPE_AT'
                },
                {
                    'orig_text': f':{official_text}',
                    'type': 'RICH_TEXT_NODE_TYPE_TEXT'
                },
            ],
        },
    }


class DynamicDetailTests(unittest.TestCase):

    def setUp(self):
        article.error_num = 0
        article.son_dynamic_cache.clear()

    def test_get_dynamic_detail_uses_polymer_api(self):
        response = Mock()
        response.json.return_value = {
            'code': 0,
            'data': {
                'item': make_dynamic_item()
            },
        }
        with patch.object(article, 'req_get', return_value=response) as req_get:
            item = article.get_dynamic_detail('123')

        url = req_get.call_args.args[0]
        self.assertIn('/x/polymer/web-dynamic/v1/detail', url)
        self.assertIn('id=123', url)
        self.assertNotIn('get_dynamic_detail', url)
        self.assertEqual(req_get.call_args.kwargs['request_headers'],
                         article.public_api_headers)
        self.assertEqual(item['basic']['comment_id_str'], '405460500')

    def test_decode_article_html_without_unicode_escape_warning(self):
        content = (
            r'https:\u002F\u002Ft.bilibili.com\u002Fopus\u002F'
            r'1236363031907139590')

        decoded = article.decode_article_html(content)

        self.assertEqual(
            decoded,
            'https://t.bilibili.com/opus/1236363031907139590',
        )

    def test_parse_article_preserves_dynamic_link_order(self):
        article_data = {
            'opus': {
                'links': [
                    'https://t.bilibili.com/1236363031907139590',
                    'https://www.bilibili.com/opus/1235614919492108292',
                    'https://t.bilibili.com/1236363031907139590',
                ]
            }
        }
        with patch.object(article,
                          'fetch_article_api_data',
                          return_value=article_data), \
                patch.object(article, 'transform_to_dy_id', return_value=[]):
            dynamic_ids = article.parse_article_get_dy('123')

        self.assertEqual(dynamic_ids, [
            '1236363031907139590',
            '1235614919492108292',
        ])

    def test_parse_article_falls_back_to_html(self):
        html = 'https://t.bilibili.com/1236363031907139590'
        with patch.object(article,
                          'fetch_article_api_data',
                          return_value={}), patch.object(
                              article,
                              'fetch_article_html',
                              return_value=html), patch.object(
                                  article,
                                  'transform_to_dy_id',
                                  return_value=[]):
            dynamic_ids = article.parse_article_get_dy('123')

        self.assertEqual(dynamic_ids, ['1236363031907139590'])

    def test_structured_opus_parser_keeps_link_title(self):
        opus = {
            'content': {
                'paragraphs': [{
                    'text': {
                        'nodes': [{
                            'link': {
                                'show_text': '七夕福利抽奖',
                                'link': (
                                    'https://www.bilibili.com/opus/'
                                    '1236363031907139590?spm_id_from=333.1387'),
                            }
                        }]
                    }
                }]
            }
        }

        entries = article.extract_opus_dynamic_entries(opus)

        self.assertEqual(entries, [{
            'id': '1236363031907139590',
            'title': '七夕福利抽奖',
            'url': (
                'https://www.bilibili.com/opus/'
                '1236363031907139590?spm_id_from=333.1387'),
        }])

    def test_parse_original_dynamic_info(self):
        info = article.parse_dynamic_info(make_dynamic_item())

        self.assertEqual(info['uid'], 3546377799862777)
        self.assertEqual(info['oid'], '405460500')
        self.assertEqual(info['comment_type'], 11)
        self.assertEqual(info['origin_id'], '')

    def test_parse_forward_dynamic_info(self):
        info = article.parse_dynamic_info(
            make_dynamic_item(dynamic_id='200',
                              oid='200',
                              comment_type=17,
                              origin_id='100'))

        self.assertEqual(info['dynamic_id'], '200')
        self.assertEqual(info['comment_type'], 17)
        self.assertEqual(info['origin_id'], '100')

    def test_extract_pre_dynamic_reference_from_new_response(self):
        uid, reference_text = article.extract_pre_dynamic_reference(
            make_new_repost_item())

        self.assertEqual(uid, '242136088')
        self.assertIn('科睿新品来啦', reference_text)

    def test_resolve_old_pre_dynamic_id_remains_compatible(self):
        repost_item = {
            'desc': {
                'pre_dy_id_str': 'child-200',
                'orig_dy_id_str': 'root-100',
            }
        }

        dynamic_id = article.resolve_son_dynamic_id('root-100', repost_item)

        self.assertEqual(dynamic_id, 'child-200')

    def test_find_official_child_dynamic_from_space_feed(self):
        child = make_dynamic_item(dynamic_id='1229642303610552338',
                                  uid=242136088,
                                  oid='1229642303610552338',
                                  comment_type=17,
                                  origin_id='1228848557119766529')
        child['modules']['module_dynamic']['desc']['text'] = (
            '#互动抽奖# 科睿新品来啦！看着很帅啊')

        response = Mock()
        response.json.return_value = {
            'code': 0,
            'data': {
                'items': [child],
                'has_more': True,
                'offset': 'next-page',
            },
        }
        with patch.object(article,
                          'create_wbi_url',
                          return_value='space-feed-url'), patch.object(
                              article,
                              'req_get',
                              return_value=response) as req_get:
            dynamic_id = article.find_official_child_dynamic(
                '1228848557119766529',
                '242136088',
                '#互动抽奖# 科睿新品来啦！看着很帅啊',
            )

        self.assertEqual(dynamic_id, '1229642303610552338')
        req_get.assert_called_once_with('space-feed-url')

    def test_create_wbi_url_adds_signature(self):
        with patch.object(article,
                          'get_wbi_mixin_key',
                          return_value='abcdefghijklmnopqrstuvwxyz123456'):
            url = article.create_wbi_url(
                'https://api.bilibili.com/test',
                {
                    'host_mid': '242136088',
                    'offset': ''
                },
                wts=1787038693,
            )

        query = parse_qs(urlparse(url).query, keep_blank_values=True)
        self.assertEqual(query['host_mid'], ['242136088'])
        self.assertEqual(query['wts'], ['1787038693'])
        self.assertEqual(len(query['w_rid'][0]), 32)

    def test_skip_additional_and_lottery_dynamic(self):
        additional = {'type': 'ADDITIONAL_TYPE_UGC'}
        self.assertTrue(
            article.should_skip_dynamic(
                make_dynamic_item(additional=additional)))

        lottery_item = make_dynamic_item()
        lottery_item['marker'] = 'RICH_TEXT_NODE_TYPE_LOTTERY'
        self.assertTrue(article.should_skip_dynamic(lottery_item))
        self.assertFalse(article.should_skip_dynamic(make_dynamic_item()))

    def test_get_uid_oid_original_dynamic(self):
        item = make_dynamic_item()
        with patch.object(article, 'get_dynamic_detail', return_value=item), \
                patch.object(article, 'get_son_lucky_dy') as get_sons:
            result = article.get_uid_oid(item['id_str'])

        self.assertEqual(result, (3546377799862777, '405460500', False, 11))
        get_sons.assert_called_once_with(item['id_str'])

    def test_get_uid_oid_forward_dynamic(self):
        item = make_dynamic_item(dynamic_id='200',
                                 oid='200',
                                 comment_type=17,
                                 origin_id='100')
        with patch.object(article, 'get_dynamic_detail', return_value=item), \
                patch.object(article, 'get_comment_word') as get_word, \
                patch.object(article, 'parse_origin_dy', return_value=1) as parse_origin:
            result = article.get_uid_oid('200')

        self.assertEqual(result, (3546377799862777, '200', True, 17))
        get_word.assert_called_once_with('100', 1)
        parse_origin.assert_called_once_with('100')

    def test_comment_uses_api_comment_type(self):
        with patch.object(article,
                          'spider_post',
                          return_value={'data': {
                              'success_toast': '发送成功'
                          }}) as spider_post:
            article.to_comment('av123', 'dynamic123', False, 1)
            payload = spider_post.call_args.args[1]
            self.assertEqual(payload['oid'], 'av123')
            self.assertEqual(payload['type'], '1')

            article.to_comment('ignored', 'dynamic123', True, 11)
            payload = spider_post.call_args.args[1]
            self.assertEqual(payload['oid'], 'dynamic123')
            self.assertEqual(payload['type'], '17')

    def test_get_son_lucky_dy_processes_resolved_child_once(self):
        original_ids = article.already_dynamic_id
        article.already_dynamic_id = set()
        try:
            with ExitStack() as stack:
                stack.enter_context(
                    patch.object(article,
                                 'get_repost_items',
                                 return_value=[make_new_repost_item()]))
                stack.enter_context(
                    patch.object(article,
                                 'resolve_son_dynamic_id',
                                 return_value='1229642303610552338'))
                stack.enter_context(patch.object(article,
                                                 'get_comment_word'))
                stack.enter_context(
                    patch.object(article, 'to_repost', return_value='sent'))
                stack.enter_context(
                    patch.object(article, 'to_comment', return_value=True))
                stack.enter_context(
                    patch.object(article,
                                 'get_mid_from_son_dy',
                                 return_value=242136088))
                to_follow = stack.enter_context(
                    patch.object(article, 'to_follow'))
                article.get_son_lucky_dy('1228848557119766529')

            self.assertIn('1229642303610552338',
                          article.already_dynamic_id)
            to_follow.assert_called_once_with(242136088)
        finally:
            article.already_dynamic_id = original_ids

    def test_dynamic_history_reads_all_ids(self):
        with tempfile.NamedTemporaryFile('w+', encoding='utf-8') as file:
            for index in range(1002):
                file.write(f'{index}==send-{index}\n')
            file.flush()

            dynamic_ids = article.get_already_dynamic_id(file.name)

        self.assertIn('0', dynamic_ids)
        self.assertIn('1001', dynamic_ids)
        self.assertEqual(len(dynamic_ids), 1002)


if __name__ == '__main__':
    unittest.main()
