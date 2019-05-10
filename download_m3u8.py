#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/8 21:37
# @Author  : ouran
# @File    : download_m3u8.py
# @funtion :
# ------------------------
import requests, os, hashlib, time, random
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
                'Connection': 'close',  # 防止过多得链接没有关闭导致max错误
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'
            }
        self.create_download_dirs(self.m3u8_file_path)
        self.create_download_dirs(self.movie_path)
        self.retry_count = 5
        self._s = requests.session()
        self._s.keep_alive = False
        self.proxies = [
            '114.226.135.246:4207',
            '124.116.172.248:4251',
            '60.210.166.230:4284',
            '182.244.168.217:4265',
            '27.25.99.13:4271',
            '125.123.22.71:4225',
            '117.66.26.161:4265',
            '117.28.113.239:4286',
            '112.114.164.51:4228',
            '182.99.153.238:4276'
        ]

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
        _title_list = []
        _url_list = []
        with open(m_file_path, 'r', encoding='utf8') as _f:
            for line in _f:
                info_list = line.replace('\n', '').split('\t')
                _title_list.append(info_list[0])
                _url_list.append(info_list[1])
        return _title_list, _url_list

    def download_movies(self, mv_file_path, start_url, title):
        """
        下载视频
        :param mv_file_path:  m3u8文件的绝对路径（可以不使用get_m3u8_body函数，直接使用下载好的m3u8文件）
        :param start_url:     起始的url
        :param title:         视频的名字
        :return: None
        """
        if mv_file_path:
            with open(mv_file_path, 'r', encoding='utf8') as f:
                assert '#EXTM3U' in f.readline(), '检查文件类型,文件起始并无m3u8格式的标识...'
                # _movie_f = open(os.path.join(self.movie_path, f'{title}.mp4'), 'ab+')
                for index, lines in tqdm(enumerate(f)):
                    if 'ts' in lines:
                        _movie_url = lines.replace('\n', '')
                        if 'http' not in lines:
                            _movie_url = self.get_compurl(start_url, _movie_url)
                        _movie_res = self.retry_request(_movie_url, headers=self.headers)
                        if not _movie_res:
                            # 如果下载失败
                            yield False, _movie_res, lines, start_url, title
                        else:
                            yield True, _movie_res, lines, start_url, title
            #             if not _movie_res:
            #                 # 这里需要将信息返回，并且关掉当前线程
            #                 return f'下载失败...url:\t{start_url}\t状态码\t位置\t{lines}', start_url, lines, title
            #             # 这里须要获取各个线成顺序性的返回，而不是直接写入文件，开启另外一个线程专门用来将所有的视频片段按顺序写成整个文件
            #             # 即使视频下载了一半也需要将一半写成文件，并记录当前失败位置，方便继续下载
            #             _movie_f.write(_movie_res.content)
            #     _movie_f.close()
            # return '', '', ''

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
        _file_res = self.retry_request(m_url, self.headers)
        if not _file_res:
            # 这里需要测试下需不需要锁
            with open('file_error.txt', 'a', encoding='utf8') as _f:
                _f.write(f'此url:\t{m_url}返回的的状态码不为200...\n')
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
                    self.download_movies(_file_path, start_url, title)

    def retry_request(self, retry_url, headers):
        try:
            for _i in range(1, self.retry_count + 1):
                # proxy = {
                #     'http': f'http://{random.choice(self.proxies)}'
                # }
                time.sleep(_i)
                _res = self._s.get(retry_url, headers=headers)
                if _res.status_code == 200:
                    return _res
            return False
        except Exception:
            return False

    def deal_res(self, m_file, url, _title):
        for flag, res, broken_liens, start_url, title in test.download_movies(m_file, url, _title):
            # 对返回的结果进行判断，生成器
            if flag:
                # 下载成功， 整合成mp4文件
                with open(os.path.join(self.movie_path, f'{title}.mp4'), 'ab+') as _f:
                    _f.write(res.content)
                print(res.url, broken_liens, start_url)
            else:
                # 下载失败， 将下载成功的部分整合成mp4文件，失败的地方记录，方便继续下载
                print(res.url, broken_liens, start_url)
                with open(f'{title}error.txt', 'a') as error_f:
                    error_f.write(f'下载失败...url:{start_url}位置{broken_liens}\t{start_url}\t{broken_liens}\t{title}')
                return False


if __name__ == '__main__':
    error_count = 0
    test = M3u8()
    _error_f = open('movie_errors.txt', 'a', encoding='utf8')
    executor = ThreadPoolExecutor(max_workers=5)
    title_list, url_list = test.get_url_from_file('test.txt')
    print(title_list, url_list)
    m_files = executor.map(test.get_m3u8_body, url_list)
    print(m_files)
    print(url_list)
    print(title_list)
    for item in executor.map(test.deal_res, m_files, url_list, title_list):
        if item is False:
            error_count += 1
        # for error_str, start_url, location, title in item:
        #     _error_f.write(f'{error_str}\t{start_url}\t{location}\t{title}\t\n')
    _error_f.close()
    print(f'下载结束....总过错误得个数为{error_count}个')
