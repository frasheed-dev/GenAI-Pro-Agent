# Gen AI Pro: Branding and Layout Engine Details

This document serves as the historical context and architecture decisions for the Gen AI Pro image rendering pipeline.

## 1. The Typographic Logo
We shifted away from complex 3D graphic logos (like the circular brain badge) to a highly scalable, pure-typography "app icon" logo approach.
- **Why?** Flat typographical logos blend seamlessly into generated news images without looking like "stickers." They also scale perfectly and are highly legible.
- **The Design:** A perfect circular badge with a semi-transparent black background (`fill=(0, 0, 0, 180)`).
- **The Text:** 
  - Line 1: `Gen` (White, `#FFFFFF`) and `AI` (Yellow, `#F4B41A`).
  - Line 2: `Pro` (Yellow, `#F4B41A`).
- **Implementation:** The logo is *mathematically drawn* natively in `src/core/image_generator.py` using Pillow. There is no source PNG file pasted during normal execution. 

## 2. Dynamic Highlight Bounding Boxes
The core feature of our news images is the yellow highlighting behind key phrases.
- **The Challenge:** Different words have different vertical drops (descenders). E.g., "Claude" sits on the baseline, while "Deploying" drops below the baseline due to the "p" and "g". If we draw a tight box for "Claude" and a deep box for "Deploying" on the same line, the highlights look jagged and stepped.
- **The Solution:** The engine pre-calculates the `max_hl_descent` for *all highlighted words on the current line*. It then uses this maximum depth to draw a perfectly flush, continuous yellow box that seamlessly wraps across contiguous words like `*status quo*`.
- **Padding:** We use exactly 10px of padding on all sides. The bounding math relies explicitly on Pillow's `font.getbbox(word)` which guarantees absolute precision.

## 3. Social Media Links
- We previously used Courier for the Facebook/LinkedIn text links at the bottom.
- We have completely moved to the main `Roboto-Black.ttf` font for the social links. 
- **Why?** It reduces our dependency on multiple font files and creates a tighter, more modern brand cohesion between the headline, the logo, and the footer links.

## 4. Standalone Profile Logo
- If you need the logo for a profile picture, execute `tests/generate_social_logo.py`. 
- This script uses the exact geometric scaling formulas as the main engine but generates a massive `1000x1000` image with a solid dark background (`#0A0A0A`) which is required by social networks. It outputs to `branding/profile_logo.png`.
