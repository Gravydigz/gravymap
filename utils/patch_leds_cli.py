#!/usr/bin/env python3
"""
LED Patching Tool - Fill missing LEDs by interpolation

This script reads a 3D LED map CSV file, identifies missing LEDs,
and fills them in by interpolating positions from adjacent LEDs.
The process repeats until the total number of LEDs matches the expected count.
"""

import argparse
import csv
from pathlib import Path
import sys
import numpy as np


def load_leds_from_csv(csv_path: Path) -> dict:
    """Load LED data from CSV file into a dictionary."""
    leds = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            led_id = int(row['index'])
            leds[led_id] = {
                'x': float(row['x']),
                'y': float(row['y']),
                'z': float(row['z']),
                'xn': float(row.get('xn', 0.0)),
                'yn': float(row.get('yn', 0.0)),
                'zn': float(row.get('zn', 0.0)),
                'error': float(row.get('error', 0.0)),
            }

    return leds


def save_leds_to_csv(leds: dict, csv_path: Path):
    """Save LED data from dictionary to CSV file."""
    with open(csv_path, 'w', newline='') as f:
        fieldnames = ['index', 'x', 'y', 'z', 'xn', 'yn', 'zn', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for led_id in sorted(leds.keys()):
            led = leds[led_id]
            writer.writerow({
                'index': led_id,
                'x': led['x'],
                'y': led['y'],
                'z': led['z'],
                'xn': led['xn'],
                'yn': led['yn'],
                'zn': led['zn'],
                'error': led['error'],
            })


def find_missing_ids(leds: dict, total_leds: int) -> list:
    """Find missing LED IDs in the sequence from 0 to total_leds-1."""
    existing_ids = set(leds.keys())
    all_ids = set(range(total_leds))
    return sorted(all_ids - existing_ids)


def find_nearest_prev_led(leds: dict, led_id: int):
    """Find the nearest existing LED with ID less than led_id."""
    prev_ids = [id for id in leds.keys() if id < led_id]
    if not prev_ids:
        return None
    return max(prev_ids)


def find_nearest_next_led(leds: dict, led_id: int):
    """Find the nearest existing LED with ID greater than led_id."""
    next_ids = [id for id in leds.keys() if id > led_id]
    if not next_ids:
        return None
    return min(next_ids)


def interpolate_led(leds: dict, led_id: int, prev_id: int, next_id: int) -> dict:
    """
    Interpolate LED position based on previous and next LEDs.

    Uses linear interpolation weighted by distance in ID space.
    """
    prev_led = leds[prev_id]
    next_led = leds[next_id]

    # Calculate interpolation weight based on position in sequence
    total_gap = next_id - prev_id
    fraction = (led_id - prev_id) / total_gap

    # Interpolate position
    interpolated = {
        'x': prev_led['x'] * (1 - fraction) + next_led['x'] * fraction,
        'y': prev_led['y'] * (1 - fraction) + next_led['y'] * fraction,
        'z': prev_led['z'] * (1 - fraction) + next_led['z'] * fraction,
        'xn': 0.0,  # No normal for interpolated LEDs
        'yn': 0.0,
        'zn': 0.0,
        'error': 0.0,
    }

    return interpolated


def patch_leds(input_csv: Path, total_leds: int, max_iterations: int = 1000) -> dict:
    """
    Patch missing LEDs by iterative interpolation.

    Args:
        input_csv: Path to input CSV file
        total_leds: Expected total number of LEDs
        max_iterations: Maximum number of interpolation passes

    Returns:
        Dictionary of all LEDs including patched ones
    """
    leds = load_leds_from_csv(input_csv)

    print(f"Loaded {len(leds)} LEDs from {input_csv}")
    print(f"Target: {total_leds} LEDs")

    iteration = 0
    while len(leds) < total_leds and iteration < max_iterations:
        iteration += 1
        missing_ids = find_missing_ids(leds, total_leds)

        if not missing_ids:
            break

        patched_this_iteration = 0

        for led_id in missing_ids:
            prev_id = find_nearest_prev_led(leds, led_id)
            next_id = find_nearest_next_led(leds, led_id)

            # Can only interpolate if we have both neighbors
            if prev_id is not None and next_id is not None:
                leds[led_id] = interpolate_led(leds, led_id, prev_id, next_id)
                patched_this_iteration += 1

        if patched_this_iteration == 0:
            print(f"Warning: Could not patch any more LEDs. {len(missing_ids)} LEDs still missing.")
            break

        print(f"Iteration {iteration}: Patched {patched_this_iteration} LEDs. "
              f"Total: {len(leds)}/{total_leds}")

    if len(leds) == total_leds:
        print(f"Successfully patched all LEDs!")
    else:
        print(f"Warning: Only patched {len(leds)}/{total_leds} LEDs")

    return leds


def main():
    parser = argparse.ArgumentParser(
        description="Patch missing LEDs in 3D map by interpolation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to input led_map_3d.csv file",
    )

    parser.add_argument(
        "--total-leds",
        type=int,
        required=True,
        help="Expected total number of LEDs",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output CSV path (default: input file with '-patched' suffix)",
        default=None,
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input_csv.exists():
        print(f"Error: Input file {args.input_csv} does not exist")
        sys.exit(1)

    # Determine output path
    if args.output is None:
        stem = args.input_csv.stem
        suffix = args.input_csv.suffix
        output_path = args.input_csv.parent / f"{stem}-patched{suffix}"
    else:
        output_path = args.output

    # Patch LEDs
    print(f"\nPatching LEDs...")
    patched_leds = patch_leds(args.input_csv, args.total_leds)

    # Save results
    print(f"\nSaving patched LEDs to {output_path}")
    save_leds_to_csv(patched_leds, output_path)

    print(f"\nDone! Patched LED map saved to: {output_path}")


if __name__ == "__main__":
    main()
