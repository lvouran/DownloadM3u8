#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/4 22:05
# @Author  : ouran
# @File    : shipin.py
# @funtion : 多线程 审判流程公开网的视频, 庭审直播和庭审录播两个
# ------------------------


import requests, json, re, time
from lxml import etree


class CourtViod(object):
    def __init__(self):
        self.cookie = 'acw_tc=76b20ffa15572184092261919e0d53f994c02e5d84438b15e6812f7fe37db7; _uab_collina=155721840947037510568572; _pk_ref.1.a5e3=%5B%22%22%2C%22%22%2C1557375305%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DqWW6RW0VPz3eMhLE_oLb2D0Gukx470-OgCJaWBe1xTc_D-cEXKga_ye09mNGWlQ3%26wd%3D%26eqid%3D8e94586b0006a144000000035cd23a68%22%5D; _pk_id.1.a5e3=387cf9b78c07822b.1557218411.3.1557375308.1557375305.; acw_sc__v2=5cd3fae9e59a9d402601239a064c9827c7a1f1c2; SERVERID=e5784715955cf8401e561e76eb6fd172|1557396203|1557373825'
        self.base_url = 'http://tingshen.court.gov.cn/live/{}'
        self.retry_count = 5
        self.headers1 = {
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate',
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Host': 'tingshen.court.gov.cn',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        }
        self.headers2 = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': self.cookie,
            'Host': 'player.videoincloud.com',
            'Referer': 'http://player.videoincloud.com/vod/3466896?src=gkw&cc=1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.url_dict = {
            'recorded': 'http://tingshen.court.gov.cn/search/a/revmor/full?keywords=&provinceCode=&cityCode=&label=&courtCode=&catalogId=&dataType=5&pageSize=10&address=&timeFlag=&caseType=&courtType=&pageNumber={}&extType=&isOts=',  # 录播
            'live': 'http://tingshen.court.gov.cn/review/getLatestCase?pageNumber=3'  # 直播
        }
        self.proxy = [
            '27.28.232.84:4216',
            '121.234.52.1:4232',
            '183.162.179.250:4248',
            '114.239.172.34:4236',
            '180.116.19.131:4276',
            '111.76.170.19:4225',
            '180.114.174.25:4283',
            '183.165.60.92:4276',
            '220.177.189.196:4217',
            '182.109.212.112:4221'
        ]
        # self.recorded_params = {
        #     'keywords': '',
        #     'provinceCode': '',
        #     'cityCode': '',
        #     'label': '',
        #     'courtCode': '',
        #     'catalogId': '',
        #     'dataType': '5',
        #     'pageSize': '10',
        #     'address': '',
        #     'timeFlag': '',
        #     'caseType': '',
        #     'courtType': '',
        #     'pageNumber': '2',
        #     'extType': '',
        #     'isOts': '',
        # }

    # 获取庭审录播的caseid, title(考虑整个json字段存放到mongo，方便新需求的解析)
    def get_recorded_caseid(self, url, flag):
        _recorded_res = self.retry_request(url, self.headers1)
        if _recorded_res:
            try:
                _recorded_dict = json.loads(_recorded_res.text)
                if 'resultList' in _recorded_dict.keys():
                    res_list = _recorded_dict.get('resultList', [])
                elif 'data' in _recorded_dict.keys():
                    res_list = _recorded_dict.get('data', [])
                else:
                    res_list = []
                for res in res_list:
                    _case_id = res.get('caseId', '')
                    _title = res.get('title', '')
                    yield _case_id, _title
            except Exception as e:
                raise ValueError(e, url, i)

    # 获取庭审录播的m3u8
    def get_recorded_m3u8(self, url, flag):
        _res = self.retry_request(url, self.headers1)
        if _res:
            html = etree.HTML(_res.text)
            _url = html.xpath('//iframe[@id="player"]/@src')
            if _url and flag == 'recorded':
                _res_m = requests.get(_url[0], headers=self.headers2)
                _recorded_m3u8 = re.search('http.*?m3u8', _res_m.text)
                if _recorded_m3u8:
                    return _recorded_m3u8.group(0)
            elif _url and flag == 'live':
                _res_m = requests.get(_url[0], headers=self.headers2)
                _recorded_m3u8 = re.search('/.*?m3u8', _res_m.text).group(0)
                return _recorded_m3u8

    def retry_request(self, retry_url, headers):
        for _i in range(1, self.retry_count + 1):
            time.sleep(_i)
            _res = requests.get(retry_url, headers=headers)
            if _res.status_code == 200:
                # self.cookie = _res.cookies
                return _res
        return False


if __name__ == '__main__':
    test = CourtViod()
    for k, v in test.url_dict.items():
        if k == 'recorded':
            for i in range(745, 5000):
                for caseid, title in test.get_recorded_caseid(v.format(i), k):
                    _url = test.base_url.format(caseid)
                    m3u8_url = test.get_recorded_m3u8(_url, k)
                    if m3u8_url:
                        with open('m3u8.txt', 'a', encoding='utf8') as f:
                            f.write(f'{title}\t{m3u8_url}\n')
