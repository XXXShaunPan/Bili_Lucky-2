import requests as rq
import random,time,dynamic_redis
import json
import re,os
from functools import reduce
from datetime import datetime
from pytz import timezone
# from lxml import etree

csrf=os.environ["CSRF"]

article_id=os.environ["article_id"]

today=datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
today_filename=datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d=%H')

official_list=[]
today_list=[]

header={
	'content-type':'application/x-www-form-urlencoded',
	'cookie':os.environ["BILI_COOKIE"],
        'origin':'https://t.bilibili.com',
	'pragma':'no-cache',
	'referer':'https://t.bilibili.com/',
	'user-agent':'mozilla/5.0 (windowS NT 6.1; win64; x64) appLewEbkit/537.36 (KHTML, likE gecko) chrome/88.0.4324.190 safari/537.36'
}

header_noCookie={
	'content-type':'application/x-www-form-urlencoded',
	'origin':'https://t.bilibili.com',
	'pragma':'no-cache',
	'referer':'https://t.bilibili.com/',
	'user-agent':'mozilla/5.0 (windowS NT 6.1; win64; x64) appLewEbkit/537.36 (KHTML, likE gecko) chrome/88.0.4324.190 safari/537.36'
}


data_follow={
	'act':'1',
	'fid':'457235238',
	'spmid':'333.169',
	're_src':'0',
	'csrf_token':csrf,
	'csrf':csrf
}


data_repost={
	'uid':'1090970340',
	'dynamic_id':'',
	'content':'我觉得会是我~！',
	'extension':'{"emoji_type":1}',
	'at_uids':'',
	'ctrl':'[]',
	'csrf_token':csrf,
	'csrf':csrf
}

data_comment={
	'oid':'116883742',
	'type':'17',
	'message':'冲一波~',
	'plat':'1',
	'ordering':'heat',
	'jsonp':'jsonp',
	'csrf':csrf
}

data_thumbsUp={
	'uid':'1090970340',
	'dynamic_id':'',
	'up':'1',
	'csrf_token':csrf,
	'csrf':csrf,
}

get_son_dy_url=lambda x:f'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost_detail?dynamic_id={x}'

func = lambda x,y:x if y in x else x + [y]  

def spider_post(url,data1):
	# asyncio.sleep(3)
	res=rq.post(url,headers=header,data=data1)
	html = res.json()
	return html

def parse_article_get_dy(article_id):
	if not article_id:
		return []
	res=rq.get(f'https://www.bilibili.com/read/cv{article_id}',headers=header_noCookie).text

	result=re.findall('https://t.bilibili.com/(.+?)\?tab=2',res)

	result = reduce(func,[[]]+result)

	return parse_dynamic(result)


def parse_dynamic(result):
	if order_dy_type(result[2]):
		result.reverse()
	return result


def order_dy_type(dy_id):	# 检查官方与非官方的顺序
	res=rq.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dy_id}",headers=header_noCookie).json()['data']['card']
	return 'extension' in res.keys()


def action():
	article_id=''
	articles=rq.get("https://api.bilibili.com/x/space/article?mid=226257459&pn=1&ps=12&sort=publish_time",headers=header_noCookie).json()['data']['articles']
	for i in articles:
		if "抽奖" in i['title'] and time.strftime('%Y-%m-%d',time.localtime(i['publish_time']))==today:
			print(i['id'])
			article_id=i['id']
			break
	# article_id=articles[1]['id']
	return parse_article_get_dy(article_id)


def get_comment_word(dy_id):
	repost_detail=rq.get(f'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost_detail?dynamic_id={dy_id}').json()
	word=json.loads(repost_detail['data']['items'][-1]['card'])['item']['content']
	data_comment['message']=word.split('//')[0]
	data_repost['content']=word  


def get_uid_oid(dy_id):
	res=rq.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dy_id}",headers=header_noCookie).json()
	keys=res['data']['card']['desc']

	if 'extension' in res['data']['card'].keys():
		return 1
	# print(keys)
	if 'origin' in keys.keys():
		if not parse_origin_dy(keys['origin']):
			return 0
	return keys['uid'],keys['rid'],keys['user_profile']['info']['uname'], keys['orig_dy_id']


def get_son_lucky_dy(dy_id):
	time.sleep(2)
	res=rq.get(get_son_dy_url(dy_id),headers=header_noCookie)['data']['items']
	print('*****子动态开始*****')
	for j in res:
		i=json.loads(j['card'])
		if all([key in i['item']['content'] for key in ['关注','抽','转']]) and '//' not in i['item']['content']:
			son_dy_id=j['desc']['dynamic_id']
			if son_dy_id not in already_dynamic_id:		
				get_comment_word(son_dy_id)
				to_comment(1,son_dy_id,True)
				to_repost(son_dy_id)
				to_follow(j['desc']['uid'])
				already_dynamic_id.append(son_dy_id)
				dynamic_redis.save_dynamic(son_dy_id)
				print()
	print("*****子动态结束*****\n\n")


def parse_origin_dy(origin):
	if origin['dynamic_id'] not in already_dynamic_id:
		print("*************原动态处理开始***************")
		if to_comment(origin['rid'],origin['dynamic_id'],origin['orig_dy_id'],origin['type']):
			to_follow(origin['uid'])
			to_thumbsUp(origin['dynamic_id'])
			# if origin['type']!=8:
			# 	to_repost(origin['dynamic_id'],True)
			dynamic_redis.save_dynamic(origin['dynamic_id'])
			already_dynamic_id.append(origin['dynamic_id'])
			print("*************原动态处理完成***************")
			get_son_lucky_dy(origin['dynamic_id'])
			return 1
		return 0
	print("*************原动态已存在***************")
	return 1


def to_follow(uid):
	data_follow['fid']=uid
	res=spider_post("https://api.bilibili.com/x/relation/modify",data_follow)
	if res['code']==0:
		print(f"关注成功 ==== {uid}")
	

def to_repost(dynamic_id,type=False):
	time.sleep(1)
	temp=data_repost['content']
	data_repost['dynamic_id']=dynamic_id
	if type:
		data_repost['content']=temp.split('//')[0]
	# data_repost['content']=tuling.get_response(random.choice(['啦啦啦','嘻嘻嘻','嘿嘿嘿']))
	res=spider_post("https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost",data_repost)
	data_repost['content']=temp
	if res['code']==0:
		print("转发成功")
		return 1
	return 0


def to_comment(oid,dy_id,not_origin,type=0):
	time.sleep(2)
	# 需要获取动态的oid，才能发送评论
	# get_oid_url="https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id="+dynamic_id
	# oid=spider_get(get_oid_url)['data']['card']['desc']['rid']
	if not not_origin:
		data_comment.update({"oid":oid,'type':'11'})
	else:
		data_comment.update({"oid":dy_id,'type':'17'})
	if type==8:
		data_comment.update({"oid":oid,'type':'1','ordering': 'heat'})
	res=spider_post("https://api.bilibili.com/x/v2/reply/add",data_comment)
	print("评论"+res['data']['success_toast'])
	return res['data']['success_toast']


def to_thumbsUp(dynamic_id):
	time.sleep(1)
	data_thumbsUp['dynamic_id']=dynamic_id
	res=spider_post("https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb",data_thumbsUp)
	print(f"动态-点赞成功" if res['code']==0 else res)


def check_dynamic_id():
	# 获取所有已经发送过的存在的动态id
	return dynamic_redis.get_dynamic()


def main():
	if article_id:
		dys=parse_article_get_dy(article_id)
	else:
		dys=action()
	if not dys:
		print("---开始用户抽奖---")
		os.system('python3 follow.py >> users_lucky.log')
		print("---结束用户抽奖---")
		return
	for dy_id in dys:
		try:
			print('https://t.bilibili.com/',dy_id)
			if dy_id in already_dynamic_id:
				print("已有")
				continue
			get_comment_word(dy_id)
			result=get_uid_oid(dy_id)
			if result==1: # 到官方抽奖了
				official_list.append(dy_id)
				print("官方抽奖")
				if len(official_list)>5:
					break
				continue
			if not result:
				print('*#*#*#*#*#*#*#*#*#*原动态处理失败*#*#*#*#*#*#*#*#*#')
				continue
			uid,oid,uname,not_origin=result
			if to_comment(oid,dy_id,not_origin) and to_repost(dy_id):
				to_follow(uid)	
				# to_thumbsUp(dy_id)
				print(uname+"\n\n")
				already_dynamic_id.append(dy_id)
				today_list.append(dy_id)
				dynamic_redis.save_dynamic(dy_id)
			time.sleep(random.randint(6,11))
		except Exception as e:
			print(e)


already_dynamic_id=check_dynamic_id()
if __name__ == '__main__':
	print("\n\n==============="+datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')+"===============")
	main()
	print("==============="+datetime.now(timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')+"===============")
	if today_list:
		with open(f'List/{today_filename}.txt', 'w') as f:
			f.write('=='.join(today_list))
