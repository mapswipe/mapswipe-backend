import pytest

from project_types.tile_map_service.base.tutorial import synthetic_tile_position


@pytest.mark.parametrize(
    ("index", "screen", "expected"),
    [
        # Screen 1: 2x3 column-major block. First 3 cells fill the left column
        # (taskX 101) top-to-bottom, next 3 fill the right column (taskX 102).
        (0, 1, (101, 131072)),
        (1, 1, (101, 131073)),
        (2, 1, (101, 131074)),
        (3, 1, (102, 131072)),
        (4, 1, (102, 131073)),
        (5, 1, (102, 131074)),
        # Screen 2: base column shifts to 103/104 with the same row pattern.
        (0, 2, (103, 131072)),
        (1, 2, (103, 131073)),
        (2, 2, (103, 131074)),
        (3, 2, (104, 131072)),
        (4, 2, (104, 131073)),
        (5, 2, (104, 131074)),
        # Wrap: index 6 maps to the same cell as 0, index 7 as 1 (the % 6).
        (6, 1, (101, 131072)),
        (7, 1, (101, 131073)),
    ],
)
def test_synthetic_tile_position(index: int, screen: int, expected: tuple[int, int]):
    assert synthetic_tile_position(index, screen) == expected
