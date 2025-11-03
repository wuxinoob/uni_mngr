"""负责从web更新加密的订阅信息，写入到data/下"""
import base64
import gzip
import os
from threading import Event, Thread
from cryptography.fernet import Fernet
import time
import requests
import subprocess
from subprocess import Popen,CREATE_NO_WINDOW
import asyncio
import json
class gost_subscribe(object):
    """
    gost订阅管理类
    负责从网络获取加密的配置信息，解密后保存到本地，并管理gost进程的启动和重启
    """
    def __init__(self,web_cfg_interval:int = 300,key:bytes = b'FMa8ZBISFRcOM_gZN2uatCf8-nW-d0SGghW__T4zRdw=') -> None:
        """
        初始化gost订阅管理器
        
        Args:
            web_cfg_interval (int): 配置更新检查间隔，默认300秒(5分钟)
            key (bytes): 解密密钥，默认使用固定密钥
        """
        self.gost_reboot_sgin = Event()  # 用于通知gost进程重启的事件信号
        self.web_cfg_interval = web_cfg_interval  # 配置更新检查间隔
        self.key = key  # 解密密钥
        
        self.task_web_req = Thread(target=self.run,args=(self.gost_reboot_sgin,))
        self.task_gost_run = Thread(target=self.run_gost,args=(self.gost_reboot_sgin,))

    async def mgs_in(self,text:str):
        pass
    def msg_out(self,text:str) -> None:    
        """
        文本输出方法（子类重写如何处理文本）
        
        Args:
            text (str): 需要输出的文本
        """
        pass


    def unzip_gost(self) -> None:
        """
        解压gost程序
        检查是否存在gost.exe，如果不存在则尝试解压gost.gz文件
        """
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(current_file_path+r"\data\gost.exe"):
            self.msg_out("gost.exe已存在")
            pass
        else:
            if os.path.exists(current_file_path+r"\data\gost.gz"):
                self.msg_out("gost.gz已存在")
                with open(current_file_path+r"\data\gost.exe", "wb") as fd:
                    with open(current_file_path+r"\data\gost.gz", "rb") as fd_gz:
                        fd.write(gzip.decompress(fd_gz.read()))
    
    def hard_encrypt(self,text:str,key =None)->str:
        """
        加密文本数据
        
        Args:
            text (str): 需要加密的文本
            key: 加密密钥，如果未提供则生成新密钥
            
        Returns:
            str: 经过base64编码的加密文本
        """
        if not key:
            key = Fernet.generate_key()
        cipher_text = Fernet(key).encrypt(text.encode())
        return base64.b64encode(cipher_text).decode()

    def hard_decrypt(self,text:str,key =None)->str:
        """
        解密文本数据
        
        Args:
            text (str): 需要解密的base64编码文本
            key: 解密密钥，如果未提供则生成新密钥
            
        Returns:
            str: 解密后的原始文本
        """
        if not key:
            key = Fernet.generate_key()
        cipher_text = base64.b64decode(text.encode())
        return Fernet(key).decrypt(cipher_text).decode()


    def config_init(self,)->list[str]:
        """
        初始化配置信息
        从data/gost_info文件中读取gost启动参数
        
        Returns:
            list[str]: gost启动参数列表
        """
        with open("data/gost_info",mode="r",) as fd:
            start_cfg :list = []
            data = fd.readline()
            while (data!=''):
                start_cfg.append(data)
                data = fd.readline()
        return start_cfg


    def run_gost(self,reboot_sgin:Event) -> None:
        """
        运行gost进程
        
        Args:
            reboot_sgin (Event): 重启信号事件
        """
        time.sleep(5)
        #如果存在未受控制的gost进程则结束该gost进程
        try:
            subprocess.run(["taskkill","/f","/im","gost.exe"])
            self.msg_out(f"gost进程已结束\n")
        except Exception as e:
            self.msg_out(f"{e}\n")
        last_cfg = self.config_init()#gost运行参数
        while True:
            data = self.config_init()#gost命令参数个数
            a :list[Popen] =[]
            for i in range(len(data)):
                a.append(Popen(args=data[i].split(" "),creationflags=CREATE_NO_WINDOW),)
            self.msg_out(f"gost进程已更新\n")
            reboot_sgin.clear()
            reboot_sgin.wait()
            time.sleep(3)
            for i in a:
                i.terminate()
            
    # 从网页上获取加密的订阅信息
    def renew_cfg(self,reboot_sgin:Event,last_cfg:list[str]) -> None:
        """
        更新配置信息
        从指定网址获取加密的clash和gost配置信息，解密后保存到本地文件
        
        Args:
            reboot_sgin (Event): 重启信号事件
            last_cfg (list[str]): 上一次的配置信息
        """
        try:
            a = requests.get("https://webcfg.cfg.novalplay.com").text
            with open(r"data\flying.yaml", "w",encoding="utf-8") as fd:
                content = self.hard_decrypt(a,self.key)
                fd.write(content)
                self.msg_out(f"clash订阅信息更新成功：{time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())}")
        except Exception as e:
            self.msg_out(f"clash订阅信息更新失败:{e}\n若一直出现，请检查能否访问：https://webcfg.cfg.novalplay.com")
        try:
            a = requests.get("https://cmdline.cfg.novalplay.com").text
            with open(r"data\gost_info", "w") as fd:
                content = self.hard_decrypt(a,self.key)
                fd.write(content)
                if last_cfg[0] != content:#配置文件有更新
                    last_cfg[0] = content
                    reboot_sgin.set()    
                    self.msg_out(f"gost配置文件发生变更:{last_cfg[0]}")
                self.msg_out(f"gost获取更新信息成功：{time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())}")
        except Exception as e:
            self.msg_out(f"gost获取更新信息失败:{e}\n若一直出现，请检查能否访问：https://cmdline.cfg.novalplay.com")

    def run(self,gost_reboot_sgin:Event) -> None:
        """
        主运行循环
        定期检查并更新配置信息
        
        Args:
            gost_reboot_sgin (Event): gost重启信号
        """

        last_cfg:list[str] = ["default"]
        self.renew_cfg(gost_reboot_sgin,last_cfg)
        while True:
            self.msg_out("http服务已更新")
            self.msg_out("clash配置文件地址为：http://127.0.0.1:8000/data/flying.yaml")
            time.sleep(self.web_cfg_interval)#每5分钟检查一次
    #        httpd.shutdown()#无须关闭服务，直接更新
    #        httpd.server_close()
            self.renew_cfg(gost_reboot_sgin,last_cfg)

    def gost_subcribe_run(self) -> None:
        """
        启动gost订阅服务
        创建并启动配置更新线程和gost运行线程
        """
        self.unzip_gost()
        self.task_web_req.start()
        self.task_gost_run.start()

