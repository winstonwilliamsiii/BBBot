import sys
sys.path.insert(0, '.')
from scripts.broadcast_all_bot_signals import ALL_BOTS, _load_bot_symbols, _pick_symbol
from frontend.utils.cosmic_signal import run_cosmic_engine_for_bot

for bot in ALL_BOTS:
    try:
        syms = _load_bot_symbols(bot)
        chosen, usize, src = _pick_symbol(bot, syms, None)
        result = run_cosmic_engine_for_bot(bot, mode='paper', symbol=chosen)
        heads = result['analytic_heads']
        print(f"{bot:10s} sym={result['symbol']:6s} src={str(result['data_source']):8s} score={result['cosmic_score']:+.4f} dec={result['decision']:5s} Mom={heads['Momentum']:+.3f} RSI={heads['RSI']:+.3f} Vol={heads['Volatility']:+.3f} Liq={heads['Liquidity']:+.3f} MLC={heads['ML_Confidence']:+.3f}")
    except Exception as e:
        print(f'{bot:10s} FAILED: {e}')
