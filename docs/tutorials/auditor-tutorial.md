# Auditor Tutorial

## Big Idea

This Python lesson builds the program step by step across 15 teaching steps, covering 7 imports, 2 classes, and a final execution flow. Along the way, students will encounter control flow, error handling, iteration, and state management.

## At a Glance

- Language: Python
- Suggested level: Advanced
- Estimated pacing: 35-45 minutes
- Lesson steps: 15
- Components covered: 7 imports, 2 classes, and a final execution flow
- Core concepts: control flow, error handling, iteration, and state management



### How the Pieces Connect

| Component | Kind | Uses | Used By |
|-----------|------|------|---------|
| `AuditResult` | class | --- | `Auditor.__init__` and `Auditor._check_page` |
| `Auditor.__init__` | class_intro | `AuditResult` | --- |
| `Auditor._load_wcag_rules` | method | --- | --- |
| `Auditor._check_missing_alt_text` | method | --- | --- |
| `Auditor._check_missing_labels` | method | --- | --- |
| `Auditor._check_missing_lang` | method | --- | --- |
| `Auditor._check_empty_links` | method | --- | --- |
| `Auditor._check_empty_buttons` | method | --- | --- |
| `Auditor._check_missing_title` | method | --- | --- |
| `Auditor._check_autofocus_inputs` | method | --- | --- |
| `Auditor._get_page` | method | --- | `Auditor._check_page` |
| `Auditor._extract_links` | method | --- | `Auditor.audit` |
| `Auditor._check_page` | method | `Auditor._get_page` and `AuditResult` | `Auditor.audit` |
| `Auditor.audit` | method | `Auditor._check_page` and `Auditor._extract_links` | --- |



## Warm-Up

Ask why someone might choose a class instead of scattered variables and helper code for this problem.


## Key Vocabulary

- `import`: code this file pulls in before the main logic starts.
- `class`: a reusable unit that groups related data and behavior.
- `method`: a behavior that belongs to a specific class.
- `state`: information an object keeps between actions.
- `iteration`: repeating work with a loop.
- `control flow`: the decisions that determine which lines run next.
- `error handling`: detecting and responding to problems at runtime.



## What You'll Learn

- Explain why each import appears before the main logic begins.
- Describe how each class groups responsibilities and manages state.
- Explain how components depend on one another by following the call chain.
- Connect the supporting definitions to the final execution flow.


## Teaching Tips

- Ask students to predict what the code will do before you reveal the explanation or run it.
- Have learners annotate where data enters, changes, and leaves the program.
- Pause after each step and connect it back to the overall goal.
- Separate what the class knows (state) from what it does (methods) so object-oriented structure feels less abstract.
- Use the dependency map to show students the order in which pieces build on each other.
- Use the final execution step as a recap: students should be able to explain every call it makes.


## Steps


### Step 1: Importing Required Modules


These imports prepare the outside tools the program depends on, including import requests, from bs4 import BeautifulSoup.

**Focus**

These lines bring in the outside tools the program relies on before any of the core logic begins.

**Look For**

- External building blocks introduced here: import requests, from bs4 import BeautifulSoup, from urllib.parse import urljoin, urlparse.
- These imports frame everything that follows.
- Compare them: which support computation versus input/output?


**Ask Your Students**

- Which import is most important for the rest of the file?
- What would break first if one of these disappeared?


```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging
```

**Predict**

If you removed the last import, which later line would be the first to fail?

**Modify**

Remove one import and predict which line will fail first.

**Try It**

Ask students to find where each import is first used later in the lesson.


### Step 2: Define the `AuditResult` class


> This class is self-contained, making it a clean building block to introduce next.


Data class to store audit results.

**Focus**

`AuditResult` bundles related data and behavior into one reusable class.

**Look For**

- Mostly about structure — identify what data or contract it represents.
- Ask what responsibilities belong inside this type and what should stay outside.


**Ask Your Students**

- What problem does `AuditResult` solve better as a class than as loose code?


```python
class AuditResult:
    """Data class to store audit results."""
    url: str
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    passed: List[Dict[str, Any]]
    page_title: Optional[str] = None
    timestamp: Optional[str] = None
```

**Predict**

What data does a new `AuditResult` instance start with?

**Modify**

Add one new method to `AuditResult` that would make it more useful. Justify why that behavior belongs here.

**Try It**

Ask students to add one new method to `AuditResult` and explain what behavior it should own.


### Step 3: Introduce the `Auditor` class


> Now that `AuditResult` is defined, we can build the `Auditor` class that relies on it.


Main auditor class for crawling and checking WCAG compliance.

**Focus**

`Auditor` bundles related data and behavior into one reusable class. We start with its constructor.

**Look For**

- Full method list: `__init__`, `_load_wcag_rules`, `_check_missing_alt_text`, `_check_missing_labels`, `_check_missing_lang`, `_check_empty_links`, `_check_empty_buttons`, `_check_missing_title`, `_check_autofocus_inputs`, `_get_page`, `_extract_links`, `_check_page`, `audit`. We will cover them one by one.
- The constructor sets up state that the other methods will read and modify.
- Depends on: `AuditResult`.
- This step introduces the class — the methods follow in the next steps.


**Ask Your Students**

- What problem does `Auditor` solve better as a class than as loose code?
- Which method is the best starting point for understanding `Auditor`?


```python
class Auditor:
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
```

**Predict**

After creating an instance of `Auditor`, what state does it hold? List each attribute and its initial value.

**Modify**

Add or change one attribute in `Auditor.__init__`. What other methods would need to change?

**Try It**

Ask students to create an instance of `Auditor` and inspect its initial attributes.


### Step 4: Define `Auditor._load_wcag_rules`


> Next we add `_load_wcag_rules` to `Auditor`.


Load WCAG 2.2 rules for checking.

**Focus**

Focus on what `_load_wcag_rules` does with the instance state and what effect it produces.

**Look For**

- No explicit inputs — focus on the internal flow.
- Returns a value — ask what and when.


**Ask Your Students**

- What single job does `_load_wcag_rules` do for `Auditor`?


```python
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
```

**Predict**

Call `_load_wcag_rules` on an instance and predict what it returns or how it changes the object's state.

**Modify**

Make `_load_wcag_rules` accept one input it currently does not. What would you pass in?

**Try It**

Ask students how `Auditor._load_wcag_rules` would need to change if it accepted one extra input.


### Step 5: Define `Auditor._check_missing_alt_text`


> Next we add `_check_missing_alt_text` to `Auditor`.


Check for images without alt text.

Per WCAG 1.1.1, ``alt=""`` is the correct way to mark a
decorative image, so only images that are completely *missing*
the ``alt`` attribute (and lack ``role="presentation"``) are
violations.

**Focus**

Focus on how `_check_missing_alt_text` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_missing_alt_text` do for `Auditor`?
- Which input changes the behavior of `_check_missing_alt_text` the most: `soup`?


```python
    def _check_missing_alt_text(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for images without alt text.

        Per WCAG 1.1.1, ``alt=""`` is the correct way to mark a
        decorative image, so only images that are completely *missing*
        the ``alt`` attribute (and lack ``role="presentation"``) are
        violations.
        """
        violations = []
        images = soup.find_all("img")

        for img in images:
            has_alt = img.has_attr("alt")  # alt="" is intentional and valid
            is_presentational = img.get("role") == "presentation"
            if not has_alt and not is_presentational:
                violations.append({
                    "element": str(img)[:100] + "..." if len(str(img)) > 100 else str(img),
                    "message": "Image missing alt attribute",
                    "suggestion": "Add descriptive alt text or role=\"presentation\" for decorative images"
                })

        return violations
```

**Predict**

Pick a simple value for `soup` and predict what `_check_missing_alt_text` returns.

**Modify**

Add a new parameter to `_check_missing_alt_text` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_missing_alt_text` and predict the new result before running the code.


### Step 6: Define `Auditor._check_missing_labels`


> Next we add `_check_missing_labels` to `Auditor`.


Check for form inputs without labels.

Supports explicit ``<label for="id">`` associations *and*
implicit wrapping labels (``<label>Name <input></label>``).

**Focus**

Focus on how `_check_missing_labels` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_missing_labels` do for `Auditor`?
- Which input changes the behavior of `_check_missing_labels` the most: `soup`?


```python
    def _check_missing_labels(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for form inputs without labels.

        Supports explicit ``<label for="id">`` associations *and*
        implicit wrapping labels (``<label>Name <input></label>``).
        """
        violations = []
        inputs = soup.find_all(["input", "select", "textarea"])

        for inp in inputs:
            if inp.get("type") in ["hidden", "submit", "button", "reset", "image"]:
                continue

            # Explicit label via for/id
            input_id = inp.get("id")
            has_label = False
            if input_id:
                label = soup.find("label", {"for": input_id})
                if label:
                    has_label = True

            # Implicit label — input is a descendant of <label>
            if not has_label:
                parent_label = inp.find_parent("label")
                if parent_label:
                    has_label = True

            if not has_label and not inp.get("aria-label") and not inp.get("aria-labelledby"):
                violations.append({
                    "element": str(inp)[:100] + "..." if len(str(inp)) > 100 else str(inp),
                    "message": "Form input missing label",
                    "suggestion": "Add a <label> element with a 'for' attribute, wrap the input in a <label>, or use aria-label"
                })

        return violations
```

**Predict**

Pick a simple value for `soup` and predict what `_check_missing_labels` returns.

**Modify**

Add a new parameter to `_check_missing_labels` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_missing_labels` and predict the new result before running the code.


### Step 7: Define `Auditor._check_missing_lang`


> Next we add `_check_missing_lang` to `Auditor`.


Check for missing lang attribute on HTML element.

**Focus**

Focus on how `_check_missing_lang` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_missing_lang` do for `Auditor`?
- Which input changes the behavior of `_check_missing_lang` the most: `soup`?


```python
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
```

**Predict**

Pick a simple value for `soup` and predict what `_check_missing_lang` returns.

**Modify**

Add a new parameter to `_check_missing_lang` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_missing_lang` and predict the new result before running the code.


### Step 8: Define `Auditor._check_empty_links`


> Next we add `_check_empty_links` to `Auditor`.


Check for links without discernible text.

An ``<img alt="">`` inside a link does **not** provide a
discernible name — the alt text must be non-empty.

**Focus**

Focus on how `_check_empty_links` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_empty_links` do for `Auditor`?
- Which input changes the behavior of `_check_empty_links` the most: `soup`?


```python
    def _check_empty_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for links without discernible text.

        An ``<img alt="">`` inside a link does **not** provide a
        discernible name — the alt text must be non-empty.
        """
        violations = []
        links = soup.find_all("a")

        for link in links:
            has_text = link.get_text(strip=True)
            has_aria = link.get("aria-label") or link.get("aria-labelledby")
            has_title = link.get("title")
            # Only count an img as providing a name if alt is non-empty
            has_img_alt = any(
                img.get("alt", "").strip()
                for img in link.find_all("img")
            )

            if not has_text and not has_aria and not has_title and not has_img_alt:
                violations.append({
                    "element": str(link)[:100] + "..." if len(str(link)) > 100 else str(link),
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content, aria-label, or an image with non-empty alt text"
                })

        return violations
```

**Predict**

Pick a simple value for `soup` and predict what `_check_empty_links` returns.

**Modify**

Add a new parameter to `_check_empty_links` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_empty_links` and predict the new result before running the code.


### Step 9: Define `Auditor._check_empty_buttons`


> Next we add `_check_empty_buttons` to `Auditor`.


Check for buttons without discernible text.

**Focus**

Focus on how `_check_empty_buttons` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_empty_buttons` do for `Auditor`?
- Which input changes the behavior of `_check_empty_buttons` the most: `soup`?


```python
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
```

**Predict**

Pick a simple value for `soup` and predict what `_check_empty_buttons` returns.

**Modify**

Add a new parameter to `_check_empty_buttons` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_empty_buttons` and predict the new result before running the code.


### Step 10: Define `Auditor._check_missing_title`


> Next we add `_check_missing_title` to `Auditor`.


Check for missing title element.

**Focus**

Focus on how `_check_missing_title` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_missing_title` do for `Auditor`?
- Which input changes the behavior of `_check_missing_title` the most: `soup`?


```python
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
```

**Predict**

Pick a simple value for `soup` and predict what `_check_missing_title` returns.

**Modify**

Add a new parameter to `_check_missing_title` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_missing_title` and predict the new result before running the code.


### Step 11: Define `Auditor._check_autofocus_inputs`


> Next we add `_check_autofocus_inputs` to `Auditor`.


Check for inputs with autofocus attribute.

**Focus**

Focus on how `_check_autofocus_inputs` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `soup`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.


**Ask Your Students**

- What single job does `_check_autofocus_inputs` do for `Auditor`?
- Which input changes the behavior of `_check_autofocus_inputs` the most: `soup`?


```python
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
```

**Predict**

Pick a simple value for `soup` and predict what `_check_autofocus_inputs` returns.

**Modify**

Add a new parameter to `_check_autofocus_inputs` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_autofocus_inputs` and predict the new result before running the code.


### Step 12: Define `Auditor._get_page`


> Next we add `_get_page` to `Auditor`.


Fetch a page and return BeautifulSoup object.

**Focus**

Focus on how `_get_page` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `url`.
- Returns a value — ask what and when.
- Used later by: `Auditor._check_page`.


**Ask Your Students**

- What single job does `_get_page` do for `Auditor`?
- Which input changes the behavior of `_get_page` the most: `url`?


```python
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
```

**Predict**

Pick a simple value for `url` and predict what `_get_page` returns.

**Modify**

Add a new parameter to `_get_page` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._get_page` and predict the new result before running the code.


### Step 13: Define `Auditor._extract_links`


> Next we add `_extract_links` to `Auditor`.


Extract internal links from page.

**Focus**

Focus on how `_extract_links` transforms its inputs and what it does with the instance state.

**Look For**

- Inputs: `soup`, `current_url`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.
- Used later by: `Auditor.audit`.


**Ask Your Students**

- What single job does `_extract_links` do for `Auditor`?
- Which input changes the behavior of `_extract_links` the most: `soup`, `current_url`?


```python
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
```

**Predict**

Pick a simple value for `soup` and predict what `_extract_links` returns.

**Modify**

Add a new parameter to `_extract_links` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._extract_links` and predict the new result before running the code.


### Step 14: Define `Auditor._check_page`


> Continuing to build out `Auditor`, we define `_check_page` which uses `_get_page` and `AuditResult`.


Check a single page for WCAG compliance.

Returns ``(AuditResult, soup)`` so callers can reuse the parsed
page without refetching.

**Focus**

Focus on how `_check_page` transforms its input and what it does with the instance state.

**Look For**

- Inputs: `url`.
- Returns a value — ask what and when.
- Contains a decision point — good for branch tracing.
- Depends on: `Auditor._get_page` and `AuditResult`.
- Used later by: `Auditor.audit`.


**Ask Your Students**

- What single job does `_check_page` do for `Auditor`?
- Which input changes the behavior of `_check_page` the most: `url`?
- Why does `_check_page` call `_get_page` and `AuditResult`?


```python
    def _check_page(self, url: str) -> tuple:
        """Check a single page for WCAG compliance.

        Returns ``(AuditResult, soup)`` so callers can reuse the parsed
        page without refetching.
        """
        soup = self._get_page(url)
        if not soup:
            return AuditResult(
                url=url,
                violations=[],
                warnings=[{"rule": "fetch-error", "message": f"Could not fetch {url}"}],
                passed=[]
            ), None
        
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
        ), soup
```

**Predict**

Pick a simple value for `url` and predict what `_check_page` returns.

**Modify**

Add a new parameter to `_check_page` and predict what else needs to change.

**Try It**

Change one argument to `Auditor._check_page` and predict the new result before running the code.


### Step 15: Module Setup


> Before the main logic runs, these module-level statements configure the runtime environment.


These module-level statements configure the runtime environment before the main logic runs.

**Focus**

This is setup code, not orchestration — it prepares the environment so the classes and functions above work correctly at runtime.

**Look For**

- This is configuration, not behavior — it prepares the environment for the logic defined above.
- Trace each assignment or call to understand what state it creates.


**Ask Your Students**

- What would go wrong if this setup code were missing?
- Is this configuration or behavior?


```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
```

**Predict**

What state does this setup code create? Trace each assignment or configuration call.

**Modify**

Change one configuration value and predict how the program's behavior changes.

**Try It**

Ask students to identify which earlier components depend on this setup being in place.



## The Complete Program

```python
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
        """Check for images without alt text.

        Per WCAG 1.1.1, ``alt=""`` is the correct way to mark a
        decorative image, so only images that are completely *missing*
        the ``alt`` attribute (and lack ``role="presentation"``) are
        violations.
        """
        violations = []
        images = soup.find_all("img")

        for img in images:
            has_alt = img.has_attr("alt")  # alt="" is intentional and valid
            is_presentational = img.get("role") == "presentation"
            if not has_alt and not is_presentational:
                violations.append({
                    "element": str(img)[:100] + "..." if len(str(img)) > 100 else str(img),
                    "message": "Image missing alt attribute",
                    "suggestion": "Add descriptive alt text or role=\"presentation\" for decorative images"
                })

        return violations
    
    def _check_missing_labels(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for form inputs without labels.

        Supports explicit ``<label for="id">`` associations *and*
        implicit wrapping labels (``<label>Name <input></label>``).
        """
        violations = []
        inputs = soup.find_all(["input", "select", "textarea"])

        for inp in inputs:
            if inp.get("type") in ["hidden", "submit", "button", "reset", "image"]:
                continue

            # Explicit label via for/id
            input_id = inp.get("id")
            has_label = False
            if input_id:
                label = soup.find("label", {"for": input_id})
                if label:
                    has_label = True

            # Implicit label — input is a descendant of <label>
            if not has_label:
                parent_label = inp.find_parent("label")
                if parent_label:
                    has_label = True

            if not has_label and not inp.get("aria-label") and not inp.get("aria-labelledby"):
                violations.append({
                    "element": str(inp)[:100] + "..." if len(str(inp)) > 100 else str(inp),
                    "message": "Form input missing label",
                    "suggestion": "Add a <label> element with a 'for' attribute, wrap the input in a <label>, or use aria-label"
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
        """Check for links without discernible text.

        An ``<img alt="">`` inside a link does **not** provide a
        discernible name — the alt text must be non-empty.
        """
        violations = []
        links = soup.find_all("a")

        for link in links:
            has_text = link.get_text(strip=True)
            has_aria = link.get("aria-label") or link.get("aria-labelledby")
            has_title = link.get("title")
            # Only count an img as providing a name if alt is non-empty
            has_img_alt = any(
                img.get("alt", "").strip()
                for img in link.find_all("img")
            )

            if not has_text and not has_aria and not has_title and not has_img_alt:
                violations.append({
                    "element": str(link)[:100] + "..." if len(str(link)) > 100 else str(link),
                    "message": "Link has no discernible text",
                    "suggestion": "Add text content, aria-label, or an image with non-empty alt text"
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
    
    def _check_page(self, url: str) -> tuple:
        """Check a single page for WCAG compliance.

        Returns ``(AuditResult, soup)`` so callers can reuse the parsed
        page without refetching.
        """
        soup = self._get_page(url)
        if not soup:
            return AuditResult(
                url=url,
                violations=[],
                warnings=[{"rule": "fetch-error", "message": f"Could not fetch {url}"}],
                passed=[]
            ), None
        
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
        ), soup
    
    def audit(self) -> Dict[str, Any]:
        """Perform full website audit."""
        logger.info(f"Starting audit of {self.base_url}")

        # Reset state so the auditor can be reused safely
        self.visited_urls = set()
        self.results = []

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

            # Check the page (returns the parsed soup to avoid refetching)
            result, soup = self._check_page(current_url)
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
            if depth < self.max_depth and soup:
                new_links = self._extract_links(soup, current_url)
                for link in new_links:
                    if link not in self.visited_urls:
                        urls_to_visit.append((link, depth + 1))
        
        # Contrast analysis requires a rendering engine — emit once per audit
        all_warnings.append({
            "rule": "low-contrast",
            "message": "Contrast check skipped — requires a browser-level rendering engine to compute actual ratios (WCAG 1.4.3)"
        })

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
```


## Checks for Understanding

- What essential job would disappear if `AuditResult` were removed?
- Where does data enter the program, and where does it leave?
- Which step would you revisit first if the final output were wrong?
- Trace the dependency chain from the first function to the last. What order do they need to be called in?
- Which earlier definition does the final execution step rely on first?


## Extension Challenge

Add one new method to `AuditResult` that makes the type more useful, and justify why that behavior belongs there.

## Recap

- Importing Required Modules: students can explain what the program needs before it begins.
- Define the `AuditResult` class: explain what responsibility `AuditResult` owns.
- Introduce the `Auditor` class: explain what `Auditor` is for and what state it starts with.
- Define `Auditor._load_wcag_rules`: trace inputs, logic, and state changes inside this method.
- Define `Auditor._check_missing_alt_text`: trace inputs, logic, and state changes inside this method.

