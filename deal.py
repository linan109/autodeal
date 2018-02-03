# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta

from lib import HuobiServices


class JsonSerializable(object):
    def toJson(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.toJson()


class Deal(JsonSerializable):
    def __init__(self, order1_id, order2_id, **kwargs):
        self.order1_id = order1_id
        self.order2_id = order2_id
        self.buy_price = kwargs.get("buy_price", "none")
        self.sell_price = kwargs.get("sell_price", "none")
        self.amount = kwargs.get("amount", "none")
        self.order1_finished = kwargs.get("order1_finished", False)
        self.order2_finished = kwargs.get("order2_finished", False)
        self.create_time = kwargs.get("create_time", datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'))

    def update(self, remain_order_ids):
        if len(remain_order_ids) >= 1 and not isinstance(remain_order_ids[0], int):
            raise Exception()

        if not self.order1_finished and int(self.order1_id) not in remain_order_ids:
            self.order1_finished = True
            logging.info("order %s finished" % self.order1_id)
        if not self.order2_finished and int(self.order2_id) not in remain_order_ids:
            self.order2_finished = True
            logging.info("order %s finished" % self.order2_id)

    def _update_by_query(self):
        if not self.order1_finished:
            query = HuobiServices.order_info(self.order1_id)
            if query and query["status"] == "ok" and query["data"]["state"] == "filled":
                self.order1_finished = True
                logging.info("order %s finished" % self.order1_id)

        if not self.order2_finished:
            query = HuobiServices.order_info(self.order2_id)
            if query and query["status"] == "ok" and query["data"]["state"] == "filled":
                self.order2_finished = True
                logging.info("order %s finished" % self.order2_id)

    def is_finished(self):
        return self.order1_finished & self.order2_finished

    def is_out_dated(self):
        create_time = datetime.strptime(self.create_time, '%Y-%m-%dT%H:%M:%S')
        return create_time + timedelta(days=7) < datetime.now()



