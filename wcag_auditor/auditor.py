"""Core auditing functionality for WCAG compliance."""
from urllib.parse import urlparse
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging
from wcag_auditor import DEFAULT_USER_AGENT
from playwright.sync_api import sync_playwright, Page

from wcag_auditor.rules.core_rules import get_core_rules
from wcag_auditor.rules import AbstractRule

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@dataclass
class AuditResult:
    """Data class to store audit results."""
    url: str
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    passed: List[Dict[str, Any]]
    page_title: Optional[str] = None
    timestamp: Optional[str] = None

class Auditor:
    """Main auditor class for crawling and checking WCAG compliance using Playwright."""
    
    def __init__(self, base_url: str, max_depth: int = 2, max_pages: int = 50, timeout: int = 30, user_agent: str = DEFAULT_USER_AGENT):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.user_agent = user_agent
        self.visited_urls: Set[str] = set()
        self.results: List[AuditResult] = []
        
        # Parse base URL
        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc
        self.scheme = parsed.scheme
        
        # WCAG 2.2 rules to check
        self.wcag_rules: List[AbstractRule] = get_core_rules()
    
    def _extract_links(self, page: Page, current_url: str) -> Set[str]:
        """Extract internal links from page using JS evaluation."""
        links = set()
        base_domain = urlparse(current_url).netloc
        
        try:
            hrefs = page.evaluate("() => Array.from(document.links).map(a => a.href)")
            for href in hrefs:
                if not href or href.startswith("javascript:") or href.startswith("mailto:"):
                    continue
                
                parsed = urlparse(href)
                
                if parsed.netloc == base_domain and parsed.scheme in ["http", "https"]:
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if parsed.query:
                        clean_url += f"?{parsed.query}"
                    links.add(clean_url)
        except Exception as e:
            logger.error(f"Error extracting links from {current_url}: {e}")
            
        return links

    def _check_page(self, page: Page, url: str) -> AuditResult:
        """Check a single page for WCAG compliance using the loaded rules."""
        violations = []
        warnings = []
        passed = []
        
        # Run all checks
        for rule in self.wcag_rules:
            try:
                rule_violations = rule.evaluate(page)
                meta = rule.metadata
                if rule_violations:
                    for violation in rule_violations:
                        violations.append({
                            "rule": meta.id,
                            "wcag": meta.wcag_criterion,
                            "level": meta.level,
                            "impact": meta.impact,
                            "description": meta.description,
                            **violation
                        })
                else:
                    passed.append({
                        "rule": meta.id,
                        "wcag": meta.wcag_criterion,
                        "level": meta.level,
                        "description": meta.description
                    })
            except Exception as e:
                logger.error(f"Rule {rule.metadata.id} failed on {url}: {str(e)}")
                warnings.append({
                    "rule": rule.metadata.id,
                    "message": f"Rule evaluation crashed: {str(e)}"
                })
                
        title = page.title()
        
        return AuditResult(
            url=url,
            violations=violations,
            warnings=warnings,
            passed=passed,
            page_title=title if title else "No title",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

    def audit(self) -> Dict[str, Any]:
        """Perform full website audit using Playwright."""
        logger.info(f"Starting audit of {self.base_url}")

        self.visited_urls = set()
        self.results = []

        urls_to_visit = [(self.base_url, 0)]  # (url, depth)
        pages_audited = 0
        all_violations = []
        all_warnings = []
        all_passed = []
        violation_types = {}
        pages = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()

                try:
                    while urls_to_visit and pages_audited < self.max_pages:
                        current_url, depth = urls_to_visit.pop(0)

                        if current_url in self.visited_urls:
                            continue

                        self.visited_urls.add(current_url)

                        logger.info(f"Attempting page {pages_audited + 1}: {current_url}")

                        try:
                            page.goto(current_url, timeout=self.timeout * 1000, wait_until="load")
                            pages_audited += 1
                            result = self._check_page(page, current_url)
                            self.results.append(result)

                            all_violations.extend(result.violations)
                            all_warnings.extend(result.warnings)
                            all_passed.extend(result.passed)

                            for violation in result.violations:
                                rule = violation.get("rule")
                                if rule:
                                    violation_types[rule] = violation_types.get(rule, 0) + 1

                            pages.append({
                                "url": current_url,
                                "title": result.page_title,
                                "violations_count": len(result.violations),
                                "warnings_count": len(result.warnings),
                                "passed_count": len(result.passed)
                            })

                            if depth < self.max_depth:
                                new_links = self._extract_links(page, current_url)
                                for link in new_links:
                                    if link not in self.visited_urls:
                                        urls_to_visit.append((link, depth + 1))
                                        
                        except Exception as e:
                            logger.error(f"Error fetching {current_url}: {e}")
                            all_warnings.append({"rule": "fetch-error", "message": f"Could not fetch {current_url}: {e}"})

                finally:
                    context.close()
                    browser.close()
        except Exception as e:
            logger.critical(f"Playwright execution failed. Please ensure browsers are installed `playwright install`. Error: {e}")
            all_warnings.append({
                "rule": "execution-failure",
                "message": f"Critical execution failure. Is Playwright installed? Error: {e}"
            })

        return {
            "base_url": self.base_url,
            "pages_audited": pages_audited,
            "total_violations": len(all_violations),
            "total_warnings": len(all_warnings),
            "total_passed": len(all_passed),
            "violation_types": violation_types,
            "violations": all_violations,
            "warnings": all_warnings,
            "passed": all_passed,
            "pages": pages
        }
