import redis
import os

# Redis_psw=os.environ["Redis_psw"]
# Redis_IP=os.environ["Redis_IP"]

# rd=redis.Redis(host=Redis_IP, port=6379, db=0, password=Redis_psw)


def save_dynamic(dynamic_id,filename='dy_id2.txt'):
	with open(filename,'a',encoding='utf-8') as f:
		f.writelines(f'{dynamic_id}\n')
# 	rd.lpush("already_dynamic_id-2", dynamic_id)


def save_official_lucky(official_lucky):
	pass
# 	rd.lpush("official_lucky_uid_dynamic", official_lucky)


def get_dynamic(filename='dy_id2.txt'):
	with open(filename,'r',encoding='utf-8') as f:
		return f.read().split('\n')[-1000:]
# 	res=rd.lrange("already_dynamic_id-2", 0, 3000)
# 	return list(map(lambda x:str(x,encoding='utf-8'),res))

# print(get_dynamic())

if __name__ == '__main__':
	print(get_dynamic())
