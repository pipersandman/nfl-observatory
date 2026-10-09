"""JSON writing that browsers can always read.

pandas/numpy produce NaN for missing values (e.g. a QB not named yet). NaN is not
valid JSON, and a single NaN makes the browser reject the whole file, which breaks
that part of the site. Every pipeline file is written through dumps() below.
"""
import json
import math

import numpy as np


def clean(o):
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.generic):
        return clean(o.item())
    return o


def dumps(obj, **kw):
    kw.setdefault('indent', 2)
    kw.setdefault('default', str)
    return json.dumps(clean(obj), allow_nan=False, **kw)
