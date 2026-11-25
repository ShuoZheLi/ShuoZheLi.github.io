---
layout: page
permalink: /publications/
title: publications
description:
nav: true
nav_order: 2
---

<!-- _pages/publications.md -->

{% include pub_styles.liquid %}

<div class="pub-filter" role="toolbar" aria-label="Filter publications by topic">
  <span class="pub-filter-label">Show:</span>
  <button type="button" data-filter="highlight" aria-pressed="true">Highlights</button>
  <button type="button" data-filter="reasoning" aria-pressed="false">LLM Reasoning &amp; RL</button>
  <button type="button" data-filter="efficiency" aria-pressed="false">Efficient LLMs</button>
  <button type="button" data-filter="rl" aria-pressed="false">Offline RL &amp; Robotics</button>
  <button type="button" data-filter="finance" aria-pressed="false">Financial Time Series</button>
  <button type="button" data-filter="sensing" aria-pressed="false">Networking &amp; Sensing</button>
  <button type="button" data-filter="all" aria-pressed="false">All</button>
</div>

<p class="pub-legend">
  Highlighted papers have a tinted background and an animation of their core method (click an animation to open it full size).
  * denotes equal contribution. Also see <a href="https://scholar.google.com/citations?user=EAth38AAAAAJ&amp;hl=en">Google Scholar</a>.
</p>

<div class="publications">

{% bibliography --group_by none %}

</div>

<p class="pub-empty">No papers in this category yet.</p>

{% include pub_filter.liquid %}
