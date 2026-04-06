from typing import Any, Dict, List

from playwright.sync_api import Page

from . import AbstractRule, RuleMetadata


class PredictableNavigationRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="predictable-navigation",
            description="Interactive controls should not trigger unexpected context changes",
            wcag_criterion="3.2.2",
            level="A",
            impact="serious",
            applicability="page",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const selectors = '[onchange], [oninput], [onfocus], form[onchange], form[oninput]';
                const navigationScript = /(submit|location\\b|window\\.open|href\\s*=|replace\\()/i;

                return Array.from(document.querySelectorAll(selectors))
                    .flatMap(el => {
                        const script = [
                            el.getAttribute('onchange') || '',
                            el.getAttribute('oninput') || '',
                            el.getAttribute('onfocus') || '',
                        ].join(' ');

                        if (!navigationScript.test(script)) return [];

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Control appears to trigger navigation or form submission as soon as its value changes',
                            suggestion: 'Require an explicit submit or continue action before changing context.',
                            remediation_code: '<button type="submit">Continue</button>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class InputAssistanceRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="input-assistance-error-msg",
            description="If an input error is automatically detected, it must be described to the user in text",
            wcag_criterion="3.3.1",
            level="A",
            impact="serious",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => Array.from(document.querySelectorAll('[aria-invalid="true"]'))
                .flatMap(el => {
                    const refs = [
                        ...(el.getAttribute('aria-errormessage') || '').split(/\\s+/).filter(Boolean),
                        ...(el.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean),
                    ];

                    const referencedText = refs
                        .map(id => document.getElementById(id))
                        .filter(Boolean)
                        .map(node => (node.textContent || '').trim())
                        .join(' ')
                        .trim();

                    if (refs.length > 0 && referencedText.length > 0) {
                        return [];
                    }

                    const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                    return [{
                        element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                        message: 'Input marked as invalid lacks an associated error message',
                        suggestion: 'Point aria-errormessage or aria-describedby at visible error text.',
                        remediation_code: '<input aria-invalid="true" aria-errormessage="email-error">\\n<p id="email-error">Enter a valid email address.</p>',
                    }];
                })"""
        )


class LabelsInstructionsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="labels-or-instructions",
            description="Inputs with constraints or non-obvious formats should include instructions",
            wcag_criterion="3.3.2",
            level="A",
            impact="serious",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const controls = Array.from(document.querySelectorAll('input, select, textarea'));
                const skipTypes = new Set(['hidden', 'submit', 'button', 'reset', 'image', 'checkbox', 'radio']);

                return controls.flatMap(el => {
                    const type = (el.getAttribute('type') || 'text').toLowerCase();
                    if (skipTypes.has(type)) return [];

                    const hasLabel = (
                        (el.labels && el.labels.length > 0) ||
                        el.hasAttribute('aria-label') ||
                        el.hasAttribute('aria-labelledby')
                    );
                    if (!hasLabel) return [];

                    const needsInstructions = (
                        ['password', 'number', 'date', 'time', 'datetime-local', 'month', 'week', 'file'].includes(type) ||
                        el.hasAttribute('pattern') ||
                        el.hasAttribute('min') ||
                        el.hasAttribute('max') ||
                        el.hasAttribute('maxlength') ||
                        el.hasAttribute('required') ||
                        el.getAttribute('aria-required') === 'true'
                    );
                    if (!needsInstructions) return [];

                    const describedBy = (el.getAttribute('aria-describedby') || '')
                        .split(/\\s+/)
                        .filter(Boolean)
                        .map(id => document.getElementById(id))
                        .filter(Boolean)
                        .map(node => (node.textContent || '').trim())
                        .join(' ')
                        .trim();
                    const fieldsetLegend = el.closest('fieldset')?.querySelector('legend')?.textContent?.trim() || '';
                    const hasInstructions = Boolean(
                        describedBy ||
                        fieldsetLegend ||
                        (el.getAttribute('placeholder') || '').trim() ||
                        (el.getAttribute('title') || '').trim()
                    );

                    if (hasInstructions) return [];

                    const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                    return [{
                        element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                        message: 'Constrained input has a label but no accompanying instructions or format guidance',
                        suggestion: 'Add helper text that explains the required format, range, or rule.',
                        remediation_code: '<p id="password-help">Use at least 12 characters.</p>\\n<input type="password" aria-describedby="password-help">',
                    }];
                }).slice(0, 10);
            }"""
        )


class ErrorSuggestionRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="error-suggestion",
            description="Detected input errors should provide a suggestion for correction when possible",
            wcag_criterion="3.3.3",
            level="AA",
            impact="moderate",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const suggestionPattern = /(enter|select|choose|must|should|use|include|format|example|at least|match)/i;

                return Array.from(document.querySelectorAll('[aria-invalid="true"]'))
                    .flatMap(el => {
                        const refs = [
                            ...(el.getAttribute('aria-errormessage') || '').split(/\\s+/).filter(Boolean),
                            ...(el.getAttribute('aria-describedby') || '').split(/\\s+/).filter(Boolean),
                        ];
                        const message = refs
                            .map(id => document.getElementById(id))
                            .filter(Boolean)
                            .map(node => (node.textContent || '').trim())
                            .join(' ')
                            .trim();

                        const canSuggest = (
                            el.hasAttribute('pattern') ||
                            el.hasAttribute('required') ||
                            el.hasAttribute('min') ||
                            el.hasAttribute('max') ||
                            ['email', 'url', 'tel', 'number', 'password'].includes((el.getAttribute('type') || '').toLowerCase())
                        );

                        if (!canSuggest || !message || suggestionPattern.test(message)) {
                            return [];
                        }

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Error text identifies a problem but does not suggest how to fix it',
                            suggestion: 'Add recovery guidance such as the expected format or a concrete next step.',
                            remediation_code: '<p id="email-error">Enter a valid email address, for example name@example.com.</p>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class RequiredFieldIndicatorsRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="required-field-indicators",
            description="Required fields should be identified in labels or instructions",
            wcag_criterion="3.3.2",
            level="A",
            impact="moderate",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const markerPattern = /(required|mandatory|\\*)/i;

                return Array.from(document.querySelectorAll('input, select, textarea'))
                    .flatMap(el => {
                        const isRequired = el.hasAttribute('required') || el.getAttribute('aria-required') === 'true';
                        if (!isRequired) return [];

                        const labelText = [
                            ...(el.labels ? Array.from(el.labels).map(label => (label.textContent || '').trim()) : []),
                            el.getAttribute('aria-label') || '',
                            el.closest('fieldset')?.querySelector('legend')?.textContent || '',
                        ].join(' ').trim();

                        if (markerPattern.test(labelText)) {
                            return [];
                        }

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Required field is not clearly identified in its label or instructions',
                            suggestion: 'Add visible required text or an asterisk explained in nearby instructions.',
                            remediation_code: '<label for="email">Email address <span aria-hidden="true">*</span></label>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class RedundantEntryRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="redundant-entry",
            description="Forms should avoid asking users to re-enter the same information unnecessarily",
            wcag_criterion="3.3.7",
            level="A",
            impact="moderate",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const purposeTokens = {
                    email: ['email'],
                    phone: ['phone', 'tel'],
                    name: ['name', 'first_name', 'last_name', 'fullname'],
                    address: ['address', 'street', 'city', 'zip', 'postal'],
                };

                return Array.from(document.querySelectorAll('form'))
                    .flatMap(form => {
                        const html = form.outerHTML || '<form>';
                        const snippet = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                        const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
                        const purposeCounts = {};
                        let hasAlternative = false;

                        inputs.forEach(input => {
                            const text = [
                                input.name || '',
                                input.id || '',
                                input.getAttribute('autocomplete') || '',
                                input.getAttribute('aria-label') || '',
                                input.placeholder || '',
                                ...(input.labels ? Array.from(input.labels).map(label => label.textContent || '') : []),
                            ].join(' ').toLowerCase();

                            if (/same as|use shipping|copy from|autofill/i.test(text)) {
                                hasAlternative = true;
                            }

                            Object.entries(purposeTokens).forEach(([purpose, tokens]) => {
                                if (tokens.some(token => text.includes(token))) {
                                    purposeCounts[purpose] = (purposeCounts[purpose] || 0) + 1;
                                }
                            });
                        });

                        const duplicatedPurpose = Object.entries(purposeCounts)
                            .find(([, count]) => count > 1);

                        if (!duplicatedPurpose || hasAlternative) {
                            return [];
                        }

                        return [{
                            element: snippet,
                            message: `Form appears to request ${duplicatedPurpose[0]} information more than once without an obvious reuse shortcut`,
                            suggestion: 'Reuse previously entered information, provide a "same as" option, or add autocomplete to reduce repeated entry.',
                            finding_type: 'needs_review',
                            remediation_code: '<label><input type="checkbox" name="same_as_shipping"> Billing address is the same as shipping</label>',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )


class AccessibleAuthenticationRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="accessible-authentication",
            description="Authentication flows should not rely solely on cognitive function tests",
            wcag_criterion="3.3.8",
            level="AA",
            impact="serious",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const authForms = Array.from(document.querySelectorAll('form')).filter(form =>
                    form.querySelector('input[type="password"], input[autocomplete="current-password"], input[autocomplete="one-time-code"]')
                );
                const challengePattern = /(captcha|i am not a robot|what is \\d+\\s*[+\\-x]\\s*\\d+|security question|memorize|solve)/i;
                const altPattern = /(magic link|email me a link|passkey|webauthn|security key|password manager|use another method)/i;
                const challengeSelector = [
                    '.g-recaptcha',
                    '[data-sitekey]',
                    'iframe[src*="captcha" i]',
                    'iframe[title*="captcha" i]',
                    'img[alt*="captcha" i]',
                    'input[name*="captcha" i]',
                    '[aria-label*="captcha" i]',
                ].join(',');
                const isVisibleChallenge = el => {
                    if (!(el instanceof HTMLElement)) return false;
                    if (el.getAttribute('type') === 'hidden') return false;

                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                };

                return authForms.flatMap(form => {
                    const text = (form.textContent || '').replace(/\\s+/g, ' ').trim();
                    const html = form.outerHTML || '<form>';
                    const snippet = html.length > 140 ? `${html.slice(0, 140)}...` : html;
                    const hasAlternative = altPattern.test(text);
                    const hasTextualChallenge = challengePattern.test(text);
                    const hasCaptchaArtifact = Array.from(form.querySelectorAll(challengeSelector)).some(isVisibleChallenge);

                    if (hasTextualChallenge && !hasAlternative) {
                        return [{
                            element: snippet,
                            message: 'Authentication flow appears to include a cognitive challenge without an obvious alternative',
                            suggestion: 'Offer a non-cognitive alternative such as a magic link, passkey, or support-assisted verification path.',
                            remediation_code: '<button type="button">Email me a sign-in link</button>',
                        }];
                    }

                    if (hasCaptchaArtifact && !hasAlternative) {
                        return [{
                            element: snippet,
                            message: 'Authentication flow appears to contain a CAPTCHA or similar challenge without an obvious non-cognitive alternative',
                            suggestion: 'Review the challenge flow and add a passkey, magic link, or another accessible alternative path.',
                            finding_type: 'needs_review',
                        }];
                    }

                    return [];
                }).slice(0, 10);
            }"""
        )


class IdentifyInputPurposeRule(AbstractRule):
    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="identify-input-purpose",
            description="The purpose of fields collecting user information can be programmatically determined",
            wcag_criterion="1.3.5",
            level="AA",
            impact="moderate",
            applicability="form",
        )

    def evaluate(self, page: Page) -> List[Dict[str, Any]]:
        return page.evaluate(
            """() => {
                const tokens = ['address', 'phone', 'email', 'name', 'postal', 'city', 'country'];

                return Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], input:not([type])'))
                    .flatMap(el => {
                        const descriptor = [
                            el.name || '',
                            el.id || '',
                            el.getAttribute('aria-label') || '',
                            el.placeholder || '',
                            ...(el.labels ? Array.from(el.labels).map(label => label.textContent || '') : []),
                        ].join(' ').toLowerCase();

                        if (!tokens.some(token => descriptor.includes(token))) {
                            return [];
                        }

                        if ((el.getAttribute('autocomplete') || '').trim()) {
                            return [];
                        }

                        const html = el.outerHTML || `<${el.tagName.toLowerCase()}>`;
                        return [{
                            element: html.length > 140 ? `${html.slice(0, 140)}...` : html,
                            message: 'Common user-information field is missing an autocomplete attribute',
                            suggestion: 'Add the most specific autocomplete token available for the collected data.',
                            remediation_code: '<input type="email" autocomplete="email">',
                        }];
                    })
                    .slice(0, 10);
            }"""
        )
