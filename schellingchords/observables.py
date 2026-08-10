"""
Per-window observables for the SchellingChords model.

This module provides functions to calculate segregation metrics for a given
window of chord slots.
"""

from typing import Callable, List, Optional


def segregation_index(
    window: List[Optional[str]],
    metric: Callable[[str, str], float],
    tolerance: float,
    radius: int = 2,
) -> float:
    """
    Calculate the mean fraction of within-tolerance occupied-neighbour pairs.

    For each occupied slot in the window, we look at its neighbors within the
    given radius. We consider only occupied neighbors. The satisfaction of an
    agent is the fraction of its occupied neighbors that are within the
    tolerance distance. The segregation index is the mean of these satisfaction
    scores across all occupied slots.

    Args:
        window: A list of chord names (strings) or None (for rests/vacant slots).
        metric: A callable that computes the distance between two chord names.
        tolerance: The maximum acceptable distance for a neighbor to be considered
                   "similar" or "within tolerance".
        radius: The neighborhood radius to consider.

    Returns:
        The mean satisfaction score across all occupied slots. Returns 0.0 if
        there are no occupied slots.
    """
    occupied_indices = [i for i, slot in enumerate(window) if slot is not None]

    if not occupied_indices:
        return 0.0

    total_satisfaction = 0.0

    for idx in occupied_indices:
        # Determine neighbors within radius
        start = max(0, idx - radius)
        end = min(len(window), idx + radius + 1)

        # Collect occupied neighbors (excluding self)
        occupied_neighbors = []
        for j in range(start, end):
            if j != idx and window[j] is not None:
                occupied_neighbors.append(window[j])

        # Calculate satisfaction for this agent
        if not occupied_neighbors:
            # Vacuously satisfied if no occupied neighbors
            satisfaction = 1.0
        else:
            current_chord = window[idx]
            satisfied_count = sum(
                1 for neighbor in occupied_neighbors
                if metric(current_chord, neighbor) <= tolerance
            )
            satisfaction = satisfied_count / len(occupied_neighbors)

        total_satisfaction += satisfaction

    return total_satisfaction / len(occupied_indices)


def region_count(
    window: List[Optional[str]],
    metric: Callable[[str, str], float],
    tolerance: float,
) -> int:
    """
    Count contiguous similar-chord runs. Rests break runs.

    A "region" is a contiguous sequence of occupied slots where each adjacent
    pair of chords is within the tolerance distance. Rests (None values) break
    the continuity, effectively ending any current run and starting a new one
    after the rest (if the next slot is occupied).

    Args:
        window: A list of chord names (strings) or None (for rests/vacant slots).
        metric: A callable that computes the distance between two chord names.
        tolerance: The maximum acceptable distance for two chords to be considered
                   part of the same region.

    Returns:
        The number of contiguous similar-chord regions.
    """
    if not window:
        return 0

    region_count = 0
    in_region = False

    for i, slot in enumerate(window):
        if slot is None:
            # Rest breaks the current region
            in_region = False
            continue

        # If we are not currently in a region, start a new one
        if not in_region:
            region_count += 1
            in_region = True
        else:
            # We are in a region, check if the current chord is similar to the previous
            # occupied chord. We need to find the previous occupied chord.
            # Since rests break runs, the previous occupied chord is the last non-None
            # slot before the current one.
            prev_occupied_idx = i - 1
            while prev_occupied_idx >= 0 and window[prev_occupied_idx] is None:
                prev_occupied_idx -= 1

            if prev_occupied_idx >= 0:
                prev_chord = window[prev_occupied_idx]
                current_chord = slot
                if metric(prev_chord, current_chord) > tolerance:
                    # Not similar, so the current region ends and a new one starts
                    region_count += 1
                    # in_region remains True because we are still in a region (the new one)
                # else: similar, continue in the same region
            else:
                # No previous occupied chord found (should not happen if in_region is True
                # and we just started a region, but for safety)
                pass

    return region_count


def stability_profile(history: List[List[Optional[str]]]) -> List[float]:
    """
    Calculate per-position settledness across the run.

    For each position in the window, calculate the fraction of steps where the
    chord at that position remained unchanged from the previous step.
    The first step is always considered stable (settledness 1.0) for all positions.

    Args:
        history: A list of window states, one per step.

    Returns:
        A list of floats, one per position, representing the settledness score.
    """
    if not history:
        return []

    n_positions = len(history[0])
    # Initialize settledness counts. Each position starts with 1.0 (stable at step 0).
    settled_counts = [1.0] * n_positions
    total_steps = len(history)

    # If only one step, all are perfectly stable (1.0)
    if total_steps <= 1:
        return settled_counts

    # Compare each step to the previous one
    for step_idx in range(1, total_steps):
        prev_window = history[step_idx - 1]
        curr_window = history[step_idx]

        for pos in range(n_positions):
            prev_val = prev_window[pos]
            curr_val = curr_window[pos]

            # If the value at this position is the same as the previous step,
            # it contributes to stability.
            if prev_val == curr_val:
                settled_counts[pos] += 1.0

    # Normalize by total number of steps to get a fraction [0.0, 1.0]
    profile = [count / total_steps for count in settled_counts]
    return profile
