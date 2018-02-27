# coding: utf-8
'''
加入了所有币种的抓取，交易路径抓取，路径利润计算，显示，待模块化，待优化
'''
from bigone import BigOneDog
from common import gen_logger

import matplotlib.pyplot as plt
import logging
import time
import json
import sqlite3

def profit_cala(symbola , symbolb , symbolc):
    sting_a_b = symbola + '-' + symbolb
    sting_a_c = symbola + '-' + symbolc
    sting_b_c = symbolb + '-' + symbolc
    try:
        a_b_data = dog.get_order_book(sting_a_b)
    except Exception:
        print('访问出现异常，暂停')
        return 0

    try:
        a_c_data = dog.get_order_book(sting_a_c)
    except Exception:
        print('访问出现异常，暂停')
        return 0

    try:
        b_c_data = dog.get_order_book(sting_b_c)
    except Exception:
        print('访问出现异常，暂停')
        return 0

    pos_anc = 0.999*0.999*0.999*\
              ((1 / (float(a_b_data['asks'][0]['price'])))
              * float(a_c_data['bids'][0]['price']) )
    pos_anc = pos_anc / float(b_c_data['asks'][0]['price']) - 1
    return pos_anc


def find_market_kinds(dog):
    data = dog.get_markets()
    return data


def creat_exchange_table():
    conn = sqlite3.connect('test.db')
    print("Opened database successfully")

    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE EXCHANGE_TABLE(SYMBOLA  char(50), SYMBOLB char(50));''')
    except Exception:
        print('EXCHANGE_TABLE创建失败，该表已存在')
        return False
    print('EXCHANGE_TABLE创建成功')
    conn.commit()
    conn.close()
    return True

def creat_trade_path_table():
    conn = sqlite3.connect('test.db')
    # print("Opened database successfully")

    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE TRADE_PATH_TABLE(SYMBOLA  char(50), SYMBOLB char(50), SYMBOLC char(50));''')
    except Exception:
        print('TRADE_PATH_TABLE创建失败，该表已存在')
        return False
    print('TRADE_PATH_TABLE创建成功')
    conn.commit()
    conn.close()
    return True

def creat_cat_trade_statics():
    conn = sqlite3.connect('test.db')
    print("Opened database successfully")

    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE CAT_TRADE_STATICS(DT time,TRADE_PATH  char(50), TRADE_PROFIT float);''')
    except Exception:
        print('CAT_TRADE_STATICS创建失败，该表已存在')
        return False
    print('CAT_TRADE_STATICS创建成功')
    conn.commit()
    conn.close()
    return True

def insert_into_table(SQL_TEXT):
    conn = sqlite3.connect('test.db')
    #
    c = conn.cursor()
    c.execute(SQL_TEXT)
    # print('数据插入成功', symbola, symbolb)
    conn.commit()
    conn.close()

def select_from_table(SQL_TEXT):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    cursor = c.execute(SQL_TEXT)
    # for row in cursor:
    #     print('交易路径：', row)
    list = cursor.fetchall()
    # print("Operation done successfully")
    conn.close()
    return list

def Data_into_trade_table():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    d = conn.cursor()
    DATA_SQL_TEXT = "select A.SYMBOLA, A.SYMBOLB, B.SYMBOLA, B.SYMBOLB from EXCHANGE_TABLE C ," \
               "EXCHANGE_TABLE A, EXCHANGE_TABLE B  where C.SYMBOLA = A.SYMBOLB and C.SYMBOLB = B.SYMBOLB " \
               "and A.SYMBOLA = B.SYMBOLA and A.SYMBOLB != B.SYMBOLB"
    cursor = c.execute(DATA_SQL_TEXT)
    print(type(cursor))
    for row in cursor:
        SQL_TEXT = "INSERT INTO TRADE_PATH_TABLE (SYMBOLA, SYMBOLB, SYMBOLC) VALUES (" + "'" + row[0] + "'" + "," + \
                   "'" + row[1] + "'" + "," + "'" + row[3] + "'" + ")"
        print(SQL_TEXT)
        d.execute(SQL_TEXT)
        print('交易路径：', row[1], '-', row[0], '-', row[3], '-', row[1])
    conn.commit()
    # print("Operation done successfully")
    conn.close()

def Data_into_cat_trade_statics(ctime, trade_path, trade_profit):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    SQL_TEXT = "INSERT INTO cat_trade_statics VALUES (" + "'" + ctime + "'" + "," +"'"+ trade_path +"'" + "," + str(trade_profit) +")"
    # SQL_TEXT = "INSERT INTO cat_trade_statics VALUES (" + ctime + ","  + trade_path +  "," + str(
    #     trade_profit) + ")"
    c.execute(SQL_TEXT)
    conn.commit()
    # print("Operation done successfully")
    conn.close()

def watch():
    SQL_TEXT = "select * from TRADE_PATH_TABLE"
    path_list = select_from_table(SQL_TEXT)
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for trade_path in path_list:
        path_profit = profit_cala(trade_path[0], trade_path[1], trade_path[2])
        trade_path = trade_path[0] + '-' + trade_path[1] + '-' + trade_path[2]
        Data_into_cat_trade_statics(t, trade_path, path_profit)
#
#     big_eth_data = dog.get_order_book('BIG-ETH')
#     big_bnc_data = dog.get_order_book('BIG-BNC')
#     eth_bnc_data = dog.get_order_book('ETH-BNC')

def visualize(x, y):
    plt.scatter(x, y, label='skitscat', color='k', s=25, marker="o")
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Interesting Graph Check it out')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    gen_logger('bigonetest')
    logger = logging.getLogger("bigone")

    with open("PRIVATE_KEY.json",'r') as f:
        private_key = json.load(f)["key"]
    dog = BigOneDog(private_key)

    SQL_TEXT_X = "select DT from CAT_TRADE_STATICS where TRADE_PATH = 'ATN-QTUM-BTC' order by DT"
    SQL_TEXT_Y = "select TRADE_PROFIT from CAT_TRADE_STATICS where TRADE_PATH = 'ATN-QTUM-BTC' order by DT"
    vis_x = select_from_table(SQL_TEXT_X)
    vis_y = select_from_table(SQL_TEXT_Y)
    visualize(vis_x, vis_y)

    # SQL_TEXT_Y = ""
    # yprofit = select_from_table()

    # # 抓取数据
    # while True:
    #     watch()
    #     print("watch successfully")
    #     time.sleep(20)

    # #
    # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    # print(time.time())
    # creat_exchange_table()
    # creat_trade_path_table()
    # Data_into_trade_table()

    # market_data = find_market_kinds(dog)
    # # print(market_data[0]['symbol'])
    # for each_list in market_data:
    #     market_symbol = each_list['symbol'].split('-')
    #     print(market_symbol[0], market_symbol[1])
    #     SQL_TEXT = "INSERT INTO EXCHANGE_TABLE (SYMBOLA, SYMBOLB) \
    # VALUES (" + "'" + market_symbol[0] + "'" + "," + "'" + market_symbol[1] + "'" + ")"
    #     insert_into_table(market_symbol[0], market_symbol[1])

    # SQL_TEXT = "select A.SYMBOLA, A.SYMBOLB, B.SYMBOLA, B.SYMBOLB from EXCHANGE_TABLE C ," \
    #            "EXCHANGE_TABLE A, EXCHANGE_TABLE B  where C.SYMBOLA = A.SYMBOLB and C.SYMBOLB = B.SYMBOLB " \
    #            "and A.SYMBOLA = B.SYMBOLA and A.SYMBOLB != B.SYMBOLB"
    # select_from_table(SQL_TEXT)



    # SQL_TEXT = "select * from TRADE_PATH_TABLE"
    # llist = select_from_table(SQL_TEXT)
    #
    # print('交易路径：', llist[0][0],'-', llist[0][1], '-', llist[0][2] , '利润:',profit_cala(llist[0][0], llist[0][1], llist[0][2]))
    #
