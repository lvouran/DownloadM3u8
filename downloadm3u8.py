# -*- coding:utf-8 -*-
# author:ouran
# datetime:2019/5/7 14:42
# software: PyCharm
# introduce: 下载m3u8视频，支持多线程和为每个线程挂代理

import requests, os, hashlib, random
from tqdm import tqdm


class M3u8(object):
    def __init__(self, start_url, file_dir='', movie_dir='', headers='', cut=False):
        """
        :param start_url:  m3u8 url
        :param file_dir:   用来保存m3u8文件的路径(默认为当前路径+m3u8_files)
        :param movie_dir:  用来保存下载好的视频的路径(默认为当前路径+movie_files)
        :param headers:    伪装头
        :param cut:        以文件名的md5前两位作为子文件夹进随机存储，防止单个文件夹文件过多
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.start_url = start_url
        self.m3u8_file_path = file_dir
        self.movie_path = movie_dir
        self.headers = headers
        self.cut = cut
        if not file_dir:
            self.m3u8_file_path = os.path.join(base_dir, 'm3u8_files')
        if not movie_dir:
            self.movie_path = os.path.join(base_dir, 'movie_files')
        if not headers:
            self.headers = {
                # 'Referer': 'http://player.videoincloud.com/vod/3457777?src=gkw&cc=1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
            }
        self.create_download_dirs(self.m3u8_file_path)
        self.create_download_dirs(self.movie_path)

    # 进行md5的加密 保证唯一性
    @staticmethod
    def md5(_str):
        """
        :param _str:  要加密的字符串
        :return:     加密后的结果
        """
        m = hashlib.md5()
        m.update(_str.encode("utf8"))
        return m.hexdigest()

    # 创建不存在的文件夹
    @staticmethod
    def create_download_dirs(path):
        """
        :param path: 文件夹的路径
        :return:     None
        """
        if not os.path.exists(path):
            os.makedirs(path)

    # 通过m3u8文件下载视频
    def download_movies(self, file_path):
        """
        :param file_path:  m3u8文件的绝对路径（可以不使用get_m3u8_body函数，直接使用下载好的m3u8文件）
        :return:           None
        """
        with open(file_path, 'r', encoding='utf8') as f:
            assert '#EXTM3U' in f.readline(), '检查文件类型,文件起始并无m3u8格式的标识...'
            _movie_f = open(os.path.join(self.movie_path, 'test1.mp4'), 'ab+')
            for index, lines in tqdm(enumerate(f)):
                if 'ts' in lines:
                    _movie_url = lines.replace('\n', '')
                    if 'http' not in lines:
                        _movie_url = self.get_compurl(_movie_url)
                    _movie_res = requests.get(_movie_url, headers=self.headers)
                    assert _movie_res.status_code == 200, f'下载失败...url:\t{_movie_url}\n状态码\t{_movie_res.status_code}'
                    _movie_f.write(_movie_res.content)
            _movie_f.close()

    # 构造完整的url
    def get_compurl(self, broken_url):
        return '/'.join(self.start_url.split('/')[:-1]) + f'/{broken_url}'

    def get_m3u8_body(self, url, file_name=''):
        """
        :param url:  起始的m3u8地址
        :return:     文件的绝对路径(默认使用m3u8_file_path作为子文件夹， url的MD5形式作为文件名)
        """
        assert url, '起始url不能为空...'
        if not file_name:
            file_name = self.md5(url)
        _file_res = requests.get(url, headers=self.headers)
        assert _file_res.status_code == 200, f'此url:\t{url}返回的的状态码{_file_res.status_code}不为200...'
        with open(os.path.join(self.m3u8_file_path, self.md5(url)), 'wb') as file_f:
            file_f.write(_file_res.content)
        return os.path.join(self.m3u8_file_path, file_name)


class Proxy(object):
    def __init__(self):
        pass

    def get_proxies(self):
        pass

    def add_proxy(self):
        pass

    def update_proxy(self):
        pass


if __name__ == '__main__':
    url = 'http://119.97.184.228:1126/trials/2019_year/05_month/07_day/558154BA_9254_D33E_FB87_4F5F0F9BD961/9B5834FB_AB7A_70B7_306A_8828917DE4F6/92304845_E648_EC77_ACA4_E9FDE6F13A78vod.m3u8'
    test = M3u8(url)
    file_path = test.get_m3u8_body(url)
    test.download_movies(file_path)
