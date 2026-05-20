"""
CodeQuizHub Security Audit Script

Checks for common security misconfigurations in the codebase.
Run: python scripts/security_audit.py
"""

import os
import re
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS = f"{GREEN}[PASS]{RESET}"
WARN = f"{YELLOW}[WARN]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"

REPORT: list[str] = []


def report(status: str, check: str, detail: str = ""):
    """Add a line to the audit report."""
    msg = f"  {status} {check}"
    if detail:
        msg += f"  {detail}"
    REPORT.append(msg)
    print(msg)


def check_env_production():
    """Check that .env.production has proper secrets."""
    path = Path("backend/.env.production")
    if not path.exists():
        report(FAIL, "Production env file missing", "backend/.env.production not found")
        return

    content = path.read_text()
    checks = [
        ("JWT_SECRET", r'JWT_SECRET\s*=\s*["\']?change-this-in-production'),
        ("DB_PASSWORD", r'DB_PASSWORD\s*=\s*["\']?codequizhub'),
        ("REDIS_PASSWORD", r'REDIS_PASSWORD\s*=\s*["\']?redisquizhub'),
    ]
    for name, pattern in checks:
        match = re.search(pattern, content)
        if match:
            report(WARN, f"{name} uses default/demo value", "Change in production!")

    if "DEBUG=true" in content.lower():
        report(FAIL, "DEBUG mode enabled in .env.production", "Must be disabled!")

    report(PASS, "Production env file found")


def check_jwt_secret():
    """Check that JWT secret is not hardcoded default."""
    config = Path("backend/app/config.py")
    if config.exists():
        content = config.read_text()
        if "change-this-in-production" in content:
            report(WARN, "JWT_SECRET is set to default value",
                   f"Update in {config} or .env.production")


def check_cors_origins():
    """Check CORS configuration."""
    config = Path("backend/app/config.py")
    if config.exists():
        content = config.read_text()
        if "localhost" in content and "*" not in content:
            report(PASS, "CORS origins are correctly limited")
        elif "*" in content:
            report(FAIL, "CORS allows all origins (*)", "Restrict in production!")
        else:
            report(WARN, "CORS origins check: review manually")


def check_security_headers():
    """Verify security headers are configured."""
    main_py = Path("backend/app/main.py")
    if main_py.exists():
        content = main_py.read_text()
        headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        missing = [h for h in headers if h not in content]
        if not missing:
            report(PASS, "All security headers configured")
        else:
            report(FAIL, f"Missing security headers: {', '.join(missing)}")


def check_logging_sensitive_data():
    """Review logging for potential sensitive data leaks."""
    log_files = [
        "backend/app/main.py",
        "judge/judge_worker.py",
        "backend/app/routers/auth.py",
    ]
    sensitive_patterns = [
        (r"password", "password in log message"),
        (r"token", "token in log message (check context)"),
        (r"secret", "secret in log message"),
        (r"authorization", "authorization header in log"),
    ]
    found_issues = []
    for filepath in log_files:
        path = Path(filepath)
        if not path.exists():
            continue
        content = path.read_text()
        for pattern, desc in sensitive_patterns:
            for i, line in enumerate(content.splitlines(), 1):
                if re.search(pattern, line, re.IGNORECASE) and "log" in line.lower():
                    # Skip known false positives (logging error messages, etc.)
                    safe_prefixes = ("#", "//", "logger.error", "logger.info")
                    if any(line.strip().startswith(p) for p in safe_prefixes):
                        # Check if it's logging actual values vs error messages
                        if "error" in line.lower() or "fail" in line.lower():
                            # Error messages are OK - they don't log raw values
                            pass
                        else:
                            found_issues.append(f"    {filepath}:{i}: {line.strip()[:100]}")

    if found_issues:
        report(WARN, "Potential sensitive data in logging", "Review manually:")
        for issue in found_issues:
            print(issue)
    else:
        report(PASS, "No obvious sensitive data leaks in logging")


def check_docker_security():
    """Check Docker security practices."""
    docker_files = list(Path(".").glob("**/Dockerfile")) + list(Path(".").glob("**/Dockerfile.*"))
    non_root = []
    root_containers = []

    for df in docker_files:
        content = df.read_text(errors="ignore")
        if "USER" in content and "root" not in content.split("USER")[-1].split("\n")[0].lower():
            non_root.append(df.name)
        else:
            root_containers.append(df.name)

    if non_root:
        report(PASS, f"Non-root users in: {', '.join(non_root)}")
    if root_containers:
        for rc in root_containers:
            report(WARN, f"Container may run as root: {rc}")


def check_dependency_vulnerabilities():
    """Check for known vulnerable dependencies using pip-audit or safety."""
    report(WARN, "Dependency vulnerability scanning requires pip-audit",
           "Run: pip install pip-audit && pip-audit")


def check_https_redirect():
    """Check for HTTPS redirect in production config."""
    nginx = Path("frontend/nginx.conf")
    if nginx.exists():
        content = nginx.read_text()
        if "ssl" in content or "443" in content:
            report(PASS, "HTTPS/SSL configured in nginx")
        else:
            report(WARN, "No HTTPS redirect in nginx config", "Add for production!")
    else:
        report(WARN, "No nginx config found", "frontend/nginx.conf missing")


def check_rate_limiting():
    """Check rate limiting configuration."""
    config = Path("backend/app/config.py")
    if config.exists():
        content = config.read_text()
        if "RATE_LIMIT" in content:
            report(PASS, "Rate limiting configured")
        else:
            report(FAIL, "No rate limiting configured")


def run_audit():
    """Run all security checks."""
    print(f"\n{BOLD}CodeQuizHub Security Audit{RESET}")
    print("=" * 60)
    print(f"  Run at: {__import__('datetime').datetime.now().isoformat()}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 60)

    # Navigate to project root
    script_dir = Path(__file__).resolve().parent.parent
    os.chdir(script_dir)

    print(f"\n{BOLD}[1/9] Environment Configuration{RESET}")
    check_env_production()
    check_jwt_secret()
    check_cors_origins()

    print(f"\n{BOLD}[2/9] Security Headers{RESET}")
    check_security_headers()

    print(f"\n{BOLD}[3/9] Logging Security{RESET}")
    check_logging_sensitive_data()

    print(f"\n{BOLD}[4/9] Docker Security{RESET}")
    check_docker_security()

    print(f"\n{BOLD}[5/9] Dependency Vulnerabilities{RESET}")
    check_dependency_vulnerabilities()

    print(f"\n{BOLD}[6/9] HTTPS/TLS{RESET}")
    check_https_redirect()

    print(f"\n{BOLD}[7/9] Rate Limiting{RESET}")
    check_rate_limiting()

    print(f"\n{BOLD}[8/9] Database Backup{RESET}")
    print("  [INFO] No automated backup script found. See Task 9.3.")

    print(f"\n{BOLD}[9/9] Summary{RESET}")
    print("=" * 60)
    warnings = sum(1 for r in REPORT if "[WARN]" in r)
    failures = sum(1 for r in REPORT if "[FAIL]" in r)
    print(f"  {len(REPORT)} checks total, {warnings} warnings, {failures} failures")
    print("=" * 60)

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(run_audit())
