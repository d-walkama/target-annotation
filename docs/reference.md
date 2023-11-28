% Note: The module sources referenced here are auto-generated with apidoc
(reference)=
# {fa}`list` API Reference
This section covers all the public interfaces of analysis-functions.

<!-- :::{tip}
It's recommended to import from the top-level `requests_cache` package, as internal module paths
may be subject to change. For example:
```python
from requests_cache import CachedSession, RedisCache, json_serializer
```
::: -->

<!--
TODO:
* move rst backend docs to md
* Copy/overwrite from extra_modules/ to modules/
-->
## Primary Modules
The following modules include the majority of the API relevant for most users:

```{toctree}
:maxdepth: 2
modules/analysis_functions.target_annotation
modules/analysis_functions.raw_simulations
modules/analysis_functions.extract_table
```

## Secondary Modules
The following modules are mainly for internal use, and are relevant for contributors and advanced users:
```{toctree}
:maxdepth: 2
modules/analysis_functions.open_targets
modules/analysis_functions.pharos
modules/analysis_functions.utils.retry
modules/analysis_functions.utils.exceptions
modules/analysis_functions.utils.util
```