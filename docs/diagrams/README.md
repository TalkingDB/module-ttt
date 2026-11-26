# Diagram sources

Every diagram in this repository's documentation is written in [Mermaid](https://mermaid.js.org/) and kept here as a `.mmd` file. The pictures in `docs/images/` are rendered from these files, once for GitHub's light theme and once for its dark theme, so they show the same on the web, in the GitHub mobile app and in any Markdown viewer.

## Change a diagram

1. Edit the `.mmd` file. Preview it on [mermaid.live](https://mermaid.live) or in your editor's Mermaid preview.
2. Re-render both images from this folder:

   ```bash
   npx -y @mermaid-js/mermaid-cli -i NAME.mmd -o ../images/NAME.svg -c light.json -b white
   npx -y @mermaid-js/mermaid-cli -i NAME.mmd -o ../images/NAME-dark.svg -c dark.json -b "#0d1117"
   ```

3. Commit the `.mmd` file and both `.svg` files together.

## Rules these diagrams follow

- Under 20 boxes; split anything bigger.
- No fixed colours; the light and dark renders take their colours from the theme. "This repository" is marked with a thicker border.
- `accTitle` and `accDescr` in every file. The description is also the image's alt text.
- Labels with brackets or colons are quoted, for example `-->|"contains (weight: 3.0)"|`.
