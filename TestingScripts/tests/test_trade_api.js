#!/usr/bin/env node
/**
 * Trade API Integration Test
 * Tests the /api/trade endpoint with various order types
 */

const API_URL = process.env.API_URL || 'http://localhost:3000/api/trade'
const TEST_MODE = process.env.TEST_MODE || 'paper' // paper or mock

console.log('=' .repeat(60))
console.log('TRADE API INTEGRATION TEST')
console.log('=' .repeat(60))
console.log(`API URL: ${API_URL}`)
console.log(`Test Mode: ${TEST_MODE}`)
console.log()

// Test cases
const testCases = [
  {
    name: 'Simple Market Buy',
    payload: {
      class: 'equities',
      symbol: 'SPY',
      qty: 1,
      side: 'buy'
    }
  },
  {
    name: 'Limit Order',
    payload: {
      class: 'equities',
      symbol: 'AAPL',
      qty: 5,
      side: 'buy',
      params: {
        type: 'limit',
        limit_price: 150.00,
        time_in_force: 'day'
      }
    }
  },
  {
    name: 'Stop Loss Order',
    payload: {
      class: 'equities',
      symbol: 'TSLA',
      qty: 2,
      side: 'sell',
      params: {
        type: 'stop',
        stop_price: 240.00,
        time_in_force: 'gtc'
      }
    }
  },
  {
    name: 'Trailing Stop Order',
    payload: {
      class: 'equities',
      symbol: 'NVDA',
      qty: 3,
      side: 'sell',
      params: {
        type: 'trailing_stop',
        trail_percent: 2.0,
        time_in_force: 'gtc'
      }
    }
  },
  {
    name: 'Extended Hours Order',
    payload: {
      class: 'equities',
      symbol: 'QQQ',
      qty: 10,
      side: 'buy',
      params: {
        type: 'limit',
        limit_price: 400.00,
        time_in_force: 'day',
        extended_hours: true
      }
    }
  }
]

// Validation test cases (should fail)
const validationCases = [
  {
    name: 'Missing Symbol',
    payload: {
      class: 'equities',
      qty: 1,
      side: 'buy'
    },
    expectedError: 'Invalid asset payload'
  },
  {
    name: 'Invalid Quantity',
    payload: {
      class: 'equities',
      symbol: 'AAPL',
      qty: -5,
      side: 'buy'
    },
    expectedError: 'Invalid quantity'
  },
  {
    name: 'Invalid Side',
    payload: {
      class: 'equities',
      symbol: 'AAPL',
      qty: 1,
      side: 'long'
    },
    expectedError: 'Invalid side'
  }
]

async function testTradeAPI(testCase, expectError = false) {
  console.log(`\n${'='.repeat(60)}`)
  console.log(`TEST: ${testCase.name}`)
  console.log('='.repeat(60))
  console.log('Payload:', JSON.stringify(testCase.payload, null, 2))

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testCase.payload)
    })

    const data = await response.json()

    if (expectError) {
      if (response.status >= 400) {
        console.log(`✅ Expected error received (${response.status})`)
        console.log('Error:', data.error)
        if (testCase.expectedError && !data.error.includes(testCase.expectedError)) {
          console.log(`⚠️  Expected error message containing "${testCase.expectedError}"`)
        }
        return { success: true, data }
      } else {
        console.log(`❌ Expected error but got success (${response.status})`)
        return { success: false, data }
      }
    }

    if (response.ok) {
      console.log(`✅ Success (${response.status})`)
      console.log('Response:', JSON.stringify(data, null, 2))
      
      // Validate response structure
      const required = ['broker', 'status', 'symbol', 'side', 'qty', 'timestamp']
      const missing = required.filter(field => !(field in data))
      
      if (missing.length > 0) {
        console.log(`⚠️  Missing required fields: ${missing.join(', ')}`)
      }
      
      // Check if order was accepted
      if (data.status === 'stubbed') {
        console.log('ℹ️  Broker adapter is stubbed (not yet implemented)')
      } else if (data.orderId) {
        console.log(`✅ Order placed successfully - ID: ${data.orderId}`)
      }
      
      return { success: true, data }
    } else {
      console.log(`❌ Failed (${response.status})`)
      console.log('Error:', JSON.stringify(data, null, 2))
      return { success: false, data }
    }

  } catch (error) {
    console.log(`❌ Request failed: ${error.message}`)
    return { success: false, error: error.message }
  }
}

async function runTests() {
  let passed = 0
  let failed = 0

  // Test valid orders
  console.log('\n' + '='.repeat(60))
  console.log('VALID ORDER TESTS')
  console.log('='.repeat(60))

  for (const testCase of testCases) {
    const result = await testTradeAPI(testCase, false)
    if (result.success) {
      passed++
    } else {
      failed++
    }
    await new Promise(resolve => setTimeout(resolve, 500)) // Rate limiting
  }

  // Test validation
  console.log('\n' + '='.repeat(60))
  console.log('VALIDATION TESTS (Expected Failures)')
  console.log('='.repeat(60))

  for (const testCase of validationCases) {
    const result = await testTradeAPI(testCase, true)
    if (result.success) {
      passed++
    } else {
      failed++
    }
    await new Promise(resolve => setTimeout(resolve, 500))
  }

  // Summary
  console.log('\n' + '='.repeat(60))
  console.log('TEST SUMMARY')
  console.log('='.repeat(60))
  console.log(`Total Tests: ${passed + failed}`)
  console.log(`✅ Passed: ${passed}`)
  console.log(`❌ Failed: ${failed}`)
  console.log(`Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`)
  console.log()

  process.exit(failed > 0 ? 1 : 0)
}

// Check if API is available
async function checkAPIHealth() {
  console.log('Checking API health...')
  
  try {
    const response = await fetch(API_URL.replace('/trade', '/health').replace('/api/trade', '/api/health'), {
      method: 'GET'
    })
    
    if (response.ok) {
      console.log('✅ API is healthy\n')
      return true
    } else {
      console.log('⚠️  API health check returned non-200 status\n')
      return true // Continue anyway
    }
  } catch (error) {
    console.log(`⚠️  API health check failed: ${error.message}`)
    console.log('Continuing with tests anyway...\n')
    return true
  }
}

// Run tests
(async () => {
  await checkAPIHealth()
  await runTests()
})()
