由于某些原因，现在需要批量翻译文献的摘要、引言等字段，并汇总到一起，因此写了这个 Python 程序来批量调用翻译 API (如百度翻译、有道翻译)，由于比较着急代码写的比较粗糙。

整体上采用了 asyncio 异步并发，读取 PDF 使用了 pdfminer3k (没有用多线程，当时写的时候没考虑到，后面比较懒了就没改)，调用 API 采用了 aiohttp，代码中涉及到的库自行安装。

作者原创真心不易，自用可以，不可商用哦！

# 总体框架
首先我们构建一个 TranslatePDF 类来保存各种方法，这里为什么采用类后面会有说明。代码如下：

```python
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
    	# 用于具体读取PDF
        pass

    def readPDFs(self, folder):
    	# 用于循环调用_readPDF来读取PDF
        pass

    def readAbstracts(self, pdfResults: dict):
    	# 用于从读取到的PDF中提取摘要
        pass

    def readKeywords(self, pdfResults: dict):
    	# 用于从读取到的PDF中提取关键词
        pass

    def readIntroductions(self, pdfResults: dict):
    	# 用于从读取到的PDF中提取引言
        pass

    async def translate(self, useAPI: str, Results: dict, *args):
    	# 用于选择使用哪个API翻译
    	pass

    async def _baiduTranslate(self, s: str, APPID, userKey, src='en', dst='zh'):
    	# 用于具体调用百度翻译API进行翻译
    	pass

    async def baiduTranslate(self, Results: dict, APPID, userKey, src='en', dst='zh'):
    	# 用于异步循环调用_baiduTranslate进行翻译
    	pass

    async def _youdaoTranslate(self, s: str, APP_KEY: str, APP_SECRET: str, src='en', dst='zh-CHS'):
    	# 用于具体调用有道翻译API进行翻译
    	pass

    async def youdaoTranslate(self, Results: dict, APP_KEY, APP_SECRET, src='en', dst='zh'):
    	# 用于异步循环调用_youdaoTranslate进行翻译
    	pass
```
## 读取PDF
经过对比，这里采用 pdfminer3k 来读取 PDF 文档，注意要安装 ==pdfminer3k== 而不是 ==pdfminer==，在 readPDF 里调用 _readPDF 方法，最终返回一个以文件名为 key 的字典 pdfResults，其 value 是包含了 PDF 所有文本字符串的列表。
```python
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
```

## 提取摘要
循环读取 pdfResults 的值，找到含有 ==ABSTRACT== 的字符串，即摘要部分。返回一个以文件名为 key，摘要为 value 的字典 abstractResults。

```python
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
```

## 提取关键词
循环读取 pdfResults 的值，找到含有 ==INDEX TERMS== 的字符串，即关键词部分。返回一个以文件名为 key，关键词为 value 的字典 keywordsResults。

```python
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
```

## 提取引言
循环读取 pdfResults 的值，找到含有 ==INTRODUCTION== 的字符串，即引言部分。返回一个以文件名为 key，引言为 value 的字典 introductionResults。

```python
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
```

## 选择翻译 API
只需要传入使用哪个API 进行翻译的标识、需要翻译的内容和调用 API 所需的信息即可，这里所需 API 的信息是不固定数量的，因此采用变长参数 *args。

```python
async def translate(self, useAPI: str, Results: dict, *args):
    if useAPI == 'baidu':
        return await self.baiduTranslate(Results, *args)
    elif useAPI == 'youdao':
        return await self.youdaoTranslate(Results, *args)
```

## 调用 API 翻译
这里对应的请求方式、请求参数自行参考对应的官方文档，由于传入了比如 userKey 等信息，需要自行到官方网址申请：
[百度翻译 API](https://api.fanyi.baidu.com/api/trans/product/desktop)
[有道翻译 API](https://ai.youdao.com/console/#/)
这里暂时只有这两个，其他的还没研究。(有道翻译比较准确，但是需要花钱，不过新人赠送50元体验金额，目前是够翻译上百篇了。)

```python
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
```

# 具体期刊修改
为什么会有这一节呢，因为期刊的种类太多了，不同的期刊读取 PDF 后得到的字符串千奇百怪，后面根本提取不出来摘要等信息，因此需要针对不同期刊修改代码。

除了具体读取PDF外，其他部分的逻辑不变，所以使用类的好处就出现了，我们不用修改基类，只需要继承基类并重写 _readPDF 方法就可以了，以 IEEE Wireless Communications 和 IEEE Journal on Selected Areas in Communications 为例如下：

## IEEE Wireless Communications
```python
from re import findall, sub
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from TranslatePDF import TranslatePDF


class TranslateIWC(TranslatePDF):
    def __init__(self):
        super().__init__()

    def _readPDF(self, file):
        with open(file, 'rb') as fp:
            praser = PDFParser(fp)
            # 创建一个PDF文档
            doc = PDFDocument()
            praser.set_document(doc)
            doc.set_parser(praser)
            doc.initialize()
            if not doc.is_extractable:
                return []
            else:
                rsrcmgr = PDFResourceManager()
                laparams = LAParams(all_texts=True)
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                results = []
                flag = None
                for page in doc.get_pages():
                    interpreter.process_page(page)
                    layout = device.get_result()
                    for x in layout:
                        if isinstance(x, LTTextBoxHorizontal):
                            results.append(x.get_text())
                            if flag in ('ABSTRACT', 'INTRODUCTION'):
                                results[-1] = results[-2].replace('\n', '') + ': ' + results[-1]
                                del results[-2]
                                flag = 1 if flag == 'ABSTRACT' else 2
                            elif flag == 2:
                                results[-1] = results[-2] + results[-1]
                                del results[-2]
                                break
                            if results[-1].replace('\n', '').upper() == 'ABSTRACT':
                                flag = 'ABSTRACT'  # 找到下一段就可以了
                            elif results[-1].replace('\n', '').upper() == 'INTRODUCTION':
                                flag = 'INTRODUCTION'
                    if flag == 2:
                        break
                results = [r.replace(' ,', ',') for r in results]
                results = [r.replace(' .', '.') for r in results]
                results = [r.replace('-\n', '') for r in results]
                results = [r.replace(' \n', ' ') for r in results]
                results = [r.replace(' r', 'r') for r in results]
                results = [r.replace(' i', 'i') for r in results]
                results = [r.replace(' l', 'l') for r in results]
                results = [r.replace(' t', 't') for r in results]
                results = [r.replace(' f', 'f') for r in results]
                results = [sub(r' +', ' ', r) for r in results]
                results[-1] = results[-1].split('\n')[0]
                return results
```

## IEEE Journal on Selected Areas in Communications

```python
from re import findall, sub
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from TranslatePDF import TranslatePDF


class TranslateIJSAIC(TranslatePDF):
    def __init__(self):
        super().__init__()

    def _readPDF(self, file):
        with open(file, 'rb') as fp:
            praser = PDFParser(fp)
            # 创建一个PDF文档
            doc = PDFDocument()
            praser.set_document(doc)
            doc.set_parser(praser)
            doc.initialize()
            if not doc.is_extractable:
                return []
            else:
                rsrcmgr = PDFResourceManager()
                laparams = LAParams(all_texts=True)
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                results = []
                flag = None
                for page in doc.get_pages():
                    interpreter.process_page(page)
                    layout = device.get_result()
                    for x in layout:
                        if isinstance(x, LTTextBoxHorizontal):
                            results1.append(x.get_text())
                    results.append(results1)

                results_firstpage = []
                for result in results:
                    for r in result:
                        if findall(r'Abstract—', r):
                            results_firstpage.append(result)
                            break
                results = {}
                for result in results_firstpage:
                    title = result[2][:-1].replace('\n', ' ')
                    results[title] = []
                    i = 3
                    temp = ''
                    while i < len(result) - 1:
                        if findall(r'Abstract—', result[i]):
                            for r in result[i:-1]:
                                if not findall(r'MANUSCRIPT', r.upper()):
                                    temp += r
                                else:
                                    temp += sub(r'Manuscript[\s\S]*$', '', r)
                        i += 1
                        if temp != '':
                            break
                    temp = temp.replace('-\n', '')
                    temp = temp.replace('\n', ' ')
                    results[title].append('Abstract:' + ' '.join(findall('Abstract—(.*?)Index Terms', temp)))
                    results[title].append(
                        'Index Terms:' + ' '.join(findall('Index Terms—(.*?)I . INTRODUCT ION', temp)))
                    results[title].append('Introduction:' + ' '.join(findall('INTRODUCT ION(.*?)$', temp)))

                self.files = list(results.keys())

                return results
```

# 主函数
这里调用上面的内容来读取翻译文献，其中使用的百度翻译或者有道翻译的 API 需要自己取申请。

由于使用了异步并发，不要放太多文献，防止电脑卡顿或者 API 端禁止批量请求。
```python
# 需要安装pdfminer3k, aiohttp
# 由于使用了异步并发，文件夹里不要放太多文献
import asyncio
from os import system
from os.path import realpath, join
from time import strftime, localtime
from TranslateIWC import TranslateIWC

# 百度翻译API认证信息，可以自己去申请一个
# APPID = ''
# userKey = ''
# 有道翻译API认证信息，可以自己去申请一个
APP_KEY = ''
APP_SECRET = ''
# 指定文献所在文件夹
folder = 'IEEE Wireless Communications_Issue3'

if __name__ == '__main__':
    tp = TranslateIWC()
    pdfResults = tp.readPDFs(folder)  # 获取pdf文本
    abstractResults = tp.readAbstracts(pdfResults)  # 提取摘要
    introductionResults = tp.readIntroductions(pdfResults)  # 提取摘要
    # 调用百度翻译API
    # useAPI = 'baidu'
    # args = (APPID, userKey)
    # 调用有道翻译API
    useAPI = 'youdao'
    args = (APP_KEY, APP_SECRET)
    print('\n翻译标题...')
    titleTranslateResults = asyncio.get_event_loop().run_until_complete(
        tp.translate(useAPI, dict([(file, file.replace('.pdf', '')) for file in tp.files]), *args))
    print('\n翻译摘要...')
    abstractTranslateResults = asyncio.get_event_loop().run_until_complete(
        tp.translate(useAPI, abstractResults, *args))
    print('\n翻译引言...')
    introductionTranslateResults = asyncio.get_event_loop().run_until_complete(
        tp.translate(useAPI, introductionResults, *args))
    # 输出文件
    outputFileName = f'translateResults_{strftime("%Y-%m-%d-%H-%M-%S", localtime())}.txt'
    print(f'\n输出文件：{realpath(join(folder, outputFileName))}')
    with open(join(folder, outputFileName), 'w', encoding='utf-8') as f:
        count = 0
        for file in tp.files:
            count += 1
            f.write(f'[{count}] ')
            f.write(file.replace('.pdf', '') + '\n')
            f.write(titleTranslateResults[file] + '\n\n')
            f.write(abstractTranslateResults[file] + '\n\n')
            f.write(introductionTranslateResults[file] + '\n\n')
    system(f'explorer /select, {join(folder, outputFileName)}')
```

作者原创真心不易，转载请联系！
