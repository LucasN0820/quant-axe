---
name: frontend-design
description: "Create Claude-inspired, production-grade frontend interfaces. Use when the user asks to build or restyle web UI, React/Next.js components, pages, dashboards, landing pages, artifacts, or apps using the visual language of the Claude/Anthropic website: warm paper surfaces, Anthropic-style typography, editorial layouts, terracotta accents, restrained motion, and polished product UI composition."
---

# Claude-Inspired Frontend Design

Design and implement real working frontend code in a style inspired by the public Claude/Anthropic website. Treat this as a visual direction, not an instruction to clone protected brand assets.

## First Principles

- Build the requested interface directly. Do not make a marketing landing page unless the user asks for one.
- Preserve the app's existing framework, routing, component patterns, and design system where possible.
- Use the Claude visual language as a design constraint: warm, editorial, precise, calm, product-forward.
- Do not use Anthropic or Claude logos, wordmarks, screenshots, or proprietary font files unless the user provides them or the project already contains them.
- Avoid generic AI design tropes: purple gradients, glass blobs, blue-slate dashboards, oversaturated neon, floating decorative orbs, and vague stock imagery.

## Visual System

Use CSS variables or the local theme system for these tokens:

```css
:root {
  --claude-bg: #faf9f5;
  --claude-bg-secondary: #f0eee6;
  --claude-bg-raised: #ffffff;
  --claude-ink: #141413;
  --claude-ink-soft: #30302e;
  --claude-muted: #87867f;
  --claude-border: #e8e6dc;
  --claude-border-strong: #c2c0b6;
  --claude-clay: #d97757;
  --claude-clay-strong: #c96442;
  --claude-oat: #e3dacc;
  --claude-olive: #788c5d;
  --claude-mineral: #629987;
  --claude-sky-focus: #3898ec;
  --claude-radius-sm: 8px;
  --claude-radius-md: 12px;
  --claude-radius-lg: 16px;
  --claude-radius-xl: 24px;
  --claude-radius-hero: 32px;
}
```

### Color

- Start with a warm paper canvas: `#faf9f5` or `#f0eee6`.
- Use near-black text: `#141413`, with `#30302e` and `#87867f` for hierarchy.
- Use terracotta/clay as the primary accent: `#d97757` or `#c96442`. Keep it special for primary actions, active states, and small editorial accents.
- Use muted green/mineral and oat tones sparingly for secondary badges, illustrations, or comparison states.
- Alternate warm light sections with occasional deep charcoal sections when the page needs chapter-like rhythm.

### Typography

- Prefer project-provided `Anthropic Sans`, `Anthropic Serif`, and `Anthropic Mono` if already available.
- If those fonts are unavailable, use stacks that preserve the same temperament without bundling proprietary files:

```css
body {
  font-family: "Anthropic Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.editorial-heading,
.serif-accent {
  font-family: "Anthropic Serif", Georgia, "Times New Roman", serif;
}

code,
.mono {
  font-family: "Anthropic Mono", "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
}
```

- Use large, calm headings with line-height around `1.0` to `1.1`.
- Use body text around `17px` to `20px` for editorial pages and `14px` to `16px` for dense app surfaces.
- Keep letter spacing at `0`. Do not squeeze type.
- Mix sans and serif intentionally: sans for product UI and navigation, serif for big editorial moments or human warmth.

## Layout

- Use a centered 12-column grid with generous margins: `clamp(2rem, 5vw, 4rem)`.
- Prefer full-width bands with constrained inner content over floating section cards.
- Make heroes product-forward: large headline, concise supporting text, primary action, and a real product/UI visual if relevant.
- Let the first viewport reveal a hint of the next section; avoid isolated poster-like heroes that trap the page.
- Use spacious chapter rhythm: small intro sections, feature bands, comparison grids, and product screenshots with breathing room.
- In dashboards or SaaS screens, keep the same warm palette but increase density: clear tables, compact controls, restrained cards.

## Components

### Buttons

- Primary: clay background, ivory text, 8-12px radius, subtle one-pixel ring.
- Secondary: warm sand or white background, near-black text, warm border.
- Dark section CTA: near-black or ivory depending on contrast.
- Use icon buttons for common actions when an icon exists; add accessible labels/tooltips.

### Cards and Panels

- Use `#ffffff` or `#faf9f5` surfaces on warm backgrounds.
- Use one-pixel warm borders: `#e8e6dc`, `#f0eee6`, or `#c2c0b6`.
- Use soft shadows only when elevation is useful: `0 4px 24px rgba(20, 20, 19, 0.06)`.
- Keep normal card radius at 8-16px; reserve 24-32px radii for hero media or large embedded product surfaces.
- Do not nest cards inside cards.

### Product UI Motifs

- Favor Claude-like product compositions: chat panels, prompt bars, document/artifact surfaces, terminal/code panels, model comparison grids, and calm command palettes.
- Use compact dividers, warm borders, small labels, pill tabs, and tactile hover states.
- Product screenshots or mock interfaces should be legible, not dark, blurred, or decorative.

### Illustrations and Media

- Prefer real product UI, generated bitmap imagery, or simple organic line illustration.
- If using illustration, keep it hand-drawn, conceptual, and limited to clay, charcoal, oat, and muted green.
- Avoid generic abstract SVG blobs and overly glossy SaaS art.

## Interaction and Motion

- Use restrained motion: short fades, small y-translates, accordion reveals, tab transitions, subtle hover color shifts.
- Keep animations under roughly `180ms` for controls and `400ms` for page reveals.
- Respect `prefers-reduced-motion`.
- Do not let motion become the main aesthetic; this style should feel composed and useful.

## Implementation Checklist

1. Inspect the existing app's stack, tokens, and component conventions.
2. Add or map the Claude-inspired tokens through the existing theme layer.
3. Build the actual requested experience, not a style sample.
4. Use responsive constraints for navs, grids, buttons, product panels, and fixed-format UI.
5. Verify text fit and contrast on mobile and desktop.
6. Run the project's formatter/linter/tests when available.
7. For local frontend apps, start the dev server and visually verify the result in a browser.

## Quality Bar

The finished interface should feel like a thoughtful product page or product surface from the Claude ecosystem: warm rather than sterile, editorial rather than loud, precise rather than generic, and useful before it is decorative.
