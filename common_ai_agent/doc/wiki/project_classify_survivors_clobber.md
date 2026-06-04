---
title: project_classify_survivors_clobber
category: issue
tags: [verification, mutation, classification, freshness]
status: historical hazard note
---

# Project classify survivors clobber

This page preserves the historical reference from [[verification-contract-model]]
to a known verification hazard: generated classification or survivor artifacts
can overwrite evidence from a previous stage if output ownership and freshness
are not explicit.

VCM treats this as an example of why stage artifacts need scoped ownership,
source fingerprints, and validators that reject stale or clobbered evidence
instead of accepting whatever file is present at the expected path.
