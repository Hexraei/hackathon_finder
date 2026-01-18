---
name: ui-to-frontend
description: Turns UI designs (Figma/screenshots/specs) into pixel-perfect, production-ready front-end components. Use when implementing new UI without breaking existing styles or layouts.
---

# UI to Frontend Skill

When implementing UI designs into front-end code, follow these steps:

## Build checklist

1. **Design accuracy**: Match spacing, layout, fonts, colors, radius, borders, shadows, and hierarchy exactly.
2. **Component architecture**: Split the UI into reusable components (Button, Card, Badge, Section) with clean props.
3. **Responsiveness**: Ensure the UI adapts correctly for mobile, tablet, and desktop without overflow or broken alignment.
4. **States & motion**: Add hover, focus, active, disabled, loading states, plus transitions/animations if the design implies them.
5. **Integration safety**: Do not modify global CSS, theme files, or shared tokens unless explicitly required. Keep styles scoped.
6. **Accessibility**: Use semantic HTML, keyboard support, visible focus states, and ARIA where needed.
7. **Performance**: Avoid layout shifts, heavy effects, unnecessary wrappers, and repeated rendering.

## Implementation workflow

- Identify the layout system first (grid/flex, container width, spacing scale)
- Extract or infer design tokens (font, colors, spacing, radius, shadows)
- Build the base structure first, then refine visuals to pixel-perfect
- Add responsive rules and test for small screens
- Add interactions and UI states last
- Keep code readable, consistent, and easy to integrate

## Output requirements

- Start with a short component plan (what files/components will be created)
- Provide complete, ready-to-paste code (not fragments)
- Use the exact stack the user requests (React/Next/Vue/HTML/Flutter, Tailwind/CSS Modules/etc.)
- If assets are missing, use placeholders and specify expected size/format
- If anything is unclear, make the best assumption and list it at the end
