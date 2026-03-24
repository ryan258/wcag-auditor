"""Core auditing functionality for WCAG compliance."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging

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
    """Main auditor class for crawling and checking WCAG compliance."""
    
    def __init__(self, base_url: str, max_depth: int = 2, max_pages: int =  50, timeout: int = 30, user_agent: str = "WCAG-Auditor/0.1.0"):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.user_agent = user_
agent
        self.visited_urls: Set[str] = set()
        self.results: List[AuditResult] = []
        
        # Parse base URL
        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc
        self.scheme = parsed.scheme
        
        # WCAG 2.2 rules to check
        self.wcag_rules = self._load_wcag_rules()
    
    def _load_wcag_rules(self) -> Dict[str, Any]:
        """Load WCAG 2.2 rules for checking."""
        # This is a simplified set of rules. In a real implementation,
        # you would load these from a configuration file or external source.
        return {
            "missing-alt-text": {
                "description": "Images must have alternate text",
                "wcag": "1.1.1",
                "level": "A",
                "impact": "critical",
                "check": self._check_missing_alt_text
            },
            "missing-labels": {
                "description": "Form elements must have labels",
                "wcag": "1.3.1",
                "level": "A",
                "impact": "serious",
                "check": self._check_missing_labels
            },
            "low-contrast": {
                "description": "Text must have sufficient contrast ratio",
                "wcag": "1.4.3",
                "level": "AA",
                "impact": "serious",
                "check": self._check_low_contrast
            },
            "missing-lang": {
                "description": "Page must have a lang attribute",
                "wcag": "3.1.1",
                "level": "A",
                "impact": "serious",
                "check": self._check_missing_lang
            },
            "empty-links": {
                "description": "Links must have discernible text",
                "wcag": "2.4.4",
                "level": "A",
                "impact": "serious",
                "check": self._check_empty_links
            },
            "empty-buttons": {
                "description": "Buttons must have discernible text",
                "wcag": "4.1.2",
                "level": "A",
                "impact": "critical",
                "check": self._check_empty_buttons
            },
            "missing-title": {
                "description": "Page must have a title element",
                "wcag": "2.4.2",
                "level": "A",
                "impact": "serious",
                "check": self._check_missing_title
            },
            "autofocus-inputs": {
                "description": "Inputs should not have autofocus",
                "wcag": "2.4.3",
                "level": "A",
                "impact": "minor",
                "check": self._check_autofocus_inputs
            }
        }
    
    def _check_missing_alt_text(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for images without alt text."""
        violations = []
        images = soup.find_all("img")
        
        for img in images:
            if not img.get("alt") and not img.get("role") == "presentation":
                violations.append({
                    "element": str(img)[:100] + "..." if len(str(img)) > 100 else str(img),
                    "message": "Image missing alt attribute",
                    "suggestion": "Add descriptive alt text or role=\"presentation\" for decorative images"
                })
        
        return violations
    
    def _check_missing_labels(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for form inputs without labels."""
        violations = []
        inputs = soup.find_all(["input", "select", "textarea"])
        
        for inp in inputs:
            if inp.get("type") in ["hidden", "submit", "button", "reset", "image"]:
                continue
            
            input_id = inp.get("id")
            has_label = False
            
            if input_id:
                label = soup.find("label", {"for": input_id})c3
                if label:
                    has_label = True
            
            if not has_label and not inp.get("aria-label") and not inp.get("aria-labelledby"):
                violations.append({
                    "element": str(inp)[:100] + "..." if len(str(inp)) > 100 else str(inp),
                    "message": "Form input missing label",
                    "suggestion": "Add a <label> element with a 'for' attribute or use aria-label"
                })
        
        return violations
    
    def _check_low_contrast(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for text with low contrast (simplified check)."""
        # This is a simplified implementation. A real implementation would
        # need to compute actual contrast ratios based on foreground/background colors.
        violations = []
        
        # Check for elements with inline styles that might have low contrast
        elements_with_style = soup.find_all(style=True)
        
        for element in elements_with_style:
            style = element.get("style", "")
            if "color:" in style and "background-color:" in style:
                # This is a placeholder - real implementation would parse colors
                # and compute contrast ratio
                pass
        
        return violations
    
    def _check_missing_lang(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for missing lang attribute on html element."""
        violations = []
        html_tag = soup.find("html")
        
        if html_tag and not html_tag.get("lang"):
            violations.append({
                "element": "<html>",
                "message": "HTML element missing lang attribute",
                "suggestion": "Add lang attribute to <html> element, e.g., <html lang=\"en\">"
            })
        
        return violations
    
    def _check_empty_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for empty links."""
        violations = []
        links = soup.find_all("a")
        
        for link in links:
            text = link.get_text(strip=True)
            aria_label = link.get("aria-label")
            title = link.get("title")
            
            if not text and not aria_label and not title:
                violations.append({
                    "element": str(link)[:100] + "..." if len(str(link)) > 100 else str(link),
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content, aria-label, or title attribute"
                })
        
        return violations
    
    def _check_empty_buttons(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for empty buttons."""
        violations = []
        buttons = soup.find_all("button")
        
        for button in buttons:
            text = button.get_text(strip=True)
            aria_label = button.get("aria-label")
            title = button.get("title")
            
            if not text and not aria_label and not title:
                violations.append({
                    "element": str(button)[:100] + "..." if len(str(button)) > 100 else str(button),
                    "message": "Button has no discernible text",
                    "suggestion": "Add text content, aria-label, or title attribute"
                })
        
        return violations
    
    def _check_missing_title(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for missing title element."""
        violations = []
        title = soup.find("title")
        
        if not title or not title.get_text(strip=True):
            violations.append({
                "element": "<head>",
                "message": "Page missing title element",
                "suggestion": "Add a descriptive <title> element in the <head>"
            })
        
        return violations
    
    def _check_autofocus_inputs(self, soup: BeautifulSoup) -> Set[Dict[str, Any]]:
        """Check for inputs with autofocus attribute."""
        violations = []
        inputs = soup.find_all(attrs={"autofocus": True})
        
        for inp in inputs:
            violations.append({
                "element": str(inp)[:100] + "..." if len(str(inp)) > 100 else str(inp),
                "message": "Element has autofocus attribute",
                "suggestion": "Remove autofocus attribute to prevent unexpected focus changes"
            })
        
        return violations
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            return soup
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract links from page for crawling."""
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            
            # Only follow links within the same domain
            if parsed.netloc == self.base_domain and parsed.scheme in ["http", "https"]:
                # Remove fragment
                clean_url = parsed._replace(fragment="").geturl()
                links.append(clean_url)
        
        return links
    
    def _audit_page(self, url: str) -> AuditResult:
        """Audit a single page for WCAG compliance."""
        logger.info(f"Auditing: {url}")
        
        soup = self._get_page(url)
        if not soup:
            return AuditResult(
                url=url,
                violations=[{"rule": "fetch-error", "message": "Failed to fetch page"}],
                warnings=[],
                passed=[]
            )
        
        violations = []
        warnings = []
        passed = []
        
        # Run all WCAG checks
        for rule_name, rule_data in self.wcag_rules.items():
            check_func = rule_data["check"]
            try:
                rule_violations = check_func(soup)
                
                if rule_violations:
                    for violation in rule_violations:
                        violation.update({
                            "rule": rule_name,
                            "wcag": rule_data["wcag"],
                            "level": rule_data["level"],
                            "impact": rule_data["impact"],
                            "description": rule_data["description"]
                        })
                    violations.extend(rule_violations)
                else:
                    passed.append({
                        "rule": rule_name,
                        "wcag": rule_data["wcag"],
                        "level": rule_data["level"],
                        "description": rule_data["description"]
                    })
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")
                warnings.append({
                    "rule": rule_name,
                    "message": f"Check failed: {e}"
                })
        
        # Get page title
        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else None
        
        return AuditResult(
            url=url,
            violations=violations,
            warnings=warnings,
            passed=passed,
            page_title=page_title,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def audit(self) -> Dict[str, Any]:
        """Perform a full website audit."""
        logger.info(f"Starting audit of {self.base_url}")
        
        urls_to_visit = [self.base_url]
        current_depth = 0
        pages_audited = 0
        
        while urls_to_visit and pages_audited < self.max_pages and current_depth <= self.max_depth:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            pages_audited += 1
            
            # Audit the page
            result = self._audit_page(current_url)
            self.results.append(result)
            
            # Extract links for next depth level if we haven't reached max depth
            if current_depth < self.max_depth:
                soup = self._get_page(current_url)
                if soup:
                    new_links = self._extract_links(soup, current_url)
                    for link in new_links:
                        if link not in self.visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)
            
            # Increment depth after processing all URLs at current depth
            if not urls_to_visit or urls_to_visit[0] in self.visited_urls:
                current_depth += 1
        
        # Compile results
        all_violations = []
        all_warnings = []
        all_passed = []
        
        for result in self.results:
            all_violations.extend(result.violations)
            all_warnings.extend(result.warnings)
            all_passed.extend(result.passed)
        
        # Count violations by type
        violation_types = {}
        for violation in all_violations:
            rule = violation.get("rule", "unknown")
            violation_types[rule] = violation_types.get(rule, 0) + 1
        
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
            "pages": [
                {
                    "url": r.url,
                    "title": r.page_title,
                    "violations_count": len(r.violations),
                    "warnings_count": len(r.warnings),
                    "passed_count": len(r.passed)
                } for r in self.results
            ]
        }