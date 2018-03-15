# -*- coding: utf-8 -*-

import os
import sys
work_dir = os.path.abspath(os.path.join(__file__, os.pardir)) + '/'


deal_interval = 6 * 60

# name, goods, money, bid_gap, bid_goal, k_size, k_period, max_deal_num, deal_size, expired(minute)
init_deals = [
    ["eth-usdt-1", "eth", "usdt", 0.1, 0.90, 8, "60min", 3, 1, 3*24*60],
    ["eos-usdt-1", "eos", "usdt", 0.1, 0.90, 8, "60min", 3, 1, 3*24*60],
    ["iost-usdt-1", "iost", "usdt", 0.1, 0.90, 8, "60min", 2, 1, 3*24*60],
    ["dta-usdt-1", "dta", "usdt", 0.1, 0.90, 8, "60min", 2, 1, 3*24*60],

    ["eth-usdt-small", "eth", "usdt", 0.04, 0.80, 12, "60min", 8, 1, 24*60],
    ["eos-usdt-small", "eos", "usdt", 0.04, 0.80, 12, "60min", 8, 1, 24*60],
    ["iost-usdt-small", "iost", "usdt", 0.04, 0.80, 12, "60min", 2, 1, 24*60],
    ["dta-usdt-small", "dta", "usdt", 0.04, 0.80, 12, "60min", 2, 1, 24*60],
    ["bch-usdt-small", "bch", "usdt", 0.04, 0.80, 12, "60min", 2, 2, 24*60],

    ["eth-usdt-small-short", "eth", "usdt", 0.04, 0.60, 12, "60min", 2, 1, 6*60],
    ["eos-usdt-small-short", "eos", "usdt", 0.04, 0.60, 12, "60min", 2, 1, 6*60],
    ["iost-usdt-small-short", "iost", "usdt", 0.04, 0.60, 12, "60min", 1, 1, 6*60],
    ["dta-usdt-small-short", "dta", "usdt", 0.04, 0.60, 12, "60min", 1, 1, 6*60],
    ["bch-usdt-small-short", "bch", "usdt", 0.04, 0.60, 12, "60min", 1, 2, 6*60],

    ["eth-usdt-fast", "eth", "usdt", 0.06, 0.70, 4, "60min", 3, 1, 3*24*60],
    ["eos-usdt-fast", "eos", "usdt", 0.06, 0.70, 4, "60min", 3, 1, 3*24*60],
    ["iost-usdt-fast", "iost", "usdt", 0.06, 0.70, 4, "60min", 2, 1, 3*24*60],
    ["dta-usdt-fast", "dta", "usdt", 0.06, 0.70, 4, "60min", 2, 1, 3*24*60],

    ["eth-usdt-tiny-short", "eth", "usdt", 0.02, 0.60, 12, "60min", 2, 1, 6*60],
    ["eos-usdt-tiny-short", "eos", "usdt", 0.02, 0.60, 12, "60min", 2, 1, 6*60],
    ["iost-usdt-tiny-short", "iost", "usdt", 0.02, 0.60, 12, "60min", 1, 1, 6*60],
    ["dta-usdt-tiny-short", "dta", "usdt", 0.02, 0.60, 12, "60min", 1, 1, 6*60],
    ["bch-usdt-tiny-short", "bch", "usdt", 0.02, 0.60, 12, "60min", 1, 2, 6*60],

    # ["eth-usdt-fast-2", "eth", "usdt", 0.05, 0.85, 8, "60min", 3, 1],
    # ["eos-usdt-fast-2", "eos", "usdt", 0.05, 0.85, 8, "60min", 3, 1],
    # ["iost-usdt-fast-2", "iost", "usdt", 0.05, 0.85, 8, "60min", 2, 1],
    # ["dta-usdt-fast-2", "dta", "usdt", 0.05, 0.85, 8, "60min", 2, 1],
    #
    # ["eth-usdt-fast-3", "eth", "usdt", 0.05, 0.95, 4, "60min", 10, 1],
    # ["eos-usdt-fast-3", "eos", "usdt", 0.05, 0.95, 4, "60min", 10, 1],
    #
    # ["eth-usdt-fast-4", "eth", "usdt", 0.05, 0.85, 2, "60min", 10, 1],
    # ["eos-usdt-fast-4", "eos", "usdt", 0.05, 0.85, 2, "60min", 10, 1],
    #
    # ["eth-usdt-fast-5", "eth", "usdt", 0.05, 0.95, 2, "60min", 10, 1],
    # ["eos-usdt-fast-5", "eos", "usdt", 0.05, 0.95, 2, "60min", 10, 1],

]

# goods unit, money unit
price_unit = {
    "ethusdt": ["%.4f", "%.2f"],
    "eosusdt": ["%.4f", "%.2f"],
    "bchusdt": ["%.4f", "%.2f"],
    "iostusdt": ["%.4f", "%.4f"],
    "dtausdt": ["%.4f", "%.4f"],
    "eoseth": ["%.2f", "%.8f"],
}
