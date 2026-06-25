"""Schedule policy: pure relocation, deterministic collision resolution."""

from typing import Any, List, Optional


def apply_relocation_policy(
    window: List[Optional[str]],
    relocating: List[int],
    targets: List[int],
    rng: Any,
    n_vacant: int,
) -> List[Optional[str]]:
    """
    Apply pure relocation policy to a window of slots.

    Args:
        window: Current state of slots (chord names or None).
        relocating: Indices of agents that wish to relocate.
        targets: Desired target indices for each relocating agent.
        rng: Random number generator (unused here, kept for signature compatibility).
        n_vacant: Number of vacant slots (preserved automatically by swap semantics).

    Returns:
        New window state after relocation.
    """
    new_window = list(window)
    vacant = sorted(i for i, v in enumerate(new_window) if v is None)

    # Process moves in ascending source index order for deterministic resolution
    moves = sorted(zip(relocating, targets))

    for src, tgt in moves:
        if tgt in vacant:
            chosen = tgt
        else:
            # Assign next available vacant slot in ascending order
            chosen = next((v for v in vacant if v > tgt), vacant[0])

        new_window[chosen] = new_window[src]
        new_window[src] = None

        vacant.remove(chosen)
        vacant.append(src)
        vacant.sort()

    return new_window
