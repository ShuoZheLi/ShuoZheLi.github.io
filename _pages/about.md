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

<!-- Text above the "research" marker sits beside the photo; everything below it spans the full width. -->

Hi! I am a Ph.D. student in Computer Science at The University of Texas at Austin, advised by
[Prof. Amy Zhang](https://www.ece.utexas.edu/people/faculty/amy-zhang) and [Prof. Leqi Liu](https://leqiliu.github.io/).
My research has been supported by Open Philanthropy and the Wesley W. Calhoun, Jr. Endowed Scholarship.

I work on **reinforcement learning for large language models**: making LLM reasoning _capable_, _reliable_, and
_efficient_.

Before focusing on LLMs, I worked on offline RL ([Iterative Dual-RL]({{ '/publications/#xu2025idrl' | relative_url }}), ICLR 2025)
and robot learning: sim-to-real manipulation with [Prof. Roberto Martín-Martín](https://robertomartinmartin.com/),
robot navigation with [Prof. Peter Stone](https://www.cs.utexas.edu/~pstone/), and the
[Robot Air Hockey](https://rlairhockey.github.io/) testbed (ICRA 2024). As an undergraduate I worked on wireless sensing and
mobile systems with [Prof. Lili Qiu](https://www.cs.utexas.edu/~lili/). I also build sequence models for financial time
series ([WaveLSFormer]({{ '/publications/#li2026wavelsformer' | relative_url }}), [Stockformer]({{ '/publications/#li2025stockformer' | relative_url }})).
In fall 2025 I was a student associate at Honda Research Institute USA, where I developed the self-play framework behind GASP.

I received my B.S. in Computer Science also from UT Austin with Honors and Research Distinction.

<p class="intro-links">
  <a href="mailto:shuozhe.li@utexas.edu">Email</a> /
  <a href="https://scholar.google.com/citations?user=EAth38AAAAAJ&amp;hl=en">Google Scholar</a> /
  <a href="https://github.com/ShuoZheLi">GitHub</a> /
  <a href="{{ '/cv/' | relative_url }}">CV</a>
</p>

<!-- research -->

<h2 class="home-section-title">research</h2>

Outcome rewards have made LLMs strong reasoners, but a correct final answer is not the same as dependable reasoning.
My thesis, _Towards Capable, Reliable, and Efficient Reasoning in Large Language Models_, asks how reasoning abilities can be
**acquired**, **assessed**, and **adapted** so they stay useful under the conditions where they are needed:

<ul class="research-thrusts">
  <li><strong>Learning from scarce outcome feedback.</strong> Self-explanations that give in-distribution positive samples on problems the model cannot yet solve (<a href="{{ '/publications/#zhou2025expo' | relative_url }}">ExPO</a>, NeurIPS 2025), and adversarial self-play that teaches a model to detect and repair corrupted reasoning (<a href="{{ '/publications/#li2026gasp' | relative_url }}">GASP</a>, NeurIPS 2026).</li>
  <li><strong>Reliability beyond accuracy.</strong> Evaluating reasoning quality on a model's most-confident traces (<a href="{{ '/publications/#pathak2026frs' | relative_url }}">FRS</a>, COLM 2026), and confidence-anchored RL finetuning that keeps calibration while improving reasoning (<a href="{{ '/publications/#li2026carerft' | relative_url }}">CARE-RFT</a>).</li>
  <li><strong>Adapting to deployment.</strong> Pruning for what the distillation teacher can repair (<a href="{{ '/publications/#li2026dap' | relative_url }}">DAP</a>), serving LLMs one block at a time (<a href="{{ '/publications/#hu2025stitchllm' | relative_url }}">StitchLLM</a>, ACL 2025), and ongoing work on adapting reasoning agents to their harness.</li>
</ul>
