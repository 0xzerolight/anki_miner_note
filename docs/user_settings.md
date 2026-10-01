# Where do I find any of this ?

Lapis comes with a few variables that alters the way it looks. In order to change any variable, select a Lapis card in the Browser (`Browse`), then click on `Cards` (top-left of the card editor), and navigate to the `Styling` section.  
These variable enable some popular CSS tweaks to the card one might want.
You should get instant feedback when changing a variable on the preview inside Anki, so don't be afraid to try changing them.  
Make sure you **don't forget** a _doublequote_ or a _semi-colon_ at the end of a line.

# Settings breakdown

`main-picture-position`, `sentence-position` and `audio-buttons` have mobile counterparts (`--mobile-…`), so phones can use a different layout. The other settings apply to every platform.

### main-picture-position

Valid values : `"right"`, `"left"`, `"alt"`.
Default value : `"right"`
| values | behaviour |
| ---------- | --------- |
| `right` | Next to the vocab (default) |
| `left` | Swaps vocab and picture |
| `alt` | Outside of the header, next to the sentence |

### sentence-furigana

Controls how your sentence furigana is displayed.
Valid values : `"hover"`, `"always"`, `"off"`
Default value : `"hover"`

### sentence-position

Displays the sentence above or below the definition box.
Valid values : `"above"`, `"below"`
Default value : `"above"`
Default on mobile  : `"below"`

### audio-buttons

Change the position of audio buttons
Valid values : `"header`, `"fixed"`, `"alt"`

| values | behaviour |
| ---------- | --------- |
| `header` | Next to the pitch |
| `fixed` | In the bottom-left corner |
| `alt` | Next to the sentence |

### nsfw-blur-contained

The blur effect for NSFW tagged card overflows outside the picture box by default. You can disable this with this variable  
Valid values : `"on"`, `"off"`
Default value : `"off"`

### open-misc-info

Expands the misc-info box by default
Valid values : `"on"`, `"off"`
Default value : `"off"`

### glossary-separator

Adds a line between different dictionaries in glossaries.
Valid values : `"on"`, `"off"`
Default value : `"off"`

Note : The formatting of JMDict has all meanings of a word in its own entry, so they all get separated.

### jitendex-format

Customizes Jitendex dictionary by removing some information
Valid values : `"full"`, `"minimal"`, space-separated list of `no-tags`, `no-sentence`, `no-forms`, `no-xref`, `no-img`
Default value : `"full"`
| values | behaviour |
| ---------- | --------- |
| `minimal` | removes **everything** except the meanings. Careful as it will also remove explanations you might want to keep. |
| `no-tags` | removes POS tags. |
| `no-sentence` | removes example sentence. |
| `no-forms` | removes the forms table. |
| `no-xref` | removes cross references to other entries (See also...) |
| `no-img` | removes images |

Therefore, having `--jitendex-format: "no-forms no-sentence no-xref";` will hide forms, examples sentences and cross references.

# Notable Settings

You can achieve a layout similar to Lapis-modified with the following settings :
```css
--main-picture-position: "alt";
--sentence-position: "below";
--audio-buttons: "alt";
--mobile-main-picture-position: "alt";
--mobile-sentence-position: "below";
--mobile-audio-buttons: "alt";
```

# Is that it ? How can I change xx or yy ?

If you think you need to change something in the layout, and that it would also benefit other users of Lapis. We are open to suggestions, please open an issue.