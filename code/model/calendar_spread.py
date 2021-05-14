from model.calc_v2_v1 import calc_v2_v1
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import numpy as np
from dateutil.parser import parse

wind_id_database = {'510050.SH': 'OPTION_LOCAL', '000300.SH': 'OPTION_LOCAL_000300',
                    '159919.SH': 'OPTION_LOCAL_159919', '510300.SH': 'OPTION_LOCAL_510300'}


def calendar_spread(wind_id, start_dt, end_dt):
    volatility = calc_v2_v1(wind_id, start_dt,end_dt)
    total_trade_dt = list(volatility['trade_date_int'])
    volatility.set_index(['trade_date_int'], inplace=True)

    option_string = wind_id_database[wind_id]

    # 作近远月波动率差值的时间序列图
    plt.plot(volatility['trade_date'], volatility['v2-v1-mean'])
    plt.plot(volatility['trade_date'], 2 * volatility['std'])
    plt.plot(volatility['trade_date'], -2 * volatility['std'])

    plt.legend(['(v2-v1) - mean', '2*std', '- 2*std'], loc='upper left')
    plt.show()

    net_value = []
    state_all = []
    gross_value = []
    long_position = pd.DataFrame(columns=['trade_date', 'wind_id', 'K', 'end_date', 'settle', 'contract_multiplier'])
    short_position = pd.DataFrame(columns=['trade_date', 'wind_id', 'K', 'end_date', 'settle', 'contract_multiplier'])

    # 判断大小，执行交易
    state = 0
    sum = 0
    for i in total_trade_dt[0:-1]:
        print(i)
        if state == 0:
            if volatility.loc[i, 'v2-v1-mean'] > 2*volatility.loc[i, 'std'] \
                    and volatility.loc[i, 'end_date_1'] > total_trade_dt[total_trade_dt.index(i)+1]:
                print('# 开仓,卖出远月，买入近月')
                # 开仓,卖出远月，买入近月
                value = volatility.loc[i, 'contract_multiplier_2']*volatility.loc[i, 'settle_2'] \
                        - volatility.loc[i, 'contract_multiplier_2']*volatility.loc[i, 'settle_1']
                state = 1
                state_all.append(state)
                net_value.append(0)
                gross_value.append(sum)
                # 记录开仓多头,买近月
                long_position = long_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                      'wind_id': volatility.loc[i, 'wind_id_1'],
                                                      'K': volatility.loc[i, 'K'],
                                                      'end_date':volatility.loc[i, 'end_date_1'],
                                                      'settle': volatility.loc[i, 'settle_1'],
                                                      'contract_multiplier': volatility.loc[
                                                          i, 'contract_multiplier_1']},
                                                     ignore_index=True)
                # 记录开仓空头，卖远月
                short_position = short_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                        'wind_id': volatility.loc[i, 'wind_id_2'],
                                                        'K': volatility.loc[i, 'K'],
                                                        'end_date': volatility.loc[i, 'end_date_2'],
                                                        'settle': volatility.loc[i, 'settle_2'],
                                                        'contract_multiplier': volatility.loc[
                                                            i, 'contract_multiplier_2']},
                                                       ignore_index=True)
            elif volatility.loc[i, 'v2-v1-mean'] < -2*volatility.loc[i, 'std'] \
                    and volatility.loc[i, 'end_date_1'] > total_trade_dt[total_trade_dt.index(i)+1]:
                print('# 开仓,卖出近月，买入远月')
                # 开仓，卖出近月，买入远月
                value = volatility.loc[i, 'contract_multiplier_1']*volatility.loc[i, 'settle_1'] \
                        - volatility.loc[i, 'contract_multiplier_2']*volatility.loc[i, 'settle_2']
                state = -1
                state_all.append(state)
                net_value.append(0)
                gross_value.append(sum)
                # 记录开仓多头,买远月
                long_position = long_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                      'wind_id': volatility.loc[i, 'wind_id_2'],
                                                      'K': volatility.loc[i, 'K'],
                                                      'end_date': volatility.loc[i, 'end_date_2'],
                                                      'settle': volatility.loc[i, 'settle_2'],
                                                      'contract_multiplier': volatility.loc[
                                                          i, 'contract_multiplier_2']},
                                                     ignore_index=True)
                # 记录开仓空头，卖远月
                short_position = short_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                        'wind_id': volatility.loc[i, 'wind_id_1'],
                                                        'K': volatility.loc[i, 'K'],
                                                        'end_date': volatility.loc[i, 'end_date_1'],
                                                        'settle': volatility.loc[i, 'settle_1'],
                                                        'contract_multiplier': volatility.loc[
                                                            i, 'contract_multiplier_1']},
                                                       ignore_index=True)
            else:
                net_value.append(0)
                state_all.append(0)
                gross_value.append(sum)
        elif state == 1:
            if volatility.loc[i, 'v2-v1-mean'] < 0 \
                    or long_position.iloc[-1]['end_date'] > total_trade_dt[total_trade_dt.index(i)+1]:
                print('# 平仓：卖出近月，买入远月')
                # 连接.db文件
                my_db = sqlite3.connect(r'D:\pc\Desktop\Algo_Trading\Assignment3\data\raw\option.db')
                # 对数据库进行操作，取出所需数据
                c = my_db.cursor()
                # 日期 和 wind_id
                x1 = i
                y1 = long_position.iloc[-1]['wind_id']
                # x1 = int(x1.strftime('%Y%m%d'))
                # 根据wind_id找出期权的当日价格
                select_part = 'SELECT close'
                from_part = 'FROM ' + option_string
                condition_part = "WHERE TRADE_DT= {x} AND WIND_ID='{y}'" .format(x=x1, y=y1)
                c.execute(select_part + ' ' + from_part + ' ' + condition_part)
                settle_1_tuple = c.fetchall()
                settle_1_array = np.array(settle_1_tuple)

                # 日期 和 wind_id
                x2 = i
                y2 = short_position.iloc[-1]['wind_id']
                # x2 = int(x2.strftime('%Y%m%d'))
                # 根据wind_id找出期权的当日价格
                select_part = 'SELECT close'
                from_part = 'FROM ' + option_string
                condition_part = "WHERE TRADE_DT= {x} AND WIND_ID='{y}'".format(x=x2, y=y2)
                c.execute(select_part + ' ' + from_part + ' ' + condition_part)
                settle_2_tuple = c.fetchall()

                # 平仓：卖出近月，买入远月
                x = long_position.iloc[-1]['contract_multiplier'] * settle_1_tuple[0][0] \
                    - short_position.iloc[-1]['contract_multiplier'] * settle_2_tuple[0][0]+value
                net_value.append(x)
                state = 0
                state_all.append(state)
                sum += x
                gross_value.append(sum)
                # 记录平仓多头,买远月
                long_position = long_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                      'wind_id': short_position.iloc[-1]['wind_id'],
                                                      'K': short_position.iloc[-1]['K'],
                                                      'end_date': short_position.iloc[-1]['end_date'],
                                                      'settle': settle_2_tuple[0][0],
                                                      'contract_multiplier':
                                                          short_position.iloc[-1]['contract_multiplier']},
                                                     ignore_index=True)
                # 记录开仓空头，卖近月
                short_position = short_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                        'wind_id': long_position.iloc[-2]['wind_id'],
                                                        'K': long_position.iloc[-2]['K'],
                                                        'end_date': long_position.iloc[-2]['end_date'],
                                                        'settle': settle_1_tuple[0][0],
                                                        'contract_multiplier':
                                                            long_position.iloc[-2]['contract_multiplier']},
                                                       ignore_index=True)
            else:
                net_value.append(0)
                state_all.append(1)
                gross_value.append(sum)
        elif state == -1:
            if volatility.loc[i, 'v2-v1-mean'] > 0 \
                    or short_position.iloc[-1]['end_date'] > total_trade_dt[total_trade_dt.index(i)+1]:
                print('# 平仓：卖出远月，买入近月')
                # 连接.db文件
                my_db = sqlite3.connect(r'D:\pc\Desktop\Algo_Trading\Assignment3\data\raw\option.db')
                # 对数据库进行操作，取出所需数据
                c = my_db.cursor()
                # 日期 和 wind_id
                x1 = i
                y1 = long_position.iloc[-1]['wind_id']
                # x1 = int(x1.strftime('%Y%m%d'))
                # 根据wind_id找出期权的当日价格
                select_part = 'SELECT close'
                from_part = 'FROM ' + option_string
                condition_part = "WHERE TRADE_DT= {x} AND WIND_ID='{y}'".format(x=x1, y=y1)
                c.execute(select_part + ' ' + from_part + ' ' + condition_part)
                settle_2_tuple = c.fetchall()
                settle_2_array = np.array(settle_2_tuple)

                # 日期 和 wind_id
                x2 = i
                y2 = short_position.iloc[-1]['wind_id']
                # x2 = int(x2.strftime('%Y%m%d'))

                # 根据wind_id找出期权的当日价格
                select_part = 'SELECT close'
                from_part = 'FROM ' + option_string
                condition_part = "WHERE TRADE_DT= {x} AND WIND_ID='{y}'".format(x=x2, y=y2)
                c.execute(select_part + ' ' + from_part + ' ' + condition_part)
                settle_1_tuple = c.fetchall()
                settle_1_array = np.array(settle_1_tuple)

                # 平仓
                x = long_position.iloc[-1]['contract_multiplier'] * settle_2_tuple[0][0] \
                    - short_position.iloc[-1]['contract_multiplier'] * settle_1_tuple[0][0] + value
                net_value.append(x)
                state = 0
                state_all.append(state)
                sum += x
                gross_value.append(sum)

                # 记录平仓多头,买近月
                long_position = long_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                      'wind_id': short_position.iloc[-1]['wind_id'],
                                                      'K': short_position.iloc[-1]['K'],
                                                      'end_date': short_position.iloc[-1]['end_date'],
                                                      'settle': settle_1_tuple[0][0],
                                                      'contract_multiplier':
                                                          short_position.iloc[-1]['contract_multiplier']},
                                                     ignore_index=True)
                # 记录开仓空头，卖远月
                short_position = short_position.append({'trade_date': volatility.loc[i, 'trade_date'],
                                                        'wind_id': long_position.iloc[-2]['wind_id'],
                                                        'K': long_position.iloc[-2]['K'],
                                                        'end_date': long_position.iloc[-2]['end_date'],
                                                        'settle': settle_2_tuple[0][0],
                                                        'contract_multiplier':
                                                            long_position.iloc[-2]['contract_multiplier']},
                                                       ignore_index=True)
            else:
                net_value.append(0)
                state_all.append(-1)
                gross_value.append(sum)
    net_value.append(0)
    state_all.append(0)
    gross_value.append(sum)
    plt.plot(volatility['trade_date'], state_all)
    plt.legend(['state'], loc='upper left')
    plt.show()
    plt.plot(volatility['trade_date'], net_value)
    plt.legend(['net_value'], loc='upper left')
    plt.show()
    plt.plot(volatility['trade_date'], gross_value)
    plt.legend(['balance'], loc='upper left')
    plt.show()
    position = pd.concat([short_position,long_position], axis=1, ignore_index=True)
    position.columns = ['trade_date', 'wind_id', 'K', 'end_date', 'settle', 'contract_multiplier',
                        'trade_date', 'wind_id', 'K', 'end_date', 'settle', 'contract_multiplier']
    position.to_csv(r'D:\pc\Desktop\Algo_Trading\Assignment3\result\data\position.csv')


if __name__ == "__main__":
    calendar_spread('510050.SH', 20160701, 20180501)