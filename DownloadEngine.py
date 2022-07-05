import ssl
import sys
import threading
import time
from glob import glob
from multiprocessing import Process
from os import path, makedirs, remove
from re import sub
from urllib import request

import requests

# 忽略 https 警告
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()

class DLWorker:
    def __init__(self, name:str, url:str, range_start, range_end, cache_dir, finish_callback,proxiesIP):
        self.name = name
        self.url = url
        self.cache_filename = f"{cache_dir}{name}.gd2"
        self.range_start = range_start # 固定不动
        self.range_end = range_end # 固定不动
        self.range_curser = range_start # curser 所指尚未开始
        self.finish_callback = finish_callback # 通知调用 DLWorker 的地方
        self.terminate_flag = False # 该标志用于终结自己
        self.FINISH_TYPE = "" # DONE 完成工作, HELP 需要帮忙, RETIRE 不干了
        self.proxiesIP = proxiesIP

    def __run(self):
        chunk_size = 1*1024 # 1 kb
        headers = {'Range': f'bytes={self.range_curser}-{self.range_end}', 'Accept-Encoding': '*','user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.44'}
        req = requests.get(self.url, stream=True, verify=False, headers=headers,proxies=self.proxiesIP)
        with open(self.cache_filename, "wb") as cache:
            for chunk in req.iter_content(chunk_size=chunk_size):
                if self.terminate_flag:
                    break
                cache.write(chunk)
                self.range_curser += len(chunk)
        if not self.terminate_flag: # 只有正常退出才能标记 DONE，但是三条途径都经过此处
            self.FINISH_TYPE = "DONE"
        req.close()
        self.finish_callback(self) # 执行回调函数，根据 FINISH_TYPE 结局不同

    def start(self):
        threading.Thread(target=self.__run,daemon=True).start()

    def help(self):
        self.FINISH_TYPE = "HELP"
        self.terminate_flag = True

    def retire(self):
        self.FINISH_TYPE = "RETIRE"
        self.terminate_flag = True

    def __lt__(self, another):
        """用于排序"""
        return self.range_start < another.range_start

    def get_progress(self):
        """获得进度"""
        _progress = {
            "curser": self.range_curser,
            "start": self.range_start,
            "end": self.range_end
        }
        return _progress

class DownloadEngine(Process):
    def __init__(self, url: str, filename: str, download_dir: str, blocks_num: int, proxiesIP):
        super(DownloadEngine, self).__init__(daemon=True)

        self.blocks_num = blocks_num
        self.download_dir = download_dir
        print(download_dir)
        self.filename = filename
        self.url = url
        self.proxiesIP = proxiesIP

        self.__bad_url_flag = False
        self.file_size = self.__get_size()

    def run(self):
        if not self.__bad_url_flag:
            # 建立下载目录
            if not path.exists(self.download_dir):
                makedirs(self.download_dir)
            # 建立缓存目录
            self.cache_dir = f"{self.download_dir}/.cache/"
            if not path.exists(self.cache_dir):
                makedirs(self.cache_dir)
            # 分块下载
            self.startdlsince = time.time()
            self.workers = []  # 装载 DLWorker
            self.AAEK = self.__get_AAEK_from_cache()  # 需要确定 self.file_size 和 self.block_num
            # 测速
            self.__done = threading.Event()
            self.__download_record = []
            # 主进程信号，直到下载结束后解除
            self.__main_thread_done = threading.Event()
            # 显示基本信息
            readable_size = self.__get_readable_size(self.file_size)
            pathfilename = f'{self.download_dir}/{self.filename}'
            sys.stdout.write(
                f"----- Ghost-Downloader [v2.0.1] -----\n[url] {self.url}\n[path] {pathfilename}\n[size] {readable_size}\n")

        # TODO 尝试整理缓存文件夹内的相关文件
        if not self.__bad_url_flag:
            # 召集 worker
            for start, end in self.__ask_for_work(self.blocks_num):
                worker = self.__give_me_a_worker(start, end)
                self.__whip(worker)
            # 卡住主进程
            self.__main_thread_done.wait()

    def __get_size(self):
        try:
            req = request.urlopen(self.url)
            content_length = req.headers["Content-Length"]
            req.close()
            return int(content_length)
        except Exception as err:
            self.__bad_url_flag = True
            print(f"[Error] {err}")
            return 0

    def __get_AAEK_from_cache(self):
        ranges = self.__get_ranges_from_cache()  # 缓存文件里的数据
        AAEK = []  # 根据 ranges 和 self.file_size 生成 AAEK
        if len(ranges) == 0:
            AAEK.append((0, self.file_size - 1))
        else:
            for i, (start, end) in enumerate(ranges):
                if i == 0:
                    if start > 0:
                        AAEK.append((0, start - 1))
                next_start = self.file_size if i == len(ranges) - 1 else ranges[i + 1][0]
                if end < next_start - 1:
                    AAEK.append((end + 1, next_start - 1))
        return AAEK

    def __get_ranges_from_cache(self):
        # 形如 ./cache/filename.1120.gd2
        ranges = []
        for filename in self.__get_cache_filenames():
            size = path.getsize(filename)
            if size > 0:
                cache_start = int(filename.split(".")[-2])
                cache_end = cache_start + size - 1
                ranges.append((cache_start, cache_end))
        ranges.sort(key=lambda x: x[0])  # 排序
        return ranges

    def __get_readable_size(self, size):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        K = 1024.0
        while size >= K:
            size = size / K
            unit_index += 1
        return "%.2f %s" % (size, units[unit_index])

    def __get_cache_filenames(self):
        return glob(f"{self.cache_dir}{self.filename}.*.gd2")

    def __get_readable_time(self, seconds: int):
        m, s = divmod(seconds, 60)
        return "{:02d}m:{:02d}s".format(m, s)

    def __ask_for_work(self, worker_num: int):
        """申请工作，返回 [work_range]，从 self.AAEK 中扣除。没工作的话返回 []。"""
        assert worker_num > 0
        task = []
        aaek_num = len(self.AAEK)
        if aaek_num == 0:  # 没任务了
            # TODO 这里挑 size 大的 DLWorker 调用 help
            self.__share_the_burdern()
            return []
        if aaek_num >= worker_num:  # 数量充足，直接拿就行了
            for _ in range(worker_num):
                task.append(self.AAEK.pop(0))
        else:  # 数量不足，需要切割
            slice_num = worker_num - aaek_num  # 需要分割几次
            task = self.AAEK  # 这个时候 task 就不可能是 [] 了
            self.AAEK = []
            for _ in range(slice_num):
                task = self.__increase_ranges_slice(task)
        task.sort(key=lambda x: x[0])
        return task

    def __increase_ranges_slice(self, ranges: list, minimum_size=1024 * 1024):
        """增加分块数目，小于 minimum_size 就不再分割了"""
        assert len(ranges) > 0
        block_size = [end - start + 1 for start, end in ranges]
        index_of_max = block_size.index(max(block_size))
        start, end = ranges[index_of_max]
        halfsize = block_size[index_of_max] // 2
        if halfsize >= minimum_size:
            new_ranges = [x for i, x in enumerate(ranges) if i != index_of_max]
            new_ranges.append((start, start + halfsize))
            new_ranges.append((start + halfsize + 1, end))
        else:
            new_ranges = ranges
        return new_ranges

    def __give_me_a_worker(self, start, end):
        worker = DLWorker(name=f"{self.filename}.{start}",
                          url=self.url, range_start=start, range_end=end, cache_dir=self.cache_dir,
                          finish_callback=self.__on_dlworker_finish, proxiesIP=self.proxiesIP)
        return worker

    def __on_dlworker_finish(self, worker: DLWorker):
        assert worker.FINISH_TYPE != ""
        self.workers.remove(worker)
        if worker.FINISH_TYPE == "HELP":  # 外包
            self.__give_back_work(worker)
            self.workaholic(2)
        elif worker.FINISH_TYPE == "DONE":  # 完工
            # 再打一份工，也可能打不到
            self.workaholic(1)
        elif worker.FINISH_TYPE == "RETIRE":  # 撂挑子
            # 把工作添加回 AAEK，离职不管了。
            self.__give_back_work(worker)
        # 下载齐全，开始组装
        if self.workers == [] and self.__get_AAEK_from_cache() == []:
            self.__sew()

    def __whip(self, worker: DLWorker):
        """鞭笞新来的 worker，让他去工作"""
        self.workers.append(worker)
        self.workers.sort()
        worker.start()

    def __give_back_work(self, worker: DLWorker):
        """接纳没干完的工作。需要按 size 从小到大排序。"""
        progress = worker.get_progress()
        curser = progress["curser"]
        end = progress["end"]
        if curser <= end:  # 校验一下是否是合理值
            self.AAEK.append((curser, end))
            self.AAEK.sort(key=lambda x: x[0])

    def __share_the_burdern(self, minimum_size=1024 * 1024):
        """找出工作最繁重的 worker，调用他的 help。回调函数中会将他的任务一分为二。"""
        max_size = 0
        max_size_name = ""
        for w in self.workers:
            p = w.get_progress()
            size = p["end"] - p["curser"] + 1
            if size > max_size:
                max_size = size
                max_size_name = w.name
        if max_size >= minimum_size:
            for w in self.workers:
                if w.name == max_size_name:
                    w.help()
                    break

    def workaholic(self, n=1):
        """九九六工作狂。如果能申请到，就地解析；申请不到，__give_me_a_worker 会尝试将一个 worker 的工作一分为二；"""
        for s, e in self.__ask_for_work(n):
            worker = self.__give_me_a_worker(s, e)
            self.__whip(worker)

    def __sew(self):
        self.__done.set()
        chunk_size = 10 * 1024 * 1024
        with open(f"{self.download_dir}/{self.filename}", "wb") as f:
            for start, _ in self.__get_ranges_from_cache():
                cache_filename = f"{self.cache_dir}{self.filename}.{start}.gd2"
                with open(cache_filename, "rb") as cache_file:
                    data = cache_file.read(chunk_size)
                    while data:
                        f.write(data)
                        f.flush()
                        data = cache_file.read(chunk_size)
        self.clear()
        # sys.stdout.write(f"\n[md5] {self.md5()}\n[info] Downloaded\n")
        self.__main_thread_done.set()

    def clear(self, all_cache=False):
        # 清除历史
        with open("history.xml", "r") as f:
            tmp = f.read()
            f.close()
            tmp = sub(f"<hst><filename>{self.filename}</filename><downdir>{self.download_dir}</downdir>", "Deleted",
                      tmp)
            print(tmp)

        with open("history.xml", "w") as f:
            f.write(tmp)
            f.close()

        if all_cache:  # TODO 需要交互提醒即将删除的文件夹 [Y]/N 确认。由于不安全，先不打算实现。
            pass
        else:
            for filename in self.__get_cache_filenames():
                remove(filename)

    # def md5(self):
    #     chunk_size = 1024 * 1024
    #     filename = f"{path.join(self.download_dir, self.filename)}"
    #     md5 = hashlib.md5()
    #     with open(filename, "rb") as f:
    #         data = f.read(chunk_size)
    #         while data:
    #             md5.update(data)
    #             data = f.read(chunk_size)
    #     return md5.hexdigest()