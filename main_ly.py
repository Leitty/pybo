# coding: utf-8
'''
加入了交易逻辑，待模块化，待优化
'''
from bigone import BigOneDog
from common import gen_logger

import logging
import time
import json

def strategy_eth_big_bnc_eth(dog):
    """
    正向：买BIG/ETH -> 卖BIG/BNC -> 买ETH/BNC
    反向：卖ETH/BNC -> 买BIG/BNC -> 卖BIG/ETH
    :param dog: implemention of BigOneDog
    :return: 正向收益率，反向收益率
    """
    try:
        big_eth_data = dog.get_order_book('BIG-ETH')
        big_bnc_data = dog.get_order_book('BIG-BNC')
        eth_bnc_data = dog.get_order_book('ETH-BNC')
    except Exception:
        time.sleep(60)
        return True

    print('BIG-ETH')
    print('卖一', big_eth_data['asks'][0]['price'], big_eth_data['asks'][0]['amount'])
    print('买一', big_eth_data['bids'][0]['price'], big_eth_data['bids'][0]['amount'])
    print('BIG-BNC')
    print('卖一', big_bnc_data['asks'][0]['price'], big_bnc_data['asks'][0]['amount'])
    print('买一', big_bnc_data['bids'][0]['price'], big_bnc_data['bids'][0]['amount'])
    print('ETH-BNC')
    print('卖一', eth_bnc_data['asks'][0]['price'], eth_bnc_data['asks'][0]['amount'])
    print('买一', eth_bnc_data['bids'][0]['price'], eth_bnc_data['bids'][0]['amount'])

    # positive transaction
    pos_anc = 0.999*0.999*0.999*\
              ((1 / (float(big_eth_data['asks'][0]['price'])))
              * float(big_bnc_data['bids'][0]['price']) )
    pos_anc = pos_anc / float(eth_bnc_data['asks'][0]['price']) - 1

    # negative transaction
    # neg_anc = 0.999 * 0.999 * 0.999 * \
    #       (float(eth_bnc_data['bids'][0]['price'])
    #        / float(big_bnc_data['asks'][0]['price'])
    #        * float(big_eth_data['asks'][0]['price']))
    # neg_anc = neg_anc / 1 - 1

    flag = False

    amt = 3.0
    if float(big_eth_data['asks'][0]['amount']) >= amt:
        if float(big_bnc_data['bids'][0]['amount']) >= amt:
            if float(eth_bnc_data['asks'][0]['amount']) >= amt * float(big_eth_data['asks'][0]['price']):
                flag = True

    msg = "预期本次[正向套利:买BIG/ETH -> 卖BIG/BNC -> 买ETH/BNC]利润:"
    if pos_anc < 0.005:
        result = "利润空间小于1%, 放弃本次套利 0"
        logger.info("{0} {1:.2f}%, {2}".format(msg,pos_anc*100,result))
    else:
        result = "利润空间大于1%"
        if flag is False:
            result = "{},{}".format(result,"量不足, 放弃本次套利 0")
            logger.info("{0} {1:.2f}%, {2}".format(msg,pos_anc*100,result))
        else:
            result = "{},{}".format(result,"执行本次套利 1")
            logger.info("{0} {1:.2f}%, {2}".format(msg,pos_anc*100,result))

            print("{}  {}  {}  {}".format('BIG-ETH','BID', big_eth_data['asks'][0]['price'], str(amt)))
            print("{}  {}  {}  {}".format('BIG-BNC','ASK', big_bnc_data['bids'][0]['price'], str(amt)))
            print("{}  {}  {}  {}".format('ETH-BNC','BID', eth_bnc_data['asks'][0]['price'],
                             str(amt * float(big_eth_data['asks'][0]['price']))))
            # dog.create_order('BIG-ETH','ASK', big_eth_data['asks'][0]['price'], '2.0')
            # dog.create_order('BIG-BNC','BID', big_bnc_data['bids'][0]['price'], '2.0')
            # dog.create_order('ETH-BNC','ASK', eth_bnc_data['asks'][0]['price'],
            #                  str(2.0 * float(big_eth_data['asks'][0]['price'])))
            # 买入BIG

            try:
                r1 = dog.create_order('BIG-ETH','BID', big_eth_data['asks'][0]['price']+0.01, '3.0')
            except Exception:
                logger.info("买入BIG失败，退出")
                print('买入BIG失败，退出')
                return False
            # r1 = dog.create_order('BIG-ETH', 'BID', big_eth_data['asks'][0]['price'], '2.0')

            bid_order_id = r1['order_id']
            try:
                ret_order = dog.get_order(bid_order_id)
            except Exception:
                logger.info("查询失败，不存在对应的订单号" )
                print('查询失败，不存在对应的订单号', ret_order )

            count = 0
            while ret_order['order_state'] == 'open':
                print('买BIG挂单仍未成交')
                logger.info("买BIG挂单仍未成交")
                print("")
                time.sleep(5)
                count = count + 1
                if count > 40:
                    dog.cancel_order(bid_order_id)
                    break

            if count > 40:
                return False

            print('买BIG挂单成交')
            # 买成功后才进行卖出操作
            try:
                r2 = dog.create_order('BIG-BNC', 'ASK', big_bnc_data['bids'][0]['price']-0.01, '3.0')
            except Exception:
                print('卖出BIG失败，退出')
                logger.info("卖出BIG失败，退出")
                return False

            ask_order_id = r2['order_id']

            try:
                ret_order = dog.get_order(ask_order_id)
            except Exception:
                print('查询失败，不存在对应的订单号', ret_order )
                logger.info("查询失败，不存在对应的订单号")

            while ret_order['order_state'] == 'open':
                print('ETH买入挂单未成交')
                logger.info("ETH买入挂单未成交")
                print("")
                time.sleep(10)

            # 卖成功后进行买
            try:
                r3 = dog.create_order('ETH-BNC', 'ASK', eth_bnc_data['asks'][0]['price']+0.01, str(3.0 * float(big_eth_data['asks'][0]['price'])))
            except Exception:
                print('买入ETH失败，退出')
                logger.info("买入ETH失败，退出")
                return False

            bid_order_id = r3['order_id']
            try:
                ret_order = dog.get_order(ask_order_id)
            except Exception:
                print('查询失败，不存在对应的订单号', ret_order )
                logger.info("查询失败，不存在对应的订单号")

            while ret_order['order_state'] == 'open':
                logger.info("ETH买入挂单未成交")
                print('ETH买入挂单未成交')
                print("")
                time.sleep(10)

            return True
    # if neg_anc < 0.01:
    #     result = "利润空间小于1%, 放弃本次套利 0"
    # else:
    #     result = "利润空间大于1%, 执行本次套利 1"
    #
    #     logger.info("预期本次[反向套利:卖ETH/BNC -> 买BIG/BNC -> 卖BIG/ETH]利润: {0:.2f}%, {1}".format(neg_anc*100,result))

    return False



    # return pos_anc, neg_anc

#乞丐版  卖出成功后才进行买入操作

def strategy_eth_bnc(dog):
    eth_bnc_data = dog.get_order_book('ETH-BNC')
    print('ETH-BNC')
    print('卖一', eth_bnc_data['asks'][0]['price'], eth_bnc_data['asks'][0]['amount'])
    print('买一', eth_bnc_data['bids'][0]['price'], eth_bnc_data['bids'][0]['amount'])
    # anc = 0.999*(float(eth_bnc_data['asks'][0]['price'])-0.012) / (float(eth_bnc_data['bids'][0]['price'])+0.012) - 1

    # 1、同时买卖方案失败，必须卖价高于买价才有可能获利
    # #买入0.01 ETH的花费的的BNC
    # bnc_used = eth_bnc_data['ask'][0]['price']*0.01
    # #卖出0.01 ETH获得的BNC
    # bnc_gain = eth_bnc_data['bids'][0]['price']*0.01
    # anc = (bnc_gain-bnc_used)/bnc_used
    #
    # #卖出ETH的获得的BNC
    # btc_in_hand = eth_bnc_data['bids'][0]['price']*0.01
    # #买入ETH的数量
    # eth_in_hand = btc_in_hand/float(eth_bnc_data['asks'][0]['price'])
    # anc = eth_in_hand/0.01
    # 2、买卖价差距小时买入，差距大时卖出
    print(anc)

    #统计一天的交易买卖价格
    #msg1 = '买卖价格:'
    #logger.info("{0}     {1}     {2}".format(msg1, eth_bnc_data['asks'][0]['price'], eth_bnc_data['bids'][0]['price']))

    #测试代码
    # r = dog.create_order('ETH-BNC', 'ASK', '5908.01', '0.01')
    # ask_order_id = r['order_id']
    # ask_order_id = '60526668-1adb-498b-b75f-03cda102eef0'
    # try:
    #     ret_order = dog.get_order(ask_order_id)
    # except Exception:
    #     print('查询失败，不存在对应的订单号', Exception )

    if anc > 0.018:
        #先卖出ETH
        r = dog.create_order('ETH-BNC', 'ASK', str(float(eth_bnc_data['asks'][0]['price'])-0.01), '0.01' )
        ask_order_id = r['order_id']
        try:
            ret_order = dog.get_order(ask_order_id)
        except Exception:
            print('查询失败，不存在对应的订单号', ask_order_id)
            return True

        count = 0
        while ret_order['order_state'] == 'open':
            print('ETH卖出挂单未成交')
            print("")
            time.sleep(5)
            count = count+1
            if count > 40:
                dog.cancel_order(ask_order_id)
                return True

        # 卖出成功后才进行买入操作
        r = dog.create_order('ETH-BNC', 'BID', str(float(eth_bnc_data['bids'][0]['price'])+0.01), '0.01' )
        bid_order_id = r['order_id']
        while ret_order['order_state'] == 'open':
            print('ETH买入挂单未成交')
            print("")
            time.sleep(5)


        return True

    # ret_order = dog.get_order(ask_order_id)
    # ret_order = dog.get_orders('ETH-BTC')
    # if ret_order is None:
    #     print('1')
    #     print(ret_order)
    # else:
    #     print('2')
    #     print(ret_order)
    #     print(type(ret_order))


    return True
    #return anc, anc


def strategy_eth_btc(dog):
    eth_btc_data = dog.get_order_book('ETH-BTC')
    print('ETH-BNC')
    print('卖一', eth_btc_data['asks'][0]['price'], eth_btc_data['asks'][0]['amount'])
    print('买一', eth_btc_data['bids'][0]['price'], eth_btc_data['bids'][0]['amount'])


    '''
    anc = (float(eth_btc_data['asks'][0]['price'])) / (float(eth_btc_data['bids'][0]['price'])) - 1
    print(anc)

    #order中ASK为卖，BID为买

    if anc > 0.02:
        #买入ETH
        r = dog.create_order('ETH-BNC', 'BID', str(float(eth_btc_data['bids'][0]['price'])+0.01), '0.01' )
        bid_order_id = r['order_id']

        #卖出ETH
        r = dog.create_order('ETH-BNC', 'ASK', str(float(eth_btc_data['asks'][0]['price'])-0.01), '0.01' )
        ask_order_id = r['order_id']
    '''
    return True

if __name__ == '__main__':
    gen_logger('bigonetest')
    logger = logging.getLogger("bigone")

    with open("PRIVATE_KEY.json", 'r') as f:
        private_key = json.load(f)["key"]
    dog = BigOneDog(private_key)

    # flag = strategy_eth_bnc(dog)


    # eth_btc_data = dog.get_order_book('ETH-BTC')
    # print('ETH-BNC')
    # print('卖一', eth_btc_data['asks'][0]['price'], eth_btc_data['asks'][0]['amount'])
    # print('买一', eth_btc_data['bids'][0]['price'], eth_btc_data['bids'][0]['amount'])
    #
    # r = dog.create_order('ETH-BNC', 'ASK', '5908.01', '0.01')
    # print(r)
    # ask_order_id = r['order_id']
    #
    # t = dog.get_order(ask_order_id)
    # print(t)
    # print(type(t[0]))
    # print(t[0]['order_id'])
    # p = dog.cancel_order((t[0]['order_id']))
    # print(p)

    # r1 = dog.create_order('BIG-ETH', 'BID', '0.003', '2.0')
    while True:
    #ASK
        flag = strategy_eth_big_bnc_eth(dog)

        print("休眠10秒")
        print("")
        time.sleep(10)


