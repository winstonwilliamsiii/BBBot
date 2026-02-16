# Quick Migration Guide

## For Developers Using BBBot

The repository has been reorganized for better structure. Here's what changed and how to adapt:

## 🔄 Quick Reference

### Environment Setup
```bash
# OLD (before reorganization)
cp .env.example .env

# NEW (current)
cp config/env-templates/.env.example .env
```

### Running Tests
```bash
# OLD
python test_alpaca_bracket_order.py

# NEW
python tests/test_alpaca_bracket_order.py
# OR
pytest tests/test_alpaca_bracket_order.py
```

### Running Trading Scripts
```bash
# OLD
python place_turb_supx_orders.py

# NEW
python scripts/trading/place_turb_supx_orders.py
```

### Running Utility Scripts
```bash
# OLD
python quick_alpaca_test.py

# NEW
python scripts/utils/quick_alpaca_test.py
```

### Accessing Documentation
```bash
# OLD
less BRACKET_ORDER_DEPLOYMENT.md

# NEW
less docs/BRACKET_ORDER_DEPLOYMENT.md
```

## 📍 New File Locations

### Tests
| Old Location | New Location |
|-------------|--------------|
| `./test_alpaca_bracket_order.py` | `tests/test_alpaca_bracket_order.py` |
| `./test_kalshi_portfolio.py` | `tests/test_kalshi_portfolio.py` |
| `./test_production_bracket.py` | `tests/test_production_bracket.py` |

### Trading Scripts
| Old Location | New Location |
|-------------|--------------|
| `./place_turb_supx_orders.py` | `scripts/trading/place_turb_supx_orders.py` |
| `./cancel_duplicate_turb.py` | `scripts/trading/cancel_duplicate_turb.py` |
| `./cancel_spy_order.py` | `scripts/trading/cancel_spy_order.py` |
| `./fix_supx_protection.py` | `scripts/trading/fix_supx_protection.py` |

### Utility Scripts
| Old Location | New Location |
|-------------|--------------|
| `./quick_alpaca_test.py` | `scripts/utils/quick_alpaca_test.py` |
| `./display_portfolio.py` | `scripts/utils/display_portfolio.py` |
| `./Main.py` | `scripts/utils/Main.py` |

### Documentation
| Old Location | New Location |
|-------------|--------------|
| `./BRACKET_ORDER_DEPLOYMENT.md` | `docs/BRACKET_ORDER_DEPLOYMENT.md` |
| `./TONIGHT_MT5_SETUP.md` | `docs/TONIGHT_MT5_SETUP.md` |
| `./TURB_SUPX_ORDER_SUMMARY.md` | `docs/TURB_SUPX_ORDER_SUMMARY.md` |
| `./MAIN_BRANCH_BREAKING_ANALYSIS.md` | `docs/MAIN_BRANCH_BREAKING_ANALYSIS.md` |

### Environment Templates
| Old Location | New Location |
|-------------|--------------|
| `./.env.example` | `config/env-templates/.env.example` |
| `./.env.template` | `config/env-templates/.env.template` |
| `./.env.brokers.example` | `config/env-templates/.env.brokers.example` |
| `./.env.development.example` | `config/env-templates/.env.development.example` |
| `./.env.production.example` | `config/env-templates/.env.production.example` |
| _...and 7 more env files_ | `config/env-templates/` |

## 🆕 New README Files

Added comprehensive README files in organized directories:

- **`config/env-templates/README.md`** - How to use environment templates
- **`scripts/trading/README.md`** - Trading scripts documentation
- **`scripts/utils/README.md`** - Utility scripts documentation
- **`docs/FILE_REORGANIZATION_SUMMARY.md`** - Complete reorganization details

## ✅ No Breaking Changes

**Good News:** All files still work exactly the same way, they're just in more logical locations!

- ✅ No code changes required
- ✅ No import paths changed
- ✅ No functionality affected
- ✅ Just update your commands to point to new paths

## 💡 Tips

1. **Update your bookmarks** to point to new file locations
2. **Check README files** in each directory for usage guides
3. **Update any local scripts** that reference old paths
4. **Bookmark this guide** for quick reference during transition

## 🆘 Need Help?

If you encounter any issues with the new structure:
1. Check the README in the relevant directory
2. See `docs/FILE_REORGANIZATION_SUMMARY.md` for complete details
3. Contact the development team

---

**Last Updated:** February 16, 2026  
**PR:** copilot/organize-repo-file-structure
