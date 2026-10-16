# Product Requirement Document (PRD) & Technical Specification

## Project Overview
Create a custom Home Assistant integration distributed via **HACS (Home Assistant Community Store)** that provides a high-precision, continuous 1-second incrementing counter sensor. 

The integration must bypass standard template refresh delays, run reliably without temporal drift on Home Assistant's event loop (`asyncio`), handle start/pause/reset/set actions via custom services, and include developer guidance on recorder exclusion to protect system performance.

---

## 1. Directory Structure

The repository must follow the standard Home Assistant custom component layout:

```text
custom_components/second_counter/
├── __init__.py
├── manifest.json
├── config_flow.py
├── const.py
├── sensor.py
├── services.yaml
├── strings.json
└── translations/
    └── en.json
```

---

## 2. File Specifications & Functional Requirements

### A. `manifest.json`
- **Domain:** `second_counter`
- **Name:** Second Counter
- **Documentation:** URL to GitHub repo.
- **IoT Class:** `local_push`
- **Config Flow:** Set to `true`.
- **Codeowners:** GitHub username placeholder (`@username`).
- **Version:** `1.0.0`

### B. `const.py`
Define component constants:
- `DOMAIN = "second_counter"`
- `DEFAULT_NAME = "Second Counter"`
- `CONF_INITIAL_VALUE = "initial_value"`
- `CONF_START_IMMEDIATELY = "start_immediately"`
- Service names: `SERVICE_START`, `SERVICE_PAUSE`, `SERVICE_RESET`, `SERVICE_SET_VALUE`

### C. `config_flow.py`
Provide a UI-based Configuration Flow so users can set up the integration without editing `configuration.yaml`:
1. **User Step (`async_step_user`):**
   - Inputs:
     - `name` (string, default: `"Second Counter"`)
     - `initial_value` (integer, default: `0`)
     - `start_immediately` (boolean, default: `True`)
   - Unique ID generation to support multiple counter instances.
2. **Options Flow (Optional but recommended):** Allow updating settings post-setup.

### D. `__init__.py`
1. Manage setup and unload routines (`async_setup_entry`, `async_unload_entry`).
2. Forward setup to the `sensor` platform.
3. Register domain-level services (`start`, `pause`, `reset`, `set_value`) that route calls directly to target entities.

### E. `sensor.py`
Implements `SecondCounterSensor(SensorEntity)`.

#### Core Functional Requirements:
1. **Precision Ticker Loop:**
   - Use `self.hass.async_create_background_task` inside `async_added_to_hass` to launch a continuous `asyncio` background loop.
   - Loop execution logic:
     ```python
     start_time = asyncio.get_running_loop().time()
     # Perform tick logic ...
     elapsed = asyncio.get_running_loop().time() - start_time
     sleep_duration = max(0.0, 1.0 - elapsed)
     await asyncio.sleep(sleep_duration)
     ```
   - Compensates for execution time per tick to prevent drift over extended durations.
2. **State Management:**
   - `native_value`: Current counter integer.
   - `is_running`: Internal boolean track state.
   - Call `self.async_write_ha_state()` every second when actively running.
3. **Extra State Attributes:**
   - Expose attributes: `is_running` (boolean), `last_ticked_at` (ISO timestamp).
4. **Lifecycle Cleanup:**
   - Cancel the background `asyncio` task in `async_will_remove_from_hass` to avoid memory leaks or orphan background loops upon entity removal or reload.
5. **Entity Methods for Custom Services:**
   - `async_start()`: Sets running state to `True`.
   - `async_pause()`: Sets running state to `False`.
   - `async_reset()`: Resets `native_value` to `initial_value`.
   - `async_set_value(value: int)`: Overrides `native_value` with a provided integer.

### F. `services.yaml`
Define UI schemas and descriptions for the four entity services:
- `second_counter.start`
- `second_counter.pause`
- `second_counter.reset`
- `second_counter.set_value` (accepts `value` key)

### G. `strings.json` & `translations/en.json`
Provide user-friendly descriptions for Config Flow steps, error handling, and service parameters.

---

## 3. Database Exclude Guidance (Documentation Requirement)

Because updating state every 1 second generates **86,400 state changes per day**, the repository `README.md` **MUST** explicitly instruct users to exclude this sensor from the `recorder` integration in their `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
      - sensor.second_counter # (or matching entity ID)
```

---

## 4. Acceptance Criteria for Generated Code

1. **HACS Compatibility:** Valid `manifest.json` and directory structure passable by HACS validation checks.
2. **Zero Drift:** Uses clock-compensated `asyncio.sleep` calculation rather than static `asyncio.sleep(1.0)`.
3. **UI Integration:** Full Config Flow functionality allowing multiple distinct counter entities to be added via **Settings > Devices & Services**.
4. **Service Functionality:** Exposed services operate seamlessly in Home Assistant automations or Developer Tools.