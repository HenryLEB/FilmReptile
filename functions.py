# coding=utf-8
import wordcloud
import collections
import re
import numpy as np
import time
from PIL import Image
import jieba
import random
import csv
from bs4 import BeautifulSoup
import pandas as pd
import requests
from pylab import *
from matplotlib.font_manager import FontProperties
from reviewsClass import Review

matplotlib.rc('font', family='SimHei', weight='bold')
plt.rcParams['axes.unicode_minus'] = False

font = FontProperties(fname="C:\Windows\Fonts\simfang.ttf", size=18)


# 爬虫返回HTML
def getHtml(url, params=''):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
        'Cookie': 'll="118286"; bid=Mt7tz8rljAs; __gads=ID=8a34ed5e7e5b3af7:T=1598885853:S=ALNI_MYjxx1OJjkFbQDKB2k3dZEOaaXrPw; _vwo_uuid_v2=DA22426902ACD9EB4A554A151DF734C59|6b6da08db5b7eec2d60b9c06bce4ed54; push_doumail_num=0; push_noty_num=0; __utmc=30149280; ap_v=0,6.0; dbcl2="215158090:9pSnz0Bd2dg"; ck=HFZN; __utma=30149280.233430570.1598885854.1598954228.1598965289.8; __utmz=30149280.1598965289.8.5.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/passport/login; __utmt=1; __utmv=30149280.21515; __utmb=30149280.2.10.1598965289'
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        # print(r.status_code)asd
        r.encoding = 'utf-8'
        # r.encoding = r.apparent_encoding
        # print(r.encoding)
        return r.text
    except:
        return ""


# 获取电影详情页
def getFirmDetailsUrl(firm_name):
    douban_url = "https://www.douban.com/search"

    params = {'q': firm_name}
    html = getHtml(douban_url, params)
    soup = BeautifulSoup(html, "html.parser")

    # 找到电影详情链接
    div = soup.find('div', class_='content')

    return div.find('a').attrs['href']


# 获取影评页面url
def getFilmReviewUrl(firm_details_url):
    # 正则表达式 匹配电影参数
    para = re.findall(r'%2F(\d*)%2F', firm_details_url)[1]

    # 拼接 得到所有影评页面url
    firmReviewUrl = 'https://movie.douban.com/subject/' + para + '/reviews'
    return firmReviewUrl


# 获取影评最大页数的参数 每页相隔20
def getMAXPages(a_lists):
    max = 0
    for a in a_lists:
        # print(a)
        try:
            if int(a.string) > max:
                max = int(a.string)
        except:
            pass
    else:
        return (max - 1) * 20


# 爬取所有影评
def getAllReviews(filmReviewUrl):
    html = getHtml(filmReviewUrl)
    soup = BeautifulSoup(html, "html.parser")
    a_lists = soup.select('.paginator')[0].findAll('a')
    maxPages_para = getMAXPages(a_lists)

    # 其实参数为 0 ----> 最大参数 maxPages_para
    para_page = 0
    # 开始循环爬取影评所有页面
    all_reviews = []  # 所有影评（不包含剧透影评）
    while para_page <= maxPages_para:
        # time.sleep(3)
        url_reviews = filmReviewUrl + '?start=' + str(para_page)
        html_reviews = getHtml(url_reviews)
        soup_reviews = BeautifulSoup(html_reviews, "html.parser")
        div_review_list = soup_reviews.select('.review-list div[data-cid]')

        for item in div_review_list:
            # 没有获取到的是：剧透影评
            short_content = item.select('.main-bd .short-content')[0].contents[0].replace('(', '').strip()
            # 跳过剧透影评
            if short_content == '':
                continue

            # 获取评论用户的 昵称 评级 时间 具体评论链接 短评论 有用数量（👍） 无用数量（👎） 回应数量
            name = item.select('.main-hd a[class=name]')[0].text
            tag_rating = item.find('span', {"class": "main-title-rating"})
            rating = tag_rating['title'] if tag_rating != None else ''
            time = item.find('span', {'class': 'main-meta'}).text
            url_details = item.select('.main-bd h2 a')[0]['href']
            useful_num = item.select('.main-bd .action a[title=有用] span')[0].text.strip()
            useless_num = item.select('.main-bd .action a[title=没用] span')[0].text.strip()
            reply_num = int(re.findall(r'(\d*)', item.select('.main-bd .action a[class=reply]')[0].text.strip())[0])

            all_reviews.append(
                Review(name, rating, time, url_details, short_content, useful_num, useless_num, reply_num))

        para_page += 20

    else:
        return all_reviews


# 将爬取到的评论数据 存为CSV文件
def saveDataToCSV(all_reviews):
    with open('评论.csv', 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['用户昵称', '评级', '评论时间', '评论内容（短评）', '具体评论链接', '点赞数', '点踩数', '回复数'])
        for review in all_reviews:
            csv_writer.writerow([review.name, review.rating, review.time, review.short_content,
                                 review.url_details, review.useful_num, review.useless_num, review.reply_num])


# 通过传入的csv文件，将所有用户的评论拼成一个长的字符串，用于生产词云
def getStrReview(csvFile):
    data_reviews = pd.DataFrame(csvFile)
    str_reviews = ''
    for review in data_reviews['评论内容（短评）']:
        str_reviews += review

    # 去除所有标点符号
    str_reviews = re.findall('[\u4e00-\u9fa5]', str_reviews)
    str_reviews = ''.join(str_reviews)

    return str_reviews


# 绘制评论词云图
def drawReviewsCloud(str_reviews):
    words = jieba.lcut(str_reviews)
    counts = {}
    for word in words:  # 筛选分析后的名词
        if len(word) == 1:  # 词组中的汉字数大于1个即认为是一个词组
            continue
        counts[word] = counts.get(word, 0) + 1

    mask = np.array(Image.open("aixin.png"))
    wcd = wordcloud.WordCloud(
        background_color="white",
        font_path='C:\Windows\Fonts\simfang.ttf',
        max_words=100,
        mask=mask
    )
    wcd.fit_words(counts)
    wcd.to_file("词云图-评论.png")


def drawSatisfactionAnalysisDiagram(csvFile):
    data_reviews = pd.DataFrame(csvFile)
    satisfaction = data_reviews['评级'].value_counts()
    # 评级总数量
    total_ratingNum = int(satisfaction.sum())
    # 评级所占比例： 例 {'力荐': 0.85 , '推荐': 0.05}
    dict_proportion_rating = {}
    satisfaction = dict(satisfaction)
    for item in satisfaction:
        dict_proportion_rating[item] = round(float(satisfaction[item]) / total_ratingNum, 4)

    # explode = [0.1, 0, 0, 0, 0]
    # explode = explode[0:len(dict_proportion_rating)]
    # 设置饼图参数
    plt.figure(figsize=(9, 9))
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.axes(aspect=1)
    colors = ['red', 'pink', 'lightskyblue', 'hotpink', 'yellow']

    patches, l_text, p_text = plt.pie(x=dict_proportion_rating.values(),
                                      labels=dict_proportion_rating.keys(),
                                      autopct='%3.2f%%',
                                      shadow=False,
                                      labeldistance=1.1,
                                      colors=colors,
                                      startangle=90,
                                      pctdistance=0.6, )

    for t in l_text:
        t.set_size(20)
    for t in p_text[0:3]:
        t.set_size(20)
    plt.axis('equal')
    plt.legend()
    plt.savefig('电影满意度分析图.png')
    plt.show()


def drawPeriodOfTimeHistogram(csvFile):
    data_reviews = pd.DataFrame(csvFile)
    dic_time = dict(data_reviews['评论时间'])

    # 一天24小时 爬取到的不一定在所有的时间段
    time_period = {}
    for i in range(24):
        time_period[str(i).zfill(2)] = 0;

    # 通过正则表达式，从日期字符串中提取小时部分
    for item in dic_time:
        dic_time[item] = re.findall(r' (\d*):', dic_time[item])[0]

    dic_time = pd.Series(dic_time).value_counts()
    dic_time = dic_time.sort_index()
    dic_time = dict(dic_time)

    for key in list(dic_time.keys()):
        time_period[key] = dic_time.get(key)

    # 设置参数 绘制条形图
    # 24 个小时
    N = 24

    x = np.arange(N)
    data = list(time_period.values())
    colors = np.random.rand(N * 3).reshape(N, -1)

    labels = []
    for i in range(N):
        labels.append(str(i).zfill(2) + '~' + str(i + 1).zfill(2))

    plt.figure(figsize=(16, 9))
    plt.title("网友评论时间段活跃度分析", fontproperties=font)
    plt.xlabel(u"时间段", fontproperties=font)
    plt.ylabel(u"活跃人数", fontproperties=font)
    plt.bar(x, data, alpha=0.8, color=colors, tick_label=labels)
    plt.savefig('网友评论时间段活跃度分析图.png')



    plt.show()
