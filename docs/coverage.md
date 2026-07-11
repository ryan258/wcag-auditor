# WCAG 2.2 Level A/AA Coverage Matrix

This matrix lists all WCAG 2.2 Level A and AA Success Criteria, showing the coverage type and the specific rule(s) implemented in `wcag-auditor`.

| Criteria | Name | Level | Coverage Type | Implemented Rule(s) |
|---|---|---|---|---|
| 1.1.1 | Non-text Content | A | automated | `complex-alt-text` |
| 1.2.1 | Audio-only and Video-only (Prerecorded) | A | manual-only | N/A |
| 1.2.2 | Captions (Prerecorded) | A | automated | `time-based-media` |
| 1.2.3 | Audio Description or Media Alternative (Prerecorded) | A | manual-only | N/A |
| 1.2.4 | Captions (Live) | AA | manual-only | N/A |
| 1.2.5 | Audio Description (Prerecorded) | AA | automated | `audio-description-track` |
| 1.3.1 | Info and Relationships | A | automated | `adaptable-landmarks` |
| 1.3.2 | Meaningful Sequence | A | automated | `reading-sequence` |
| 1.3.3 | Sensory Characteristics | A | manual-only | N/A |
| 1.3.4 | Orientation | AA | manual-only | N/A |
| 1.3.5 | Identify Input Purpose | AA | automated | `identify-input-purpose` |
| 1.4.1 | Use of Color | A | manual-only | N/A |
| 1.4.2 | Audio Control | A | manual-only | N/A |
| 1.4.3 | Contrast (Minimum) | AA | partial-heuristic | `contrast-minimum` |
| 1.4.4 | Resize Text | AA | manual-only | N/A |
| 1.4.5 | Images of Text | AA | manual-only | N/A |
| 1.4.10 | Reflow | AA | manual-only | N/A |
| 1.4.11 | Non-text Contrast | AA | manual-only | N/A |
| 1.4.12 | Text Spacing | AA | manual-only | N/A |
| 1.4.13 | Content on Hover or Focus | AA | manual-only | N/A |
| 2.1.1 | Keyboard | A | automated | `keyboard-accessibility` |
| 2.1.2 | No Keyboard Trap | A | automated | `keyboard-trap` |
| 2.1.4 | Character Key Shortcuts | A | manual-only | N/A |
| 2.2.1 | Timing Adjustable | A | manual-only | N/A |
| 2.2.2 | Pause, Stop, Hide | A | automated | `enough-time-controls` |
| 2.3.1 | Three Flashes or Below Threshold | A | manual-only | N/A |
| 2.4.1 | Bypass Blocks | A | automated | `navigable-skip-links` |
| 2.4.2 | Page Titled | A | automated | `missing-title` |
| 2.4.3 | Focus Order | A | automated | `autofocus-inputs` |
| 2.4.4 | Link Purpose (In Context) | A | automated | `empty-links`, `link-purpose` |
| 2.4.5 | Multiple Ways | AA | manual-only | N/A |
| 2.4.6 | Headings and Labels | AA | manual-only | N/A |
| 2.4.7 | Focus Visible | AA | automated | `focus-appearance` |
| 2.4.11 | Focus Not Obscured (Minimum) | AA | needs-review-only | `focus-not-obscured` |
| 2.5.1 | Pointer Gestures | A | automated | `pointer-gestures` |
| 2.5.2 | Pointer Cancellation | A | automated | `pointer-cancellation` |
| 2.5.3 | Label in Name | A | manual-only | N/A |
| 2.5.4 | Motion Actuation | A | manual-only | N/A |
| 2.5.7 | Dragging Movements | AA | automated | `dragging-movements` |
| 2.5.8 | Target Size (Minimum) | AA | automated | `target-size-minimum` |
| 3.1.1 | Language of Page | A | automated | `missing-lang` |
| 3.1.2 | Language of Parts | AA | automated | `inline-language-change` |
| 3.2.1 | On Focus | A | manual-only | N/A |
| 3.2.2 | On Input | A | automated | `predictable-navigation` |
| 3.2.3 | Consistent Navigation | AA | manual-only | N/A |
| 3.2.4 | Consistent Identification | AA | manual-only | N/A |
| 3.2.6 | Consistent Help | A | manual-only | N/A |
| 3.3.1 | Error Identification | A | automated | `input-assistance-error-msg` |
| 3.3.2 | Labels or Instructions | A | automated | `missing-labels`, `labels-or-instructions`, `required-field-indicators` |
| 3.3.3 | Error Suggestion | AA | automated | `error-suggestion` |
| 3.3.4 | Error Prevention (Legal, Financial, Data) | AA | manual-only | N/A |
| 3.3.7 | Redundant Entry | A | automated | `redundant-entry` |
| 3.3.8 | Accessible Authentication (Minimum) | AA | automated | `accessible-authentication` |
| 4.1.2 | Name, Role, Value | A | automated | `empty-buttons`, `aria-validation` |
| 4.1.3 | Status Messages | AA | automated | `status-messages` |
