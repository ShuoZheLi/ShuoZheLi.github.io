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

{% include pub_filter_bar.liquid %}

<p class="pub-legend">
  Highlighted papers have a tinted background and an animation of their core method (click an animation to open it full size).
  * denotes equal contribution. Also see <a href="https://scholar.google.com/citations?user=EAth38AAAAAJ&amp;hl=en">Google Scholar</a>.
</p>

<div class="publications">

{% bibliography --group_by none %}

</div>

<p class="pub-empty">No papers in this category yet.</p>

{% include pub_filter.liquid sync_hash=true %}
