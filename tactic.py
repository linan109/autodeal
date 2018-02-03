# -*- coding: utf-8 -*-
import json
import logging
import os
from datetime import datetime

import config

from deal import Deal
from lib import HuobiServices


class Tactic(object):
    def run(self):
        raise NotImplemented

    def create_deal(self, high, low, close, amount):
        raise NotImplemented

    def __repr__(self):
        return json.dumps(self.__dict__)

    pass


class PriceDiffTactic(Tactic):
    """取最近一段时间的最高价与最低价,以及当前价.
       算最高价与最低价的差价, 如果大于一定阈值, 则生成一对交易"""
# bid_gap, bid_goal, k_period, k_size, max_deal_num
    def __init__(self, init_deal):
        self.deals = []
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

        self.goods_unit = config.price_unit[self.symbol][0]
        self.money_unit = config.price_unit[self.symbol][1]

        self.live_file = "save/%s_deals" % self.name
        self.finish_file = "finished/%s" % self.name

        self.recover()

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

    def recover(self):
        if os.path.exists(self.live_file):
            with open(self.live_file, "r") as live:
                live_deals = json.load(live)
                [self.deals.append(Deal(**json.loads(d))) for d in live_deals]

    def store_deals(self):
        if os.path.exists(self.live_file):
            os.rename(self.live_file, self.live_file + ".bak")
        with open(self.live_file, "w") as live:
            json.dump(self.deals, live, default=lambda x: repr(x))

    def record_finished(self, deal):
        with open(self.finish_file, "a") as finish:
            finish.write("%s. deal complete. create at %s. buy at %s. sell at %s. amount = %s. \n" % (datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'), deal.create_time, deal.buy_price, deal.sell_price, deal.amount))


    def record_outdated(self, deal):
        # todo
        pass


    def update_deal(self):
        req = HuobiServices.orders_list(symbol=self.symbol, states="pre-submitted,submitted,partial-filled",
                                        size=max(100, 5*self.max_deal_num))
        if req["status"] != "ok":
            logging.error("query orders failed. skip. reason: %s" % req["err-msg"])
            return

        remain_orders = [o["id"] for o in req["data"]]

        for i, deal in enumerate(self.deals):
            deal.update(remain_orders)
            if deal.is_finished():
                logging.info("SUCCESS! deal %s %s finished" % (deal.order1_id, deal.order2_id))
                self.deals.pop(i)
                self.record_finished(deal)
            if deal.is_out_dated():
                logging.info("FAIL! deal %s %s out of date. create at %s" % (deal.order1_id, deal.order2_id, deal.create_time))
                self.deals.pop(i)
                self.record_outdated(deal)
        self.store_deals()

    def run(self):
        # update deal
        logging.info("%s start run" % self.name)
        self.update_deal()

        # search market
        if len(self.deals) >= self.max_deal_num:
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
        # check balance
        balance = HuobiServices.get_balance()
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
        bid_high = high * self.bid_goal + close * (1 - self.bid_goal)
        bid_low = close * (1 - self.bid_goal) + low * self.bid_goal

        order1 = HuobiServices.send_order(self.fg(amount), None, self.symbol, "sell-limit", price=self.fm(bid_high))
        if order1['status'] != "ok":
            logging.error("send order failed: %s" % order1["err-msg"])
            return
        order1_id = order1["data"]
        logging.info("success create order %s" % order1_id)

        order2 = HuobiServices.send_order(self.fg(amount), None, self.symbol, "buy-limit", price=self.fm(bid_low))
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
        logging.info("success create order %s" % order2_id)

        self.deals.append(Deal(order1_id, order2_id,
                               buy_price=self.fm(bid_low),
                               sell_price=self.fm(bid_high),
                               amount="%.4f" % amount))
        logging.info(
            """create deal in %s.
            sell price=%s
            buy price=%s
            amount=%.4f""" % (self.symbol, self.fm(bid_high), self.fm(bid_low), amount))

        self.store_deals()


if __name__ == '__main__':
    test_deal = ["test", "eth", "usdt", 0.1, 0.90, 8, "60min", 20, 1]

    a = PriceDiffTactic(test_deal)
    a.deals.append(Deal("111", "222", buy_price="232"))
    # [print(d) for d in a.deals]
    a.store_deals()
    a.record_finished(a.deals[-1])
