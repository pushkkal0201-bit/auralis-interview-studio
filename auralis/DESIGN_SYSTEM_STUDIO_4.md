# Auralis Studio 4 / Editorial Product Design System

## Positioning
Auralis rehearses interviews grounded in a candidate's CV and a particular job. It asks contextual questions, takes voice or typed answers, captures question rationale, and provides evidence-backed practice feedback. It is not a hiring, credentialing, or verification service.

## Art direction
An independent technical journal with a working product inside it. Precision and warmth over spectacle. Not an analytics SaaS kit: no dashboards on the home page, feature cards, sparkles, ambient gradients, fake charts, or invented user testimonials.

### Palette (core inks)
- Paper: `#F1EEE5`, large surfaces and page background.
- Carbon: `#242B26`, typography, masthead, buttons, focus-rich areas.
- Field olive: `#6E795D`, navigational and provenance accents.
Supporting tonal variations (e.g. `#E8E8DC`) are explicitly derived for accessibility and separation; the primary palette stays at three hues. There is no pure black or pure white.

### Type
- **Bodoni Moda**: sharp editorial display, major headings and chapter breaks.
- **DM Sans**: forms, body, buttons and controls.
- **IBM Plex Mono**: labels, sequence numbers, provenance, timestamps and status.
Stylesheets load via Google Fonts with declared system fallbacks. Server CSP allows only the two Google font domains for styles and font files; JavaScript remains same-origin.

### Grid / spacing
- Left fixed 202 px book-spine navigation on large desktops, horizontal scrollable text navigation on tablet/mobile.
- Product-led split hero: conversational headline and actual local app screenshot, labeled as a scripted demonstration.
- Story section: two unequal columns, with three rows of numbered content separated by thin rules.
- Setup brief: two staggered editable columns; pace settings as a charcoal band. Optional tools behind native disclosure. Privacy and primary CTA at a single finishing stage.
- Interview: prominent question/answer surface and narrow competency rail; responsive to a single vertical column.
- Assessment: evidence as readable document sections; compact and full-replay printing owned by the established v3.3 stylesheet.

### Interaction contract
`app.js` owns data, API, speech, model choice and session state. `premium.js` only enhances navigation state and the sample/empty-room shortcuts. IDs and existing endpoint contracts are preserved, including CV/JD, CodeProof, optional incidents/REA, voice and typed responses, model controls, Skill DNA, X-Ray, retries, role comparison, saved sessions, and JSON/PDF workflows.

### Quality gates
No horizontal overflow at 1440, 1024, 768, 390 or 360 CSS pixels. Keyboard focus indicators, native details, no excessive animation, reduced-motion support. No fabricated inference outcomes. Graceful font fallback. Frontend remains local and all network-bound live AI use requires explicit consent.
