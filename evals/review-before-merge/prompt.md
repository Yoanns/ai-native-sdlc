---
name: review-before-merge
description: A review request runs the defined passes and ranks findings by severity.
tags: [routing, stage-4]
expected_outcome: >
  Claude loads the sdlc-deploy-review skill, runs the review passes defined in
  REVIEW.md (bugs, security, spec conformance), and reports findings ranked by
  severity with file, line, trigger and fix.
runs: 3
max_turns: 25
allowed_tools: [Read, Glob, Grep, Skill]
---

I've got a PR up that adds the invoice export endpoint. Review it before I merge.
