# Security Policy

## 🛡️ Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## 🚨 Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly:

### 📧 Email

Send an email to: **security@aegis-box.dev**

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### 🔒 What to Expect

- **Response Time**: We will acknowledge your report within 48 hours
- **Updates**: We will keep you informed about our progress
- **Disclosure**: We will coordinate with you on public disclosure timing
- **Credit**: We will credit you in our security advisory (unless you prefer to remain anonymous)

### 🎯 Scope

Security vulnerabilities we're particularly interested in:

#### High Priority

- **Code Injection**: Vulnerabilities in patch application or AST parsing
- **Path Traversal**: Issues that could access files outside the project directory
- **Command Injection**: Vulnerabilities in Git operations or shell commands
- **Arbitrary Code Execution**: Any way to execute arbitrary code
- **Credential Leakage**: Issues that could expose API keys or secrets

#### Medium Priority

- **Denial of Service**: Resource exhaustion or infinite loops
- **Information Disclosure**: Leaking sensitive information in logs or errors
- **Access Control**: Bypassing file ignore rules or permissions

#### Out of Scope

- **Social Engineering**: Phishing attacks or user manipulation
- **Third-Party Dependencies**: Vulnerabilities in upstream packages (report to them first)
- **Theoretical Attacks**: Issues with no practical impact

## 🔐 Security Best Practices for Users

### API Key Protection

```yaml
# ❌ DON'T: Hardcode API keys
llm:
  tier1_fast:
    api_key: "sk-ant-xxxxx"

# ✅ DO: Use environment variables
llm:
  tier1_fast:
    api_key_env_var: "ANTHROPIC_API_KEY"
```

### File Ignore Rules

```yaml
# Always ignore sensitive directories
ignore_dirs:
  - ".git"
  - "secrets"
  - "proprietary"
  - "customer_data"

ignore_files:
  - "*.key"
  - "*.pem"
  - "*_secret.*"
```

### Git Sandbox

Always enable Git sandbox for automated patching:

```yaml
git:
  auto_stash: true
  verify_syntax: true
```

### Privacy

Review what gets sent to LLMs:

```bash
# Enable debug mode to see what's transmitted
export AEGIS_DEBUG=1
aegis run --auto

# Check logs
cat artifacts/llm_requests.log
```

## 🏆 Security Hall of Fame

We thank the following security researchers for responsibly disclosing vulnerabilities:

_No reports yet. Be the first!_

## 📜 Security Updates

Subscribe to security advisories:

- 🐙 **GitHub**: Watch the repo and enable security alerts
- 📧 **Email**: Subscribe to our security mailing list (security-announce@aegis-box.dev)

## 🔍 Security Audits

- **Last Audit**: Not yet conducted
- **Next Planned Audit**: Q4 2026

We welcome independent security audits. Please contact us at security@aegis-box.dev if you're interested in auditing Aegis Box.

## 🛡️ Our Commitment

- **Transparency**: We will publicly disclose all security vulnerabilities (after fixing)
- **Speed**: Critical vulnerabilities will be patched within 7 days
- **Communication**: We will keep reporters informed throughout the process
- **Recognition**: We will credit all security researchers (with permission)

---

**🛡️ Security is a core value of Aegis Box. Thank you for helping keep our users safe.**
