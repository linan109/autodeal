# -*- coding: utf-8 -*-
import logging
import time
import config


from tactic import PriceDiffTactic


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, filename="log/server.log", filemode="a",
                        level=logging.INFO)
    dps = list()
    for deal_pair in config.init_deals:
        dps.append(PriceDiffTactic(deal_pair))
    logging.info("server start")
    while True:
        logging.info("start loop")
        for dp in dps:
            dp.run()
        time.sleep(config.deal_interval)

