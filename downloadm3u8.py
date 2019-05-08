# -*- coding:utf-8 -*-
# author:ouran
# datetime:2019/5/7 14:42
# software: PyCharm
# introduce: 下载m3u8视频，支持多线程和为每个线程挂代理

import requests, os, hashlib
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


class M3u8(object):
    def __init__(self, file_dir='', movie_dir='', headers='', cut=False):
        """
        :param file_dir:   用来保存m3u8文件的路径(默认为当前路径+m3u8_files)
        :param movie_dir:  用来保存下载好的视频的路径(默认为当前路径+movie_files)
        :param headers:    伪装头
        :param cut:        以文件名的md5前两位作为子文件夹进随机存储，防止单个文件夹文件过多
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
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

    @staticmethod
    def md5(_str):
        """
        进行md5的加密 保证唯一性
        :param _str:  要加密的字符串
        :return:     加密后的结果
        """
        m = hashlib.md5()
        m.update(_str.encode("utf8"))
        return m.hexdigest()

    @staticmethod
    def create_download_dirs(path):
        """
        创建不存在的文件夹
        :param path: 文件夹的路径
        :return: None
        """
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_url_from_file(m_file_path):
        """
        从文件中获取m3u8流视频的url
        :param m_file_path: 文件的绝对路径
        :return: None
        """
        with open(m_file_path, 'r', encoding='utf8') as _f:
            for line in _f:
                yield line.replace('\n', '')

    def download_movies(self, mv_file_path, start_url):
        """
        下载视频
        :param mv_file_path:  m3u8文件的绝对路径（可以不使用get_m3u8_body函数，直接使用下载好的m3u8文件）
        :param start_url:     起始的url
        :return: None
        """
        if mv_file_path:
            with open(mv_file_path, 'r', encoding='utf8') as f:
                assert '#EXTM3U' in f.readline(), '检查文件类型,文件起始并无m3u8格式的标识...'
                _movie_f = open(os.path.join(self.movie_path, 'test1.mp4'), 'ab+')
                for index, lines in tqdm(enumerate(f)):
                    if 'ts' in lines:
                        _movie_url = lines.replace('\n', '')
                        if 'http' not in lines:
                            _movie_url = self.get_compurl(start_url, _movie_url)
                        _movie_res = requests.get(_movie_url, headers=self.headers)
                        if _movie_res.status_code != 200:
                            return f'下载失败...url:\t{start_url}\t状态码\t{_movie_res.status_code}\t位置\t{lines}', start_url, lines
                        _movie_f.write(_movie_res.content)
                _movie_f.close()
            return '', '', ''

    def get_compurl(self, m_base_url, broken_url):
        """
        构造完整的url
        :param m_base_url:  起始url
        :param broken_url:  从m3u8文件中读取出来的不含主域名的url
        :return:            拼凑出完整的url
        """
        return '/'.join(m_base_url.split('/')[:-1]) + f'/{broken_url}'

    def get_m3u8_body(self, m_url, m_file_name=''):
        """
        :param m_url:       起始的m3u8地址
        :param m_file_name  m3u8的文件名
        :return:            文件的绝对路径(默认使用m3u8_file_path作为子文件夹， url的MD5形式作为文件名)
        """
        assert m_url, '起始url不能为空...'
        if not m_file_name:
            m_file_name = self.md5(m_url)
        _file_res = requests.get(m_url, headers=self.headers)
        if _file_res.status_code != 200:
            # 这里需要测试下需不需要锁
            with open('file_error.txt', 'a', encoding='utf8') as _f:
                _f.write(f'此url:\t{m_url}返回的的状态码{_file_res.status_code}不为200...')
                return None
        with open(os.path.join(self.m3u8_file_path, self.md5(m_url)), 'wb') as file_f:
            file_f.write(_file_res.content)
        return os.path.join(self.m3u8_file_path, m_file_name)

    def continue_download(self, broken_location, start_url, file_path=''):
        """
        找到下载失败的文件，从断点处继续下载
        :param broken_location: 断点位置
        :param start_url:       下载失败的url（如果给了，此参数不起作用，会去file_path给定的位置找到对应的m3u8文件然后找到断点的位置）
        :param file_path:       下载失败的文件路径
        :return:
        """
        _file_path = file_path
        if not _file_path:
            _file_path = self.get_m3u8_body(start_url)
        _flag = 0
        with open(_file_path, 'r', encoding='utf8') as _f:
            for line in _f:
                if line == broken_location:
                    _flag = 1
                if _flag:
                    self.download_movies(_file_path, start_url)
# class Proxy(object):
#     def __init__(self):
#         pass
#
#     def get_proxies(self):
#         pass
#
#     def add_proxy(self):
#         pass
#
#     def update_proxy(self):
#         pass


if __name__ == '__main__':
    url = 'http://119.97.184.228:1126/trials/2019_year/05_month/07_day/558154BA_9254_D33E_FB87_4F5F0F9BD961/9B5834FB_AB7A_70B7_306A_8828917DE4F6/92304845_E648_EC77_ACA4_E9FDE6F13A78vod.m3u8'
    test = M3u8()
    _error_f = open('movie_errors.txt', 'a', encoding='utf8')
    url_list = test.get_url_from_file('包含多个m3u8地址的文件')
    executor = ThreadPoolExecutor(max_workers=100)
    m_files = executor.map(test.get_m3u8_body, url_list)
    for item in executor.map(test.download_movies, m_files, url_list):
        for error_str, start_url, title in item:
            _error_f.write(f'{error_str}\t{start_url}\t\n')
    _error_f.close()
