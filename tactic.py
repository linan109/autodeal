# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta
from models.deal import Deal

import config

from lib import HuobiServices
from config import work_dir

ORDER_JUSTIFY = 0.02
ORDER_LIMIT = 15


class Tactic(object):
    def run(self):
        raise NotImplemented

    def create_deal(self, high, low, close, amount):
        raise NotImplemented

    def __repr__(self):
        return json.dumps(self.__dict__)

    pass

last_query_time = datetime.now() - timedelta(minutes=1)
last_result = None
balance_changed = True


def get_balance():
    if globals()['balance_changed'] or datetime.now() - timedelta(minutes=1) >= globals()['last_query_time']:
        globals()['last_result'] = HuobiServices.get_balance()
        globals()['last_query_time'] = datetime.now()
        globals()['balance_changed'] = False
    return globals()['last_result']


class PriceDiffTactic(Tactic):
    """取最近一段时间的最高价与最低价,以及当前价.
       算最高价与最低价的差价, 如果大于一定阈值, 则生成一对交易"""
# bid_gap, bid_goal, k_period, k_size, max_deal_num
    def __init__(self, init_deal):
        self.name = init_deal[0]
        self.goods = init_deal[1]
        self.money = init_deal[2]
        self.bid_gap = init_deal[3]
        self.bid_goal = init_deal[4]
        self.k_size = init_deal[5]
        self.k_period = init_deal[6]
        self.max_deal_num = init_deal[7]
        self.deal_size = init_deal[8]
        self.symbol = self.goods + self.money
        self.expired = init_deal[9]

        self.goods_unit = config.price_unit[self.symbol][0]
        self.money_unit = config.price_unit[self.symbol][1]

        self.live_file = work_dir + "save/%s_deals" % self.name
        self.finish_file = work_dir + "finished/%s" % self.name

        # self.recover()

    def format_money(self, money):
        if not isinstance(money, float):
            raise Exception()
        return self.money_unit % money
    fm = format_money

    def format_goods(self, goods):
        if not isinstance(goods, float):
            raise Exception()
        return self.goods_unit % goods
    fg = format_goods

    def __repr__(self):
        return self.name

    def get_remain_orders(self):
        req = HuobiServices.orders_list(symbol=self.symbol, states="pre-submitted,submitted,partial-filled",
                                        size=max(100, 5*self.max_deal_num))
        if req["status"] != "ok":
            logging.error("query remain orders failed. skip. reason: %s" % req["err-msg"])
            return

        remain_orders = [o["id"] for o in req["data"]]
        return remain_orders

    def get_canceled_orders(self):
        req = HuobiServices.orders_list(symbol=self.symbol, states="canceled",
                                        start_date=(datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
                                        size=max(100, 5*self.max_deal_num))
        if req["status"] != "ok":
            logging.error("query canceled orders failed. skip. reason: %s" % req["err-msg"])
            return

        canceled_orders = [o["id"] for o in req["data"]]
        return canceled_orders

    def update_deal(self):
        remain_orders = self.get_remain_orders()
        canceled_orders = self.get_canceled_orders()
        deals = Deal.objects(status="waiting", tactic=self.name)
        for i, deal in enumerate(deals):
            deal.update_status(remain_orders, canceled_orders)
        # update failed
        deals = Deal.objects(status="failed", tactic=self.name)
        for i, deal in enumerate(deals):
            deal.update_status(remain_orders, canceled_orders)

    def run(self):
        # update deal
        logging.info("%s start run" % self.name)
        self.update_deal()

        deals = Deal.objects(status="waiting", tactic=self.name)

        # search market
        if deals.count() >= self.max_deal_num:
            logging.info("max deal num (%d) reached. wait for current deal completed" % self.max_deal_num)
            return
        result = HuobiServices.get_kline(self.symbol, self.k_period, self.k_size)
        if not result or result["status"] != "ok":
            logging.error("query kline failed. skip. reason: %s" % result.get("err-msg", "none"))
            return

        high = max(float(k['high']) for k in result["data"])
        low = min(float(k['low']) for k in result["data"])
        close = float(result["data"][0]['close'])

        amount = self.deal_size / low

        if (high - low) / low > self.bid_gap / self.bid_goal:
            logging.info("start to create deal. price diff %s - %s)" % (self.fm(low), self.fm(high)))
            self.create_deal(high, low, close, amount)
        else:
            logging.info("do not create deal. price diff (%s - %s) is not high" % (self.fm(low), self.fm(high)))

    def create_deal(self, high, low, close, amount):
        # calc price
        bid_high = high * self.bid_goal + close * (1 - self.bid_goal)
        bid_low = close * (1 - self.bid_goal) + low * self.bid_goal
        buy_amount = amount*(1+self.bid_gap/2)

        # check current deal (don't make too many deals at one price)
        # the limit of deals whose selling price below (1+5%) * sell_price
        sell_count = 0
        buy_count = 0
        deals = Deal.objects(tactic__contains='-'.join([self.goods, self.money]), status__in=['waiting', 'failing'])
        for d in deals:
            if not d['order1_finished'] and float(d['sell_price']) < (bid_high * (1 + ORDER_JUSTIFY)):
                sell_count += 1
            if not d['order2_finished'] and float(d['buy_price']) > (bid_low * (1 - ORDER_JUSTIFY)):
                buy_count += 1
        if sell_count >= ORDER_LIMIT:
            logging.warning("too many unfinished selling order(%d) below %.4f" % (sell_count, bid_high * (1 + ORDER_JUSTIFY)))
            return
        if buy_count >= ORDER_LIMIT:
            logging.warning("too many unfinished buying order(%d) above %.4f" % (buy_count, bid_low * (1 - ORDER_JUSTIFY)))
            return

        # check balance
        balance = get_balance()
        if balance["status"] != "ok":
            logging.error("query balance failed. skip create deal. reason: %s" % balance["err-msg"])
            return

        for b in balance["data"]["list"]:
            if b["currency"] == self.goods and \
                            b["type"] == "trade" and \
                            float(b["balance"]) <= amount:
                logging.warning("not enough balance %s:%s" % (self.goods, self.fg(amount)))
                return
            if b["currency"] == self.money and \
                            b["type"] == "trade" and \
                            float(b["balance"]) <= self.deal_size:
                logging.warning("not enough balance %s:%.4f" % (self.money, self.deal_size))
                return

        # create deal
        order1 = HuobiServices.send_order(self.fg(amount), None, self.symbol, "sell-limit", price=self.fm(bid_high))
        if order1['status'] != "ok":
            logging.error("send order failed: %s" % order1["err-msg"])
            return
        order1_id = order1["data"]
        logging.info("success create order %s" % order1_id)

        order2 = HuobiServices.send_order(self.fg(buy_amount), None, self.symbol, "buy-limit", price=self.fm(bid_low))
        if order2['status'] != "ok":
            logging.error("send order failed: %s" % order2["err-msg"])
            # 撤回order1
            resp = HuobiServices.cancel_order(order1_id)
            if resp['status'] == "ok":
                logging.error("withdraw order %d succeed" % order1_id)
            else:
                logging.error("withdraw order %d failed. reason: %s" % (order1_id, resp["err-msg"]))
            return
        order2_id = order2["data"]
        globals()['balance_changed'] = True
        logging.info("success create order %s" % order2_id)

        Deal(tactic=self.name,
             order1_id=order1_id,
             order2_id=order2_id,
             expired=self.expired,
             buy_price=self.fm(bid_low),
             sell_price=self.fm(bid_high),
             buy_amount="%.4f" % buy_amount,
             sell_amount="%.4f" % amount).save()

        logging.info(
            """create deal in %s.
            sell price=%s
            buy price=%s
            amount=%.4f""" % (self.symbol, self.fm(bid_high), self.fm(bid_low), amount))


if __name__ == '__main__':
    test_deal = ["test", "eth", "usdt", 0.1, 0.90, 8, "60min", 20, 1, 24*60]

    a = PriceDiffTactic(test_deal)
    print(a.get_canceled_orders())
    print(a.get_remain_orders())
