# -*- coding:utf8 -*-
import sys

import re
import threading
from collections import OrderedDict
from Queue import Queue

import pymysql
import requests
import time
import logging

reload(sys)
sys.setdefaultencoding("utf8")

logging.basicConfig(
    level=logging.ERROR,
    filename='error.log',
    filemode='w',
)

INTERVAL_TIME = 5


def get_header():
    header = {}
    with open("header") as f:
        for line in f.readlines():
            ln = line.split(":")
            key = ln.pop(0).strip()
            value = "".join(ln).strip()
            header[key] = value
    return header

class DBHandler(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = pymysql.connect(
            host="localhost",
            port=3306,
            user='root',
            passwd='root',
            db='fishc',
            charset='utf8',
            autocommit=False,
            read_timeout=5,
            write_timeout=5,
        )

        self.cursor = self.conn.cursor()

        self.sql = {
            # 表【category】可下载栏目相关信息保存
            "insert": "INSERT INTO `category`(`id`,`num`,`title`,`name`,`url`,`state`) VALUES (%s,%s,%s,%s,%s,%s);",
            #表 【detail】 详情页面相关信息的保存
            "insert_detail": "INSERT INTO `detail` (`id`, `num`,`name`, `link`, `state`) VALUES (%s,%s,%s,%s,%s);",
            "select": "SELECT `id`, `num`, `url` FROM `category` WHERE `state`=1;",
            "select_link": "SELECT `link` FROM `detail` WHERE `state` = '1';",
            # 表 【detail】 更新并存储  链接-验证码
            "update": "UPDATE `detail` SET `_link`=%s,`_verify`=%s, `state`='0' WHERE `link`=%s ;",
        }

    def save(self,sql,value):
        with self.lock:
            try:
                # print sql,value
                self.cursor.execute(sql,value)
                self.conn.commit()
                print "保存成功：%s",value
            except pymysql.err.IntegrityError:
                # print "数据重复"
                # print "数据重复",e.message
                pass
            except pymysql.err.DataError as e:
                logging.error('save_error'+e.message)

    def select(self,sql,value=None):
        try:
            self.cursor.execute(sql,value)

            return self.cursor.fetchall()

        except pymysql.MySQLError as e:
            pass

    def update(self,sql,value=None):
        with self.lock:
            try:
                self.cursor.execute(sql,value)
                self.conn.commit()
            except pymysql.MySQLError as e:
                pass

class FishC(object):
    def __init__(self):
        self.url = "http://blog.fishc.com/"
        self.header = get_header()
        self.items = None
        self.sel_list = []

        self.db = DBHandler()
        self.sql = self.db.sql

    def get_html(self, url):
        print '+++正在请求...\t',url
        resp = requests.get(url, headers=self.header)
        # print resp.status_code
        html = resp.content
        time.sleep(INTERVAL_TIME)

        return html

    def parse(self, html):
        data_slice = re.search("<div id=\"nav\">(.*)<li class=\"dropdownlink\">", html, re.S).group(0)

        dicts = OrderedDict()

        #多栏目item
        re_item = re.compile("<li class=\"dropdownlink\">.*?</ul>.*?</li>", re.S)
        st = re.sub(re_item, "", data_slice)
        #单栏目
        sigle_item = re.findall("<li><a href=\"(?P<link>.*?)\">(?P<name>.*?)</a></li>", st)

        for item in sigle_item:
            dicts[item[1]] = [item]

        many_item = re.findall(re_item, data_slice)
        for item in many_item:
            title = re.search("<a href=\"javascript.*?>(.*?)<span></span></a>", item).group(1)
            temp_item = re.findall("<li><a href=\"(.*?)\">(.*?)</a></li>", item)
            dicts[title] = temp_item

        return dicts

    def get_data_dict(self):
        html = self.get_html(self.url)
        self.items = self.parse(html)

        for item in enumerate(self.items):
            # print item[0],item[1]
            self.sel_list.append(item[1])

    def save_db_category(self):
        self.get_data_dict()

        id = 1
        num = 0
        state = 1
        for key, values in self.items.items():
            num +=1
            for link, name in values:

                print '+++正在保存【%s---%s】%s'%(id,num, link)
                self.db.save(self.sql["insert"], (id, num, key, name, link, state))
                id += 1
                # try:
                #     print (id,num,key,name,link,state)
                #
                #     self.cursor.execute(self.sql["insert"],(id,num,key,name,link,state))
                #     self.conn.commit()
                #     id += 1
                # except pymysql.Error as e:
                #     logging.error("save_db_error"+e.message)
                #     self.conn.rollback()

        print("数据全部保存成功！！！")

    def get_results(self):
        results = self.db.select(self.sql["select"])
        if not results:
            self.save_category_db()
            results = self.db.select(self.sql["select"])

        return results

class FishC_detail(FishC, threading.Thread):
    def __init__(self,threadNum=1):
        FishC.__init__(self)
        threading.Thread.__init__(self)

        self.threadNum = threadNum

        self.lock = threading.Lock()

        # self.url = "http://blog.fishc.com/category/cpp"

        self.h2_cmpl = re.compile('<h2><a\s+?href="(?P<link>.*?)".*?>(?P<title>.*?)</a>.*?</h2>',re.S)
        self.page_cmpl = re.compile("<a\s+?href='(?P<link>.*?)'\s+?class='inactive'",re.S)
        self._verify = re.compile('<a href="(http://pan.baidu.com/s/.*?)".*?>.*?密码：([\w\d]{4})')
        self._qq_xuanfeng = re.compile(".*<a href=\"(.*?)\" target=\"_blank\">QQ旋风</a>", re.S)
        self.re_compile = {
            "h2_re":self.h2_cmpl,
            "page_re":self.page_cmpl,
            "verify":self._verify,
            "qq_xuanfeng":self._qq_xuanfeng,
        }

        self.urls = Queue()

        # self.item_links_list = deque()
        self.item_links_list = Queue()

        self.init()

    def init(self):
        results = self.get_results()
        for result in results:
            self.urls.put(result)
        print len(results)


    def parse_link(self,html):
        temp = re.findall(self.re_compile["h2_re"],html)

        return temp

    def parse_next_link(self,html):

        next_link = re.findall(self.re_compile["page_re"],html)

        return next_link

    def get_item_link(self):

        while not self.urls.empty():
            temp = self.urls.get()

            temp_id = temp[0]
            temp_num = temp[1]
            temp_url = temp[2]


            html = self.get_html(temp_url)
            next_links = self.parse_next_link(html)
            page_links = self.parse_link(html)
            while next_links:
                url = next_links.pop()
                html = self.get_html(url)
                page_links += self.parse_link(html)

            for item in page_links:
                print "item",item
                self.db.save(self.sql["insert_detail"], (temp_id, temp_num, item[1], item[0], 1))


    def start(self):
        thread1 = []
        for i in range(self.threadNum):
            t = threading.Thread(target=self.get_item_link)
            thread1.append(t)
        for i in range(len(thread1)):
            thread1[i].start()

        for i in range(len(thread1)):
            thread1[i].join()

class VerifyLink(FishC):
    def __init__(self,threadNum=1):
        FishC.__init__(self)

        self.threadNum = threadNum

        self.fetchItem = Queue()

        self.fenye = re.compile('<div class="fenye">',flags=re.S)
        self.fenye_link = re.compile('<div class="fenye">.*<a href="(.*?)"><span>\d+</span></a>')

        self._verify = re.compile('<a href="(http[s]?://pan.baidu.com/s/.*?)".*?>.*?密码：([\w\d]{4})')
        self._qq_xuanfeng = re.compile(".*<a href=\"(.*?)\" target=\"_blank\">QQ旋风</a>")

        self.re_compile = {
            "verify": self._verify,
            "fenye": self.fenye,
            "fenye_link":self.fenye_link,
            "qq_xf":self._qq_xuanfeng,
        }

        self.init()


    def init(self):
        results = self.db.select(self.sql["select_link"])

        for result in results:
            self.fetchItem.put(result[0])

    def save_verify(self):

        while not self.fetchItem.empty():
            link = self.fetchItem.get()
            html = self.get_html(link)

            fenye = re.search(self.re_compile["fenye"],html)

            if fenye :
                fenye_link = re.search(self.re_compile["fenye_link"],html)
                html = self.get_html(fenye_link.group(1))

            link_ver = re.search(self.re_compile["verify"], html)
            if link_ver:
                data = link_ver.groups()
                self.db.save(self.sql["update"],(data[0],data[1],link))
            else:
                qq_xf = re.search(self.re_compile["qq_xf"], html)
                if qq_xf:
                    data = qq_xf.groups()
                    self.db.save(self.sql["update"], (data[0],None,link))

    def start(self):

        thread_list = []

        for i in range(self.threadNum):
            t = threading.Thread(target=self.save_verify)
            thread_list.append(t)
            t.setDaemon(True)

        for i in range(len(thread_list)):
            thread_list[i].start()

        for i in range(len(thread_list)):
            thread_list[i].join()

if __name__ == '__main__':
    # category = FishC()
    #保存栏目列表
    # category.save_db_category()
    #保存详细信息
    # detail = FishC_detail(threadNum=2)
    # detail.start()

    ver = VerifyLink(threadNum=2)
    #保存验证码--链接
    ver.save_verify()