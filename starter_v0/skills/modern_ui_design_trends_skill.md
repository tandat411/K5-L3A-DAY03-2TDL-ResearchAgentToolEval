# Skill: ui-design-modern-trends

## Overview
This skill defines the modern standards, aesthetic principles, and technical guidelines for creating cutting-edge, highly usable, and visually stunning user interfaces (UI) and user experiences (UX) for web and mobile applications.

---

## 1. Layout & Grid Systems
* **Bento Grid Layout:** Utilize asymmetrical grid structures (inspired by Japanese bento boxes) to organize content cards of varying sizes with clean padding and rounded corners (`rounded-2xl` or `rounded-3xl`).
* **Whitespace & Breathing Room:** Avoid clutter. Maintain generous spacing around primary actions and key data visualizations.
* **Responsive Fluidity:** Combine CSS Grid and Flexbox for seamless adaptation across mobile, tablet, and widescreen desktop displays.

---

## 2. Color Theory & Dark Mode
* **Semantic Palettes:** Use restrained primary colors paired with rich neutrals. Avoid pure black (`#000000`) for dark mode; instead, use deep charcoal/slate tones (`#0f172a`, `#111827`) to reduce eye strain and allow subtle elevation layers.
* **Surface Hierarchy (Dark Mode):** 
  * Background: Base layer.
  * Cards/Modals: Elevated layers with slightly lighter hex codes or subtle white borders (`border-white/10`).
* **Accents & Glows:** Use vivid, high-contrast accent gradients or subtle neon glows to highlight primary CTAs.

---

## 3. Typography & Hierarchy
* **Font Pairing:** Combine a clean, geometric or humanist sans-serif for body text (e.g., Inter, Plus Jakarta Sans, Geist) with a modern display font for headings.
* **Type Scale & Line Height:** 
  * Headings: Tight line-height (`leading-tight` or `1.1`) with bold weights (`font-bold`, `font-extrabold`).
  * Body: Readable line-height (`leading-relaxed` or `1.6`) with regular or medium weights.
* **Fluid Typography:** Use CSS `clamp()` or Tailwind responsive text classes (`text-sm md:text-base`) to scale text smoothly across viewports.

---

## 4. Visual Styles & Effects
* **Glassmorphism:** Use semi-transparent backgrounds with backdrop blur (`backdrop-blur-md bg-white/10 border border-white/20`) for floating headers, navigation bars, and modal overlays.
* **Subtle Depth & Shadows:** Avoid heavy drop shadows. Instead, use soft, multi-layered shadows combined with thin border strokes to define depth.
* **Gradients:** Apply subtle mesh gradients or linear gradients on text highlights, badges, and card backgrounds for a dynamic, premium feel.

---

## 5. Spacing & Component Architecture
* **Spacing Rule:** Strictly adhere to the 4px/8px grid system for margins, padding, and gaps (`p-2`, `p-4`, `p-6`, `p-8`).
* **Micro-Components:** 
  * **Buttons:** Generous padding (`px-5 py-2.5`), smooth hover/active state transitions (`transition-all duration-200`), and clear focus rings.
  * **Inputs:** Clean borders with distinct focus states (`ring-2 ring-primary/50`).

---

## 6. Micro-interactions & Motion
* **Smooth Transitions:** Ensure all state changes (hover, click, modal open/close) feature short, buttery-smooth transitions (`duration-200 ease-in-out`).
* **Feedback States:** Provide immediate visual feedback for user actions (loading spinners, checkmark animations on success, subtle shake on error).

---

## 7. Accessibility (a11y)
* **Contrast Ratios:** Ensure text and interactive elements meet WCAG AA standards (minimum 4.5:1 contrast ratio for normal text).
* **Touch Targets:** Interactive elements must have a minimum interactive area of $44 \times 44 \text{ px}$ on mobile devices.