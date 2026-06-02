---
name: claude-design
description: "Create or refactor production frontend interfaces in a Claude-inspired visual language. Use when building or restyling web pages, dashboards, SaaS tools, React/Next.js components, landing pages, or design systems that should feel like the public Claude/Anthropic product experience: warm paper surfaces, charcoal dark mode, terracotta accents, editorial typography, calm product layouts, restrained motion, and a functional light/dark theme switch."
---

# Claude Design

Build working interfaces inspired by the public Claude/Anthropic design language. Treat this as a visual direction, not a request to clone protected brand assets.

## Design Direction

- Make the experience warm, calm, editorial, precise, and product-forward.
- Prefer ivory paper surfaces, near-black text, clay accents, warm borders, and quiet elevation.
- Keep operational tools dense and scannable. Use generous editorial spacing only where the page purpose supports it.
- Avoid purple gradients, blue-slate SaaS palettes, glass effects, decorative blobs, neon accents, and excessive card nesting.
- Preserve the existing framework, data flow, routing, component patterns, and accessibility behavior.
- Do not use Claude logos, screenshots, proprietary font files, or wordmarks unless the user provides them or the project already contains them.

## Theme Tokens

Define semantic variables first, then map existing utility classes or components onto them.

```css
:root {
  color-scheme: light;
  --background: #faf9f5;
  --foreground: #141413;
  --foreground-soft: #30302e;
  --muted: #87867f;
  --surface: #ffffff;
  --surface-soft: #f0eee6;
  --border: #dedcd1;
  --border-strong: #c2c0b6;
  --accent: #c96442;
  --accent-soft: rgba(201, 100, 66, 0.13);
  --accent-contrast: #fffaf2;
  --focus: #3898ec;
  --chart-up: #b53333;
  --chart-down: #2f7f68;
  --radius-control: 10px;
  --radius-panel: 16px;
  --shadow-soft: 0 12px 44px rgba(20, 20, 19, 0.08);
}

[data-theme="dark"] {
  color-scheme: dark;
  --background: #141413;
  --foreground: #faf9f5;
  --foreground-soft: #e8e6dc;
  --muted: #b0aea5;
  --surface: #1d1d1b;
  --surface-soft: #262623;
  --border: #3d3d3a;
  --border-strong: #5e5d59;
  --accent: #d97757;
  --accent-soft: rgba(217, 119, 87, 0.18);
  --accent-contrast: #141413;
  --focus: #6a9bcc;
  --chart-up: #f07f70;
  --chart-down: #78bca9;
  --shadow-soft: 0 18px 54px rgba(0, 0, 0, 0.32);
}
```

Use clay for primary actions and active states. Use mineral green, oat, olive, and sky tones sparingly for secondary information.

## Typography

Prefer `Anthropic Sans`, `Anthropic Serif`, and `Anthropic Mono` only when the project already provides licensed files. Otherwise use local aliases or open substitutes that preserve the same temperament.

For offline-safe local aliases:

```css
@font-face {
  font-family: "Claude Sans Local";
  src: local("Avenir Next"), local("Helvetica Neue"), local("PingFang SC");
  font-weight: 300 800;
}

@font-face {
  font-family: "Claude Serif Local";
  src: local("New York"), local("Charter"), local("Georgia"), local("Songti SC");
  font-weight: 400 800;
}

@font-face {
  font-family: "Claude Mono Local";
  src: local("SF Mono"), local("Menlo"), local("Monaco");
  font-weight: 400 800;
}
```

- Use sans for navigation, controls, body copy, and dense product UI.
- Use serif selectively for page titles, editorial headings, and warm human moments.
- Use mono for code, tickers, symbols, dates, and financial values.
- Keep letter spacing at `0`. Use line-height around `1.0-1.1` for large headings.
- Avoid network font dependencies when the build environment must work offline. If using `next/font/google`, confirm production builds can fetch and self-host the files.

## Layout And Components

- Use a centered 12-column grid and responsive outer margins such as `clamp(2rem, 5vw, 4rem)`.
- Prefer full-width bands with constrained content over floating page sections.
- Keep normal card radius around `8-16px`; reserve `24-32px` for hero media or large product surfaces.
- Use one-pixel warm borders and subtle shadows. Avoid cards inside cards.
- Build clear primary clay buttons, quiet secondary buttons, compact icon buttons, segmented controls, tabs, toggles, and data tables.
- Favor legible product UI: prompt bars, chat panels, document surfaces, command palettes, terminal panels, dashboards, and comparison grids.
- Use Lucide icons where available. Add accessible labels and tooltips for icon-only actions.

## Light And Dark Mode

Always implement both modes unless the user explicitly opts out.

- Store semantic tokens in CSS variables and switch them with `data-theme`.
- Persist the selected theme in `localStorage`.
- Default to the operating-system preference when no stored choice exists.
- Use a compact sun/moon toggle with an accessible label and visible focus state.
- In React SSR frameworks, prevent hydration mismatches: return a stable server snapshot and synchronize browser preference after hydration. Keep browser-only logic in a small client component.
- Make charts and canvas-based widgets reread CSS variables after theme changes.

## Motion

- Keep control transitions around `120-180ms`.
- Keep page reveals below roughly `400ms`.
- Use small fades, short y-translates, accordion reveals, tab transitions, and subtle hover color changes.
- Respect `prefers-reduced-motion`.

## Implementation Workflow

1. Inspect the current stack, global CSS entry, theme layer, and shared layout components.
2. Read local framework documentation before changing framework-specific code.
3. Add semantic light/dark tokens and font stacks.
4. Refactor shared surfaces first so the theme reaches all pages with minimal churn.
5. Add a persisted theme toggle and verify SSR hydration behavior.
6. Update charts, tables, empty states, and active controls so they use semantic colors.
7. Run formatter, lint, tests, and production build.
8. Start the dev server and verify desktop/mobile views in a browser.

## Browser Verification

Check both light and dark mode on every primary route:

- Confirm the page canvas, panels, controls, and charts change together.
- Click the theme toggle and reload to verify persistence.
- Inspect computed fonts for body, headings, and mono values.
- Check for console hydration warnings and runtime errors.
- Verify text fit, contrast, focus states, and non-overlapping layouts.

The finished interface should feel Claude-inspired without pretending to be an official Claude product.
