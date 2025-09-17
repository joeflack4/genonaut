"""Create synthetic data"""
import itertools
import os
import sys
from pathlib import Path
from random import randint, uniform

import pandas as pd

project_root = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
# sys.path.insert(0, str(project_root))
demo_data_dir = project_root / 'docs' / 'init' / 'rdmbs'
backup_dir = demo_data_dir / 'bak'

gen_jobs_path = demo_data_dir / "generation_jobs1.tsv"
content_items_path = demo_data_dir / "content_items1.tsv"

# Load the uploaded TSV files
gen_jobs = pd.read_csv(gen_jobs_path, sep="\t")
content_items = pd.read_csv(content_items_path, sep="\t")

# Back up original ones first
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

def get_next_filename(base_path):
    """get next filename"""
    counter = 1
    while True:
        # Add counter before the .tsv extension
        new_path = base_path.parent / f"{base_path.stem}_{counter}.tsv"
        if not new_path.exists():
            return new_path
        counter += 1


gen_jobs_base = backup_dir / "generation_jobs"
content_items_base = backup_dir / "content_items"

gen_jobs_bak_path = get_next_filename(gen_jobs_base)
content_items_bak_path = get_next_filename(content_items_base)

gen_jobs.to_csv(gen_jobs_bak_path, sep="\t", index=False)
content_items.to_csv(content_items_bak_path, sep="\t", index=False)


base_names = ["fashionista", "styleguru", "trendsetter", "couturelover", "runwaystar"]
suffixes = [str(randint(100, 999)) for _ in range(5)]
usernames = [f"{base}{suf}" for base, suf in zip(base_names, suffixes)]

# 40 diverse fashion prompts (with Stable Diffusion style additions)
fashion_prompts = [
    "young man in futuristic streetwear, neon-lit city street, glowing sneakers, oversized hoodie, cyberpunk vibe, "
    "cinematic lighting, highly detailed, 8k, trending on artstation",
    "elegant woman on a fashion runway, avant-garde haute couture dress inspired by cherry blossoms, flowing silk, "
    "pastel tones, spotlight photography, ultra realistic, 8k",
    "two models in cozy autumn outfits, colorful park with falling leaves, warm sweaters, scarves, boots, golden hour "
    "light, detailed texture, photorealistic",
    "woman at a summer music festival, bohemian style dress, layered jewelry, flower crown, desert sunset background, "
    "dreamy atmosphere, high resolution illustration",
    "businessman in a modern glass office, tailored charcoal suit, tie, leather briefcase, confident pose, natural "
    "daylight through windows, sharp focus, 8k realism",
    "woman in sleek cybernetic fashion, glowing accessories, metallic bodysuit, holographic makeup, futuristic city "
    "skyline at night, ultra detail, trending on artstation",
    "models walking down a snow-covered city street, layered winter coats, fur-trimmed hoods, knit scarves, steamy "
    "breath, dramatic lighting, photorealistic",
    "man in 1950s retro fashion, leather jacket, slicked hair, sitting in an old diner booth, neon signs in background"
    ", nostalgic tone, cinematic realism",
    "fashion model in dramatic couture gown, flowing fabric in desert winds, bold jewelry, golden dunes, Vogue-style "
    "editorial photo, ultra detailed",
    "two models in surreal avant-garde fashion, sculptural clothing shapes, futuristic accessories, bold makeup, "
    "minimalistic white abstract studio backdrop, photorealistic",
]

# Add 30 more with variation in gender, setting, season, style, accessories
extra_variations = [
    "teenager in punk fashion, graffiti alley, spiked hair, leather jacket, chains, photorealistic",
    "woman in beachwear fashion, tropical island, straw hat, sunglasses, flowing sarong, illustration",
    "man in luxury tuxedo, red carpet event, paparazzi cameras, spotlight, photorealistic",
    "female in gothic lolita dress, Victorian garden, parasol accessory, anime style",
    "male hiker in rugged outdoor fashion, snowy mountain peak, backpack, windbreaker, photorealistic",
    "woman in summer casual fashion, cafe terrace, iced coffee, straw bag, photorealistic",
    "male skater fashion, urban skatepark, ripped jeans, sneakers, graffiti background, illustration",
    "female in elegant evening gown, opera house interior, pearl necklace, dramatic spotlight, photorealistic",
    "male in futuristic armor-inspired fashion, glowing visor, sci-fi metropolis, anime style",
    "woman in retro 1970s disco outfit, glitter jumpsuit, dance floor, strobe lights, photorealistic",
    "man in military-inspired fashion, long coat, boots, leather gloves, snowy battlefield backdrop, photorealistic",
    "female in cyber-goth rave outfit, neon lights, fluorescent makeup, industrial warehouse, anime style",
    "man in surfer fashion, boardwalk, surfboard, wetsuit, sunset ocean backdrop, illustration",
    "female in classic Parisian chic, beret, striped shirt, cobblestone street, vintage cafe, photorealistic",
    "male in desert nomad-inspired fashion, flowing robes, turban, sandstorm background, photorealistic",
    "female in futuristic minimalist fashion, geometric dress, metallic sheen, abstract neon backdrop, photorealistic",
    "male in steampunk attire, goggles, leather straps, brass details, Victorian factory, illustration",
    "woman in bridal couture, cathedral setting, lace veil, bouquet, dramatic aisle perspective, photorealistic",
    "man in carnival-inspired fashion, feathers, beads, mask, parade street background, anime style",
    "female in athletic streetwear, rooftop basketball court, sneakers, headphones, photorealistic",
    "male in medieval-inspired fantasy fashion, armor mixed with fabric, castle backdrop, illustration",
    "woman in luxury fur fashion, snowy palace grounds, diamond earrings, photorealistic",
    "man in desert festival outfit, goggles, bandana, art installations in background, photorealistic",
    "female in traditional Japanese kimono, cherry blossoms, parasol, serene river setting, anime style",
    "male in futuristic VR-inspired fashion, glowing visor, gloves, neon city, photorealistic",
    "woman in flamenco-inspired dress, Spanish courtyard, fan accessory, dramatic pose, photorealistic",
    "male in cowboy western fashion, desert canyon, horse by side, revolver holster, illustration",
    "female in sci-fi armor couture, glowing lines, spaceship hangar, anime style",
    "male in business casual fashion, coworking space, laptop bag, coffee cup, photorealistic",
    "female in renaissance-inspired gown, oil painting backdrop, candlelight, illustration",
]

fashion_prompts.extend(extra_variations)

# Rotate through usernames, sizes, styles
sizes = ["512x512", "768x1024", "1024x768"]
styles = ["photorealistic", "illustration", "anime"]
rotator = itertools.cycle(zip(usernames, sizes, styles))

# Build new generation_jobs entries
new_jobs = []
new_content = []

for i, prompt in enumerate(fashion_prompts, start=1):
    user, size, style = next(rotator)
    title = f"Fashion Prompt {i}"
    job_entry = {
        "user_username": user,
        "job_type": "image",
        "prompt": prompt,
        "parameters": str({"model": "stable-diffusion", "size": size, "style": style}),
        "status": "pending",
        "result_content_title": title,
        "error_message": None,
    }
    content_entry = {
        "title": title,
        "content_type": "image",
        "content_data": f"/images/fashion_{i:03d}.png",
        "item_metadata": str({"resolution": size, "style": style}),
        "creator_username": user,
        "tags": str(["fashion", style, size]),
        "quality_score": round(uniform(0.75, 0.95), 2),
        "is_public": True,
    }
    new_jobs.append(job_entry)
    new_content.append(content_entry)

# Append to original dataframes
gen_jobs_extended = pd.concat([gen_jobs, pd.DataFrame(new_jobs)], ignore_index=True)
content_items_extended = pd.concat([content_items, pd.DataFrame(new_content)], ignore_index=True)

# Save updated TSVs
gen_jobs_extended.to_csv(gen_jobs_path, sep="\t", index=False)
content_items_extended.to_csv(content_items_path, sep="\t", index=False)
