"""sf_wh - Warhammer 40K combat probability calculations."""
from sf_wh.wh40k import (
    get_df_atk_matrix,
    get_prob_save,
    get_prob_h,
    get_prob_w,
    get_prob_dmg,
    cartesian_product_itertools,
    roll_n_dice,
    roll_D,
    _apply_halving,
    process_D,
    get_D_out,
    get_df_atk_raw,
    get_df_def_raw,
)

__all__ = [
    "get_df_atk_matrix",
    "get_prob_save",
    "get_prob_h",
    "get_prob_w",
    "get_prob_dmg",
    "cartesian_product_itertools",
    "roll_n_dice",
    "roll_D",
    "_apply_halving",
    "process_D",
    "get_D_out",
    "get_df_atk_raw",
    "get_df_def_raw",
]
