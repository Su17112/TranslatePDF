# 需要安装pdfminer3k, aiohttp
# 由于使用了异步并发，文件夹里不要放太多文献
from re import findall, sub
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from TranslatePDF import TranslatePDF


class TranslateIWC(TranslatePDF):
    def __init__(self):
        super().__init__()

    def _readPDF(self, file):  # 具体读取pdf的函数
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
                flag = None  # 找到摘要标志
                for page in doc.get_pages():  # doc.get_pages() 获取page列表
                    interpreter.process_page(page)
                    # 接受该页面的LTPage对象
                    layout = device.get_result()
                    # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性，
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
