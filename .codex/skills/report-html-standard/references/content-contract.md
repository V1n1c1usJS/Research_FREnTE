# Content Contract

Use this shape when normalizing report input before rendering.

```json
{
  "report_title": "string",
  "report_subtitle": "string",
  "context_summary": "string",
  "metadata": {
    "date_label": "string",
    "source_note": "string"
  },
  "metrics": [
    {
      "label": "string",
      "value": "string",
      "icon": "string",
      "tone": "blue|green|red|dark"
    }
  ],
  "sections": [
    {
      "id": "string",
      "title": "string",
      "intro": "string"
    }
  ],
  "figures": [
    {
      "id": "string",
      "section": "string",
      "title": "string",
      "tag": "string",
      "tag_color": "blue|green|purple|orange|red",
      "icon": "string",
      "image_path": "string",
      "summary": "string",
      "interpretation": "string",
      "highlight": "string"
    }
  ],
  "output_path": "string"
}
```

## Notes

- `figures` is the core collection for presentation-like reports.
- `metrics` is optional if the chosen report pattern is purely narrative.
- `section` should map figures into visual groups when the report has thematic blocks.
- `image_path` should point to a local generated image whenever possible.
- If an image is missing, render a placeholder instead of removing the card.
