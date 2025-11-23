If your Modal code grows, you can use **App composition** (from Modal docs):

```python
import modal
from .ltx_video import app as ltx_app
# Future: from .other_modal_function import app as other_app

# Compose all Modal apps together
full_app = modal.App("brainwrought-all").include(ltx_app)
```

Then deploy with: `modal deploy modal_functions
