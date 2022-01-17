# 需要安装pdfminer3k, aiohttp
# 由于使用了异步并发，文件夹里不要放太多文献
from re import findall, sub
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from TranslatePDF import TranslatePDF


class TranslateIJSAIC(TranslatePDF):
    def __init__(self):
        super().__init__()

    def readPDFs(self, file):  # 具体读取pdf的函数
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
                laparams = LAParams(all_texts=True)
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                # 创建一个PDF解释器对象
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                # 每页文字内容
                results = []
                # 循环遍历列表，每次处理一个page的内容
                for page in doc.get_pages():  # doc.get_pages() 获取page列表
                    results1 = []
                    interpreter.process_page(page)
                    # 接受该页面的LTPage对象
                    layout = device.get_result()
                    # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性，
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
