"""Core auditing functionality for WCAG compliance."""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from wcag_auditor import DEFAULT_USER_AGENT
from wcag_auditor.remediation import get_default_remediation_code
from wcag_auditor.rules import AbstractRule
from wcag_auditor.rules.core_rules import get_core_rules


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class AuditResult:
    """Data class to store audit results."""

    url: str
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    passed: List[Dict[str, Any]]
    manual_reviews: List[Dict[str, Any]] = field(default_factory=list)
    page_title: Optional[str] = None
    timestamp: Optional[str] = None
    page_insights: Dict[str, Any] = field(default_factory=dict)


class Auditor:
    """Main auditor class for crawling and checking WCAG compliance using Playwright."""

    def __init__(
        self,
        base_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        timeout: int = 30,
        user_agent: str = DEFAULT_USER_AGENT,
        sample_strategy: str = "representative",
    ):
        self.base_url = base_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = timeout
        self.user_agent = user_agent
        self.sample_strategy = sample_strategy
        self.visited_urls: Set[str] = set()
        self.results: List[AuditResult] = []
        self.sampled_templates: Set[str] = set()

        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc
        self.scheme = parsed.scheme
        self.wcag_rules: List[AbstractRule] = get_core_rules()

    def _normalize_template(self, url: str) -> str:
        """Normalize URL paths into coarse page templates for representative sampling."""
        path = urlparse(url).path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        parts = [part for part in path.split("/") if part]
        normalized_parts = []
        for part in parts:
            lower_part = part.lower()
            if re.fullmatch(r"\d{6,}", part):
                normalized_parts.append(":id")
            elif re.fullmatch(r"[0-9a-f]{24}", lower_part):
                normalized_parts.append(":id")
            elif re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                lower_part,
            ):
                normalized_parts.append(":id")
            else:
                normalized_parts.append(lower_part)

        return "/" if not normalized_parts else f"/{'/'.join(normalized_parts)}"

    def _extract_links(self, page: Page, current_url: str) -> Set[str]:
        """Extract internal links and SPA route hints from the current page."""
        links = set()

        try:
            hrefs = page.evaluate(
                """() => {
                    const routeElements = Array.from(document.querySelectorAll(
                        'a[href], [data-href], [data-route], [routerLink], [routerlink], [xlink\\:href]'
                    ));
                    return routeElements
                        .map(el =>
                            el.getAttribute('href') ||
                            el.getAttribute('data-href') ||
                            el.getAttribute('data-route') ||
                            el.getAttribute('routerLink') ||
                            el.getAttribute('routerlink') ||
                            el.getAttribute('xlink:href') ||
                            ''
                        )
                        .filter(Boolean);
                }"""
            )
            for href in hrefs:
                if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                    continue

                if href.startswith("#") and not href.startswith("#/"):
                    continue

                if href.startswith("#/"):
                    absolute = urljoin(f"{self.scheme}://{self.base_domain}/", href[1:])
                else:
                    absolute = urljoin(current_url, href)

                parsed = urlparse(absolute)
                path = parsed.path or "/"
                if parsed.fragment.startswith("/"):
                    path = parsed.fragment

                if parsed.netloc != self.base_domain or parsed.scheme not in {"http", "https"}:
                    continue

                clean_url = f"{parsed.scheme}://{parsed.netloc}{path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                links.add(clean_url)
        except Exception as exc:
            logger.error("Error extracting links from %s: %s", current_url, exc)

        return links

    def _classify_page(self, url: str, insights: Dict[str, Any]) -> str:
        """Classify a page for reporting and representative sampling."""
        path = urlparse(url).path.lower()
        if insights.get("has_auth_form") or any(token in path for token in ("login", "sign-in", "signin", "auth")):
            return "authentication"
        if insights.get("video_count", 0) > 0 or "video" in path or "media" in path:
            return "media"
        if insights.get("form_count", 0) > 0 or any(
            token in path for token in ("checkout", "register", "contact", "subscribe", "form")
        ):
            return "form"
        if path in {"", "/"}:
            return "home"
        if any(token in path for token in ("pricing", "product", "plans")):
            return "product"
        if "search" in path:
            return "search"
        return "content"

    def _collect_page_insights(self, page: Page, url: str) -> Dict[str, Any]:
        """Capture per-page metadata needed for site-level findings and WCAG-EM reporting."""
        insights = page.evaluate(
            """() => {
                const navLinks = Array.from(document.querySelectorAll('nav a[href]'))
                    .map(link => ({
                        text: (link.textContent || link.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' '),
                        href: link.getAttribute('href') || ''
                    }))
                    .filter(link => link.text.length > 0)
                    .slice(0, 10);

                const routeCandidates = Array.from(document.querySelectorAll('[data-route], [routerLink], [routerlink], a[href^="#/"]'))
                    .map(el =>
                        el.getAttribute('data-route') ||
                        el.getAttribute('routerLink') ||
                        el.getAttribute('routerlink') ||
                        el.getAttribute('href') ||
                        ''
                    )
                    .filter(Boolean)
                    .slice(0, 20);

                return {
                    nav_labels: navLinks.map(link => link.text),
                    nav_links: navLinks,
                    route_candidates: routeCandidates,
                    form_count: document.querySelectorAll('form').length,
                    video_count: document.querySelectorAll('video').length,
                    has_auth_form: !!document.querySelector(
                        'input[type="password"], input[autocomplete="current-password"], input[autocomplete="one-time-code"]'
                    ),
                    title: document.title || ''
                };
            }"""
        )
        insights["url"] = url
        insights["template"] = self._normalize_template(url)
        insights["page_type"] = self._classify_page(url, insights)
        return insights

    def _site_level_findings(self, page_insights: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate site-level findings that require multiple sampled pages.

        This is an extension point. Today it only emits consistent-navigation review
        findings, but it returns grouped finding buckets so additional site-level checks
        can be added without changing the audit result contract again.
        """
        findings: Dict[str, List[Dict[str, Any]]] = {"violations": [], "manual_reviews": []}

        navigation_signatures: Dict[Tuple[str, ...], List[str]] = {}
        for insight in page_insights:
            signature = tuple(insight.get("nav_labels", []))
            if signature:
                navigation_signatures.setdefault(signature, []).append(insight["url"])

        if len(navigation_signatures) > 1:
            findings["manual_reviews"].append(
                {
                    "rule": "consistent-navigation",
                    "wcag": "3.2.3",
                    "level": "AA",
                    "impact": "moderate",
                    "description": "Primary navigation should remain consistent across sampled pages",
                    "finding_type": "needs_review",
                    "element": "<site navigation>",
                    "message": "Primary navigation labels or order differ across sampled pages",
                    "suggestion": "Review the representative sample to confirm navigation stays consistent for repeated UI.",
                }
            )

        return findings

    def _build_sampling_summary(self, page_insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build representative sample metadata for reporting."""
        representatives: Dict[str, Dict[str, Any]] = {}
        page_types: Dict[str, int] = {}
        spa_routes: Set[str] = set()

        for insight in page_insights:
            representatives.setdefault(insight["template"], insight)
            page_type = insight.get("page_type", "content")
            page_types[page_type] = page_types.get(page_type, 0) + 1
            for route in insight.get("route_candidates", []):
                spa_routes.add(route)

        representative_pages = [
            {
                "template": template,
                "url": insight["url"],
                "page_type": insight["page_type"],
                "title": insight.get("title") or "Untitled",
            }
            for template, insight in sorted(representatives.items())
        ]

        return {
            "strategy": self.sample_strategy,
            "sampled_pages": len(page_insights),
            "unique_templates": len(representatives),
            "representative_pages": representative_pages,
            "page_types": page_types,
            "spa_routes_detected": sorted(spa_routes),
        }

    def _check_page(self, page: Page, url: str) -> AuditResult:
        """Check a single page for WCAG compliance using the loaded rules."""
        violations: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        passed: List[Dict[str, Any]] = []
        manual_reviews: List[Dict[str, Any]] = []
        page_insights = self._collect_page_insights(page, url)

        for rule in self.wcag_rules:
            try:
                rule_findings = rule.evaluate(page)
                meta = rule.metadata
                if rule_findings:
                    for finding in rule_findings:
                        finding_type = finding.get("finding_type", "violation")
                        enriched = {
                            "rule": meta.id,
                            "wcag": meta.wcag_criterion,
                            "level": meta.level,
                            "impact": meta.impact,
                            "description": meta.description,
                            **finding,
                        }
                        if "remediation_code" not in enriched:
                            remediation_code = get_default_remediation_code(meta.id)
                            if remediation_code:
                                enriched["remediation_code"] = remediation_code

                        if finding_type == "needs_review":
                            manual_reviews.append(enriched)
                        else:
                            violations.append(enriched)
                else:
                    passed.append(
                        {
                            "rule": meta.id,
                            "wcag": meta.wcag_criterion,
                            "level": meta.level,
                            "description": meta.description,
                        }
                    )
            except Exception as exc:
                logger.error("Rule %s failed on %s: %s", rule.metadata.id, url, exc)
                warnings.append(
                    {
                        "rule": rule.metadata.id,
                        "message": f"Rule evaluation crashed: {exc}",
                    }
                )

        title = page.title()
        return AuditResult(
            url=url,
            violations=violations,
            warnings=warnings,
            passed=passed,
            manual_reviews=manual_reviews,
            page_title=title if title else "No title",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            page_insights=page_insights,
        )

    def audit(self) -> Dict[str, Any]:
        """Perform a full website audit using Playwright."""
        logger.info("Starting audit of %s", self.base_url)

        self.visited_urls = set()
        self.results = []
        self.sampled_templates = set()

        urls_to_visit = [(self.base_url, 0)]
        queued_urls = {self.base_url}
        pages_audited = 0
        all_violations: List[Dict[str, Any]] = []
        all_warnings: List[Dict[str, Any]] = []
        all_passed: List[Dict[str, Any]] = []
        all_manual_reviews: List[Dict[str, Any]] = []
        violation_types: Dict[str, int] = {}
        manual_review_types: Dict[str, int] = {}
        pages: List[Dict[str, Any]] = []
        page_insights: List[Dict[str, Any]] = []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()

                try:
                    while urls_to_visit and pages_audited < self.max_pages:
                        current_url, depth = urls_to_visit.pop(0)
                        queued_urls.discard(current_url)

                        if current_url in self.visited_urls:
                            continue

                        self.visited_urls.add(current_url)
                        logger.info("Attempting page %s: %s", pages_audited + 1, current_url)

                        try:
                            page.goto(current_url, timeout=self.timeout * 1000, wait_until="load")
                            pages_audited += 1
                            result = self._check_page(page, current_url)
                            self.results.append(result)
                            page_insights.append(result.page_insights)
                            self.sampled_templates.add(result.page_insights["template"])

                            all_violations.extend(result.violations)
                            all_warnings.extend(result.warnings)
                            all_passed.extend(result.passed)
                            all_manual_reviews.extend(result.manual_reviews)

                            for finding in result.violations:
                                rule = finding.get("rule")
                                if rule:
                                    violation_types[rule] = violation_types.get(rule, 0) + 1

                            for finding in result.manual_reviews:
                                rule = finding.get("rule")
                                if rule:
                                    manual_review_types[rule] = manual_review_types.get(rule, 0) + 1

                            pages.append(
                                {
                                    "url": current_url,
                                    "title": result.page_title,
                                    "template": result.page_insights["template"],
                                    "page_type": result.page_insights["page_type"],
                                    "violations_count": len(result.violations),
                                    "manual_reviews_count": len(result.manual_reviews),
                                    "warnings_count": len(result.warnings),
                                    "passed_count": len(result.passed),
                                }
                            )

                            if depth < self.max_depth:
                                new_links = sorted(self._extract_links(page, current_url))
                                filtered_links = [
                                    link
                                    for link in new_links
                                    if link not in self.visited_urls and link not in queued_urls
                                ]
                                if self.sample_strategy == "representative":
                                    filtered_links.sort(
                                        key=lambda link: (self._normalize_template(link) in self.sampled_templates, link)
                                    )
                                for link in filtered_links:
                                    urls_to_visit.append((link, depth + 1))
                                    queued_urls.add(link)

                        except Exception as exc:
                            logger.error("Error fetching %s: %s", current_url, exc)
                            all_warnings.append(
                                {
                                    "rule": "fetch-error",
                                    "message": f"Could not fetch {current_url}: {exc}",
                                }
                            )
                finally:
                    context.close()
                    browser.close()
        except Exception as exc:
            logger.critical(
                "Playwright execution failed. Ensure browsers are installed with `playwright install`. Error: %s",
                exc,
            )
            all_warnings.append(
                {
                    "rule": "execution-failure",
                    "message": f"Critical execution failure. Is Playwright installed? Error: {exc}",
                }
            )

        site_findings = self._site_level_findings(page_insights)
        all_violations.extend(site_findings["violations"])
        all_manual_reviews.extend(site_findings["manual_reviews"])
        for finding in site_findings["violations"]:
            rule = finding.get("rule")
            if rule:
                violation_types[rule] = violation_types.get(rule, 0) + 1
        for finding in site_findings["manual_reviews"]:
            rule = finding.get("rule")
            if rule:
                manual_review_types[rule] = manual_review_types.get(rule, 0) + 1

        sampling = self._build_sampling_summary(page_insights)
        wcag_em = {
            "scope": {
                "base_url": self.base_url,
                "sample_strategy": self.sample_strategy,
                "pages_audited": pages_audited,
                "unique_templates": sampling["unique_templates"],
            },
            "methodology": (
                "Representative crawl using a live Playwright browser session with automated rule checks and "
                "explicit needs-review findings for criteria that require human judgment."
            ),
            "sample": sampling["representative_pages"],
            "limitations": [
                "Automated checks do not replace manual accessibility validation.",
                "Needs-review findings should be resolved before claiming conformance.",
                "SPA routes are inferred from discovered client-side route hints and crawlable links.",
            ],
        }

        return {
            "base_url": self.base_url,
            "pages_audited": pages_audited,
            "total_violations": len(all_violations),
            "total_manual_reviews": len(all_manual_reviews),
            "total_warnings": len(all_warnings),
            "total_passed": len(all_passed),
            "violation_types": violation_types,
            "manual_review_types": manual_review_types,
            "violations": all_violations,
            "manual_reviews": all_manual_reviews,
            "warnings": all_warnings,
            "passed": all_passed,
            "pages": pages,
            "sampling": sampling,
            "wcag_em": wcag_em,
        }
