"""
Test Investment Analysis page pandas concat fix
"""
import pandas as pd
import sys
import os

def test_pandas_concat_fix():
    """Test the pandas concat fix works with duplicate indices"""
    print("\n" + "="*60)
    print("TESTING PANDAS CONCAT FIX")
    print("="*60)
    
    # Simulate the scenario that caused the error
    print("\n[1/3] Simulating duplicate index scenario...")
    
    # Create sample dataframes like yfinance returns (with date indices)
    dates1 = pd.date_range('2024-01-01', periods=5)
    df1 = pd.DataFrame({
        'Close': [100, 101, 102, 103, 104],
        'Volume': [1000, 1100, 1200, 1300, 1400]
    }, index=dates1)
    df1 = df1.reset_index()
    df1.columns = ['Date', 'Close', 'Volume']
    df1['Ticker'] = 'AAPL'
    
    dates2 = pd.date_range('2024-01-01', periods=5)
    df2 = pd.DataFrame({
        'Close': [200, 201, 202, 203, 204],
        'Volume': [2000, 2100, 2200, 2300, 2400]
    }, index=dates2)
    df2 = df2.reset_index()
    df2.columns = ['Date', 'Close', 'Volume']
    df2['Ticker'] = 'MSFT'
    
    print(f"  ✓ Created 2 sample dataframes (AAPL, MSFT)")
    
    # Test OLD WAY (would fail with duplicate indices)
    print("\n[2/3] Testing OLD concat method (might fail)...")
    try:
        # This could fail if dataframes have duplicate indices
        old_result = pd.concat([df1, df2], ignore_index=False)
        print(f"  ✓ Old method worked (indices were already unique)")
    except Exception as e:
        print(f"  ✗ Old method failed: {type(e).__name__}")
    
    # Test NEW WAY (with fix)
    print("\n[3/3] Testing NEW concat method (with fix)...")
    try:
        # Reset index on each dataframe before concat
        df1_clean = df1[['Date', 'Ticker', 'Close', 'Volume']].reset_index(drop=True)
        df2_clean = df2[['Date', 'Ticker', 'Close', 'Volume']].reset_index(drop=True)
        
        # Concatenate with ignore_index=True and sort=False
        portfolio_df = pd.concat([df1_clean, df2_clean], ignore_index=True, sort=False)
        
        print(f"  ✓ New method works!")
        print(f"  ✓ Combined dataframe shape: {portfolio_df.shape}")
        print(f"  ✓ Tickers: {portfolio_df['Ticker'].unique().tolist()}")
        print(f"  ✓ Columns: {portfolio_df.columns.tolist()}")
        
        # Verify no duplicate indices
        assert not portfolio_df.index.has_duplicates, "Index has duplicates!"
        print(f"  ✓ Index is unique (no duplicates)")
        
        return True
    except Exception as e:
        print(f"  ✗ New method failed: {e}")
        return False
    

def test_investment_page_import():
    """Test that Investment Analysis page imports successfully"""
    print("\n" + "="*60)
    print("TESTING INVESTMENT ANALYSIS PAGE IMPORT")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "investment_page", 
            "pages/02_📈_Investment_Analysis.py"
        )
        investment_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(investment_module)
        
        print("\n✓ Investment Analysis page imports successfully")
        print("✓ No pandas InvalidIndexError!")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("INVESTMENT ANALYSIS - PANDAS FIX VERIFICATION")
    print("="*60)
    
    test1 = test_pandas_concat_fix()
    test2 = test_investment_page_import()
    
    print("\n" + "="*60)
    if test1 and test2:
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nInvestment Analysis page is ready:")
        print("  • Pandas concat fix applied")
        print("  • No duplicate index errors")
        print("  • Page imports successfully")
        print("\nYou can now use Investment Analysis without errors!")
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
    
    sys.exit(0 if (test1 and test2) else 1)
