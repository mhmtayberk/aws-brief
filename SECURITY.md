# Security Policy

## 🔒 Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in AWS-Brief, please report it responsibly.

### How to Report

**DO NOT** open a public issue for security vulnerabilities.

Instead, please email the maintainers at:
- **Email**: [Create a private security advisory on GitHub](https://github.com/mhmtayberk/aws-brief/security/advisories/new)

Or use GitHub's private vulnerability reporting feature.

### What to Include

Please include the following information:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** and severity assessment
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: 1-3 days
  - **High**: 1-2 weeks
  - **Medium**: 2-4 weeks
  - **Low**: Best effort

## 🛡️ Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅ Yes             |
| < 1.0   | ❌ No              |

We only support the latest version. Please update to the latest release before reporting issues.

## 🔐 Security Best Practices

### For Users

1. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Secure Your Credentials**
   - Never commit `.env` files
   - Use environment variables for secrets
   - Rotate API keys regularly

3. **Use HTTPS Only**
   - All feed URLs use HTTPS
   - Webhook URLs should use HTTPS

4. **Docker Security**
   - Run containers as non-root user (already configured)
   - Keep Docker images updated
   - Use official Python base images

5. **Database Security**
   - SQLite file permissions: `chmod 600 aws_brief.db`
   - Regular backups
   - No sensitive data in database

### For Contributors

1. **Code Review**
   - All PRs require review
   - Security-sensitive changes need extra scrutiny

2. **Dependency Management**
   - Pin dependency versions
   - Review dependency updates carefully
   - Use Dependabot alerts

3. **Input Validation**
   - Validate all external inputs
   - Sanitize HTML content
   - Use parameterized SQL queries (SQLAlchemy ORM)

4. **SSRF Protection**
   - URL whitelist validation (already implemented)
   - No arbitrary URL fetching

## 🚨 Known Security Features

### Implemented Protections

- ✅ **SSRF Protection**: URL whitelist validation
- ✅ **SQL Injection**: SQLAlchemy ORM (parameterized queries)
- ✅ **HTML Sanitization**: BeautifulSoup text extraction
- ✅ **Secret Management**: Pydantic SecretStr
- ✅ **Non-root Docker**: User `appuser` in container
- ✅ **Retry Mechanism**: Exponential backoff prevents DoS

### Security Considerations

- **AI API Keys**: Stored in environment variables, never logged
- **Webhook URLs**: Validated before use
- **Database**: Local SQLite, no network exposure
- **Feed Sources**: Whitelisted AWS domains only

## 📋 Security Checklist for PRs

Before submitting security-related PRs:

- [ ] No hardcoded credentials
- [ ] Input validation added
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies are up to date
- [ ] Tests include security scenarios
- [ ] Documentation updated

## 🔍 Vulnerability Disclosure

When a vulnerability is fixed:

1. **Private Fix**: Develop fix in private
2. **Security Advisory**: Publish GitHub security advisory
3. **Release**: Tag new version with fix
4. **Announcement**: Notify users via README/releases
5. **CVE**: Request CVE if applicable

## 📞 Contact

For security concerns:
- GitHub Security Advisories (preferred)
- Project maintainers via GitHub

Thank you for helping keep AWS-Brief secure! 🙏
