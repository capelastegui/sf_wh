"""wh40k.py - Warhammer 40K combat probability calculations.

Functions are organised into four areas:
- Attack matrix construction
- Combat probabilities (hit, wound, save, damage)
- Damage dice rolling
- Sample data helpers
"""
import itertools

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Attack matrix
# ---------------------------------------------------------------------------

def get_df_atk_matrix(df_atk, df_def):
    """Return attack matrix: cross join of attack and defense stats."""
    df_def_clean = (
        df_def.rename(columns=dict(
            army='def_army',
            unit='def_unit',
            model='def_model',
        ))
        .drop(columns='faction')
    )
    df_atk_matrix = pd.merge(df_atk, df_def_clean, how='cross')
    return df_atk_matrix


# ---------------------------------------------------------------------------
# Combat probabilities
# ---------------------------------------------------------------------------

def get_prob_save(is_melee, AP, ignore_cover, SV, SV_invul, rr_save, **kwargs):
    """Return probability of saving, for a series of (attacker, defender)."""
    cover_mod = ~is_melee & ~ignore_cover
    # Min save: 2 if SV is 2, 3 otherwise
    min_save = SV.mask(SV > 2, 3)
    sv_modified = (
        (SV + AP - cover_mod)
        .pipe(np.maximum, min_save)
        .pipe(np.minimum, SV_invul.fillna(7).astype(int))
    )
    prob_save = (7 - sv_modified) / 6.

    # TO DO: Add rr_save

    df_result = pd.DataFrame(dict(
        cover_mod=cover_mod, min_save=min_save, sv_modified=sv_modified,
        prob_save=prob_save,
    ))
    return df_result


def get_prob_h(H, rr_hit, bonus_hit, minus_hit, **kwargs):
    """Return probability of hitting, for a series of (attacker, defender).

    Note: bonus_hit and minus_hit are always positive values.
    """
    net_bonus = (
        (bonus_hit - minus_hit)
        # Ensure net modifier is within [-1, 1]
        .pipe(np.minimum, 1)
        .pipe(np.maximum, -1)
    )
    H_mod = (
        (H + net_bonus)
        # Ensure modified hit roll is within [2, 6]
        .pipe(np.minimum, 6)
        .pipe(np.maximum, 2)
    )
    prob_h = (
        ((7 - H) / 6)
        # If unmodified H is 1 (i.e. torrent weapon) then prob = 1.0
        .mask(H == 1, 1.)
    )

    # TODO: Add rr_hit

    df_result = pd.DataFrame(dict(net_bonus=net_bonus, H_mod=H_mod, prob_h=prob_h))
    return df_result


def get_prob_w(S, anti_inf, anti_tank, rr_wound, bonus_w, T, minus_w, **kwargs):
    """Return probability of wounding given a hit, for a series of (attacker, defender).

    S:T mapping:
    - S <= T/2  -> 1/6
    - S < T     -> 2/6
    - S == T    -> 3/6
    - S > T     -> 4/6
    - S >= 2*T  -> 5/6
    """
    div_s_t = S / T

    condlist = [div_s_t <= 0.5, div_s_t < 1, div_s_t == 1, div_s_t < 2, div_s_t >= 2]
    choicelist = [1/6, 2/6, 3/6, 4/6, 5/6]
    prob_w = np.select(condlist, choicelist, 0.5)

    # TO DO: Add anti_inf, anti_tank, rr_wound, bonus_w, minus_w

    df_result = pd.DataFrame(dict(div_s_t=div_s_t, prob_w=prob_w))
    return df_result


def _get_prob_dmg(prob_h, prob_w, prob_save):
    """Return probability of (hitting AND wounding AND not saving)."""
    prob_dmg = prob_h * prob_w * (1 - prob_save)
    return pd.DataFrame(dict(prob_dmg=prob_dmg))


def get_prob_dmg(df_atk_matrix):
    """Return damage probability for each row of an attack matrix DataFrame."""
    df_prob_h = get_prob_h(**df_atk_matrix)
    df_prob_w = get_prob_w(**df_atk_matrix)
    df_prob_save = get_prob_save(**df_atk_matrix)
    return _get_prob_dmg(
        prob_h=df_prob_h['prob_h'],
        prob_w=df_prob_w['prob_w'],
        prob_save=df_prob_save['prob_save'],
    )


# ---------------------------------------------------------------------------
# Damage dice rolling
# ---------------------------------------------------------------------------

def cartesian_product_itertools(*arrays):
    """Return cartesian product of input arrays as a 2-D numpy array.

    Reference: https://stackoverflow.com/questions/11144513
    """
    return np.array(list(itertools.product(*arrays)))


def roll_n_dice(dice_size, n_dice):
    """Return all possible outcomes when rolling n_dice of dice_size."""
    l_arrays = [list(range(dice_size))] * n_dice
    return cartesian_product_itertools(*l_arrays)
    # TO DO: get row sum and aggregate to get probabilities


def roll_D(D_n_dice, D_dice_size):
    """Return probability table for rolling D_n_dice dice of D_dice_size sides.

    Returns a DataFrame with columns [D_value, D_prob].

    Note: in the original notebook roll_D referenced `s_2d6` (a notebook-level
    variable) inside the function. Fixed here to use the locally computed `s_d`.
    """
    valid_dice = [3, 6]
    assert D_dice_size in valid_dice, f'Error: wrong dice size: {D_dice_size}'
    assert D_n_dice in [1, 2]

    s_d = pd.Series(list(range(1, D_dice_size + 1)), name='D_value')
    # In case of 2 dice rolled, get all combinations and sum
    if D_n_dice == 2:
        s_d = pd.merge(s_d, s_d, how='cross').apply('sum', axis=1).rename('D_value')

    # Get probability table
    df_D_prob = (
        s_d
        .groupby(s_d).size()
        .pipe(lambda x: x / x.sum())
        .rename('D_prob')
        .reset_index()
    )
    return df_D_prob


def _apply_halving(D_value, is_D_halved):
    """Halve D_value (rounding up) when is_D_halved is True.

    Note: is_D_halved must be a scalar.
    """
    if not is_D_halved:
        return D_value
    return np.ceil(D_value / 2).astype(int)


def process_D(df_D_prob, W, D_mod, is_D_halved):
    """Apply damage modifiers to a probability table returned by roll_D.

    Rounding is applied after all modifiers (round up).
    """
    df_D = (
        df_D_prob
        .assign(
            D_value_raw=lambda x: x.D_value,
            D_value=lambda x: (
                (x.D_value + D_mod)
                .pipe(np.maximum, 1)
                .pipe(_apply_halving, is_D_halved)
            ),
        )
    )
    return df_D


def get_D_out(D_fixed, D_n_dice, D_dice_size, W):
    """Return average damage output (stub — not yet implemented)."""
    pass
    # D_capped = np.minimum(D_fixed, W)


