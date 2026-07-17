<!--
Copyright (C) 2023-2026 Sebastien Rousseau.
Licensed under the Apache License, Version 2.0.
-->

# Examples

Runnable, self-contained scripts demonstrating the public
`structured_address_fix.services` facade. Each uses only the public
service API plus the re-exported domain models, prints readable output,
and exits `0`.

Run any script from the repository root:

```console
python examples/01_classify_address.py
```

| Script | What it shows |
| --- | --- |
| [`01_classify_address.py`](01_classify_address.py) | Classify addresses as structured / hybrid / unstructured. |
| [`02_assess_address_pre_post_cliff.py`](02_assess_address_pre_post_cliff.py) | Assess one address on both sides of the November 2026 cliff. |
| [`03_remediate_address.py`](03_remediate_address.py) | Remediate an unstructured address; print before, after, and operations. |
| [`04_list_policies.py`](04_list_policies.py) | List the policies registered in the default registry. |
| [`05_assess_message.py`](05_assess_message.py) | Assess every addressed party in a pacs.008 message. |
| [`06_remediate_apply_message.py`](06_remediate_apply_message.py) | Remediate a message with `apply=True` and print the patched XML. |
| [`07_preview_patch.py`](07_preview_patch.py) | Preview the patch operations remediation would apply (a dry run). |
| [`08_non_default_policy.py`](08_non_default_policy.py) | Contrast a non-default policy (SEPA, HVPS+) against the CBPR+ default. |

Every script is exercised by the test suite
(`tests/test_examples.py`), which runs each as a subprocess and asserts a
clean exit.
