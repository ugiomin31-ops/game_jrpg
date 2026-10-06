"""Glacier grotto: blue ashlar, ice ribs, snowflakes and frozen shrine props."""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _kit_interact_a import NorthernKit
from _pipeline import run
TS = "frost_grotto"
DESIGN = NorthernKit(frozen=True)
PIECES = DESIGN.frost_pieces()


def main():
    run(TS, PIECES, world="#243c58")


if __name__ == "__main__":
    main()
