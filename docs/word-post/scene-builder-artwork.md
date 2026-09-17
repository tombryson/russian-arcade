# Scene Builder artwork

Generated on 16 September 2026 using the built-in image generation tool. These are bundled assets. Starting a game does not generate images or incur image API costs.

The scene uses a small set of reusable illustrations. CSS positions the cat and book relative to the table. The walking and taxi pictures illustrate transport, while the written scenario supplies time, destination and repetition. A still image cannot establish those facts by itself.

## Files

Paths are relative to `flask_vocab_app/static/images/scene-builder/`.

| File | Dimensions | Background | Size |
| --- | --- | --- | --- |
| `cat-v1.webp` | 1200 × 1200 | Transparent alpha | 254 KB |
| `table-v1.webp` | 1200 × 1200 | Transparent alpha | 106 KB |
| `book-v1.webp` | 1200 × 1200 | Transparent alpha | 137 KB |
| `book-upright-v1.webp` | 1200 × 1200 | Transparent alpha | 134 KB |
| `walking-v1.webp` | 1200 × 800 | Cream | 79 KB |
| `taxi-v1.webp` | 1200 × 800 | Cream | 88 KB |
| `walking-away-v1.webp` | 1200 × 800 | Cream | 61 KB |
| `taxi-moving-v1.webp` | 1200 × 800 | Cream | 70 KB |
| `taxi-away-v1.webp` | 1200 × 800 | Cream | 65 KB |
| `doorway-inside-v1.webp` | 1200 × 800 | Interior scene | 74 KB |
| `courtyard-in-v1.webp` | 1200 × 800 | Courtyard scene | 105 KB |
| `courtyard-out-v1.webp` | 1200 × 800 | Courtyard scene | 112 KB |

Generated PNG files were resized to a maximum edge of 1200 pixels and encoded as WebP at quality 90. Alpha was retained for the four isolated illustrations. No objects were removed, repainted or added during conversion.

## Layout guidance

- The table has transparent space above and below it. Its tabletop is at roughly 13–35% of the image height; the front feet are at about 87%.
- Place the cat well inside the empty space beneath the tabletop for **под столом**. Do not let its ears overlap the tabletop.
- For **на столе**, align the cat's feet with the visible top surface.
- Use `book-v1.webp` for a book lying flat and `book-upright-v1.webp` for a book standing on its bottom edge. Rotating the flat image does not establish the correct perspective.
- For **перед столом** and **за столом**, layering must show the depth relationship. Position alone is insufficient.
- Keep the table and cat at consistent scales across related questions. Changes should reflect the tested relationship, not arbitrary decoration.
- The motion scenes are illustrative context. Do not reuse the arrival illustration for departure unless the scene and its accompanying description clearly establish departure.
- `walking-away-v1.webp` shows the man facing away from the café. `taxi-moving-v1.webp` shows the passenger travelling towards it; `taxi-away-v1.webp` shows him travelling away.
- `doorway-inside-v1.webp` places his feet on the indoor side of the café threshold. `courtyard-in-v1.webp` places the taxi inside the gate; `courtyard-out-v1.webp` places it on the street outside. These boundaries support the entry and exit contrasts.

## Generation prompts

### walking-away-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: The man is walking AWAY from the café. Place café on right of image, man to its left moving LEFT with his face and leading foot pointing left. Café is visibly behind him, he has already left the doorway and is striding away along pavement. Do not show him facing toward café.


### taxi-moving-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: The man is seated as a visible PASSENGER inside a yellow taxi with a separate driver in front. Show taxi side-threequarter view on left facing and travelling RIGHT toward a distant smaller café on right. A short stretch of road clearly separates taxi from café. All car doors closed. Man must not be standing outside. This is a journey in progress, not an arrival.


### taxi-away-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: The man is seated as a visible PASSENGER inside a yellow taxi with a separate driver in front. Taxi is on left of image, nose pointed LEFT, moving LEFT away from the café which is behind it on the right. All car doors closed. Clearly departing café, not approaching it. Man must not be standing outside.


### doorway-inside-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: View from INSIDE the simple café toward its open teal doorway. The man has just entered and stands fully INSIDE the café, on the indoor wooden floor immediately in front of the door. The outdoor pavement is visible THROUGH the open door BEHIND him. One small café table and chair on left establishes interior; no people besides man. His whole body including feet is visibly on inside side of threshold. Show doorway frame and clear threshold.


### courtyard-in-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: A yellow taxi with the man visible as a PASSENGER and a separate driver has just entered a small enclosed courtyard through its open double gate. Show a clear three-quarter overhead-ish view: gate/fence line across lower foreground, taxi is BEYOND gate INSIDE courtyard facing further inward away from foreground, all wheels already across threshold. Outside street visible below gate. Courtyard contains only paving and simple building wall. Gate leaves open. Make spatial boundary unambiguous. All doors closed. No café required.


### courtyard-out-v1.webp

Use case: illustration-story. Asset type: Russian educational exercise scene. Reference images provide the character, café, yellow taxi and style. Keep the same adult man with brown hair, ochre jacket and blue trousers, the teal café with orange/cream awning, and the simple warm gouache / paper-cut illustration style. Few objects, plain pale cream background, no words or letters anywhere, no arrows or directional symbols, no decorative clutter, no watermark. Landscape composition 3:2 with all central subjects fully visible. Primary request: A yellow taxi with the man visible as a PASSENGER and a separate driver has just exited a small enclosed courtyard through its open double gate. Show a clear three-quarter view: gate/fence line across middle background, taxi in foreground OUTSIDE courtyard facing viewer-left along exterior street. All wheels outside threshold, enclosed courtyard paving and simple building wall visible BEHIND it through gate. Gate leaves open. Make spatial boundary unambiguous. All doors closed. No café required.


### book-upright-v1.webp

Use case: illustration-story. Reference image: the existing red book sprite is a style and object reference. Create a companion isolated transparent sprite showing this SAME red closed hardback book STANDING UPRIGHT ON ITS SHORT BOTTOM EDGE. This must visibly be a portrait-oriented vertical book, long spine vertical on the left, bottom edge horizontal on an implied surface. Front three-quarter view with front red cover dominant and a narrow cream page edge at the right. Keep the simple warm gouache / paper-cut educational illustration and plain red cover with inset border; restrained texture. The book is standing with full height visible, not tilted, not lying flat and not an overhead view. No support props or hands, no lettering, no external drop shadow. Genuinely transparent alpha background, not a depicted checkerboard or white background. One book only, centered in square canvas with safe margins.

### cat-v1.webp

Use case: illustration-story. Asset type: isolated transparent sprite for a Russian educational scene-building game. Create one friendly orange tabby cat, sitting upright in a relaxed pose, front three-quarter view facing slightly left. Round warm face, cream muzzle and belly, orange striped tail curling beside feet. Simple warm flat gouache / paper-cut illustration with clean readable silhouettes and restrained texture, deep navy facial lines. No clothes, no bag, no props. Subject fills most of square canvas with small even safe margin, all ears/tail/feet fully visible. Background must be genuinely transparent with alpha, not a checkerboard depiction or white background. No external drop shadow, ground, scene, letters or watermark. This must be suitable to place beneath or on top of a separate table illustration with HTML.

### table-v1.webp

Use case: scientific-educational. Asset type: isolated transparent wooden table sprite for a Russian learning scene. Create a simple light warm wooden rectangular table, front view with a little visible tabletop surface, table top horizontal, four legs clearly separated with wide open empty space beneath. Flat gouache / paper-cut illustration, clean readable shapes, dark warm outlines, restrained texture, friendly educational storybook style. No objects on or under table. The table fills the majority of a square image, complete table and all feet visible with small even safe margins. Background genuinely transparent with alpha including the empty spaces between legs, not a checkerboard depiction. No ground or external drop shadow, no lettering, no watermark.

### book-v1.webp

Use case: scientific-educational. Asset type: isolated transparent book sprite for a Russian learning scene. Create one simple red closed hardback book resting horizontally, front three-quarter view, pale cream page edges and dark red cover. Clean warm flat gouache / paper-cut illustration, dark warm outlines, restrained texture, readable silhouette. Full book visible, fills most of square canvas with small even safe margins. Genuinely transparent background with alpha, not checkerboard or white. No writing on cover or spine, no surrounding objects, no ground or external shadow, no watermark.

### walking-v1.webp

Use case: illustration-story. Asset type: simple scene illustration for Russian verbs-of-motion learning. One adult man in an ochre jacket and blue trousers walking on foot to a small café entrance, seen from the side. His walking legs and the café door clearly visible; man is on left moving right toward café on right. Simple storefront has one window, entrance door and striped small awning only; no text or symbols. Flat warm gouache / paper-cut educational illustration, clean shapes, limited palette of cream, muted teal, orange and navy, extremely uncluttered. Pale cream background, short pavement line, no cars, no crowds, no extra decorative objects, no letters, no watermark. Landscape composition 3:2, all primary subjects fully in frame. This is a clear simple visual prompt, not a detailed painting.

### taxi-v1.webp

Use case: illustration-story. Asset type: simple scene illustration for Russian verbs-of-motion learning. One adult man in an ochre jacket and blue trousers stands beside a stopped small yellow taxi immediately outside the entrance of a small café, as if he has just got out and arrived. Show him clearly between taxi and café entrance, the taxi stationary with a small plain roof light. Simple storefront has one window, entrance door and striped small awning only; no text or symbols anywhere. Flat warm gouache / paper-cut educational illustration, clean shapes, limited palette of cream, muted teal, orange and navy, extremely uncluttered. Pale cream background, short pavement line, no other cars, crowds or decorative objects, no letters, no watermark. Landscape composition 3:2, all primary subjects fully in frame. This is a clear simple visual prompt, not a detailed painting.


## Activity card illustration

`flask_vocab_app/ui/src/assets/scene-builder-activity-v1.webp` replaces the original inline SVG on the activity card, setup page and completion screen. It is bundled by Vite and displayed at the existing artwork sizes. The question illustrations are unchanged.

Generated with the built-in image tool using the original `barsik.webp` as the character and paper-collage style reference. Final output: 512 × 512 WebP, quality 90.

Prompt: Create a compact activity thumbnail showing the original orange Barsik in his cobalt blue postal jacket, sitting on a small honey-coloured wooden table beside a red book. Preserve his cream muzzle, large cream eyes with navy pupils, triangular ears and tactile torn-paper texture. Keep the whole cat, striped tail and table visible. Use few details and a clear silhouette for display at 86–180 pixels. No text, badges, mailbox, moon or stars.

Final background edit prompt: Preserve the exact cat, table and red book. Replace every checkerboard square, including gaps under the table, with a plain pale warm cream background matching the activity card. Preserve the composition and paper texture; add no scenery, border or text.

The remaining activity cards now use [matching Barsik illustrations](game-activity-artwork.md).
