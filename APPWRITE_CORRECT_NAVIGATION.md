# 🎯 Correct Appwrite Navigation Guide

## Issue #1: Functions Are Not Named - Can't Identify Them

When you manually upload TAR.GZ files, Appwrite might create functions with generic names or IDs instead of meaningful names.

### How to Check Function Names:

1. **Go to Functions page:**
   ```
   https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
   ```

2. **What you should see:**
   - List of 16 functions
   - Each with a name like "get_transactions_streamlit" or just numbers/IDs

3. **If names are missing or generic:**
   - You need to rename them manually
   - OR the upload didn't work properly

### How to Rename Functions:

```
1. Click on a function (even if it's just an ID)
2. Click "Settings" at the top
3. Find "Name" field
4. Change to: get_transactions_streamlit (or appropriate name)
5. Click Save
6. Repeat for all 16 functions
```

### The 16 Function Names Should Be:

1. ✅ `get_transactions_streamlit`
2. ✅ `add_to_watchlist_streamlit`
3. ✅ `get_watchlist_streamlit`
4. ✅ `get_user_profile_streamlit`
5. ✅ `create_transaction`
6. ✅ `get_transactions`
7. ✅ `update_transaction`
8. ✅ `delete_transaction`
9. ✅ `add_to_watchlist`
10. ✅ `get_watchlist`
11. ✅ `remove_from_watchlist`
12. ✅ `get_auditlogs`
13. ✅ `create_payment`
14. ✅ `manage_roles`
15. ✅ `manage_permissions`
16. ✅ `get_bot_metrics`

---

## Issue #2: Wrong Settings Menu - You're in Project Settings!

You clicked "Settings" from the **bottom left** - that's **PROJECT settings**, not **FUNCTION settings**!

### ❌ WRONG PATH (What You Did):

```
Appwrite Console
└── Settings (bottom left, gear icon)
    └── Environment Variables
        └── Global Variables  ← This applies to ENTIRE PROJECT
            └── You pasted variables here (not ideal!)
```

**Problem:** Global Variables apply to your entire Appwrite project (all functions, databases, storage, etc.). While functions *might* be able to read them, it's not the correct place.

### ✅ CORRECT PATH (What You Should Do):

```
Appwrite Console
└── Functions (left sidebar)
    └── [Click on a SPECIFIC function name]
        └── Settings (top navigation bar)
            └── Configuration section
                └── Variables  ← This is where you add environment variables!
                    └── Add 4 variables for THIS function
```

### Visual Navigation Guide:

```
┌─────────────────────────────────────────────────────────────┐
│  Appwrite Console                                           │
│                                                             │
│  ┌───────────────┐  ┌─────────────────────────────────┐   │
│  │ Left Sidebar  │  │ Main Content Area                │   │
│  │               │  │                                   │   │
│  │ Overview      │  │                                   │   │
│  │ Auth          │  │                                   │   │
│  │ Databases     │  │                                   │   │
│  │ ► Functions ◄ │←─┤ CLICK HERE FIRST!                │   │
│  │ Storage       │  │                                   │   │
│  │               │  │ Then you'll see list of functions │   │
│  │               │  │                                   │   │
│  ├───────────────┤  │ 1. get_transactions_streamlit    │   │
│  │ Settings  ⚙   │  │ 2. add_to_watchlist_streamlit    │   │
│  │ (DON'T CLICK) │  │ 3. ...                            │   │
│  └───────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

STEP 1: Click "Functions" in left sidebar
STEP 2: Click on ONE specific function name (e.g., "get_transactions_streamlit")
STEP 3: Click "Settings" in the TOP navigation bar (not bottom left!)
STEP 4: Scroll to "Variables" section
STEP 5: Click "Add Variable"
STEP 6: Add each of the 4 variables
```

### Step-by-Step with Screenshots References:

**Step 1: Go to Functions**
- URL: https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
- You should see a list of all your functions

**Step 2: Click on ONE function**
- Example: Click "get_transactions_streamlit"
- URL changes to: .../functions/[function-id]

**Step 3: Top Navigation Bar**
- You'll see tabs: Overview | Settings | Deployments | Executions | Logs
- Click "Settings"

**Step 4: In Settings Page**
- Scroll down to "Configuration" section
- You'll see:
  - Name
  - Function ID
  - Runtime
  - **Variables** ← THIS IS WHAT YOU NEED!

**Step 5: Add Variables**
- Click "Add Variable" button
- Key: `APPWRITE_FUNCTION_ENDPOINT`
- Value: `https://fra.cloud.appwrite.io/v1`
- Click Save
- Repeat 3 more times for:
  - `APPWRITE_FUNCTION_PROJECT_ID`
  - `APPWRITE_API_KEY`
  - `APPWRITE_DATABASE_ID`

---

## Global Variables vs Function Variables

### Global Variables (What You Used):
- **Location:** Settings (bottom left) → Environment Variables → Global
- **Scope:** Entire Appwrite project
- **Use Case:** Values that ALL services need (rare)
- **Functions can read:** Maybe (depends on Appwrite version)
- **Recommended:** NO for function-specific config

### Function Variables (What You Should Use):
- **Location:** Functions → [Specific Function] → Settings → Variables
- **Scope:** Only that specific function
- **Use Case:** Function-specific configuration
- **Functions can read:** YES, always
- **Recommended:** YES for function environment variables

---

## What to Do Now

### Option A: Test if Global Variables Work

1. **Keep Global Variables** (you already added them)
2. **Test ONE function:**
   - Go to Functions → get_transactions_streamlit
   - Click "Execute" tab
   - Add test data:
     ```json
     {
       "user_id": "test123"
     }
     ```
   - Click "Execute"
3. **Check result:**
   - ✅ If it works: Great! Global Variables are accessible
   - ❌ If it fails: You need to add Function Variables

### Option B: Add Function Variables (Recommended)

Even if Global Variables work, best practice is Function Variables:

1. **For EACH of your 16 functions:**
   - Go to Functions → [Click function name]
   - Settings (top) → Variables
   - Add 4 variables (values from your terminal earlier)
   - Save

2. **Total entries:** 4 variables × 16 functions = 64 entries

---

## Quick Command Reference

### Check what's in Global Variables:
```
1. Settings (bottom left)
2. Environment Variables
3. Global Variables
4. You should see what you pasted
```

### Check what's in Function Variables:
```
1. Functions (left sidebar)
2. Click function name
3. Settings (top)
4. Variables section
5. Should see 4 variables per function (or empty if not added)
```

### Test a Function:
```
1. Functions → [function name]
2. Execute tab
3. Add JSON body
4. Click Execute
5. Check output/errors
```

---

## Your Specific Situation

Based on your message:
- ✅ You found Global Variables
- ✅ You added APPWRITE_DATABASE_ID and APPWRITE_API_KEY
- ❓ You're missing 2 variables: APPWRITE_FUNCTION_ENDPOINT and APPWRITE_FUNCTION_PROJECT_ID
- ❌ You haven't added Function Variables yet
- ❓ Function names might not be showing properly

### Immediate Next Steps:

1. **Complete Global Variables (add missing 2):**
   - Go back to Settings → Global Variables
   - Add Variable:
     - Key: `APPWRITE_FUNCTION_ENDPOINT`
     - Value: `https://fra.cloud.appwrite.io/v1`
   - Add Variable:
     - Key: `APPWRITE_FUNCTION_PROJECT_ID`
     - Value: `68869ef500017ca73772`

2. **Check function names:**
   - Go to Functions (left sidebar)
   - Take screenshot of what you see
   - If names are missing, rename them

3. **Test if Global Variables work:**
   - Try executing ONE function
   - If it works, you're done!
   - If it fails, add Function Variables

---

## Summary

**You made progress!** Global Variables might actually work. But:

1. ✅ Add the 2 missing variables to Global Variables
2. ✅ Check function names (rename if needed)
3. ✅ Test ONE function to see if it works
4. ⚠️ If fails, add Function Variables (correct approach)

**The key difference:** You were in Project Settings (Global), not Function Settings (Specific).
