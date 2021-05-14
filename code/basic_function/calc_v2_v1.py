from basic_function.calc_implied_volatility import call_implied_vol
import sqlite3
import pandas as pd
import numpy as np
# from math import e
import datetime
from dateutil.parser import parse
import matplotlib.pyplot as plt

wind_id_database = {'510050.SH': 'OPTION_LOCAL', '000300.SH': 'OPTION_LOCAL_000300',
                    '159919.SH': 'OPTION_LOCAL_159919', '510300.SH': 'OPTION_LOCAL_510300'}


def calc_v2_v1(wind_id='510050.SH', start_dt=20200102, end_dt=20200701):
    # 利率
    R = 0.02

    # 期权标的
    option_string=wind_id_database[wind_id]

    # 连接.db文件
    my_db = sqlite3.connect(r'D:\pc\Desktop\Algo_Trading\Assignment2\data\raw\option.db')

    # 对数据库进行操作，取出所需数据
    c = my_db.cursor()

    # 选出所有交易日
    sql = 'SELECT DISTINCT TRADE_DT FROM {z} WHERE TRADE_DT>={x} and TRADE_DT<={y} order by TRADE_DT'\
        .format(z=option_string, x=start_dt, y=end_dt)
    c.execute(sql)
    trade_dt_tuple = c.fetchall()
    trade_dt_df = pd.DataFrame(trade_dt_tuple)
    trade_dt_array = np.array(trade_dt_df)
    total_trade_dt = len(trade_dt_array[:,0])

    # 选出开始交易日与截止交易日
    start_date_str = str(trade_dt_array[0,0])
    end_date_str = str(trade_dt_array[total_trade_dt-1,0])

    # 提取出标的在所有交易日的收盘价
    etf_price_df = pd.read_csv(r'D:\pc\Desktop\Algo_Trading\Assignment3\data\raw\eft_daily_close.csv')
    etf_price_df.set_index(['date'], inplace=True)
    etf_price_df = etf_price_df.loc[start_dt:end_dt,:]

    trade_date_count = []
    trade_date_int_count=[]
    volatility_1_all = []
    volatility_2_all = []
    volatility_2_minus_1_all=[]
    settle_1 = []
    settle_2 = []
    K_all = []   # 记录所有的k
    wind_id_option_1_all = []
    wind_id_option_2_all = []
    contract_multiplier_1_all = []
    contract_multiplier_2_all = []
    option_end_date_1_all = []
    option_end_date_2_all = []

    # 计算每个交易日的波动率
    for i in range(total_trade_dt):
        # 第i个交易日
        trade_date = trade_dt_array[i, 0]
        print(trade_date)
        if trade_date == 20180119:
            continue

        # 提取第i个交易日的标的价格
        S0 = etf_price_df.iloc[i, 0]

        # 选出第i个交易日对应的四个到期日
        sql = 'SELECT DISTINCT OPTION_ENDTRADE FROM {z} WHERE TRADE_DT={x} order by OPTION_ENDTRADE'\
            .format(z=option_string, x=trade_date)
        c = my_db.cursor()
        c.execute(sql)
        option_end_trade_tuple = c.fetchall()
        option_end_trade_df = pd.DataFrame(option_end_trade_tuple)
        option_end_trade_array = np.array(option_end_trade_df)

        # 选取第i个交易日对应的第一个到期日
        option_end_date_1 = option_end_trade_array[0,0]
        option_end_date_2 = option_end_trade_array[1,0]
        option_end_date_3 = option_end_trade_array[2,0]

        # 将int转换为时间戳
        d0 = parse(str(trade_date))
        d1 = parse(str(option_end_date_1))
        d2 = parse(str(option_end_date_2))
        d3 = parse(str(option_end_date_3))
        if (d1 - d0).days <= 3:
            if d3.month-d2.month == 1:
                option_end_date_1 = option_end_date_2
                option_end_date_2 = option_end_date_3
                d1 = parse(str(option_end_date_1))
                d2 = parse(str(option_end_date_2))
            else:
                continue

        # 根据交易日和第一个到期日选出执行所有价格K及对应的期权价格
        select_part = "SELECT K,SETTLE,CALL_PUT,WIND_ID,CONTRACT_MULTIPLIER"
        from_part = "FROM " + option_string + ""
        condition_part = 'WHERE TRADE_DT= {x} AND OPTION_ENDTRADE={y}' \
            .format(x=trade_date, y=option_end_date_1)
        order_part = "ORDER BY K"
        c.execute(select_part + " " + from_part + " " + condition_part + " " + order_part)
        option_1_information_tuple = c.fetchall()
        option_1_information_df = pd.DataFrame(option_1_information_tuple)
        option_1_information_array = np.array(option_1_information_df)

        # 针对第一个到期日，计算K_i：由小到大的所有执行价(i = 1,2,3, … . ),选出平值期权的执行价格及价格
        total_k_1 = option_1_information_array.shape[0] // 2
        price_difference = abs(option_1_information_array[0, 1] - option_1_information_array[1, 1])
        k = 0
        for i in range(1, total_k_1):
            if abs(option_1_information_array[2*i,1] - option_1_information_array[2*i+1,1]) < price_difference:
                price_difference = abs(option_1_information_array[2*i,1] - option_1_information_array[2*i+1,1])
                k = i
        K = option_1_information_array[2*k, 0]
        price_1 = option_1_information_array[2*k, 1]
        wind_id_option_1 = option_1_information_array[2*k, 3]
        contract_multiplier_1 = float(option_1_information_array[2*k, 4])

        # 根据交易日和第二个到期日选出执行所有价格K及对应的期权价格
        select_part = "SELECT K,SETTLE,CALL_PUT,WIND_ID,CONTRACT_MULTIPLIER"
        from_part = "FROM " + option_string + ""
        condition_part = 'WHERE TRADE_DT= {x} AND OPTION_ENDTRADE={y}' \
            .format(x=trade_date, y=option_end_date_2)
        order_part = "ORDER BY K"
        c.execute(select_part + " " + from_part + " " + condition_part + " " + order_part)
        option_2_information_tuple = c.fetchall()
        option_2_information_df = pd.DataFrame(option_2_information_tuple)
        option_2_information_array = np.array(option_2_information_df)

        # 根据近月的k值找出远月k的下标
        K_index = np.argwhere(option_2_information_array[:, 0] == K)

        # 若远月不存在执行价为K的合约，则终止该次循环，该天的数据不计入结果
        if len(K_index) == 0:
            continue
        price_2 = option_2_information_array[K_index[0,0], 1]
        wind_id_option_2 = option_2_information_array[K_index[0,0], 3]
        contract_multiplier_2 = float(option_2_information_array[K_index[0,0], 4])

        # 计算T
        T1 = (d1 - d0).days / 365
        T2 = (d2 - d0).days / 365

        # 计算隐含波动率
        volatility_1 = call_implied_vol(S0, K, T1, price_1, r=0.02)
        volatility_2 = call_implied_vol(S0, K, T2, price_2, r=0.02)

        # 若隐含波动率等于0或者等于1，则终止该次循环，当天的数据不计入结果
        if volatility_1 < 0.00001 or volatility_2 < 0.00001 or 1-volatility_2 < 0.00001 or 1-volatility_1 < 0.00001:
            print(trade_date)
            continue
        trade_date_count.append(parse(str(trade_date)))
        trade_date_int_count.append(trade_date)
        volatility_1_all.append(volatility_1)
        volatility_2_all.append(volatility_2)
        volatility_2_minus_1_all.append(volatility_2-volatility_1)
        settle_1.append(price_1)
        settle_2.append(price_2)
        K_all.append(K)
        wind_id_option_1_all.append(wind_id_option_1)
        wind_id_option_2_all.append(wind_id_option_2)
        contract_multiplier_1_all.append(contract_multiplier_1)
        contract_multiplier_2_all.append(contract_multiplier_2)
        option_end_date_1_all.append(option_end_date_1)
        option_end_date_2_all.append(option_end_date_2)

    # 转成pd
    trade_date_count_pd = pd.DataFrame(trade_date_count)
    trade_date_int_count_pd = pd.DataFrame(trade_date_int_count)
    volatility_1_all_pd = pd.DataFrame(volatility_1_all)
    volatility_2_all_pd = pd.DataFrame(volatility_2_all)
    volatility_2_minus_1_all_pd = pd.DataFrame(volatility_2_minus_1_all)
    settle_1_pd = pd.DataFrame(settle_1)
    settle_2_pd = pd.DataFrame(settle_2)
    K_all_pd=pd.DataFrame(K_all)
    wind_id_option_1_all_pd = pd.DataFrame(wind_id_option_1_all)
    wind_id_option_2_all_pd = pd.DataFrame(wind_id_option_2_all)
    contract_multiplier_1_all_pd = pd.DataFrame(contract_multiplier_1_all)
    contract_multiplier_2_all_pd = pd.DataFrame(contract_multiplier_2_all)
    option_end_date_1_all_bd = pd.DataFrame(option_end_date_1_all)
    option_end_date_2_all_bd = pd.DataFrame(option_end_date_2_all)
    # 计算波动率差的平均值和标准差
    volatility_2_minus_1_mean_rolling = volatility_2_minus_1_all_pd.rolling(20, min_periods=1).mean()
    volatility_2_minus_1_std_rolling = volatility_2_minus_1_all_pd.rolling(20, min_periods=1).std()

    volatility = pd.concat([trade_date_count_pd,
                            trade_date_int_count_pd,
                            settle_1_pd,
                            settle_2_pd,
                            volatility_1_all_pd,
                            volatility_2_all_pd,
                            volatility_2_minus_1_all_pd,
                            volatility_2_minus_1_mean_rolling,
                            volatility_2_minus_1_std_rolling,
                            volatility_2_minus_1_all_pd-volatility_2_minus_1_mean_rolling,
                            K_all_pd,
                            wind_id_option_1_all_pd,
                            wind_id_option_2_all_pd,
                            contract_multiplier_1_all_pd,
                            contract_multiplier_2_all_pd,
                            option_end_date_1_all_bd,
                            option_end_date_2_all_bd
                            ], axis=1, ignore_index=True)
    volatility.columns = ['trade_date', 'trade_date_int', 'settle_1', 'settle_2', 'v1', 'v2', 'v2-v1',
                          'mean', 'std', 'v2-v1-mean', 'K', 'wind_id_1', 'wind_id_2',
                          'contract_multiplier_1', 'contract_multiplier_2', 'end_date_1', 'end_date_2']

    return volatility


if __name__=="__main__":
    volatility = calc_v2_v1('510050.SH', 20200102, 20200701)
    volatility.to_csv(r'D:\pc\Desktop\Algo_Trading\Assignment3\result\data\volatility.csv')


