---
layout: about
title: about
permalink: /

profile:
  image: prof_pic.jpg
  image_circular: false

selected_papers: true # highlighted papers are those marked selected={true} in _bibliography/papers.bib
service: true # renders the community service list from _data/service.yml
social: true

announcements:
  enabled: true
  scrollable: true
  limit: 5

latest_posts:
  enabled: false
---

Hi! I am a Ph.D. student in Computer Science at The University of Texas at Austin, advised by
[Prof. Amy Zhang](https://www.ece.utexas.edu/people/faculty/amy-zhang) and [Prof. Leqi Liu](https://leqiliu.github.io/)
supported by Open Philanthropy and the Wesley W. Calhoun, Jr. Endowed Scholarship.

I work on **reinforcement learning for large language models**: making LLM reasoning _capable_, _reliable_, and _efficient_.

<ul class="research-thrusts">
  <li><strong>Capable.</strong> RL only reinforces what a model can already sample, so I give it better starting points: explanations of answers it cannot yet reach (<a href="{{ '/publications/#zhou2025expo' | relative_url }}">ExPO</a>) and self-play that teaches it to catch and repair corrupted reasoning (<a href="{{ '/publications/#li2026gasp' | relative_url }}">GASP</a>).</li>
  <li><strong>Reliable.</strong> A right answer can hide flawed reasoning or false confidence, so I evaluate the reasoning itself (<a href="{{ '/publications/#pathak2026frs' | relative_url }}">FRS</a>) and keep models calibrated as RL makes them more accurate (<a href="{{ '/publications/#li2026carerft' | relative_url }}">CARE-RFT</a>).</li>
  <li><strong>Efficient.</strong> Compression should respect how a model is trained and served: prune what distillation can repair (<a href="{{ '/publications/#li2026dap' | relative_url }}">DAP</a>) and stitch models block by block under load (<a href="{{ '/publications/#hu2025stitchllm' | relative_url }}">StitchLLM</a>).</li>
</ul>

Earlier, I worked on offline RL ([Iterative Dual-RL]({{ '/publications/#xu2025idrl' | relative_url }})) and robot learning with
[Prof. Roberto Martín-Martín](https://robertomartinmartin.com/) and [Prof. Peter Stone](https://www.cs.utexas.edu/~pstone/),
and on Transformers for financial time series ([WaveLSFormer]({{ '/publications/#li2026wavelsformer' | relative_url }}), [Stockformer]({{ '/publications/#li2025stockformer' | relative_url }})).
Before Ph.D., I worked on wireless sensing and mobile systems with [Prof. Lili Qiu](https://www.cs.utexas.edu/~lili/).

<p class="intro-links">
  <a href="mailto:shuozhe.li@utexas.edu">Email</a> /
  <a href="https://scholar.google.com/citations?user=EAth38AAAAAJ&amp;hl=en">Google Scholar</a> /
  <a href="https://github.com/ShuoZheLi">GitHub</a> /
  <a href="{{ '/cv/' | relative_url }}">CV</a>
</p>
