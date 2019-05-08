# dowload_m3u8

下载
----
使用命令git clone 项目地址 或者直接右上角download

如何使用
--------
url = ''
test = M3u8(url)
file_path = test.get_m3u8_body(url)
test.download_movies(file_path)
