# 3D LED Map - New Features

This project extends [marimapper](https://github.com/TheMariday/marimapper) with additional features for more flexible and accurate 3D LED mapping.

## New Features

### 1. Camera Orientation Support

Control camera orientation for portrait or landscape mode.

**Usage:**
```bash
# Default landscape mode
python -m gravymap.scripts.scanner_cli wled --ip 192.168.1.100

# Portrait mode (rotates camera 90° clockwise)
python -m gravymap.scripts.scanner_cli wled --ip 192.168.1.100 --orientation portrait
```

**When to use:** Use portrait mode when your camera setup requires a 90-degree rotation for better LED coverage or viewing angle.

---

### 2. Configurable Number of Views with Auto-Rotation Guidance

Specify the number of views to capture and get automatic rotation angle calculations.

**Usage:**
```bash
# Capture 4 views (90° rotation between each view)
python -m gravymap.scripts.scanner_cli wled --ip 192.168.1.100 --num_views 4

# Capture 8 views (45° rotation between each view)
python -m gravymap.scripts.scanner_cli wled --ip 192.168.1.100 --num_views 8
```

**How it works:**
- System calculates rotation angle: 360° / num_views
- After each scan, displays: "Rotate camera 90.0° clockwise and press Enter to continue"
- Automatically exits after capturing all views

**Example output:**
```
Scan 1/4 complete.
Rotate camera 90.0° clockwise and press Enter to continue.

Scan 2/4 complete.
Rotate camera 90.0° clockwise and press Enter to continue.

...

Completed all 4 views!
```

---

### 3. Brightness Recording (Enhanced)

LED brightness values are now captured and stored during scanning.

**What changed:**
- Brightness is calculated during LED detection
- Stored in 2D CSV files with new `brightness` column format: `index,u,v,brightness`
- Backward compatible with old CSV format (index,u,v)

**CSV Format:**
```csv
index,u,v,brightness
0,0.512345,0.498765,15234.5
1,0.523456,0.501234,14987.2
```

---

### 4. Brightness-Based Z-Axis Alignment (New)

When an LED is detected in multiple views, brightness values are used to weight the 3D position calculation.

**How it works:**
- Brighter LED captures indicate the LED is facing more directly toward the camera
- Z-axis positioning uses brightness-weighted averaging
- Results in more accurate depth information

**Technical details:**
- Modified `merge()` function in `led.py`
- Uses `np.average()` with brightness as weights
- Falls back to equal weighting if all brightnesses are zero

---

### 5. LED Patching Tool (New)

Fill in missing LEDs by interpolating positions from adjacent LEDs.

**Usage:**
```bash
# Basic usage
gravymap_patch_leds led_map_3d.csv --total-leds 100

# Specify custom output path
gravymap_patch_leds led_map_3d.csv --total-leds 100 --output my_patched_map.csv
```

**How it works:**
1. Loads existing LED positions from CSV
2. Identifies missing LED IDs (gaps from 0 to total-leds-1)
3. For each missing LED:
   - Finds nearest previous and next existing LEDs
   - Interpolates position using linear interpolation
4. Repeats until all LEDs from 0 to total-leds-1 exist
5. Saves to new CSV with "-patched" suffix

**Example:**
```
$ gravymap_patch_leds led_map_3d.csv --total-leds 100

Patching LEDs...
Loaded 87 LEDs from led_map_3d.csv
Target: 100 LEDs

Iteration 1: Patched 13 LEDs. Total: 100/100
Successfully patched all LEDs!

Saving patched LEDs to led_map_3d-patched.csv
Done! Patched LED map saved to: led_map_3d-patched.csv
```

---

## Complete Example Workflow

Here's a complete workflow using all new features:

```bash
# 1. Scan LEDs with portrait camera and 8 views
python -m gravymap.scripts.scanner_cli wled \
  --ip 192.168.1.100 \
  --orientation portrait \
  --num_views 8 \
  --start 0 \
  --end 99

# Follow the rotation prompts:
# "Rotate camera 45.0° clockwise and press Enter to continue."

# 2. After scanning completes, patch any missing LEDs
gravymap_patch_leds led_map_3d.csv --total-leds 100

# 3. Result files:
# - led_map_3d.csv (original scan with brightness data)
# - led_map_3d-patched.csv (complete 100 LED map)
```

---

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from pyproject.toml
pip install .
```

---

## Command Reference

### Main Scanner
```bash
gravymap wled --ip <IP> [OPTIONS]
```

**New options:**
- `--orientation {landscape,portrait}` - Camera orientation (default: landscape)
- `--num_views N` - Number of views to capture with auto-rotation guidance

### LED Patching Tool
```bash
gravymap_patch_leds INPUT_CSV --total-leds N [--output OUTPUT_CSV]
```

**Arguments:**
- `INPUT_CSV` - Input led_map_3d.csv file
- `--total-leds N` - Expected total number of LEDs (required)
- `--output PATH` - Custom output path (default: input-patched.csv)

---

## Technical Implementation

### Brightness Storage
- **Point2D class**: Added `brightness` field
- **detector.py**: Modified `find_led_in_image()` to capture brightness
- **file_tools.py**: Updated CSV I/O for brightness column

### Brightness-Weighted Merging
- **led.py**: Modified `merge()` function
- Uses `np.average()` with brightness weights
- Preserves all detections for analysis

### Camera Orientation
- **camera.py**: Added `orientation` parameter and `rotate_image()` method
- **detector_process.py**: Passes orientation to Camera
- Uses `cv2.rotate()` for 90° clockwise rotation

---

## Credits

Based on [marimapper](https://github.com/TheMariday/marimapper) by TheMariday.

Extended features by trobertson for enhanced LED mapping capabilities.
