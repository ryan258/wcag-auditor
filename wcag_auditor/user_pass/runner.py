"""Synthetic reviewer orchestration for site-level user-pass analysis."""

from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .agents import (
    COPYWRITER_AGENT,
    EXECUTIVE_AGENT,
    REVIEW_AGENTS,
    build_copywriter_system_prompt,
    build_copywriter_user_prompt,
    build_executive_system_prompt,
    build_executive_user_prompt,
    build_review_system_prompt,
    build_review_user_prompt,
)
from .client import OpenRouterClient
from .config import UserPassConfig


class UserPassRunner:
    """Run synthetic reviewer agents against representative page artifacts."""

    def __init__(self, config: UserPassConfig, client: Optional[OpenRouterClient] = None):
        self.config = config
        self.client = client or OpenRouterClient(config)

    def run(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run the synthetic user pass and return serializable results."""

        selected_pages = self._select_pages(results)
        agent_specs = [
            {
                "agent_id": agent.agent_id,
                "label": agent.label,
                "role": agent.role,
                "model": self.config.models[agent.agent_id],
            }
            for agent in REVIEW_AGENTS + (COPYWRITER_AGENT,)
        ]

        limitations = [
            "Synthetic reviewers are not a substitute for disabled human participants or moderated usability research.",
            "Suggestions are derived from sampled page artifacts, not a full task-based session across the site.",
            "Copy rewrites should be reviewed by the product/content owner before publication.",
        ]

        if not selected_pages:
            return {
                "status": "skipped",
                "provider": "openrouter",
                "pages_reviewed": 0,
                "agents": agent_specs,
                "findings": [],
                "themes": [],
                "rewrite_suggestions": [],
                "errors": [],
                "limitations": limitations,
            }

        findings: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for page_artifact in selected_pages:
            page_summary = self._page_summary(results, page_artifact)
            for agent in REVIEW_AGENTS:
                try:
                    response = self.client.complete_json(
                        model=self.config.models[agent.agent_id],
                        system_prompt=build_review_system_prompt(),
                        user_prompt=build_review_user_prompt(agent, page_artifact, page_summary),
                    )
                    findings.extend(self._normalize_findings(agent.agent_id, self.config.models[agent.agent_id], page_artifact, response))
                except Exception as exc:
                    errors.append(
                        {
                            "stage": "review",
                            "agent_id": agent.agent_id,
                            "page_url": page_artifact.get("url"),
                            "message": str(exc),
                        }
                    )

        rewrite_suggestions: List[Dict[str, Any]] = []
        try:
            response = self.client.complete_json(
                model=self.config.models[COPYWRITER_AGENT.agent_id],
                system_prompt=build_copywriter_system_prompt(),
                user_prompt=build_copywriter_user_prompt(selected_pages, findings),
            )
            rewrite_suggestions = self._normalize_rewrites(response)
        except Exception as exc:
            errors.append(
                {
                    "stage": "copywriter",
                    "agent_id": COPYWRITER_AGENT.agent_id,
                    "message": str(exc),
                }
            )

        status = "completed"
        if errors and (findings or rewrite_suggestions):
            status = "partial"
        elif errors:
            status = "error"

        return {
            "status": status,
            "provider": "openrouter",
            "pages_reviewed": len(selected_pages),
            "agents": agent_specs,
            "findings": findings,
            "themes": self._build_themes(findings),
            "rewrite_suggestions": rewrite_suggestions,
            "errors": errors,
            "limitations": limitations,
        }

    def _select_pages(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        artifacts = list(results.get("page_artifacts", []))
        if not artifacts:
            return []

        representative_urls = [
            sample.get("url")
            for sample in results.get("sampling", {}).get("representative_pages", [])
            if sample.get("url")
        ]
        artifacts_by_url = {artifact.get("url"): artifact for artifact in artifacts if artifact.get("url")}
        selected = [artifacts_by_url[url] for url in representative_urls if url in artifacts_by_url]
        if not selected:
            selected = artifacts
        return selected[: self.config.max_pages]

    def _page_summary(self, results: Dict[str, Any], page_artifact: Dict[str, Any]) -> Dict[str, Any]:
        page_url = page_artifact.get("url")
        page_lookup = {
            page.get("url"): page
            for page in results.get("pages", [])
            if page.get("url")
        }
        page_summary = dict(page_lookup.get(page_url, {}))
        page_summary.setdefault("url", page_url)
        page_summary.setdefault("title", page_artifact.get("title"))
        page_summary.setdefault("page_type", page_artifact.get("page_type"))
        page_summary.setdefault("template", page_artifact.get("template"))
        return page_summary

    def _normalize_findings(
        self,
        agent_id: str,
        model: str,
        page_artifact: Dict[str, Any],
        response: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for raw_finding in response.get("findings", [])[:5]:
            if not isinstance(raw_finding, dict):
                continue
            normalized.append(
                {
                    "page_url": page_artifact.get("url"),
                    "page_title": page_artifact.get("title"),
                    "page_type": page_artifact.get("page_type"),
                    "agent_id": agent_id,
                    "model": model,
                    "category": str(raw_finding.get("category", "general")).strip().lower() or "general",
                    "target_text": str(raw_finding.get("target_text", "General page flow")).strip() or "General page flow",
                    "issue": str(raw_finding.get("issue", "")).strip(),
                    "evidence": str(raw_finding.get("evidence", "")).strip(),
                    "why_it_matters": str(raw_finding.get("why_it_matters", "")).strip(),
                    "suggested_change": str(raw_finding.get("suggested_change", "")).strip(),
                    "confidence": _clamp_confidence(raw_finding.get("confidence", 0.5)),
                }
            )
        return normalized

    def _normalize_rewrites(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for raw_rewrite in response.get("rewrites", [])[:10]:
            if not isinstance(raw_rewrite, dict):
                continue
            normalized.append(
                {
                    "page_url": str(raw_rewrite.get("page_url", "")).strip(),
                    "location": str(raw_rewrite.get("location", "General copy")).strip() or "General copy",
                    "current_text": str(raw_rewrite.get("current_text", "")).strip(),
                    "proposed_text": str(raw_rewrite.get("proposed_text", "")).strip(),
                    "rationale": str(raw_rewrite.get("rationale", "")).strip(),
                    "confidence": _clamp_confidence(raw_rewrite.get("confidence", 0.5)),
                    "agent_id": COPYWRITER_AGENT.agent_id,
                    "model": self.config.models[COPYWRITER_AGENT.agent_id],
                }
            )
        return normalized

    def _build_themes(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        for finding in findings:
            key = "{0}|{1}|{2}".format(
                finding.get("page_url", ""),
                finding.get("category", "general"),
                _normalize_target(finding.get("target_text", "")),
            )
            theme = grouped.get(key)
            if theme is None:
                theme = {
                    "page_url": finding.get("page_url"),
                    "page_title": finding.get("page_title"),
                    "category": finding.get("category"),
                    "target_text": finding.get("target_text"),
                    "issue": finding.get("issue"),
                    "suggested_change": finding.get("suggested_change"),
                    "agent_ids": [],
                    "confidence": 0.0,
                }
                grouped[key] = theme
            else:
                # When multiple agents flag the same theme, keep the
                # higher-confidence version's issue and suggested_change.
                if finding.get("confidence", 0.0) > theme["confidence"]:
                    theme["issue"] = finding.get("issue")
                    theme["suggested_change"] = finding.get("suggested_change")

            if finding.get("agent_id") and finding["agent_id"] not in theme["agent_ids"]:
                theme["agent_ids"].append(finding["agent_id"])
            theme["confidence"] = max(theme["confidence"], finding.get("confidence", 0.0))

        themes = list(grouped.values())
        themes.sort(key=lambda item: (-len(item["agent_ids"]), -item["confidence"], item.get("page_url") or ""))
        return themes[:10]

    def generate_executive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an AI-powered executive compliance report.

        Returns a dict with keys: executive_summary, risk_assessment,
        priority_actions, quick_wins, scorecard, and status.
        """
        payload = self._build_executive_payload(results)
        try:
            response = self.client.complete_json(
                model=self.config.models[EXECUTIVE_AGENT.agent_id],
                system_prompt=build_executive_system_prompt(),
                user_prompt=build_executive_user_prompt(payload),
            )
        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
                "scorecard": payload["scorecard"],
                "violation_groups": payload["violation_groups"],
                "executive_summary": "",
                "risk_assessment": "unknown",
                "priority_actions": [],
                "quick_wins": [],
            }

        return {
            "status": "completed",
            "scorecard": payload["scorecard"],
            "violation_groups": payload["violation_groups"],
            "executive_summary": str(response.get("executive_summary", "")),
            "risk_assessment": str(response.get("risk_assessment", "unknown")),
            "priority_actions": response.get("priority_actions", []),
            "quick_wins": response.get("quick_wins", []),
        }

    def _build_executive_payload(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build a compact summary payload for the executive writer agent."""
        violations = results.get("violations", [])
        manual_reviews = results.get("manual_reviews", [])

        # Group violations by rule
        groups: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        for v in violations:
            rule = v.get("rule", "unknown")
            if rule not in groups:
                groups[rule] = {
                    "rule": rule,
                    "wcag": v.get("wcag", "Unknown"),
                    "level": v.get("level", "Unknown"),
                    "impact": v.get("impact", "unknown"),
                    "description": v.get("description", ""),
                    "suggestion": v.get("suggestion", ""),
                    "remediation_code": v.get("remediation_code", ""),
                    "count": 0,
                    "sample_elements": [],
                }
            groups[rule]["count"] += 1
            if len(groups[rule]["sample_elements"]) < 3:
                element = str(v.get("element", ""))[:120]
                if element and element not in groups[rule]["sample_elements"]:
                    groups[rule]["sample_elements"].append(element)

        violation_groups = sorted(groups.values(), key=lambda g: (-_impact_rank(g["impact"]), -g["count"]))

        # Compute scorecard
        level_a = sum(1 for v in violations if v.get("level") == "A")
        level_aa = sum(1 for v in violations if v.get("level") == "AA")
        critical = sum(1 for v in violations if v.get("impact") == "critical")
        serious = sum(1 for v in violations if v.get("impact") == "serious")
        moderate = sum(1 for v in violations if v.get("impact") == "moderate")

        scorecard = {
            "url": results.get("base_url", ""),
            "pages_audited": results.get("pages_audited", 0),
            "total_violations": len(violations),
            "total_manual_reviews": len(manual_reviews),
            "total_passed": results.get("total_passed", 0),
            "unique_rules_violated": len(groups),
            "level_a_failures": level_a,
            "level_aa_failures": level_aa,
            "critical_count": critical,
            "serious_count": serious,
            "moderate_count": moderate,
        }

        return {
            "scorecard": scorecard,
            "violation_groups": violation_groups,
            "synthetic_reviewer_insights": self._extract_reviewer_insights(results),
            "rewrite_suggestions": self._extract_rewrite_suggestions(results),
        }

    def _extract_reviewer_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract compact synthetic reviewer themes for the executive payload."""
        user_pass = results.get("user_pass", {})
        themes = user_pass.get("themes", [])
        # Cap at 10 themes and trim to essential fields
        compact = []
        for theme in themes[:10]:
            if not isinstance(theme, dict):
                continue
            compact.append({
                "page_url": theme.get("page_url", ""),
                "category": theme.get("category", ""),
                "target_text": theme.get("target_text", ""),
                "issue": theme.get("issue", ""),
                "suggested_change": theme.get("suggested_change", ""),
                "agent_ids": theme.get("agent_ids", []),
                "confidence": theme.get("confidence", 0.0),
            })
        return compact

    def _extract_rewrite_suggestions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract compact copywriter rewrite suggestions for the executive payload."""
        user_pass = results.get("user_pass", {})
        rewrites = user_pass.get("rewrite_suggestions", [])
        # Cap at 10 and trim to essential fields
        compact = []
        for rewrite in rewrites[:10]:
            if not isinstance(rewrite, dict):
                continue
            compact.append({
                "page_url": rewrite.get("page_url", ""),
                "location": rewrite.get("location", ""),
                "current_text": rewrite.get("current_text", ""),
                "proposed_text": rewrite.get("proposed_text", ""),
                "rationale": rewrite.get("rationale", ""),
            })
        return compact


def _clamp_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.5
    return max(0.0, min(1.0, numeric))


def _normalize_target(value: str) -> str:
    return " ".join(str(value).lower().split())


def _impact_rank(impact: str) -> int:
    """Return a numeric rank for impact severity (higher = more severe)."""
    return {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}.get(impact, 0)
