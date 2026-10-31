# Auralis / Editorial Practice Studio — art direction

## Intent
Auralis is an interview rehearsal workspace, not a metrics SaaS dashboard. Its first screen should look like an independent design journal: precise, quiet, technical, and highly readable. The candidate is the focus, not a fictitious AI persona.

## Three-color system (no gradients)
- `#F1EEE5` / Archive paper — the large editorial canvas and secondary surface tints.
- `#242B26` / Ink — primary text, navigation rail, key action backgrounds.
- `#6E795D` / Field olive — selected states, labels, fine rules, intentional emphasis.
Derived lighter/darker tonal layers, alpha and outline treatments are allowed. No pure black, pure white, neon, or purple-blue gradients.

## Typography
- **Bodoni Moda** — high-contrast editorial headline serif, loaded from Google Fonts with Georgia as fallback.
- **DM Sans** — calm compact sans for product controls and prose, loaded from Google Fonts with Trebuchet MS as fallback.
- **IBM Plex Mono** — tiny numerical information and question provenance, loaded from Google Fonts with Consolas as fallback.
No font files are bundled with the deliverable; stylesheet includes web font links and system fallbacks.

## Composition
- Charcoal masthead-like vertical rail with numbered navigation, not icon tiles.
- Split opening spread: giant editorial title at left; single typographic illustrated interview prompt at right. Intentionally no fake dashboards, stock photos or glowing wallpaper.
- Story-led numbered process strip, followed by an asymmetric CV / role brief layout with open edges rather than cards.
- Advanced evidence tools use quieter separated sections, not repeated feature tiles.
- Interview and report screens retain all existing controls and become part of the same visual vocabulary.

## Copy
Plain, verifiable product statements: paste a CV and job advert; hear questions, answer aloud or in text; inspect rationale, review evidence, and retry. Sample questions are labeled illustrative. Never assert scores or live AI availability unless measured by the app.

## Usability
Responsive: 1440 / 1024 / 768 / 390 widths. Focus rings remain visible. No interaction requires motion, hover, external font loading, or photographic assets. All current IDs, URLs, inputs and JS API contracts are preserved. Native PDF printing rules from v3.3 remain untouched.

## Quality gate
Validate DOM IDs, syntax, all backend regression tests, browser console/network state, target viewport screenshots, keyboard focus and working sample/role-navigation interactions. Check for forbidden gradients, generically repeated 3-column cards, unused icon groups and accidentally hidden form controls.
