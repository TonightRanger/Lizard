# coding=utf-8
import sys
import time
import queue
import socket
import requests
import threading
def whois_sniff(URL):
    '''
    功能：whois查询
    参数：URL网站地址    
    '''
    import whois
    print(whois.whois(URL))
def shodan_search(str):
    '''
    功能：傻蛋批量搜索
    参数：str关键字
    '''
    import shodan
    SHODAN_API_KEY = "PSKINdQe1GyxGgecYz2191H2JoS9qvgD"#可以用自己的
    api = shodan.Shodan(SHODAN_API_KEY)
    try:
        results = api.search(str)
        for result in results['matches']:         
                print ("\033[0;32;40m%s\033[0m:\033[0;31m%s\033[1;37;40m|%s|%s"%(result['ip_str'],result['port'],result['location']['country_name'],result['hostnames']))
        print ('Results found: %s' % results['total'])
    except shodan.APIError as e:
        print ('Error: %s' % e)
def start_dirscan(URL,Dict,thread):
    scan = Dirscan(URL, Dict, 0, thread)
    for i in range(thread):
        t = threading.Thread(target=scan.run)
        t.setDaemon(True)
        t.start()

    while True:
        if threading.activeCount() <= 1 :
            break
        else:
            try:
                time.sleep(0.1)
            except KeyboardInterrupt as e:
                print ('\n[WARNING] User aborted, wait all slave threads to exit, current(%i)'% threading.activeCount())
                scan.STOP_ME = True

    print ('Scan end!!!')
class Dirscan(object):
    '''
    功能：扫描目录
    参数：scanSite网站地址,
         scanDict目录字典,      
         scanOutput输出文件名称,
         threadNum线程，        
    '''
    def __init__(self, scanSite, scanDict, scanOutput=0,threadNum=60):
        print ('正在扫描目录',scanDict)
        self.scanSite = scanSite if scanSite.find('://') != -1 else 'http://%s' % scanSite
        print ('扫描目标',self.scanSite)
        self.scanDict = scanDict
        self.scanOutput = scanSite.rstrip('/').replace('https://', '').replace('http://', '')+'_webdir.txt' if scanOutput == 0 else scanOutput
        truncate = open(self.scanOutput,'w')
        truncate.close()
        self.threadNum = threadNum
        self.lock = threading.Lock()
        self._loadHeaders()
        self._loadDict(self.scanDict)
        self._analysis404()
        self.STOP_ME = False

    def _loadDict(self, dict_list):
        self.q = queue.Queue()
        with open(dict_list,encoding='utf-8') as f:
            for line in f:
                if line[0:1] != '#':
                    self.q.put(line.strip())
        if self.q.qsize() > 0:
            print ('字典总计',self.q.qsize())
        else:
            print ('字典为空?')
            quit()

    def _loadHeaders(self):
        self.headers = {
            'Accept': '*/*',
            'Referer': 'http://www.baidu.com',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; ',
            'Cache-Control': 'no-cache',
        }
    def _analysis404(self):
        notFoundPage = requests.get(self.scanSite + '/songgeshigedashuaibi/hello.html', allow_redirects=False)
        self.notFoundPageText = notFoundPage.text.replace('/songgeshigedashuaibi/hello.html', '')

    def _writeOutput(self, result):
        self.lock.acquire()
        with open(self.scanOutput, 'a+') as f:
            f.write(result + '\n')
        self.lock.release()

    def _scan(self, url):
        html_result = 0
        try:
            html_result = requests.get(url, headers=self.headers, allow_redirects=False, timeout=60)
        except requests.exceptions.ConnectionError:
            # print 'Request Timeout:%s' % url
            pass
        finally:
            if html_result != 0:
                if html_result.status_code == 200 and html_result.text != self.notFoundPageText:
                    print ('[%i]%s' % (html_result.status_code, html_result.url))
                    self._writeOutput('[%i]%s' % (html_result.status_code, html_result.url))

    def run(self):
        while not self.q.empty() and self.STOP_ME == False:
            url = self.scanSite + self.q.get()
            self._scan(url)

def isIP(ip):
   #判断是否为正确的IP地址。
  ip_addr = ip.split('.')
  if len(ip_addr) != 4:
   return False
  for ipnum in ip_addr:
   if not (0 <= int(ipnum) < 255):
     return False
  else:
   return True
def isurl(url):
    header = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
    import requests as r
    re=r.get(url,headers=header)
    if re.status_code==200:
        return True
    if re.status_code==404:
        return False
class ScanPort:
    # 端口扫描工具
    def __init__(self,ip):# 注意这个调用需要缀上.start()才能启动
        self.ip = ip
 
    def scan_port(self, port):
        try:
            info=""
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            res = s.connect_ex((self.ip, port))
            portwd=open(r'modules/ports.txt','rb')
            if res == 0:  # 端口开启
                content=portwd.readlines()
                for c in content:   #从ports.txt中查找端口对应的服务        
                    if str(port)+"端口"in c.decode(encoding='UTF-8'):
                        info=c.decode(encoding='UTF-8').strip(str(port)+"端口：")
                        break
                    else:
                        continue
                print(f'地址:{format(self.ip)}\033[0;32;40m端口:{str(port)} \033[0m\t{info}')
                with open(self.ip+"_port",'a+',encoding="utf-8") as f:
                    f.write(str(port) +"\t"+info+'\n')
        except Exception as e:
            print(e)
            sys.exit(1)
            
        finally:
            s.close()
 
    def start(self):
        from datetime import datetime
        from multiprocessing.dummy import Pool as ThreadPool
        ports = [i for i in range(0, 65535)]
        socket.setdefaulttimeout(0.5)
        truncate = open(self.ip+"_port",'w')
        truncate.close()
        print("正在扫描")
        # 开始时间
        t1 = datetime.now()
        # 设置多进程
        try:
            pool = ThreadPool(processes=60)
            pool.map(self.scan_port, ports)
            pool.close()
            pool.join()
            print('端口扫描已完成，耗时：', datetime.now() - t1)
        except KeyboardInterrupt:#守护线程池
            pool.terminate()

class ScanPort_:
    # 模块化端口扫描工具
    # 返回数组给exp
    def __init__(self,ip):
        self.ip = ip
        self.ports=[]
    def scan_port(self, port):
            s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            res = s.connect_ex((self.ip, port))
            if res == 0:  # 端口开启
                print(f"发现端口{port}")
                self.ports.append(port)

    def start(self):
        from multiprocessing.dummy import Pool as ThreadPool
        ports = [i for i in range(0, 100)]
        socket.setdefaulttimeout(0.5)
        # 设置多进程
        try:
            pool = ThreadPool(processes=60)
            pool.map(self.scan_port,ports)
            pool.close()
            pool.join()
            return self.ports
        except KeyboardInterrupt:#守护线程池
            pool.terminate()