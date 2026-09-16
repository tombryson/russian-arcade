# Barsik setting off — transparent cutout

Created 10 September 2026 from the [original cream-background PNG](barsik-setting-off-v1.png), with the user's explicit approval to use local image processing. This version replaces the framed illustration on the first-delivery introduction; its position and size are unchanged.

- [Transparent PNG](barsik-setting-off-transparent-v2.png): 1254 × 1254 RGBA master.
- [Application WebP](../../../flask_vocab_app/ui/src/assets/barsik-setting-off-transparent-v2.webp): quality 85, with lossless alpha.
- [Original generation prompts](barsik-setting-off-v1.md): character and illustration provenance.

The attempted built-in background extraction produced an opaque checkerboard and was not used. The final cutout uses the original artwork, processed locally with Python and Pillow; no new character illustration was generated.

Cream pixels within 14 RGB levels of (253, 245, 219), connected to the canvas boundary, were made transparent. This connectivity rule preserves enclosed cream details such as the eyes and letter. A narrow edge pass estimated opacity from nearby solid foreground pixels and removed the original cream matte, reducing pale fringes on dark backgrounds. Interior foreground pixels, composition and canvas dimensions were preserved. The opaque original remains available.

The WebP was encoded with `cwebp -q 85 -m 6 -alpha_q 100 -alpha_filter best`. Its alpha channel was verified to match the PNG exactly, with values spanning 0–255. The result was inspected against both application background colours and in the live tutorial preview. The old CSS corner clipping was removed so the cutout's silhouette is displayed in full.
