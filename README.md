# Network-Sonification-Framework
## Overview
This is a project that I'm doing for personal curiousity as well as a class project. It examines what network traffic sounds like mapped to various soundscapes. The goal of this project is to potentially test how different soundscapes affect a listener's experience to both normal network traffic and traffic during different cyber attacks.
## Part 1: Soundscape
This part of the project took place in the first half of the semester and turned malware network captures into nature soundscapes. I found that direct packet-to-sound mapping mostly produced noise with common traffic masking important events. This part was definetly a learning experience and led to a refinement of goals.
## Part 2: Adaptive Music Engine
Taking my experience from the first part I wanted to turn these captures into something that actually sounded good with the album Cascadia being an inspiration. My research question narrowed to this: Can network traffic be turned into music that sounds good without losing what it reveals about an attack? This part of the project will use Suricata to turn captures into attack timelines, which I'll turn into an adaptive score using FMOD. In addition, I will most likely add polish using a music generation model.
