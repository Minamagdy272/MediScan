---
name: Clinical Clarity
colors:
  surface: '#f9f9ff'
  surface-dim: '#d1daf4'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e9edff'
  surface-container-high: '#e1e8ff'
  surface-container-highest: '#d9e2fc'
  on-surface: '#121b2e'
  on-surface-variant: '#424752'
  inverse-surface: '#273044'
  inverse-on-surface: '#edf0ff'
  outline: '#727783'
  outline-variant: '#c2c6d4'
  surface-tint: '#005db8'
  primary: '#004c99'
  on-primary: '#ffffff'
  primary-container: '#1464c0'
  on-primary-container: '#d8e4ff'
  inverse-primary: '#aac7ff'
  secondary: '#00687b'
  on-secondary: '#ffffff'
  secondary-container: '#73e0fe'
  on-secondary-container: '#006275'
  tertiary: '#044c99'
  on-tertiary: '#ffffff'
  tertiary-container: '#2e65b3'
  on-tertiary-container: '#d9e4ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#aac7ff'
  on-primary-fixed: '#001b3e'
  on-primary-fixed-variant: '#00468d'
  secondary-fixed: '#afecff'
  secondary-fixed-dim: '#66d5f2'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5d'
  tertiary-fixed: '#d6e3ff'
  tertiary-fixed-dim: '#aac7ff'
  on-tertiary-fixed: '#001b3e'
  on-tertiary-fixed-variant: '#00458d'
  background: '#f9f9ff'
  on-background: '#121b2e'
  surface-variant: '#d9e2fc'
  surface-soft: '#F4F9FD'
  surface-cyan: '#EAF8FC'
  border-muted: '#DCE6F0'
  text-muted: '#667085'
  status-critical: '#D93025'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-metadata:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar-width: 280px
  chat-max-width: 800px
  gutter: 24px
  margin-mobile: 16px
  stack-gap: 32px
  composer-bottom-offset: 40px
---

## Brand & Style

The brand personality is authoritative yet empathetic—a digital clinician that prioritizes accuracy and evidence over flair. It targets medical professionals and patients who require a focused, distraction-free environment for health data analysis. 

The design style is **Minimalism** blended with **Corporate / Modern**. It adopts the functional simplicity of a chatbot-first interface (like ChatGPT) but implements a stricter, more structured aesthetic to evoke a sense of clinical reliability. The interface relies on generous whitespace, a light-flooded "clean room" color palette, and high-quality typography rather than decorative elements. Visual hierarchy is established through precise alignment and intentional use of the brand’s blue tones for primary actions.

## Colors

The palette is rooted in medical blues and clinical whites to establish immediate trust. 

- **Primary Blue (#1464C0)** is reserved for the most important interactions: the "Send" button, primary action items, and active sidebar states.
- **Surface Tones** utilize `#F4F9FD` and `#EAF8FC` to create subtle differentiation between the sidebar, the main chat canvas, and secondary information blocks like evidence citations.
- **Neutral Text (#172033)** provides high legibility against the light surfaces, ensuring that clinical findings are easy to read.
- **Borders (#DCE6F0)** are kept extremely light, acting as faint guides rather than heavy separators. 
- **Status Colors** should be used sparingly; the "Critical" red is only for safety escalations or insufficient evidence warnings.

## Typography

This design system uses **Hanken Grotesk** as its primary typeface. It is a modern, sharp, and highly legible sans-serif that balances a technical feel with human warmth. 

- **Clinical Reports:** Use `body-lg` for all assistant responses to ensure maximum readability. Use `headline-md` for internal section headers (e.g., "Imaging Findings").
- **Metadata & Citations:** Evidence IDs (e.g., [EV-001]) should use the `label-caps` or a subtle `mono-metadata` font to distinguish them as technical references.
- **Hierarchy:** Maintain a clear vertical rhythm. Information density should be low, with increased line heights (1.5x) for body text to reduce cognitive load during analysis.

## Layout & Spacing

The layout follows a **Fixed-Column Chat** model. While the screen may be wide, the conversation container is constrained to `800px` to maintain optimal line lengths for reading clinical text.

- **Sidebar:** A fixed-width left sidebar (`280px`) houses the logo and chat history. It collapses into a hamburger menu on mobile.
- **Main Surface:** A wide, white canvas with a centered column. 
- **Message Spacing:** Use a `32px` vertical gap between user and assistant messages to allow the conversation to "breathe."
- **Mobile Adaptivity:** On devices smaller than 768px, the sidebar is hidden, and the central column takes 100% width with `16px` side margins. The message composer remains pinned to the bottom but scales to the screen width.

## Elevation & Depth

To maintain a "clinical" and "flat" aesthetic, avoid traditional heavy shadows. Depth is communicated through **Tonal Layers** and extremely subtle **Ambient Shadows**.

- **Level 0 (Canvas):** The primary background color (White).
- **Level 1 (Sidebar/Containers):** Uses `surface-soft` (#F4F9FD) to define the sidebar and evidence blocks.
- **The Composer:** This is the only element with a shadow. Use a very diffused, low-opacity shadow (`0 4px 20px rgba(23, 32, 51, 0.05)`) to make it appear slightly lifted above the scrolling text.
- **Borders:** Use `border-muted` (#DCE6F0) for the message composer and horizontal dividers within clinical reports. Borders should be 1px thick.

## Shapes

The shape language is **Rounded**, striking a balance between the sterile "sharp" corners of legacy medical software and the overly "bubbly" feel of consumer apps.

- **Message Composer:** Uses `rounded-xl` (1.5rem) to create a soft, inviting focal point at the bottom of the screen.
- **Action Buttons & Chips:** Use `rounded-lg` (1rem) for "New Chat" and citation chips.
- **Status Banners:** Use `rounded-md` (0.5rem) to signify importance while maintaining a structural look.

## Components

### Chat Composer
The primary input is a large, `rounded-xl` text area with a 1px border. The "Send" button is a solid Primary Blue icon or pill positioned inside the right edge of the composer.

### Assistant Messages
Assistant responses are unboxed (no bubble) and appear directly on the white canvas. This emphasizes that the AI is providing a "document" or "report" rather than just a chat bubble. User messages may be slightly boxed in `surface-soft` or right-aligned to provide contrast.

### Evidence & Citations
- **Citation Chips:** Small, `#EAF8FC` background chips with `#1464C0` text.
- **Evidence Accordion:** A collapsed section at the bottom of a response. When expanded, it reveals a `surface-soft` card containing the source details in `body-sm`.

### Processing States
A vertical stepper-style list appears inside the assistant’s message area while the pipeline is active. Use a small, rotating primary blue spinner for the active step and a checkmark for completed steps.

### Safety Banners
Warnings (e.g., "Insufficient Evidence") appear as full-width banners with a light tint of the status color and a 1px stroke. They should be positioned immediately above or below the relevant message.

### Action Buttons (PDF/Email)
Ghost-style buttons (transparent background, primary blue border and text) positioned discretely under a completed report to keep the interface focused on the information.