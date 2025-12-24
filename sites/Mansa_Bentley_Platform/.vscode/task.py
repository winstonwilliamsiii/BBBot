from celery_app import celery_app
from broker_api import execute_trade

@celery_app.task
def async_execute_trade(broker, symbol, side, quantity):
    return execute_trade(broker, symbol, side, quantity)