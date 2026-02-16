# Changelog

All notable changes to the Bentley Budget Bot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production environment configuration files
- Development environment configuration files
- GitHub Actions workflow validation for conventional commits
- Multi-stage deployment pipeline (dev → staging → main)

### Changed
- Improved database connection handling for trading bot
- Enhanced production deployment workflow

### Fixed
- Trading bot database connection issues
- Production deployment configuration

## [1.0.0] - 2026-02-10

### Added
- Initial production deployment to Streamlit Cloud (bbbot305.streamlit.app)
- Yahoo Finance integration for real-time portfolio data
- CSV portfolio upload functionality
- Multi-platform deployment support (Docker + Vercel)
- Comprehensive CI/CD pipeline with GitHub Actions
- Security audit and secrets scanning
- Production readiness validation
- Automated testing and linting

### Security
- Environment-based credential management
- SSL/TLS enforcement for production
- API key protection and validation
- Secrets scanning in CI/CD pipeline
