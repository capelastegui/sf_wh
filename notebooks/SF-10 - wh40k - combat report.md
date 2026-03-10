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

Generate a combat report: kills per round for all (weapon, defender) combinations using the wh40k combat rules module.


## 1.2 Common imports

Common library imports used across my notebooks

```python
import pandas as pd
import numpy as np

pd.options.display.max_columns = 100
pd.options.display.width = 400

```

## 1.3 Project imports

```python
from sf_wh.common.unit_loader import read_unit_rules, read_unit_weapons
from sf_wh.common.combat_rules import get_df_atk_matrix, get_df_atk_report, get_k_per_r
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

# 4. Kills per round

```python
df_k_per_r = get_k_per_r(df_atk_matrix)
df_k_per_r
```

```python
df_k_per_r_report = get_df_atk_report(df_atk_matrix, pd.DataFrame(dict(k_per_r=df_k_per_r)))
df_k_per_r_report
```
