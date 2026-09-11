# 管道验证用桩策略:只证明数据->回测->报告链路通,不代表任何真实边际,禁止直接实盘
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy


class ResearchStub(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "15m"
    can_short = False

    minimal_roi = {
        "0": 0.05,
        "60": 0.02,
        "120": 0.01,
    }
    stoploss = -0.08
    startup_candle_count = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["rsi"] < 30, ["enter_long", "enter_tag"]
        ] = (1, "rsi_oversold")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["rsi"] > 70, ["exit_long", "exit_tag"]
        ] = (1, "rsi_overbought")
        return dataframe
