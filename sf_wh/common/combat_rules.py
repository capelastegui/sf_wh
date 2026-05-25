"""
combat_rules - Warhammer 40K combat probability calculations.

Functions are organised into these areas:
- Utility functions
- Attack matrix construction
- Attack steps
- Attack outcomes - direct
- Attack outcomes - Inverse
- Damage dice rolling (work in progress)


These functions are intended to work with pandas dataframe inputs and outputs. 
However, they should also be able to take scalar inputs

Attack sequence summary:
- Each attack has an attacker and a defender
- An attacker has attack stats, a defender has defense stats
- An attack action has other properties independent of attacker and defender, such as distance
- We generate an attack matrix, where each row represents an (attacker, defender, attack_properties) tuple
  that will be used to resolve an attack
- Each attack goes through the following steps:
    - in a given round, `r`
    - determine number of attacks, `a`
    - determine number of hits, `h`
      - Includes non-critical hits `nh` and critical hits `ch`
    - determine number of wounding attacks pre-save, `w`
      - Includes non-critical wounds `nw` and critical wounds `cw`
    - determine number of unsaved attacks, `ua`
    - determine value of unsaved damage, `d`
    - evaluate number of target models killed, `k`


We have functions to resolve each step in the attack sequence, and also to 
get the outcome of a series of steps. For example:
- Kills per round: k_per_r
- Kills per attack: k_per_a
- Damage per hit: d_per_h

, as well as the inverse functions:
- Rounds to kill: r_to_k
- Hits to wound: h_to_w
"""

# -- Public Imports

import itertools

import numpy as np
import pandas as pd

# -- Private Imports

# -- Globals

ATK_MATRIX_KEYS = ['faction', 'army', 'unit', 'model', 'name', 'mode',
                   'def_army', 'def_unit', 'def_model']

# -- Functions

# ---- Utility functions

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


def normalize_col(col):
    """In a numeric column, normalize all data based on the first value"""
    if not pd.api.types.is_numeric_dtype(col):
        return col
    col_norm = col/col.iloc[0]
    return col_norm


def normalize_df(df, cols_exc=None):
    """In a table, normalize all numeric columns not in index"""
    if cols_exc is None:
        cols_exc = []

    l_cols_norm = [c for c in df.columns if c not in cols_exc]
    df_norm = df.copy()
    df_norm[l_cols_norm] = df_norm[l_cols_norm].apply(normalize_col, axis=0)
    return df_norm



# ---- Attack matrix construction

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


def get_df_atk_report(df_atk_matrix, *args):
    if not len(args):
        return df_atk_matrix
    df_atk_matrix_keys = df_atk_matrix[ATK_MATRIX_KEYS]
    df_atk_report = pd.concat([df_atk_matrix_keys]+list(args), axis=1)
    return df_atk_report


# ---- Attack steps

# TO DO: Add a_extra to attack matrix - for random bonuses


def get_a_blast(blast, n_models, **kwargs):
    """Get number of extra attacks from Blast ability"""
    a_blast = blast * (n_models % 5)
    return pd.Series(a_blast, name='a_blast').fillna(0)


def get_a_rapid_fire(rapid_fire, is_half_range, **kwargs):
    """Get number of extra attacks from rapid fire"""
    a_rapid_fire = rapid_fire * is_half_range
    return pd.Series(a_rapid_fire, name='a_rapid_fire').fillna(0)


def get_a(A, rapid_fire, is_half_range, blast, n_models, **kwargs):
    """Get number of attacks"""
    a = A + get_a_rapid_fire(rapid_fire, is_half_range) + get_a_blast(blast, n_models)  # +a_extra
    return pd.Series(a, name='a').fillna(0)


def get_prob_h(H, rr_hit, bonus_hit, minus_hit, crit_h, **kwargs):
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
        (H - net_bonus)
        # Ensure modified hit roll is within [2, 6]
        .pipe(np.minimum, 6)
        .pipe(np.maximum, 2)
    )
    prob_h = (
        ((7 - H_mod) / 6)
        # If unmodified H is 1 (i.e. torrent weapon) then prob = 1.0
        .mask(H == 1, 1.)
    )
    prob_ch = (
        ((7 - crit_h) / 6)
        .mask(crit_h.isna() | (crit_h >= 7), 0.)
        .pipe(np.minimum, prob_h)
    )
    # TODO: Add rr_hit

    df_result = pd.DataFrame(dict(net_bonus=net_bonus, H_mod=H_mod, prob_h=prob_h, prob_ch=prob_ch))
    return df_result


def get_prob_w(S, anti_inf, anti_tank, rr_wound, bonus_w, T, minus_w, crit_w, **kwargs):
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

    prob_cw = (
        ((7 - crit_w) / 6)
        .mask(crit_w.isna()|(crit_w >= 7), 0.)
    )

    # TO DO: Add anti_inf, anti_tank, rr_wound, bonus_w, minus_w

    df_result = pd.DataFrame(dict(div_s_t=div_s_t, prob_w=prob_w, prob_cw=prob_cw))
    return df_result


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


def _get_prob_ua(prob_h, prob_ch, prob_w, prob_cw, prob_save, sustained_hits, lethal_hits, dev_w):
    """
    Return probability of (hitting AND wounding AND not saving) per attack

    Internal function.
    """
    # non-lethal hits
    prob_h_nonlethal = prob_h + prob_ch*sustained_hits - prob_ch*lethal_hits
    prob_h_lethal = prob_ch*lethal_hits

    # non-lethal, non-mortal wounds
    prob_w_nonlethal = prob_h_nonlethal * (prob_w - prob_cw*dev_w)
    prob_w_lethal = prob_h_lethal
    prob_w_dev = prob_h_nonlethal * prob_cw * dev_w

    # save
    prob_ua = (prob_w_nonlethal + prob_w_lethal) * (1 - prob_save) + prob_w_dev
    return pd.Series(prob_ua, name='prob_ua')




# TO DO: get_d_melta
# d_melta = melta * is_half_range

def get_ua_per_a(df_atk_matrix):
    """Return probability of unsaved attacks per attack"""
    df_prob_h = get_prob_h(**df_atk_matrix)
    df_prob_w = get_prob_w(**df_atk_matrix)
    df_prob_save = get_prob_save(**df_atk_matrix)

    df_prob_w_input = pd.concat([
        df_prob_h[['prob_h', 'prob_ch']],
        df_prob_w[['prob_w', 'prob_cw']],
        df_prob_save[['prob_save']],
        df_atk_matrix[['sustained_hits', 'lethal_hits', 'dev_w']].fillna(0)
    ], axis=1)

    return _get_prob_ua(**df_prob_w_input)

def get_d_per_ua(D_fixed,D_n_dice,D_dice_size, W, **kwargs):
    """Return average damage per unsaved attack - simplified calculation"""

    # Number of dice is either 0 or 1
    D_n_dice_clean = np.minimum(D_dice_size.fillna(0),1)
    d_roll = (
        D_dice_size
        .map({3:np.array([1,2,3]), 6:np.array([1,2,3,4,5,6]), 0:np.array([0])})
    )

    ud_values = D_fixed + d_roll * D_n_dice_clean
    df_uncapped = pd.DataFrame(dict(ud=ud_values, W=W))
    d_values = df_uncapped.apply(lambda x: np.minimum(x.ud, x.W), axis=1)
    ud = ud_values.apply(lambda x:np.mean(x))
    d = d_values.apply(lambda x: np.mean(x))
    df_result = pd.DataFrame(dict(
        d=d, ud=ud
    ))

    # Note: doesn't quite match expectations
    # For 1d3 vs 2W
    # Expected w to k: 1.33
    # d_avg: 1.66 -> w to k: 1.2
    # w_to_k != 1/d_avg - explore!
    # Likely reason: only considering isolated attacks
    # For attacks in sequence, damage cap may lower -> d_avg will lower
    # Would need model for d_avg for seq of attacks

    return df_result


def get_d_to_k(d, W, **kwargs):
    """
    Given Average damage, estimate how many unsaved attacks to kill

    Note: This is inaccurate
    We shouldn't be using average damage, but a more detailed estimation based on damage roll
    """
    # TO DO: - review!

    # The following is true only when D_n_dice=0
    return np.maximum(np.ceil(W/d),1)


# ---- Attack outcomes

# TO DO: get average damage per attack
# d_per_a = prob_dmg * avg_d_roll


# DEPRECATE
def get_d_per_r(df_atk_matrix, d_per_ua=None):
    if d_per_ua is None:
        d_per_ua = get_d_per_ua(**df_atk_matrix)

    a = get_a(**df_atk_matrix)
    ua_per_a = get_ua_per_a(df_atk_matrix)
    d_per_r = a * ua_per_a * d_per_ua.d
    return d_per_r


def get_r_to_d(df_atk_matrix):
    return 1/get_d_per_r(df_atk_matrix)


def get_r_to_k(df_atk_matrix):
    r_to_k = 1/get_k_per_r(df_atk_matrix)
    return r_to_k


def get_k_per_r(df_atk_matrix):

    a = get_a(**df_atk_matrix)
    ua_per_a = get_ua_per_a(df_atk_matrix)
    ua_per_r = a * ua_per_a

    d_per_ua = get_d_per_ua(**df_atk_matrix)
    d_to_k = get_d_to_k(d_per_ua.d, df_atk_matrix.W)

    k_per_r = ua_per_r / d_to_k

    return k_per_r

 
# ---- Damage roll calculations (work in progress)


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


