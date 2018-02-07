from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient()
autodeal = client.autodeal


tactics = sorted(autodeal.deal.distinct("tactic"))

for t in tactics:
    if issubclass(t, unicode):
        symbol = t.decode()
    else:
        symbol = t
    print("%s: waiting:%d, succeed:%d, failed:%d." % (
        symbol,
        autodeal.deal.find({"tactic": {"$eq": t},
                            "status": {"$eq": "waiting"}}).count(),
        autodeal.deal.find({"tactic": {"$eq":  t},
                            "status": {"$eq": "succeed"}}).count(),
        autodeal.deal.find({"tactic": {"$eq": t},
                            "status": {"$eq": "failed"}}).count(),
                                                       ))

# succeed earning
print ("\n total earning \n")
for t in tactics:
    if issubclass(t, unicode):
        symbol = t.decode()
    else:
        symbol = t
    strs = symbol.split('-')
    goods = strs[0]
    money = strs[1]

    deals = list(autodeal.deal.find({"tactic": {"$eq": t},
                                    "status": {"$eq": "succeed"}}))
    earn_goods = 0
    earn_money = 0
    for d in deals:
        buy_price = float(d['buy_price'])
        sell_price = float(d['sell_price'])
        buy_amount = float(d['buy_amount'])
        sell_amount = float(d['sell_amount'])

        earn_goods += buy_amount - sell_amount
        earn_money += sell_amount * sell_price - buy_amount * buy_price

    print("%s: %s:%.4f, %s:%.4f." % (symbol, goods, earn_goods, money, earn_money))


# earning in 24hr
print ("\n earning in 24hr \n")
for t in tactics:
    symbol = t.decode()
    strs = symbol.split('-')
    goods = strs[0]
    money = strs[1]

    deals = list(autodeal.deal.find({"tactic": {"$eq": t},
                                    "status": {"$eq": "succeed"},
                                     "finish_time": {"$gt": datetime.utcnow() - timedelta(days=1)}}))
    earn_goods = 0
    earn_money = 0
    for d in deals:
        buy_price = float(d['buy_price'])
        sell_price = float(d['sell_price'])
        buy_amount = float(d['buy_amount'])
        sell_amount = float(d['sell_amount'])

        earn_goods += buy_amount - sell_amount
        earn_money += sell_amount * sell_price - buy_amount * buy_price

    print("%s: %s:%.4f, %s:%.4f." % (symbol, goods, earn_goods, money, earn_money))


# total failed
print ("\n total failed \n")
for t in tactics:
    symbol = t.decode()
    strs = symbol.split('-')
    goods = strs[0]
    money = strs[1]

    deals = list(autodeal.deal.find({"tactic": {"$eq": t},
                                    "status": {"$eq": "failed"}}))
    earn_goods = 0
    earn_money = 0
    for d in deals:
        buy_price = float(d['buy_price'])
        sell_price = float(d['sell_price'])
        buy_amount = float(d['buy_amount'])
        sell_amount = float(d['sell_amount'])

        # order1 sell
        if d['order1_finished']:
            earn_goods -= sell_amount
            earn_money += sell_amount * sell_price
        # order2 buy
        if d['order2_finished']:
            earn_goods += buy_amount
            earn_money -= buy_amount * buy_price

    print("%s: %s:%.4f, %s:%.4f." % (symbol, goods, earn_goods, money, earn_money))

# failed in 24hr
print ("\n failed in 24hr \n")
for t in tactics:
    symbol = t.decode()
    strs = symbol.split('-')
    goods = strs[0]
    money = strs[1]

    deals = list(autodeal.deal.find({"tactic": {"$eq": t},
                                    "status": {"$eq": "failed"},
                                     "finish_time": {"$gt": datetime.utcnow() - timedelta(days=1)}}))
    earn_goods = 0
    earn_money = 0
    for d in deals:
        buy_price = float(d['buy_price'])
        sell_price = float(d['sell_price'])
        buy_amount = float(d['buy_amount'])
        sell_amount = float(d['sell_amount'])

        # order1 sell
        if d['order1_finished']:
            earn_goods -= sell_amount
            earn_money += sell_amount * sell_price
        # order2 buy
        if d['order2_finished']:
            earn_goods += buy_amount
            earn_money -= buy_amount * buy_price

    print("%s: %s:%.4f, %s:%.4f." % (symbol, goods, earn_goods, money, earn_money))


