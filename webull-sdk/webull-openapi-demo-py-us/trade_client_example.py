# -*- coding: utf-8 -*-

import json
import sys
import uuid
from time import sleep

from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

# The current example uses the Webull US test environment URL and account.
# Please update the configuration according to your actual setup when using it.
optional_api_endpoint = "us-openapi-alb.uat.webullbroker.com"
your_app_key = "eecbf4489f460ad2f7aecef37b267618"
your_app_secret = "8abf920a9cc3cb7af3ea5e9e03850692"
region_id = "us"
api_client = ApiClient(your_app_key, your_app_secret, region_id)
api_client.add_endpoint(region_id, optional_api_endpoint)


if __name__ == '__main__':
    trade_client = TradeClient(api_client)

    # [Note] In the test example, the first account ID returned by the query is used by default for subsequent tests.
    # In a real scenario, you should select and set the desired account_id yourself.
    account_id = None
    res = trade_client.account_v2.get_account_list()
    if res.status_code == 200:
        print('get account list:', res.json())
        account_id = res.json()[0].get('account_id') if res.json() else None
        if not account_id:
            print('Interrupting test process: account_id not found.')
            sys.exit(0)
        else:
            print('get first account_id:', account_id)

    # Query account balance
    res = trade_client.account_v2.get_account_balance(account_id)
    if res.status_code == 200:
        print('get account balance res:', res.json())

    # Query account positions
    res = trade_client.account_v2.get_account_position(account_id)
    if res.status_code == 200:
        print('get account position res:', res.json())

    # normal equity
    normal_equity_client_order_id = uuid.uuid4().hex
    print('normal equity client order id:', normal_equity_client_order_id)
    new_normal_equity_orders = [
        {
            "combo_type": "NORMAL",
            "client_order_id": normal_equity_client_order_id,
            "symbol": "BULL",
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": "LIMIT",
            "limit_price": "7",
            "quantity": "1",
            "support_trading_session": "CORE",
            "side": "BUY",
            "time_in_force": "DAY",
            "entrust_type": "QTY"
        }
    ]

    res = trade_client.order_v2.preview_order(account_id, new_normal_equity_orders)
    if res.status_code == 200:
        print('preview normal equity res:', res.json())

    res = trade_client.order_v2.place_order(account_id, new_normal_equity_orders)
    if res.status_code == 200:
        print('place normal equity res:', res.json())
    sleep(3)

    modify_normal_orders = [
        {
            "client_order_id": normal_equity_client_order_id,
            "quantity": "2",
            "limit_price": "200"
        }
    ]
    res = trade_client.order_v2.replace_order(account_id, modify_normal_orders)
    if res.status_code == 200:
        print('replace normal equity res:', res.json())
    sleep(3)

    res = trade_client.order_v2.get_order_open(account_id=account_id)
    if res.status_code == 200:
        print("order open res:" + json.dumps(res.json(), indent=4))

    res = trade_client.order_v2.cancel_order(account_id, normal_equity_client_order_id)
    if res.status_code == 200:
        print('cancel normal equity res:', res.json())

    res = trade_client.order_v2.get_order_detail(account_id, normal_equity_client_order_id)
    if res.status_code == 200:
        print('get normal equity detail res:', res.json())


    # combo equity
    master_client_order_id = uuid.uuid4().hex
    stop_profit_client_order_id = uuid.uuid4().hex
    stop_loss_client_order_id = uuid.uuid4().hex
    print('master_client_order_id:', master_client_order_id)
    print('stop_profit_client_order_id:', stop_profit_client_order_id)
    print('stop_loss_client_order_id:', stop_loss_client_order_id)
    new_combo_orders = [
        {
            "client_order_id": master_client_order_id,
            "combo_type": "MASTER",
            "symbol": "BULL",
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": "LIMIT",
            "quantity": "1",
            "support_trading_session": "CORE",
            "limit_price": "10.5",
            "side": "BUY",
            "entrust_type": "QTY",
            "time_in_force": "DAY"
        },
        {
            "client_order_id": stop_profit_client_order_id,
            "combo_type": "STOP_PROFIT",
            "symbol": "BULL",
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": "LIMIT",
            "quantity": "1",
            "support_trading_session": "CORE",
            "limit_price": "11.5",
            "side": "SELL",
            "entrust_type": "QTY",
            "time_in_force": "DAY"
        },
        {
            "client_order_id": stop_loss_client_order_id,
            "combo_type": "STOP_LOSS",
            "symbol": "BULL",
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": "STOP_LOSS",
            "quantity": "1",
            "support_trading_session": "CORE",
            "stop_price": "10",
            "side": "SELL",
            "entrust_type": "QTY",
            "time_in_force": "DAY"
        }
    ]

    res = trade_client.order_v2.place_order(account_id, new_combo_orders)
    if res.status_code == 200:
        print('place combo order res:', res.json())



    # normal option
    new_normal_option_client_order_id = uuid.uuid4().hex
    new_normal_option_orders = [
        {
            "client_order_id": new_normal_option_client_order_id,
            "combo_type": "NORMAL",
            "order_type": "LIMIT",
            "quantity": "1",
            "limit_price": "1.5",
            "option_strategy": "SINGLE",
            "side": "BUY",
            "time_in_force": "DAY",
            "entrust_type": "QTY",
            "legs": [
                {
                    "side": "BUY",
                    "quantity": "1",
                    "symbol": "AAPL",
                    "strike_price": "220",
                    "option_expire_date": "2026-02-20",
                    "instrument_type": "OPTION",
                    "option_type": "CALL",
                    "market": "US"
                }
            ]
        }
    ]

    # preview
    res = trade_client.order_v2.preview_option(account_id, new_normal_option_orders)
    if res.status_code == 200:
        print("preview normal option res:" + json.dumps(res.json(), indent=4))

    # place
    res = trade_client.order_v2.place_option(account_id, new_normal_option_orders)
    if res.status_code == 200:
        print("place normal option res:" + json.dumps(res.json(), indent=4))
    sleep(3)

    # cancel
    res = trade_client.order_v2.cancel_option(account_id, new_normal_option_client_order_id)
    if res.status_code == 200:
        print("cancel normal option res:" + json.dumps(res.json(), indent=4))
    sleep(3)