# Progress bar artwork

Updated 16 September 2026.

The progress bar uses its own running Barsik illustration. The introduction and map images remain separate.

## Asset

[barsik-progress-run-v1.webp](../../flask_vocab_app/static/images/barsik-progress-run-v1.webp) is a 448 × 299 WebP with transparency. It was generated using the built-in image tool, then resized and converted while preserving its alpha channel. No paid application API was used.

The shared header displays it at 56 × 40 CSS pixels, or 48 × 36 on small screens. The whole running pose is visible, with the paws resting within the progress line. Its position is clamped at both ends. Existing progress calculations and introduction steps are unchanged.

The original generated PNG is kept locally at `.codex/generated_images/barsik-progress-run-v1.png`.

## Generation prompt

Use case: illustration-story.
Asset type: a single transparent character sprite for a slim website progress bar.
Input image: character identity and torn-paper material reference ONLY. Create a NEW distinct pose.
Subject: Barsik, the same orange tabby postal cat with cream muzzle and eye whites, dark navy eyes and whiskers, cobalt blue postal jacket with a yellow button, red satchel. A clearly side-on RUNNING pose facing RIGHT, leaning forward, arms bent pumping, one back leg stretched behind and the other driving forwards, striped tail streaming behind. Intent, cheerful expression. A small cream envelope peeks from the satchel. No coin. No waving.
Style: tactile hand-torn painted-paper collage, richly textured orange, cobalt, vermilion and cream. Simplify small details so the full silhouette is very readable at only 56 pixels wide, while preserving the familiar Barsik character.
Composition: landscape 3:2, one complete cat fills the canvas with only a small safe margin; all ears, tail, paws fully visible. Clear energetic compact running silhouette, not a scene.
Background must be genuinely TRANSPARENT with an alpha channel, not a checkerboard depiction or a white/cream background. Isolated character only. No ground, scenery, ground shadow, speed lines, badge, frame, text or watermark.
