# Second Counter — Home Assistant Integration

A custom Home Assistant integration distributed via [HACS](https://hacs.xyz/) that provides a high-precision, continuous **1-second incrementing counter sensor**.

It bypasses standard template refresh delays, runs reliably without temporal drift on Home Assistant's event loop (`asyncio`), and exposes `start`, `pause`, `reset`, and `set_value` services for use in automations or Developer Tools.

---

## Features

- ⏱ **Zero-drift ticker** — clock-compensated `asyncio.sleep` prevents counter from skewing over time.
- 🧩 **Multiple instances** — add as many counters as you need via **Settings › Devices & Services**.
- 🔧 **Four services** — `start`, `pause`, `reset`, `set_value` available in automations and Developer Tools.
- 🖥 **UI config flow** — no `configuration.yaml` editing required.

---

## Installation via HACS

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/username/ha-second-counter` with category **Integration**.
4. Search for **Second Counter** and install.
5. Restart Home Assistant.
6. Go to **Settings › Devices & Services › Add Integration** and search for **Second Counter**.

---

## Configuration

During setup you can configure:

| Field | Default | Description |
|---|---|---|
| Name | `Second Counter` | Friendly name for the sensor entity |
| Initial Value | `0` | Value the counter starts/resets to |
| Start Immediately | `true` | Whether to begin counting right away |

These settings can be updated later via the integration's **Configure** button.

---

## Services

| Service | Description |
|---|---|
| `second_counter.start` | Resume (or begin) counting |
| `second_counter.pause` | Pause without resetting |
| `second_counter.reset` | Reset to the configured initial value |
| `second_counter.set_value` | Set counter to a specific integer (`value` field) |

---

## ⚠️ IMPORTANT: Exclude from Recorder

Because this sensor fires a state change **every second** (86,400 per day), you **must** exclude it from the `recorder` integration to protect your database and system performance.

Add the following to your `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
      - sensor.second_counter   # replace with your actual entity ID if renamed
```

Without this exclusion, your Home Assistant database will grow extremely quickly and may degrade performance.

---

## Sensor Attributes

| Attribute | Type | Description |
|---|---|---|
| `is_running` | `boolean` | Whether the counter is currently ticking |
| `last_ticked_at` | `string` (ISO 8601 UTC) | Timestamp of the most recent tick |

---

## License

MIT — see [LICENSE](LICENSE).
