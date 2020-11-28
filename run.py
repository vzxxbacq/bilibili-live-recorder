from Live import BiliBiliLive
import os, sys
import requests
import time
import config
import utils
import re
import multiprocessing
import urllib3
urllib3.disable_warnings()


class BiliBiliLiveRecorder(BiliBiliLive):
    def __init__(self, room, out_dir, check_interval=5 * 60):
        self.room_owner = room[1]
        super().__init__(room[0])
        self.out_dir = out_dir
        self.inform = utils.inform
        self.print = utils.print_log
        self.check_interval = check_interval

    def check(self, interval):
        while True:
            try:
                room_info = self.get_room_info()
                if room_info['status']:
                    self.inform(room_id=self.room_id,
                                desp=room_info['roomname'])
                    self.print(self.room_id, self.room_owner +'\t'+room_info['roomname'])
                    break
                else:
                    self.print(self.room_id, self.room_owner + '\t' + '等待开播')
            except Exception as e:
                self.print(self.room_id, 'Error:' + str(e))
            time.sleep(interval)
        return self.get_live_urls()

    def record(self, record_url, output_filename):
        try:
            self.print(self.room_id, '√ 正在录制...' + self.room_id)
            headers = dict()
            headers['Accept-Encoding'] = 'identity'
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'
            headers['Referer'] = re.findall(
                r'(https://.*\/).*\.flv',
                record_url)[0]
            resp = requests.get(record_url, stream=True, headers=headers)
            with open(output_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    f.write(chunk) if chunk else None
        except Exception as e:
            self.print(self.room_id, 'Error while recording:' + str(e))

    def run(self):
        while True:
            try:
                urls = self.check(interval=self.check_interval)
                filename = utils.generate_filename()
                utils.checkRecordDirExisted()
                if not os.path.exists(os.path.join(self.out_dir, self.room_owner)):
                    os.makedirs(os.path.join(self.out_dir, self.room_owner))
                c_filename = os.path.join(self.out_dir, self.room_owner, filename)
                self.record(urls[0], c_filename)
                self.print(self.room_id, '录制完成' + c_filename)
            except Exception as e:
                self.print(self.room_id,
                           'Error while checking or recording:' + str(e))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        inputs = [str(sys.argv[1])]
    elif len(sys.argv) == 1:
        inputs = config.rooms  # input_id = '917766' '1075'
    else:
        raise ValueError('请检查输入的命令是否正确 例如：python3 run.py 10086')
    OUT_DIR = config.out_dir
    mp = multiprocessing.Process
    tasks = [
        mp(target=BiliBiliLiveRecorder(room, OUT_DIR).run) for room in inputs
    ]
    for i in tasks:
        i.start()
    for i in tasks:
        i.join()
