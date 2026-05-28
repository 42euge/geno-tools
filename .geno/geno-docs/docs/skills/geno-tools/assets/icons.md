---
title: geno-icons
description: Generate pixel art icons for geno-ecosystem projects using SD 1
---

# geno-icons

`/geno-icons "[generate|refine|status] [project-name] [--seeds N] [--prompts 'custom prompt']"`

> Generate pixel art icons for geno-ecosystem projects using SD 1

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

Generate 8-bit pixel art icons for geno-ecosystem projects using Stable Diffusion 1.5 with a pixel art LoRA, running locally on MPS (Apple Silicon).

```!
python3.12 --version >/dev/null 2>&1 || echo "⚠️ Python 3.12 required (python3.14 has compatibility issues with diffusers)"
```

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Stack

- **Model**: `stable-diffusion-v1-5/stable-diffusion-v1-5` (~2GB)
- **LoRA**: `artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5` (~50MB)
- **LoRA weight file**: `PixelArtRedmond15V-PixelArt-PIXARFK.safetensors`
- **LoRA trigger word**: `pixelarfk`
- **Device**: MPS (Apple Silicon) or CUDA
- **Memory**: ~3GB — safe for 24GB machines with normal workloads running
- **Speed**: ~75 sec/image on MPS at 512x512, 25 steps

## Dependencies

```
torch torchvision diffusers transformers accelerate safetensors Pillow peft
```

## Commands

Parse the user's arguments to determine the action:

### `/geno-icons generate [project-name]` or `/geno-icons`

Generate pixel art icon variants for one or all geno-ecosystem projects.

#### Workflow

1. **Set up the venv** (if not already present):
   ```bash
   VENV_DIR="/tmp/geno-icons-venv"
   if [ ! -d "$VENV_DIR" ]; then
     python3.12 -m venv "$VENV_DIR"
     source "$VENV_DIR/bin/activate"
     pip install torch torchvision diffusers transformers accelerate safetensors Pillow peft
   else
     source "$VENV_DIR/bin/activate"
   fi
   ```

2. **Determine target projects.** If a project name is given, generate for that one. Otherwise, scan the ecosystem repos directory for all `geno-*` repos:
   ```
   ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/
   ```

3. **Write and run a generation script.** Use the template below, customizing the `projects` dict with themed prompts for each target project. Write the script to `/tmp/geno-icons-venv/generate.py` and run it.

4. **Output** goes to `/tmp/geno-icons/<project-name>/` with naming: `<NN>_p<prompt-idx>_s<seed>.png`

5. **After generation**, open all non-black images in Preview:
   ```bash
   for f in /tmp/geno-icons/<project>/*.png; do
     size=$(stat -f%z "$f")
     [ "$size" -gt 5000 ] && echo "$f"
   done | xargs open
   ```
   (The NSFW safety filter produces false positive black images — filter by file size >5KB)

6. **Let the user pick.** When they select an image, copy it to the project's `docs/assets/icon.png`:
   ```bash
   mkdir -p "<repo-path>/docs/assets"
   cp "<selected-image>" "<repo-path>/docs/assets/icon.png"
   ```

#### Generation Script Template

```python
import torch
import os
import time
from diffusers import StableDiffusionPipeline, DDIMScheduler

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float32

print("Loading SD 1.5 pipeline...")
pipe = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=dtype,
)

print("Loading pixel art LoRA...")
pipe.load_lora_weights(
    "artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5",
    weight_name="PixelArtRedmond15V-PixelArt-PIXARFK.safetensors",
)

pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to(device)
pipe.enable_attention_slicing()

neg = "blurry, photorealistic, 3d, text, watermark, complex, noisy, border, frame, multiple objects, scenery, landscape, black background"

# Customize per project — 7 base prompts × 6 seed variations = 42 variants
projects = {
    "project-name": [
        "description of icon concept 1",
        "description of icon concept 2",
        # ... 7 total
    ],
}

output_base = "/tmp/geno-icons"
os.makedirs(output_base, exist_ok=True)

for project, base_prompts in projects.items():
    project_dir = os.path.join(output_base, project)
    os.makedirs(project_dir, exist_ok=True)
    img_num = 0
    for prompt_idx, base_prompt in enumerate(base_prompts):
        full_prompt = f"pixelarfk, pixel art, {base_prompt}, white background, game item sprite, centered, clean simple sprite, icon"
        for seed_offset in range(6):
            img_num += 1
            seed = 100 + prompt_idx * 10 + seed_offset
            print(f"  [{img_num}/42] seed={seed} | {base_prompt[:50]}...")
            image = pipe(
                prompt=full_prompt,
                negative_prompt=neg,
                guidance_scale=8.5,
                num_inference_steps=25,
                width=512,
                height=512,
                generator=torch.Generator(device="cpu").manual_seed(seed),
            ).images[0]
            filename = f"{img_num:02d}_p{prompt_idx}_s{seed}.png"
            image.save(os.path.join(project_dir, filename))
```

#### Prompt Design Guidelines

- Frame subjects as **game items, sprites, or RPG inventory icons** — the LoRA excels at these
- Use **white or light backgrounds** — dark backgrounds trigger the NSFW filter frequently
- Keep descriptions **concrete and object-focused** — "purple wrench" not "developer tools concept"
- Always prefix with `pixelarfk, pixel art,` (the LoRA trigger)
- End with `white background, game item sprite, centered, clean simple sprite, icon`

#### Reference Prompts by Project

| Project | Good prompt themes |
|---|---|
| geno-tools | toolbox, Swiss army knife, magic toolkit, treasure chest of tools, mechanical hand with wrench |
| geno-agents | robot, network nodes, team of small robots, AI brain, radar dish, group of characters |
| geno-dev | retro computer terminal, wrench + screwdriver, laptop with code, keyboard with glowing keys |
| geno-media | film camera, microphone, music note + headphones, video player, speaker, paintbrush |
| geno-research | magnifying glass + book, telescope, laboratory flask, open book with glowing pages, microscope |
| geno-kaggle | trophy cup, medal, bar chart with arrow, podium, leaderboard |
| geno-bench | stopwatch, speedometer, racing car, lightning bolt + clock, progress bar |
| geno-cli | retro TUI window, terminal with sparkles, prompt cursor in a chat bubble, command line wand |
| geno-iso | shipping container, sealed glass dome, isolation chamber, padlocked box, sandbox border |
| geno-mon | eye with alert, security camera, heartbeat monitor, radar screen, shield with eye, watchtower |
| geno-msg | speech bubble, envelope with lightning, chat bubbles, megaphone, carrier pigeon, walkie talkie |
| geno-notes | notepad with pencil, sticky notes, journal with bookmark, clipboard, quill pen + scroll |
| geno-term | terminal with cursor, command prompt, CRT monitor, keyboard, matrix rain, retro monitor |
| geno-vla | eye + neural network, camera lens + AI brain, robotic arm, AR glasses, scanner beam |

### `/geno-icons refine <project-name> [--prompts 'custom prompt']`

Regenerate icons for a single project with custom or adjusted prompts.

1. Check if `/tmp/geno-icons/<project>/` already has images — show the user what exists
2. Ask the user what direction to take: new prompts, same prompts with different seeds, or custom prompts
3. Generate a new batch (use seed range 200+ to avoid collisions with prior runs)
4. Open results and let the user pick

### `/geno-icons status`

Show which projects have icons and which don't:
```bash
REPOS_DIR="<ecosystem-repos-path>"
for repo in "$REPOS_DIR"/geno-* "$REPOS_DIR"/obsidian-*; do
  name=$(basename "$repo")
  if [ -f "$repo/docs/assets/icon.png" ]; then
    echo "  ✓ $name"
  else
    echo "  ✗ $name"
  fi
done
```

### `/geno-icons animate <project-name>`

Generate an animated GIF from the selected icon using AnimateDiff.

**Note:** AnimateDiff at small sizes produces noisy results. This is experimental. For better animated icons, consider using the static icon as a base and animating with simpler frame interpolation (glow pulse, rotation, etc.) via Pillow/imageio.

## Completion

When this skill finishes, emit a trace:

```bash
geno-trace emit \
  --skill geno-icons \
  --status <success|failure|abandoned> \
  --tool-calls <approximate count> \
  --errors <count of tool/command errors>
```

- `success` = icon images generated and user selected one (or status report completed)
- `failure` = venv setup failed, SD pipeline error, or all images were black/unusable
- `abandoned` = user stopped before selecting an icon

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

**Related skills:** `geno-ecosystem`, `geno-icons-venv`

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.
- **Observability contract** — emitting traces at completion feeds the self-improvement loop (health cards, retro, mining).

</div>

</div>

[:material-arrow-left: Back to geno-tools](index.md)
