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
