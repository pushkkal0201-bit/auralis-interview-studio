# Auralis 5.3 / Practical Lab Design System

Inherits Studio 4 editorial design: Bodoni Moda for display, DM Sans for UI, IBM Plex Mono for code and evidence. Warm paper, forest-charcoal and muted olive; no gradients, glows, feature-grid filler or generic sparkles.

## Page anatomy

1. Large left-aligned editorial heading (“Show your work. Not just your words.”) with plainspoken explanation.
2. Two-text tab control to switch Python ↔ Engineering.
3. Split workbench: editable source/inputs on left; dark verification notebook on right.
4. Transparent assumptions, visible formula provenance and hidden-edge-case labels.
5. Simple ruled practice history (metadata only).

Responsive: split layout changes to stacked at <=900px, tabs equal-width and history wraps on small screens. Text content is always inserted with `textContent`, never unsafe HTML interpolation.
