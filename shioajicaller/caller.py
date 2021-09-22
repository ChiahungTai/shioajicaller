# -*- coding: utf-8 -*-
import sys, logging
from datetime import datetime
from . import config
import time
import shioaji as sj
from shioaji import TickFOPv1, TickSTKv1, BidAskSTKv1, BidAskFOPv1,Exchange

class Caller(object):
    def __init__(self):
        self._userID = config.userId
        self._userPassowrd = config.userPassowrd
        self._connected = False
        self._api = sj.Shioaji()
        logging.info("shioaji version:"+sj.__version__)
        self._api.quote.set_event_callback(self._event_callback)
        self._api.quote.set_on_tick_stk_v1_callback(self.Quote_callback_stk_v1_tick)
        self._api.quote.set_on_bidask_stk_v1_callback(self.Quote_callback_stk_v1_bidask)
        self._api.quote.set_on_tick_fop_v1_callback(self.Quote_callback_fop_v1_tick)
        self._api.quote.set_on_bidask_fop_v1_callback(self.Quote_callback_fop_v1_bidask)

    def SetEnevtCallBack(self,callback):
        if callable(callback):
            self.EventCallback=callback

    def SetSubscribeStocksCallBack(self,callback):
        if callable(callback):
            self.SubscribeStocksCallBack= callback

    def SetSubscribeFuturesCallBack(self,callback):
        if callable(callback):
            self.SubscribeFuturesCallBack= callback

    def SetAccount(self,userId:str="",userPassowrd:str=""):
        if userId != None and userId !="":
            self._userID = userId
        if userPassowrd != None and userPassowrd !="":
            self._userPassowrd = userPassowrd

    def GetAccount(self):
        if (self._check_connect()):
            return self._accounts
        return False

    def Login(self):
        if self._userPassowrd == None or self._userPassowrd == "" or self._userID == None or self._userID == "":
            logging.error("Error!! No UserId or UserPassowrd.")
            sys.exit(70)
        self._accounts = self._api.login(self._userID, self._userPassowrd)

    def SubscribeStocks(self,code:str="",quote_type:str="tick",intraday_odd:bool=False,version:str="v1"):
        if (code == None or code ==""):
            return False
        logging.info(f"SubscribeStocks {code} {quote_type} {version}")
        if (self._check_connect()):
            contract = self._api.Contracts.Stocks[code]
            if contract != None:
                self._api.quote.subscribe(contract ,quote_type=quote_type, intraday_odd=intraday_odd ,version=version)
                return True
            else:
                return False
        else:
            return False
    def SubscribeFutures(self,code:str="",quote_type:str="tick",intraday_odd:bool=False,version:str="v1"):
        if (code == None or code ==""):
            return False
        logging.info(f"SubscribeFutures {code} {quote_type} {version}")
        if (self._check_connect()):
            contract = self._api.Contracts.Futures[code]
            if contract != None:
                self._api.quote.subscribe(contract ,quote_type=quote_type, intraday_odd=intraday_odd ,version=version)
                return True
            else:
                return False
        else:
            return False

    def Quote_callback_stk_v1_tick(self,exchange: Exchange, tick:TickSTKv1):
        tickdata = tick.to_dict(raw=True)
        tickdata['UNTime']= datetime.now()
        # strMsg = json.dumps(tickdata, default=str)
        # print(strMsg)
        if hasattr(self, 'SubscribeStocksCallBack'):
            self.SubscribeStocksCallBack(tickdata)

    def Quote_callback_stk_v1_bidask(exchange: Exchange, bidask:BidAskSTKv1):
        print(f"Exchange: {exchange}, BidAsk: {bidask}")

    def Quote_callback_fop_v1_tick(self,exchange: Exchange, tick:TickFOPv1):
        tickdata = tick.to_dict(raw=True)
        tickdata['UNTime']= datetime.now()
        # strMsg = json.dumps(tickdata, default=str)
        # print(strMsg)
        if hasattr(self, 'SubscribeFuturesCallBack'):
            self.SubscribeFuturesCallBack(tickdata)

    def Quote_callback_fop_v1_bidask(exchange: Exchange, bidask:BidAskFOPv1):
        print(f"Exchange: {exchange}, BidAsk: {bidask}")

    def Quote_callback(self,topic: str, quote: dict):
        print(f"Tpoic:{topic} Quote: {quote}")

    def _event_callback(self,ResponseCode:int,Code:int, Message:str,Description:str):
        logging.info(f'EventCallback {ResponseCode} {Code} {Message} Event: {Description}')
        if ResponseCode == 0 and Code == 0:
            self._connected = True
            self._connected_ts=time.time()
        if hasattr(self, 'EventCallback'):
            item = {
                "ResponseCode":ResponseCode,
                "Code": Code,
                "Message": Message,
                "Description": Description,
                }
            self.EventCallback(item)
            # self.EventQueue.put_nowait(item)
        #     print(f'EventQueue >>>> {ResponseCode} {Code} {Message} Event: {Description}')

    def _check_connect(self, timeout=10, period=0.25):
        # token timeout 24hr before 30sec will relogin
        if self._connected and (time.time() - self._connected_ts) < 86400-30:
            return self._accounts
        self.Login()
        mustend = time.time() + timeout
        while time.time() < mustend:
            if self._connected == True: return True
            time.sleep(period)
        return False

    def getContractsStocks(self,Exchange:str):
        if (self._check_connect()):
            return self._api.Contracts.Stocks[Exchange]

    def getContractsStockByCode(self,Code:str):
        if (self._check_connect()):
            return self._api.Contracts.Stocks[Code]

    def getContractsFutures(self,Name=""):
        if (self._check_connect()):
            if Name == "":
                return self._api.Contracts.Futures
            else:
                return self._api.Contracts.Futures[Name]

    def __del__(self):
        del self._api