import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
load_dotenv()
path = os.getenv('MT5_PATH')
print(f'Using path: {path}')
result = mt5.initialize(path=path, timeout=25000)
print(f'initialize: {result}, error: {mt5.last_error()}')
ok = False
if result:
    ok = mt5.login(login=531220202, password='*zH4!B5ZGB!8a', server='FTMO-Server3')
    print(f'login: {ok}, error: {mt5.last_error()}')
    mt5.shutdown()
