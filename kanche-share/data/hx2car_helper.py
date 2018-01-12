# coding=utf-8
__author__ = 'zhuonima'

# 辅助生成json格式的 用户名-密钥
if __name__ == '__main__':
    f = open('hx_api_account.txt')
    lines = f.readlines()
    lines = map(lambda line: line.split("\t"), lines)
    lines = map(lambda line: [line[0], line[4].strip()], lines)
    for (usr, key) in lines:
        print('"%s": "%s",' % (usr, key))
