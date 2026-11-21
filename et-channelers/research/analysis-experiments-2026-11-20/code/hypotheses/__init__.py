"""Analysis code for the registered hypotheses H1, H2, H4, H5, H6 and H9 (registry.md, hypotheses.md).

Every module here is hashed at freeze 2. Nothing in the package calls a language model, opens a transcript of a
creator outside the seen group, or computes a hypothesis quantity on real labels before the freeze-2 record exists
(adapter.require_permission). The simulation battery (simulate.py) works on synthetic creators only.
"""
VERSION = "hypotheses-analysis-1"
