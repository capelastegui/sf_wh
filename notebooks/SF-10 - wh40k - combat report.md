---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
  kernelspec:
    display_name: sf_wh (3.13.11)
    language: python
    name: python3
---

# 1. Introduction


## 1.1 Notebook description

Generate a combat report: kills per round for all (weapon, defender) combinations using the wh40k combat rules module.


## 1.2 Common imports

Common library imports used across my notebooks

```python
import pandas as pd
import numpy as np

pd.options.display.max_columns = 100
pd.options.display.max_rows = 100
pd.options.display.width = 400

```

## 1.3 Project imports

```python
from sf_wh.common.unit_loader import read_unit_rules, read_unit_weapons
from sf_wh.common.combat_rules import get_df_atk_matrix, get_df_atk_report, get_r_to_k
```

# 2. Load data

```python
df_atk = read_unit_weapons('army1', ruleset='gw')
df_def = read_unit_rules('army1', ruleset='gw')
```

```python
df_atk
```

```python
df_def
```

# 3. Attack matrix

```python
df_atk_matrix = get_df_atk_matrix(df_atk, df_def)
df_atk_matrix
```

## x.1 tmp -debug

```python
from sf_wh.common.combat_rules import get_prob_h, get_prob_w, get_prob_save
```

```python
df_prob_h = get_prob_h(**df_atk_matrix)
df_prob_w = get_prob_w(**df_atk_matrix)
df_prob_save = get_prob_save(**df_atk_matrix)
```

```python
get_df_atk_report(df_atk_matrix, pd.concat([df_prob_h, df_prob_w, df_prob_save], axis=1))
```

# 4. Rounds to kill

```python
df_r_to_k = get_r_to_k(df_atk_matrix)
df_r_to_k
```

```python
df_r_to_k_report = get_df_atk_report(df_atk_matrix, pd.DataFrame(dict(r_to_k=df_r_to_k)))
df_r_to_k_report.tail()
```

```python
df_r_to_k_report_wide = (
    df_r_to_k_report
    [['name', 'mode','def_unit', 'r_to_k']]
    .set_index(['name', 'mode','def_unit'])
    .unstack(sort=False)
    .round(3)
)
df_r_to_k_report_wide
```

```python

```
