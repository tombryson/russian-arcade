# Barsik setting off — illustration provenance

Created 10 September 2026 with the built-in image-generation tool, using the existing Barsik artwork as the character/style reference. This asset originally appeared beside the introduction on the first-delivery tutorial's opening screen. The app now uses a [transparent cutout derived from this original](barsik-setting-off-transparent-v2.md).

- [Source PNG](barsik-setting-off-v1.png): the final generated image, copied without changes.
- [Application WebP](../../../flask_vocab_app/ui/src/assets/barsik-setting-off-v1.webp): the same composition encoded at quality 85 for web delivery.
- [Identity reference](../../../flask_vocab_app/ui/src/assets/barsik.webp): the existing hero illustration, unchanged.

The first result painted a checkerboard rather than producing an alpha channel. It was not used in the app. A targeted built-in edit replaced that background with warm cream; the final image is intentionally opaque, framed using CSS. No CLI generation or application API key was used.

## Initial prompt

Use case: illustration-story.
Asset type: a new standalone character illustration for the “Before we set off…” introduction in a Russian-learning application.
Input image 1 is the identity and illustration-style reference, not the composition to reproduce.
Primary request: the exact same Barsik, a ginger cat postman, cheerfully jogging towards the right as he sets off on his delivery, holding a small stack of three gold Lingocoins in his forward paw. His red satchel is across his body, with the cream envelope and its cobalt circular seal peeking securely out of the bag.
Preserve Barsik’s recognizable face: orange tabby forehead stripes, triangular ears, cream muzzle, large cream eyes with dark navy oval pupils, little coral nose, simple smiling mouth and fine dark whiskers; preserve the oversized cobalt-blue postal jacket, gold button, tomato-red satchel and orange striped tail.
Pose: full body in a lively three-quarter side view, one foot forward and the other lifted behind, tail curved back, ears alert, looking ahead with a friendly expression. Two arms and two legs with natural cat paws. The forward paw visibly holds the coins; no loose shower of money.
Style: match the reference’s handmade torn-paper collage, richly tactile painted paper, visible paper fibres and ink grain, irregular cut edges, simple bold shapes and restrained paper-layer shadows. This should look like another illustration from the same picture book, with the same ginger, cobalt, tomato, marigold, cream and dark-ink palette.
Composition: compact standalone cutout on a genuinely transparent alpha background, approximately square 1024px canvas, the entire cat, tail, bag, letter and coins comfortably inside the edges with a small clear margin. Strong readable silhouette at 250–320px on a webpage.
Coins: warm gold paper circles; the visible front coin bears a single dark-ink Cyrillic “Л”, matching the application’s Lingocoin symbol.
No moon, postbox, landscape, planets, stars, scenery, floor, rectangular paper backdrop, lettering apart from “Л”, captions, borders or watermark. No glossy 3D, vector-flat clip art or photographic rendering. Preserve actual transparency, not a checkerboard painted into the artwork.

## Final edit prompt

Use case: precise-object-edit.
Input image: the new Barsik illustration is the edit target.
Change only the background: remove the entire grey-and-white checkerboard and replace it with one perfectly uniform warm cream colour, hex #FFF5DC, including all gaps between the cat’s legs, whiskers, tail, coins and bag. No checkerboard, transparency effect, pattern, gradient, border or new scenery.
Keep the exact same orange cat, face, jogging pose, proportions, three coins with the Cyrillic Л, blue jacket, red satchel, cream envelope, torn-paper texture and colours unchanged. Keep the whole composition and framing. Preserve crisp irregular paper edges against the cream background. Output a clean finished picture-book illustration with a plain cream background.
