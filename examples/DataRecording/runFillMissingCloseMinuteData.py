# encoding: UTF-8

from __future__ import print_function
import json
from datetime import datetime, timedelta, time
import requests
from pymongo import MongoClient

from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME, TICK_DB_NAME
from vnpy.trader.vtUtility import get_VolSize
from vnpy.trader.vtFunction import getJsonPath
# 这里以商品期货为例
FUTURES_URL = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol="
INDEX_URL = "http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFuturesMiniKLine5m?symbol="
FUTURES_DAYURL = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine?symbol="
INDEX_DAYURL = "http://stock2.finance.sina.com.cn/futures/api/json.php/CffexFuturesService.getCffexFuturesDailyKLine?symbol="


def getSymbolMapping(): 
    symbolMap = {}
    dataContent = ""
    settingFileName = 'DR_mapping.json'
    settingfilePath = getJsonPath(settingFileName, __file__)      
    with open(settingfilePath, 'r') as fileObj:
        #print(f.read())
        dataContent = fileObj.read()
        #print(dataContent)
    symbolMap = json.loads(dataContent)   
    return symbolMap     

def getXminBarData(dataUrl):  
    url_str = dataUrl
    r = requests.get(url_str)
    r.encoding = "gbk" 
    r_json = r.json()
    r_lists = list(r_json)
    return r_lists
    #print('future_code,date,open,high,low,close,vol')

def getDailyBarData(dataUrl):  
    url_str = dataUrl
    r = requests.get(url_str)
    r.encoding = "gbk" 
    r_json = r.json()
    r_lists = list(r_json)
    return r_lists
    #print('future_code,date,open,high,low,close,vol')

        
def fillMissingData(dbName, collectionName, start,cfgdata,cfgMap):
    """
    如果收盘数据,比如14点59数据没有，使用前一根K线的数据。
    """
    print(u'\n补充收盘数据：%s, 集合：%s, 起始日：%s' %(dbName, collectionName, start))
    
    var_Symbol = ""
    var_Symbol = var_Symbol.join(list(filter(lambda x: x.isalpha(),collectionName)))            
    var_Time = cfgdata[var_Symbol][1]
    timeList = var_Time.split(":")
    startDate = start.replace(hour=int(timeList[0]), minute=int(timeList[1]), second=int(timeList[2]), microsecond=0)

    conMonth = collectionName[-3:]
    if conMonth == '901':
        return

    var_CloseTime = "14:59:00"            
    var_CloseTime = cfgdata[var_Symbol][1] 
    var_CloseTimeList =  var_CloseTime.split(":")       
    
    contractCode = cfgMap[collectionName][0]
    urlType = cfgMap[collectionName][1]
    #minKLineNo = 0
    dataUrl = ""
    if urlType == "url2":
        dataUrl = INDEX_URL + contractCode
        #minKLineNo = 240
    else:
        dataUrl = FUTURES_URL + contractCode
        
    fiveMinBar = getXminBarData(dataUrl)
    if fiveMinBar == None:
        print("Cannot read data from Sina, check it!")
        return
    fiveMinBar.sort()
    startString = datetime.strftime(startDate,'%Y-%m-%d %H:%M:%S') 

    mc = MongoClient('localhost', 27017)    # 创建MongoClient
    cl = mc[dbName][collectionName]         # 获取数据集合 
    sampleData = cl.find_one()
    #del sampleData["_id"]
    for theBar in fiveMinBar:
        if theBar[0] < startString:
            continue
        barDatetime = datetime.strptime(theBar[0],'%Y-%m-%d %H:%M:%S')
        if  (var_Symbol == 'T' or var_Symbol == 'IF' or var_Symbol == 'IC' or var_Symbol =='IH'):
        
            if theBar[0][11:13] == '15' and theBar[0][14:16] == '15':
                barDatetime = barDatetime + timedelta(minutes = -1)
        else:
            if theBar[0][11:13] == '15' and theBar[0][14:16] == '00':
                barDatetime = barDatetime + timedelta(minutes = -1)

        
        searchItem = {'datetime':barDatetime}  
        searchResult = cl.find_one(searchItem)
        if searchResult == None:  
            del sampleData["_id"]            
            sampleData["volume"] = int(float(theBar[5])/5)
            sampleData["datetime"] = barDatetime
            sampleData["high"] = float(theBar[2])
            sampleData["time"] = datetime.strftime(barDatetime,'%H:%M:%S')
            sampleData["date"] = datetime.strftime(barDatetime,'%Y%m%d')
            sampleData["close"]= float(theBar[4]) 
            sampleData["open"]= float(theBar[1]) 
            sampleData["low"]= float(theBar[3])   
            #print(sampleData)       
            insertResult = cl.insert_one(sampleData) 
            print("fill in data for:",theBar[0])  
    print(u'\n补充数据完成：%s, 集合：%s, 起始日：%s' %(dbName, collectionName, start))        
#----------------------------------------------------------------------
def runDataRefilling():
    """运行数据清洗"""
    print(u'开始数据清洗工作')
    
    # 加载配置
    setting = {}
    with open("DR_setting.json") as f:
        setting = json.load(f)
    
    volSize = get_VolSize()  
    symbolMap = getSymbolMapping() 
    print(symbolMap)
    # 遍历执行清洗
    today = datetime.now()
    start = today - timedelta(10)   # 清洗过去10天数据
    start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(5)
        
    for l in setting['bar']:
        symbol = l[0]
        
        fillMissingData(MINUTE_DB_NAME, symbol, start,volSize,symbolMap)
        #fillMissingDailyData(MINUTE_DB_NAME, symbol, start,end,volSize,symbolMap)
    
    print(u'数据清洗工作完成')
    

if __name__ == '__main__':
    runDataRefilling()
