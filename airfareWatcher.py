#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import datetime
import sys
import os
import pinyin


def write_record(dcity, acity, email, price, date):
    # 先假设是新记录
    newrecord = True
    filename = "notification" + str(datetime.date.today()) + ".log"
    with open(filename, "r+", encoding='utf-8') as f:
        while True:
            fp = f.tell()
            line = f.readline()
            if not line:
                break
            else:
                # 若找到记录，修改记录的通知次数或打印通知次数已满
                if line.split(' ')[1] == dcity + "-" + acity:
                    if line.split(' ')[2] == email:
                        if int(line.split(' ')[3]) == int(price):
                            if line.split(' ')[4] == date:
                                newrecord = False
                                if int(line.split(' ')[5]) < 3:
                                    # 通知次数小于等于3次，修改通知次数，进行通知
                                    f.seek(fp)
                                    now = time.strftime("%H:%M:%S", time.localtime())
                                    print("[" + now + "] " + dcity + "-" + acity + " " + email + " " + str(price) + \
                                            " " + date + " " + str(int(line.split(' ')[5]) + 1))
                                    f.write("[" + now + "] " + dcity + "-" + acity + " " + email + " " + str(price) + \
                                            " " + date + " " + str(int(line.split(' ')[5]) + 1) + "\n")
                                    # todo: 通知
                                else:
                                    print(dcity + "-" + acity + " " + email + " " + str(price) + \
                                            "元 " + date + " " + str(int(line.split(' ')[5])) + " 该记录今日通知次数已满")
    if newrecord == False:
        # 修改记录
        return False
    else:
        # 增加记录
        with open(filename, "a", encoding='utf-8') as f:
            now = time.strftime("%H:%M:%S", time.localtime())
            print("[" + now + "] " + dcity + "-" + acity + " " + email + " " + str(price) + " " + date + " 1")
            f.write("[" + now + "] " + dcity + "-" + acity + " " + email + " " + str(price) + " " + date + " 1\n")


def get_city_letters(city):
    html = requests.post("https://flights.ctrip.com/itinerary/api/poi/get")
    first_letter = pinyin.get_initial(city[0:1], delimiter="").upper()
    groups = ["ABCDEF", "GHIJ", "KLMN", "PQRSTUVW", "XYZ"]
    #print(first_letter)
    for i in range(0, len(groups)):
        if first_letter in groups[i]:
            #print(groups[i])
            cities = json.loads(html.text)["data"][groups[i]][first_letter]
            for i in range(0, len(cities)):
                if cities[i]['display'] == city:
                    #print(cities[i]['data'])
                    return cities[i]['data'].split('|')[-1]


def get_price(expected_price, fdate, tdate, dcity, acity, email):
    # 通过POST方法获取90天内每天的机票最低价
    payload = {"flightWay": "Oneway", "dcity": get_city_letters(dcity), "acity": get_city_letters(acity)}
    html = requests.post("https://flights.ctrip.com/itinerary/api/12808/lowestPrice", data=payload)
    res = json.loads(html.text)

    # 如果数据爬取成功，解析“日期-最低价”字典数据
    if res["msg"] == "success":
        prices = res["data"]["oneWayPrice"][0]
        #print(prices)
        #print(type(prices)) #class 'dict'
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        #print(type(tomorrow)) # datetime.date
        tomorrow_struct = time.strptime(str(tomorrow), '%Y-%m-%d')
        #print(type(tomorrow_struct)) # time.struct_time
        tomorrow_string = time.strftime('%Y%m%d', tomorrow_struct)
        #print(tomorrow_string)
        minval = int(prices[tomorrow_string])
        mindate = tomorrow_string
        # 遍历最低价字典
        for key, val in prices.items():
            # 获取90天内的最低价
            if int(val) < minval:
                minval = int(val)
                mindate = str(key)
            tmptime = time.mktime(time.strptime(str(key), '%Y%m%d'))
            # 将监控日期范围内的价格与期望价格进行比较
            if tmptime >= time.mktime(fdate) and tmptime <= time.mktime(tdate):
                #print("[监控价格] %s元 %s" % (val, key))
                if int(val) <= expected_price:
                    write_record(dcity, acity, email, val, key)
            #print("[DATA] %s [PRICE] %d" % (key, int(val)))
        print("[%d天内最低价] %d元 %s" % (len(prices), minval, mindate))


if __name__ == "__main__":
    # 从命令行参数获取监控日期范围以及期望价格
    expected_price = int(sys.argv[1])
    print("预期价格：%d元" % expected_price)
    fdate = time.strptime(sys.argv[2], '%Y-%m-%d')
    tdate = time.strptime(sys.argv[3], '%Y-%m-%d')
    # 从命令行参数获取出发地和目的地，通过get_city_letters(city)函数转换为城市名的字母表示
    fcity = sys.argv[4]
    tcity = sys.argv[5]
    # 从命令行参数获取通知邮箱
    email = sys.argv[6]

    # 创建日志文件
    filename = "notification" + str(datetime.date.today()) + ".log"
    if not os.path.isfile(filename):
        with open(filename, 'a', encoding='utf-8'):
            print('日志文件%s' % filename)

    print('从%s到%s' % (fcity, tcity))
    get_price(expected_price, fdate, tdate, fcity, tcity, email)
    print('\n从%s到%s' % (tcity, fcity))
    get_price(expected_price, fdate, tdate, tcity, fcity, email)
