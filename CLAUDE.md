# Python Module Structure

All Python modules in this project must follow this section template (excludes `__init__.py` files):

```python
"""
[brief module description]
"""

# -- Public Imports

# -- Private Imports

# -- Globals

# -- Functions

# -- Classes
```

**Section guidelines:**
- **Public Imports**: standard library and third-party packages (e.g. `import numpy as np`, `from pathlib import Path`)
- **Private Imports**: internal project imports (e.g. `from sf_wh.common.unit_loader import ...`)
- **Globals**: module-level constants and variables (private globals use underscore prefix, e.g. `_RULES_DIR`)
- **Functions**: all function definitions
- **Classes**: all class definitions

Include all section headers even when a section is empty.
