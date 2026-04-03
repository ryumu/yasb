# Desktop Name Widget

| Option | Type | Default | Description |
|---|---|---|---|
| `label` | string | `"{name}"` | Primary label template. |
| `label_alt` | string | `"Desktop {index}"` | Alternative label template. |
| `update_interval` | integer | `1` | Update interval in seconds. Must be between 1 and 3600. |
| `class_name` | string | `""` | Additional CSS class name for the widget. |
| `callbacks` | dict | `{ 'on_left': 'toggle_label', 'on_middle': 'do_nothing', 'on_right': 'do_nothing' }` | Mouse callbacks. |
| `animation` | dict | `{'enabled': true, 'type': 'fadeInOut', 'duration': 200}` | Animation settings for label toggle. |
| `container_shadow` | dict | `None` | Container shadow options. |
| `label_shadow` | dict | `None` | Label shadow options. |

## Placeholders

`label` and `label_alt` support these placeholders:
- `{name}`: Current virtual desktop name.
- `{index}`: Current virtual desktop index (1-based).
- `{desktop[name]}` and `{desktop[index]}`: Same values as above.

## Example Configuration

```yaml
desktop_name:
  type: "ryumu.desktop_name.DesktopNameWidget"
  options:
    label: "<span>\udb81\udc3d</span> {name}"
    label_alt: "Desktop {index}"
    update_interval: 1
    callbacks:
      on_left: "toggle_label"
      on_middle: "do_nothing"
      on_right: "do_nothing"
    label_shadow:
      enabled: true
      color: "black"
      radius: 3
      offset: [1, 1]
```

## Description of Options
- **label**: Primary label template.
- **label_alt**: Alternative label template shown by callback (for example `toggle_label`).
- **update_interval**: Refresh rate in seconds.
- **class_name**: Extra CSS class name.
- **callbacks**: Mouse callback mapping (`on_left`, `on_middle`, `on_right`).
- **animation**: Toggle animation config.
- **container_shadow**: Container shadow options.
- **label_shadow**: Label shadow options.

## Example Style

```css
.desktop-name {}
.desktop-name.your_class {} /* If class_name is set */
.desktop-name .widget-container {}
.desktop-name .label {}
.desktop-name .label.alt {}
.desktop-name .icon {}
```
