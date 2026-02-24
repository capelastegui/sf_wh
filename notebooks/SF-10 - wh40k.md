---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.18.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# 1. Introduction


## 1.1 Notebook description

Playing with warhammer logic


## 1.2 Common imports

Common library imports used across my notebooks

```python
import pandas as pd
import numpy as np

pd.options.display.max_columns = 100
pd.options.display.width = 400

```

# 2. Implementation

```python

```

## 2.1 Define logic


Inputs:
- df_atk: Table with stats of attacking weapon
- df_def: Table with stats of defending unit
- df_atk_matrix: Cross join table of df_atk and df_def

```python
def get_df_atk_matrix(df_atk, df_def):
    """Get attack matrix, a table combining attack stats and defense stats"""
    df_def_clean = (
            df_def.rename(columns=dict(
            army='def_army',
            unit='def_unit',
            model='def_model'
        ))
        .drop(columns='faction')
    )
    df_atk_matrix = pd.merge(df_atk, df_def_clean, how='cross')
    return df_atk_matrix
    

def get_prob_save(is_melee, AP, ignore_cover, SV, SV_invul, rr_save, **kwargs):
    """Get probability of saving, for a series of (attacker, defender)"""
    # Note: we can calculate this as series
    cover_mod = ~is_melee & ~ignore_cover
    # Min save: 2 if SV is 2, 3 otherwise
    min_save = SV.mask(SV>2, 3)
    sv_modified = (
            (SV+AP-cover_mod)
            .pipe(np.maximum, min_save)
            .pipe(np.minimum, SV_invul.fillna(7).astype(int))
        )
    prob_save = (7-sv_modified)/6.

    # TO DO: Add rr_save

    df_result = pd.DataFrame(dict(
        cover_mod=cover_mod, min_save=min_save, sv_modified=sv_modified,
        prob_save=prob_save
    ))
    return df_result
    
    

def get_prob_h(H, rr_hit, bonus_hit, minus_hit, **kwargs):
    """Get probability of hitting, for a series of (attacker, defender)"""
    # Note: bonus_hit, minus_hit are always positive
    net_bonus = (
        (bonus_hit-minus_hit)
        # Ensure net modifier is within -1,1
        .pipe(np.minimum,1)
        .pipe(np.maximum,-1)
    )
    H_mod = (
        (H+net_bonus)
        # Ensure modified Hit roll is within (2,6)
        .pipe(np.minimum,6)
        .pipe(np.maximum,2)
    )
    prob_h = (
        ((7-H)/6 )
        # If unmodified H is 1.0 (i.e. torrent weapon) then prob=1.0
        .mask(H==1, 1.)
    )

    # TODO: Add rr_hit
    
    df_result = pd.DataFrame(dict(net_bonus=net_bonus, H_mod=H_mod, prob_h=prob_h))
    return df_result

# def get_prob_from_div_s_t(div_s_t):
#     condlist = [div_s_t<=0.5, div_s_t<1, div_s_t==1, div_s_t<2, div_s_t >=2]
#     choicelist = [1/6, 2/6, 3/6, 4/6, 5/6]
#     return np.select(condlist, choicelist, 0.5)

def get_prob_w(S, anti_inf, anti_tank, rr_wound, bonus_w, T, minus_w, **kwargs):
    """Get probability of wounding, given a hit, for a series of (attacker, defender)"""
    div_s_t = S/T

    condlist = [div_s_t<=0.5, div_s_t<1, div_s_t==1, div_s_t<2, div_s_t >=2]
    choicelist = [1/6, 2/6, 3/6, 4/6, 5/6]
    prob_w = np.select(condlist, choicelist, 0.5)

    # TO DO: Add anti_inf, anti_tank, rr_wound, bonus_w, minus_w

    df_result = pd.DataFrame(dict(dMiv_s_t = div_s_t, prob_w=prob_w))
    return df_result
    

def get_prob_dmg(prob_h, prob_w, prob_save, **kwargs):
    """Get probability of (hitting, wounding, not saving), for a series of (attacker, defender)"""
    prob_dmg = prob_h*prob_w*(1-prob_save)
    df_result = pd.DataFrame(dict(prob_dmg=prob_dmg))
    return df_result 
```

```python
# See https://stackoverflow.com/questions/11144513/cartesian-product-of-x-and-y-array-points-into-single-array-of-2d-points
import itertools

def cartesian_product_itertools(*arrays):
    return np.array(list(itertools.product(*arrays)))


def roll_n_dice(dice_size, n_dice):
    l_arrays = [list(range(dice_size))]*n_dice
    return cartesian_product_itertools(*l_arrays)
    # TO DO: get row sum
    # Aggregate, get probabilities
```

```python
def roll_D(D_n_dice, D_dice_size):
    valid_dice=[3,6]
    assert D_dice_size in valid_dice, f'Error: wrong dice size: {D_dice_size}'
    assert D_n_dice in [1,2]
    s_d = pd.Series(list(range(1,D_dice_size+1)), name='D_value')
    # In case of 2 dice rolled, get all combinations
    if D_n_dice == 2:
        s_d = pd.merge(s_d, s_d, how='cross').apply('sum', axis=1).rename('D_value')

    # Get probability table
    df_D_prob = (
        s_d
        .groupby(s_2d6).size()
        .pipe(lambda x:x/x.sum())
        .rename('D_prob')
        .reset_index()
    )
    return df_D_prob
    
    
```

```python
def _apply_halving(D_value, is_D_halved):
    # is_D_halved is scalar!
    if not is_D_halved:
        return D_value
    # else:
    s_result = np.ceil(D_value/2).astype(int)
    return s_result

def process_D(df_D_prob, W, D_mod, is_D_halved):
    # rounding: round up after all mods


    
    df_D = (
        df_D_prob
        .assign(D_value_raw=lambda x: x.D_value,
                D_value = lambda x: (x.D_value+D_mod)
                                    .pipe(np.maximum,1)
                                    .pipe(_apply_halving, is_D_halved)
                )
    )
    return df_D
```

```python
def get_D_out(D_fixed, D_n_dice, D_dize_size, W):
    pass
    # D_capped = np.minimum(D_fixed, W)
```

### Dice rolling

We want a function to roll damage dice before modifiers, roll_D
- For this ruleset, this is only required for damage
- We get a table with all dice results
- Returns 2 columns: D_prob, D_value

Later processing:
- Cap by remaining wounds
- Damage modifiers: penalties, bonuses, half damage
- This 


S:T scenarios:
- S<=T/2 : 1/6
- S<T : 2/6
- S==T: 3/6
- S>T: 4/6
- S>=2*T : 5/6


What we want to do:
- 2 families of functions:
- get attack probabilities
- simulate attack outcome

Note: We can get 2) from 1)


Defining get_D_out():
- Outputs:
- average damage
- damage rolls to kill
- Internal values
- capped average damage: cap dice rolls based on W. For vectorisation, we may want to implement this via table to merge

Consider: get_D_out_single
- we take values for a single instance
- simulate dice rolls, get probability distribution
- outputs:
- average damage
- average damage rolls to kill

Then, we either:
- apply get_D_out_single()
- turn it into a table, merge

What I want:
- each die is a list
- roll n dice: array that is x join of n lists


```python

```

### Damage out

D represents average damage rolled against an unwounded target, after accounting for target wounds

For each (D_fixed, D_n_dice, D_dice_size, W),
- if D_n_dice is 0, then D = min(D_fixed, W)

Otherwise, we 




## 2.2 Process data

```python
# Attack data input - v0

df_atk_raw = pd.DataFrame(
    columns=[
        'faction', 'army', 'family', 'type', 'unit', 'model', 'is_melee', 'name', 'mode','is_half_range',
         'R', 'A', 'H', 'S', 'AP', 'D_fixed', 'D_n_dice', 'D_dice_size',
         'rapid_fire', 'blast', 'melta', 'sustained_hits', 'letal_hits', 'dev_w', 'anti_inf', 'anti_tank',
         'ignore_cover', 'rr_hit', 'rr_wound', 'bonus_hit', 'bonus_w'
    ],
    data=[
    [
        'imperium', 'any', 'Bolter', 'Basic', 'any', 'any', False, 'Bolt gun', '-', False,
        24, 2, 3, 4, 0, 1, 0, 0, 
        None, None, None, None, None, None, None, None,
        False, False, False, 0, 0, 
    ],
        [
        'imperium', 'any', 'Bolter', 'Basic', 'any', 'any', False, 'Melta gun', '-', False,
        12, 1, 3, 9, 4, 0, 1, 6, 
        None, None, 2, None, None, None, None, None,
        False, False, False, 0, 0
    ],

        [
        'imperium', 'any', 'Bolter', 'Basic', 'any', 'any', False, 'Melta gun', 'close range', True, 
        12, 1, 3, 9, 4, 0, 1, 6, 
        None, None, 2, None, None, None, None, None,
        False, False, False, 0, 0
    ],
            [
        'imperium', 'any', 'Melee', 'Basic', 'Intercessor', 'any', True, 'Close Combat Weapon', '-', False,
        0, 3, 3, 4, 0, 1, 0, 0, 
        None, None, None, None, None, None, None, None,
        False, False, False, 0, 0
    ],
        
    ]
)
```

```python
df_atk_raw
```

```python
# def clean_df_atk(df_atk_raw):
#     df_atk = (
#         df_atk_raw
#         .assign(

#         )
#     )
```

```python
df_def_raw = pd.DataFrame(
    columns = [
        'faction', 'army', 'unit', 'model', 'is_inf', 'n_models',
        'T', 'SV', 'SV_invul', 'W', 'FNP',
        'minus_hit', 'minus_w', 'D_subtract', 'D_halve', 'rr_save'
    ],
    data = [
        [
        'imperium', 'Space Marines', 'Intercessors', None, True, 1,
        4, 3, None, 2, None,
        0, 0, 0, False, False
        ],

                        [
        'imperium', 'Space Marines', 'Terminators', None, True, 1,
        5, 2, 4, 3, None,
        0, 0, 0, False, False
        ],
        
                [
        'imperium', 'Space Marines', 'impulsor', None, True, 1,
        9, 3, 5, 10, None,
        0, 0, 0, False, False
        ],

        
    ]
)
```

```python
df_atk= df_atk_raw
df_def = df_def_raw
```

```python
df_def_raw
```

```python
df_atk_matrix = get_df_atk_matrix(df_atk, df_def)
```

```python
df_atk_matrix
```

```python
df_atk.head(1).pipe(print)
df_def.head(1).pipe(print)
```

```python

df_atk.head(1).pipe(print)
df_def.head(1).pipe(print)
```

```python
#get_prob_from_div_s_t(np.array([0, 0.5, 1, 1.5, 2, 3]))
```

```python
H = 6
(7-H)/6
```

```python
H = pd.Series([1,2,3,4,5,6])
rr_hit = pd.Series(False)
bonus_hit = pd.Series([0,0,0,1,1,2])
minus_hit = pd.Series([0,1,2,0,1,1])

df_prob_h = get_prob_h(H, rr_hit, bonus_hit, minus_hit)
df_prob_h
```

```python
df_atk_matrix[['S', 'T']]
```

```python
df_atk = df_atk_raw
df_def = df_def_raw

df_prob_w = get_prob_w(**df_atk_matrix)
df_prob_w
```

```python
df_atk = df_atk_raw
df_def = df_def_raw

df_prob_save = get_prob_save(**df_atk_matrix)
df_prob_save
```

```python
df_prob_h = get_prob_h(**df_atk_matrix)
df_prob_h
```

```python
df_atk.head(1).pipe(print)
df_def.head(1).pipe(print)
```

```python
[list(range(6))]*2
```

```python
roll_n_dice(3,3)
```

```python
cartesian_product_itertools(np.arange(6),np.arange(6))
```

```python
#
```

```python
l_d6 = list(range(1,7))
s_d6 = pd.Series(l_d6, name='D_value')
```

```python
(
    s_d6
    .groupby(s_d6).size()
    .pipe(lambda x:x/x.sum())
    .rename('D_prob')
    .reset_index()
)
```

```python
s_2d6 = pd.merge(s_d6, s_d6, how='cross').apply('sum', axis=1).rename('D_value')

(
    s_2d6
    .groupby(s_2d6).size()
    .pipe(lambda x:x/x.sum())
    .rename('D_prob')
    .reset_index()
)
```

```python
l_d6
```

```python
list(range(1,7))
```

```python
3/2
```

```python
_apply_halving(pd.Series(range(1,7)),True)
```

```python
d_tmp = roll_D(1,6)

print(d_tmp)
print(process_D(d_tmp, 3,1,True))
print(process_D(d_tmp, 3,1,False))
```

```python
roll_D(2,6)
```

```python

```

```python

```

```python

```

```python

```

```python
df_atk_matrix
```

```python
df_tmp = pd.concat([#df_atk_matrix,
           df_prob_h, df_prob_w, df_prob_save], axis=1)

get_prob_dmg(**df_tmp)
```

```python

```

```python

```

```python

```
