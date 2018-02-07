import mongoengine as db
import logging
from datetime import datetime, timedelta


class Deal(db.Document):
    tactic = db.StringField()
    order1_id = db.StringField(max_length=12, unique=True)
    order2_id = db.StringField(max_length=12, unique=True)
    expired = db.IntField()
    buy_price = db.StringField()
    sell_price = db.StringField()
    buy_amount = db.StringField()
    sell_amount = db.StringField()
    order1_finished = db.BooleanField(default=False)
    order2_finished = db.BooleanField(default=False)
    create_time = db.DateTimeField(default=datetime.utcnow())
    finish_time = db.DateTimeField()
    status = db.StringField(default="waiting")

    def update_status(self, remain_order_ids):
        if len(remain_order_ids) >= 1 and not isinstance(remain_order_ids[0], int):
            raise Exception()

        # check isfinished
        if not self.order1_finished and int(self.order1_id) not in remain_order_ids:
            self.order1_finished = True
            logging.info("order %s finished" % self.order1_id)
        if not self.order2_finished and int(self.order2_id) not in remain_order_ids:
            self.order2_finished = True
            logging.info("order %s finished" % self.order2_id)
        if self.order1_finished and self.order2_finished:
            logging.info("SUCCESS! deal %s %s finished" % (self.order1_id, self.order2_id))
            self.status = "succeed"
            self.finish_time = datetime.utcnow()

        # check isoutdated
        if self.create_time + timedelta(minutes=self.expired) < datetime.utcnow():
            logging.info("FAIL! deal %s %s out of date. create at %s" % (self.order1_id, self.order2_id, deal.create_time))
            self.status = "failed"
            self.finish_time = datetime.utcnow()

        self.save()


