# encoding: UTF-8

"""
DualThrust交易策略 by Leon 
"""

from datetime import time
import talib
from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate, BarGenerator, ArrayManager
from sqlalchemy.sql.expression import false
import random


########################################################################
class TestLogOrderStrategy(CtaTemplate):
    """DualThrust交易策略"""
    className = 'TestLogOrderStrategy'
    author = u'Leon Zhao'

    # 策略参数
    flipcoil = 0
    timeinterval = 0
    hasorder = False
    countdown = 0
    # 策略变量
    barList = []                # K线对象的列表
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol'
                 ]    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos'
               ] 
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(TestLogOrderStrategy, self).__init__(ctaEngine, setting) 
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()
        self.barList = []
        self.flipcoil = 0 
        self.timeinterval =  5
        self.hasorder = False
        self.countdown = self.timeinterval
                
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
    
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        #ignore data before real open
        if (tick.datetime.hour == 8 or tick.datetime.hour ==20):
            return
        self.bg.updateTick(tick)
        
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        self.cancelAll()

        self.bg.updateBar(bar)
    # 计算指标数值
        self.barList.append(bar)
        
        if len(self.barList) <= 2:
            return
        else:
            self.barList.pop(0)
        lastBar = self.barList[-2]
        
        if self.countdown > 0:
            self.countdown -= 1
            return
        
        self.flipcoil = random.random() 
        orderqty = [1,2,3]
        if self.pos == 0:
            if self.flipcoil > 0.5:
                self.buy(bar.close,random.choice(orderqty))
            else:
                self.short(bar.close,random.choice(orderqty))
        elif self.pos > 0:
            self.sell(bar.close,self.pos)
        else:
            self.cover(bar.close,abs(self.pos))
        self.countdown = self.timeinterval
            
            
            
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        logtext = self.name + "," + self.vtSymbol
        logtext = logtext + ","+trade.date
        logtext = logtext + "," +trade.datetime
        logtext = logtext + "," + trade.offset        
        logtext = logtext + "," + trade.direction
        logtext = logtext + "," + trade.volume
        self.writeCtaLog(logtext)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass