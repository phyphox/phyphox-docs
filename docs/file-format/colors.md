# Colors

When creating your own experiments, you can use arbitrary colors by a 6-digit hex code representing the byte values or red, green and blue (see [1](https://en.wikipedia.org/wiki/Web_colors#Hex_triplet) for details), without a leading hash "#".

Alternatively, you can use the names of defined colors. Phyphox often uses orange (#ff7e22) as its default trademark color, but it also defines a palette of additional colors that work well on the typical dark background of phyphox. These are:

| Name | Hex | |
|---|---|---|
| `orange` | `ff7e22` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#ff7e22;border:1px solid rgba(128,128,128,.4)"></span> |
| `red` | `fe005d` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#fe005d;border:1px solid rgba(128,128,128,.4)"></span> |
| `magenta` | `eb46f4` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#eb46f4;border:1px solid rgba(128,128,128,.4)"></span> |
| `blue` | `39a2ff` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#39a2ff;border:1px solid rgba(128,128,128,.4)"></span> |
| `green` | `2bfb4c` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#2bfb4c;border:1px solid rgba(128,128,128,.4)"></span> |
| `yellow` | `edf668` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#edf668;border:1px solid rgba(128,128,128,.4)"></span> |
| `white` | `ffffff` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#ffffff;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakorange` | `ffc399` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#ffc399;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakred` | `ff7cac` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#ff7cac;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakmagenta` | `f6aafa` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#f6aafa;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakblue` | `9dd1ff` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#9dd1ff;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakgreen` | `a1fdaf` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#a1fdaf;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakyellow` | `e7e09b` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#e7e09b;border:1px solid rgba(128,128,128,.4)"></span> |
| `weakwhite` | `c4c4c4` | <span style="display:inline-block;width:3em;height:1em;vertical-align:middle;background:#c4c4c4;border:1px solid rgba(128,128,128,.4)"></span> |

The advantage of using these color (besides using intuitive names) is that phyphox can adapt them even for future functions. For example, a bright mode or an export function for printing is introduced, which requires colors to work on a bright (or even white) background. Yellow from the list above could automatically be replaced by a darker variation working well on the bright background.
