# -*- coding: utf-8 -*-
import logging
import time
import config
from config import work_dir
from mongoengine import connect


from tactic import PriceDiffTactic


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, filename=work_dir + "log/server.log", filemode="a",
                        level=logging.INFO)
    connect('autodeal')
    dps = list()
    for deal_pair in config.init_deals:
        dps.append(PriceDiffTactic(deal_pair))
    logging.info("server start")
    while True:
        logging.info("start loop")
        for dp in dps:
            dp.run()
        time.sleep(config.deal_interval)

