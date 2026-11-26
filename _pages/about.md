---
layout: about
title: about
permalink: /

profile:
  image: prof_pic.jpg
  image_circular: false
  # shown under the photo
  links: >
    <a href="mailto:shuozhe.li@utexas.edu">Email</a> /
    <a href="https://scholar.google.com/citations?user=EAth38AAAAAJ&amp;hl=en">Google Scholar</a> /
    <a href="https://github.com/ShuoZheLi">GitHub</a> /
    <a href="/cv/">CV</a>

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
  <li><strong>Capable.</strong> Let a model learn problems it can't yet solve by training on its own explanation of the right answer (<a href="{{ '/publications/#zhou2025expo' | relative_url }}">ExPO</a>), and learn to spot and fix errors by attacking its own reasoning (<a href="{{ '/publications/#li2026gasp' | relative_url }}">GASP</a>).</li>
  <li><strong>Reliable.</strong> Score reasoning quality, not just answers, on a model's most confident traces (<a href="{{ '/publications/#pathak2026frs' | relative_url }}">FRS</a>), and stop RL from making models overconfident while keeping its accuracy gains (<a href="{{ '/publications/#li2026carerft' | relative_url }}">CARE-RFT</a>).</li>
  <li><strong>Efficient.</strong> Prune what a distillation teacher can repair (<a href="{{ '/publications/#li2026dap' | relative_url }}">DAP</a>), and serve by stitching a big model's lower layers to a small model's upper layers, adapting to load (<a href="{{ '/publications/#hu2025stitchllm' | relative_url }}">StitchLLM</a>).</li>
</ul>

Before focusing on LLMs, I worked on offline RL ([Iterative Dual-RL]({{ '/publications/#xu2025idrl' | relative_url }})), Sim2Real
([Robot Air Hockey]({{ '/publications/#chuck2024airhockey' | relative_url }})), and navigation ([DynaBARN]({{ '/publications/#nair2022dynabarn' | relative_url }}))
using robot learning. I have also worked on financial time series forecasting
([WaveLSFormer]({{ '/publications/#li2026wavelsformer' | relative_url }}), [Stockformer]({{ '/publications/#li2025stockformer' | relative_url }})).
Before Ph.D., I worked on wireless sensing and mobile systems with [Prof. Lili Qiu](https://www.cs.utexas.edu/~lili/).
