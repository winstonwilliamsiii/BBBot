from frontend.utils.yahoo import fetch_portfolio_list, fetch_portfolio_tickers

url = 'https://finance.yahoo.com/portfolio/p_10/view/view_4'
print('Fetching portfolio list from root portfolio page...')
pl = fetch_portfolio_list('https://finance.yahoo.com/portfolio')
print('Found', len(pl), 'portfolios (sample 5):')
for p in pl[:5]:
    print(p)

print('\nFetching portfolios linked from specific view page:')
pl2 = fetch_portfolio_list(url)
print('Found', len(pl2), 'portfolios (sample 5):')
for p in pl2[:5]:
    print(p)

print('\nTrying to extract holdings from specific view URL...')
ht = fetch_portfolio_tickers(url)
print('Holdings found:', ht)
