# 需要安装pdfminer3k, aiohttp
# 由于使用了异步并发，文件夹里不要放太多文献
import asyncio
from os import walk
from os.path import join
from re import findall
from hashlib import md5, sha256
from time import time
from uuid import uuid1
from aiohttp import ClientSession
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter


class TranslatePDF(object):
    def __init__(self):
        self.folder = None
        self.files = []

    def _readPDF(self, file):
        with open(file, 'rb') as fp:  # 以二进制读模式打开
            # 用文件对象来创建一个pdf文档分析器
            praser = PDFParser(fp)
            # 创建一个PDF文档
            doc = PDFDocument()
            # 连接分析器与文档对象
            praser.set_document(doc)
            doc.set_parser(praser)
            # 提供初始化密码 如果没有密码 就创建一个空的字符串
            doc.initialize()
            # 检测文档是否提供txt转换，不提供就忽略
            if not doc.is_extractable:
                return []
            else:
                # 创建PDf 资源管理器 来管理共享资源
                rsrcmgr = PDFResourceManager()
                # 创建一个PDF设备对象
                laparams = LAParams()
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                # 创建一个PDF解释器对象
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                # 每页文字内容
                results = []
                # 循环遍历列表，每次处理一个page的内容
                for page in doc.get_pages():  # doc.get_pages() 获取page列表
                    interpreter.process_page(page)
                    # 接受该页面的LTPage对象
                    layout = device.get_result()
                    # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性，
                    for x in layout:
                        if isinstance(x, LTTextBoxHorizontal):
                            results.append(x.get_text())
                return results

    def readPDFs(self, folder):
        print('读取PDF...')
        self.folder = folder
        files_tmp = []
        for root, path, files_tmp in walk(self.folder):
            pass
        for file in files_tmp:
            if findall('\.PDF|\.pdf', file):  # 过滤非pdf文件
                self.files.append(file)
        del files_tmp
        pdfResults = {}
        for file in self.files:
            print(file)
            pdfResults[file] = self._readPDF(join(self.folder, file))
        return pdfResults

    def readAbstracts(self, pdfResults: dict):
        print('\n提取摘要...')
        abstractResults = {}
        for file in pdfResults:
            for result in pdfResults[file]:
                if findall('ABSTRACT', result.upper()):
                    abstractResults[file] = result
                    break
            else:
                abstractResults[file] = ''

        return abstractResults

    def readKeywords(self, pdfResults: dict):
        print('\n提取关键词...')
        keywordsResults = {}
        for file in pdfResults:
            for result in pdfResults[file]:
                if findall('INDEX.*?TERMS', result.upper()):
                    keywords = result.replace('\n', ' ')
                    keywordsResults[file] = keywords
                    break
            else:
                keywordsResults[file] = ''
        return keywordsResults

    def readIntroductions(self, pdfResults: dict):
        print('\n提取引言...')
        introductionResults = {}
        for file in pdfResults:
            for result in pdfResults[file]:
                if findall('INTRODUCTION', result.upper()):
                    introductionResults[file] = result
                    break
            else:
                introductionResults[file] = ''

        return introductionResults

    async def translate(self, useAPI: str, Results: dict, *args):
        if useAPI == 'baidu':
            return await self.baiduTranslate(Results, *args)
        elif useAPI == 'youdao':
            return await self.youdaoTranslate(Results, *args)

    async def _baiduTranslate(self, s: str, APPID, userKey, src='en', dst='zh'):
        salt = int(time())
        s1 = APPID + s + str(salt) + userKey
        sign = md5(s1.encode('utf-8')).hexdigest()
        url = f'http://api.fanyi.baidu.com/api/trans/vip/translate?q={s}&from={src}&to={dst}&appid={APPID}&salt={salt}&sign={sign}'
        async with ClientSession() as session:
            async with session.get(url) as result:
                result = await result.json()
                try:
                    result = result['trans_result']
                    if result:
                        return result[0]['dst']
                    else:
                        return ''
                except KeyError:
                    return ''

    async def baiduTranslate(self, Results: dict, APPID, userKey, src='en', dst='zh'):
        translateResults = {}

        async def translate(pdfsResult, fileList):
            for file in fileList:
                print(file)
                s = pdfsResult[file]
                translateResults[file] = await self._baiduTranslate(s, APPID, userKey, src, dst) if s != '' else ''
            return translateResults

        t_num = 1  # 线程数(百度翻译API标准版只能用单线程)
        filesPerThread = len(Results) // t_num  # 每线程文件数
        t_list = []  # 线程列表
        for i in range(t_num):
            if i < t_num - 1:
                t_list.append(asyncio.get_event_loop().create_task(
                    translate(Results, self.files[i * filesPerThread:(i + 1) * filesPerThread])))
            else:
                t_list.append(
                    asyncio.get_event_loop().create_task(translate(Results, self.files[i * filesPerThread:])))
        await asyncio.gather(*t_list)
        return translateResults

    async def _youdaoTranslate(self, s: str, APP_KEY: str, APP_SECRET: str, src='en', dst='zh-CHS'):
        truncate_s = s if len(s) <= 20 else s[0:10] + str(len(s)) + s[len(s) - 10:]
        salt = str(uuid1())
        curtime = str(int(time()))
        signStr = APP_KEY + truncate_s + salt + curtime + APP_SECRET
        hash_algorithm = sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        sign = hash_algorithm.hexdigest()
        url = 'https://openapi.youdao.com/api'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        postdata = {'from': src, 'to': dst, 'signType': 'v3', 'curtime': curtime, 'appKey': APP_KEY, 'q': s,
                    'salt': salt, 'sign': sign}
        async with ClientSession() as session:
            async with session.post(url, data=postdata, headers=headers) as result:
                result = await result.json()
                try:
                    result = result['translation']
                    if result:
                        return '\n'.join(result)
                    else:
                        return ''
                except KeyError:
                    return ''

    async def youdaoTranslate(self, Results: dict, APP_KEY, APP_SECRET, src='en', dst='zh'):
        translateResults = {}

        async def translate(pdfsResult, fileList):
            for file in fileList:
                print(file)
                s = pdfsResult[file]
                translateResults[file] = await self._youdaoTranslate(s, APP_KEY, APP_SECRET, src,
                                                                     dst) if s != '' else ''
            return translateResults

        t_num = 1  # 线程数(百度翻译API标准版只能用单线程)
        filesPerThread = len(Results) // t_num  # 每线程文件数
        t_list = []  # 线程列表
        for i in range(t_num):
            if i < t_num - 1:
                t_list.append(asyncio.get_event_loop().create_task(
                    translate(Results, self.files[i * filesPerThread:(i + 1) * filesPerThread])))
            else:
                t_list.append(
                    asyncio.get_event_loop().create_task(translate(Results, self.files[i * filesPerThread:])))
        await asyncio.gather(*t_list)
        return translateResults
