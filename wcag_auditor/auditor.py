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
    
    def __init__(self, base_url: str, max_depth: int = 2, max_pages: int = 50, timeout: int = 30, user_agent: str = "WCAG-Auditor/0.1.0"):
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
                label = soup.find("label", {"for": input_id})
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
            style = element.get('style', '')
            if 'color' in style and 'background' in style:
                # This is a placeholder - real implementation would parse colors and calculate contrast
                violations.append({
                    "element": str(element)[:100] + "..." if len(str(element)) > 100 else str(element),
                    "message": "Potential low contrast detected",
                    "suggestion": "Ensure text has sufficient contrast ratio (4.5:1 for normal text, 3:1 for large text)"
                })
        
        return violations
    
    def _check_missing_lang(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for missing lang attribute on HTML element."""
        violations = []
        html_tag = soup.find("html")
        
        if html_tag and not html_tag.get("lang"):
            violations.append({
                "element": str(html_tag)[:100] + "..." if len(str(html_tag)) > 100 else str(html_tag),
                "message": "HTML element missing lang attribute",
                "suggestion": "Add lang attribute to <html> element (e.g., <html lang=\"en\">)"
            })
        
        return violations
    
    def _check_empty_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for links without discernible text."""
        violations = []
        links = soup.find_all("a")
        
        for link in links:
            has_text = link.get_text(strip=True)
            has_aria = link.get("aria-label") or link.get("aria-labelledby")
            has_title = link.get("title")
            has_img_alt = link.find("img", alt=True)
            
            if not has_text and not has_aria and not has_title and not has_img_alt:
                violations.append({
                    "element": str(link)[:100] + "..." if len(str(link)) > 100 else str(link),
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content, aria-label, or an image with alt text"
                })
        
        return violations
    
    def _check_empty_buttons(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for buttons without discernible text."""
        violations = []
        buttons = soup.find_all("button")
        
        for button in buttons:
            has_text = button.get_text(strip=True)
            has_aria = button.get("aria-label") or button.get("aria-labelledby")
            has_title = button.get("title")
            has_value = button.get("value")
            
            if not has_text and not has_aria and not has_title and not has_value:
                violations.append({
                    "element": str(button)[:100] + "..." if len(str(button)) > 100 else str(button),
                    "message": "Button has no discernible text",
                    "suggestion": "Add text content, aria-label, or value attribute"
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
    
    def _check_autofocus_inputs(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for inputs with autofocus attribute."""
        violations = []
        autofocus_elements = soup.find_all(attrs={"autofocus": True})
        
        for element in autofocus_elements:
            violations.append({
                "element": str(element)[:100] + "..." if len(str(element)) > 100 else str(element),
                "message": "Element has autofocus attribute",
                "suggestion": "Remove autofocus to avoid disorienting users"
            })
        
        return violations
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> Set[str]:
        """Extract internal links from page."""
        links = set()
        base_domain = urlparse(current_url).netloc
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            
            # Skip empty, fragment, and non-http links
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)
            
            # Only include links from same domain
            if parsed.netloc == base_domain and parsed.scheme in ["http", "https"]:
                # Remove fragment
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                links.add(clean_url)
        
        return links
    
    def _check_page(self, url: str) -> AuditResult:
        """Check a single page for WCAG compliance."""
        soup = self._get_page(url)
        if not soup:
            return AuditResult(
                url=url,
                violations=[],
                warnings=[{"rule": "fetch-error", "message": f"Could not fetch {url}"}],
                passed=[]
            )
        
        violations = []
        warnings = []
        passed = []
        
        # Run all checks
        for rule_name, rule_info in self.wcag_rules.items():
            check_func = rule_info["check"]
            rule_violations = check_func(soup)
            
            if rule_violations:
                for violation in rule_violations:
                    violations.append({
                        "rule": rule_name,
                        "wcag": rule_info["wcag"],
                        "level": rule_info["level"],
                        "impact": rule_info["impact"],
                        "description": rule_info["description"],
                        **violation
                    })
            else:
                passed.append({
                    "rule": rule_name,
                    "wcag": rule_info["wcag"],
                    "level": rule_info["level"],
                    "description": rule_info["description"]
                })
        
        # Get page title
        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else "No title"
        
        return AuditResult(
            url=url,
            violations=violations,
            warnings=warnings,
            passed=passed,
            page_title=page_title,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def audit(self) -> Dict[str, Any]:
        """Perform full website audit."""
        logger.info(f"Starting audit of {self.base_url}")
        
        # Initialize with base URL
        urls_to_visit = [(self.base_url, 0)]  # (url, depth)
        pages_audited = 0
        all_violations = []
        all_warnings = []
        all_passed = []
        violation_types = {}
        pages = []
        
        while urls_to_visit and pages_audited < self.max_pages:
            current_url, depth = urls_to_visit.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            pages_audited += 1
            
            logger.info(f"Checking page {pages_audited}: {current_url}")
            
            # Check the page
            result = self._check_page(current_url)
            self.results.append(result)
            
            # Collect violations, warnings, and passed checks
            all_violations.extend(result.violations)
            all_warnings.extend(result.warnings)
            all_passed.extend(result.passed)
            
            # Count violation types
            for violation in result.violations:
                rule = violation.get("rule")
                if rule:
                    violation_types[rule] = violation_types.get(rule, 0) + 1
            
            # Add page info
            pages.append({
                "url": current_url,
                "title": result.page_title,
                "violations_count": len(result.violations),
                "warnings_count": len(result.warnings),
                "passed_count": len(result.passed)
            })
            
            # Extract links for further crawling if within depth limit
            if depth < self.max_depth:
                soup = self._get_page(current_url)
                if soup:
                    new_links = self._extract_links(soup, current_url)
                    for link in new_links:
                        if link not in self.visited_urls:
                            urls_to_visit.append((link, depth + 1))
        
        # Compile final results
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