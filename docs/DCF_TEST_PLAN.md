# DCF Analysis - Quick Test Plan

## 🎯 Quick Test Checklist

### Database Setup Test
- [ ] Run: `python scripts/setup_dcf_db.py`
- [ ] Enter MySQL password when prompted
- [ ] Verify output shows: "✅ SUCCESS! DCF Database Setup Complete"
- [ ] Check row counts: fundamentals_annual (10 rows), prices_latest (2 rows)

### Single Ticker Test
- [ ] Start app: `streamlit run streamlit_app.py`
- [ ] Navigate to "📊 Fundamental Analysis" section
- [ ] Mode: "Single Ticker" (default)
- [ ] Enter: `AAPL`
- [ ] Click "🔬 Run DCF Analysis"
- [ ] Verify: Analysis completes, shows valuation badge

### CSV Upload Test
- [ ] Switch to: "CSV Upload (Batch)" mode
- [ ] Click: "📥 Download CSV Template"
- [ ] Upload the downloaded template
- [ ] Verify: Preview shows 5 tickers (AAPL, MSFT, GOOGL, AMZN, TSLA)
- [ ] Click: "🔬 Run Batch DCF Analysis"
- [ ] Verify: Progress bar completes, results table shows
- [ ] Test: Click "📥 Download DCF Results CSV"

### Sidebar Login Test
- [ ] Check sidebar structure:
  - "🔐 Personal Budget Login" section appears
  - Located ABOVE "Mansa Capital Funds" section
- [ ] Expand "🔑 Login" if not logged in
- [ ] Verify login form is visible and functional

### Error Handling Test
- [ ] Enter invalid ticker: `INVALID123`
- [ ] Verify: Graceful error message (not crash)
- [ ] Upload CSV with missing Ticker column
- [ ] Verify: Error message about required column

## ✅ Pass Criteria

All tests pass if:
1. Database setup completes without errors
2. Single ticker analysis works for AAPL and MSFT
3. CSV upload processes at least 2 tickers successfully
4. Login section visible above Mansa Funds
5. No application crashes on invalid input

## 🐛 Known Test Failures

### Expected Failures (Not Issues)
- Tickers not in database will fail (GOOGL, AMZN, TSLA in template)
- This is expected behavior - only AAPL and MSFT have sample data
- Test will show partial success (2/5 succeed, 3/5 error)

### How to Fix for Full Success
1. Add more ticker data to database
2. Or edit template to only include AAPL, MSFT

## 📊 Test Results Template

```markdown
## Test Run: [Date/Time]

### Environment
- OS: Windows
- Python: [version]
- MySQL: [version]
- Branch: dev

### Results
| Test | Status | Notes |
|------|--------|-------|
| Database Setup | ✅ / ❌ | |
| Single Ticker (AAPL) | ✅ / ❌ | |
| Single Ticker (MSFT) | ✅ / ❌ | |
| CSV Upload | ✅ / ❌ | |
| Sidebar Login Positioning | ✅ / ❌ | |
| Error Handling | ✅ / ❌ | |

### Issues Found
[List any issues discovered]

### Screenshots
[Attach relevant screenshots]
```

---

**Created:** February 16, 2026  
**Version:** 1.0.0
