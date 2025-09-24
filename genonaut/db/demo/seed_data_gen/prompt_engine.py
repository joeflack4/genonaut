"""Prompt generation engine with domain-specific templates."""

import random
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor
from jinja2 import Template


# Global tag pool for metadata.tags and user preferences
GLOBAL_TAGS = [
    "realistic", "stylized", "abstract", "surreal", "cinematic", "minimalism", "vintage",
    "modern", "futuristic", "fantasy", "sci-fi", "horror", "gothic", "whimsical", "colorful",
    "monochrome", "high-detail", "low-poly", "hand-drawn", "photorealistic", "3D", "2D",
    "illustration", "digital-painting", "anime", "editorial", "concept-art", "experimental",
    "moody", "vibrant", "HDR", "8k", "4k", "trending", "painterly", "expressive", "atmospheric",
    "dreamy", "ethereal", "mystical", "elegant", "gritty", "dark", "moody", "bright", "neon",
    "pastel", "warm", "cool", "soft-light", "hard-light", "dynamic", "action", "still-life",
    "panoramic", "close-up", "macro", "wide-angle", "fisheye", "tilt-shift", "isometric",
    "top-down", "overhead", "bird's-eye", "worm's-eye", "cinematic-framing", "editorial-style",
    "magazine-cover", "poster-style", "thumbnail", "logo-ready", "minimalist-typography",
    "ornate", "decorative", "symmetrical", "asymmetrical", "textured", "flat", "glossy",
    "matte", "vector", "raster", "pixel-art", "voxel", "cel-shaded", "line-art", "inked",
    "watercolor", "oil-painting", "acrylic", "charcoal", "chalk", "pastel", "marker", "crayon",
    "collage", "photobash", "3D-render", "sculpture", "installation", "mixed-media",
    "surreal-collage", "glitch"
]

# General phrases pool
GENERAL_PHRASES = [
    "highly detailed", "ultra realistic", "cinematic lighting", "soft lighting",
    "dramatic shadows", "HDR", "8k", "4k", "trending on artstation", "hyper-realistic",
    "surreal", "dreamy", "fantasy-inspired", "science fiction", "vivid colors", "muted tones",
    "monochrome", "sepia", "wide shot", "close-up", "portrait shot", "landscape format",
    "symmetrical", "asymmetrical", "painterly", "photorealistic", "digital painting",
    "illustration", "anime style", "stylized"
]

# Domain-specific phrase pools
DOMAIN_PHRASES = {
    "Fashion": [
        "runway", "haute couture", "streetwear", "vintage", "bohemian", "chic", "minimalism",
        "oversized jacket", "skinny jeans", "leather boots", "denim", "trench coat",
        "cocktail dress", "ball gown", "tuxedo", "accessories", "handbag", "scarf", "jewelry",
        "high heels", "sneakers", "aviator sunglasses", "catwalk", "editorial", "Vogue style",
        "casual wear", "business attire", "gothic fashion", "punk", "cyberpunk", "futuristic",
        "sportswear", "hoodie", "cap", "beanie", "knitted sweater", "floral dress", "kimono",
        "sari", "suit", "bow tie", "ruffles", "lace", "silk", "velvet", "satin", "embroidery",
        "sequins", "metallic", "distressed jeans", "plaid", "polka dots"
    ],
    "Portraits": [
        "close-up", "bust shot", "headshot", "candid", "profile view", "three-quarter view",
        "lighting contrast", "dramatic shadows", "smiling", "serious expression", "soft gaze",
        "intense gaze", "freckles", "makeup", "natural skin", "retouched", "digital painting",
        "oil painting style", "charcoal sketch", "pencil drawing", "pastel tones", "realistic",
        "ultra-detailed", "cinematic lighting", "Rembrandt lighting", "chiaroscuro", "beauty shot",
        "editorial style", "fashion portrait", "studio photography", "bokeh background",
        "blurred depth", "sharp focus", "side lighting", "rim light", "hair detail",
        "eye reflections", "golden ratio", "soft focus", "candid expression", "symmetrical",
        "asymmetrical", "stylized", "fantasy portrait", "futuristic cyborg", "alien face",
        "royal attire", "painted lips", "glowing eyes", "digital hyper-realism", "surreal portrait"
    ],
    "Landscapes": [
        "mountain range", "valley", "canyon", "desert", "tundra", "savanna", "rainforest",
        "jungle", "river delta", "coastline", "cliffside", "snowy peak", "glacier", "waterfall",
        "lake", "pond", "ocean waves", "beach", "sand dunes", "prairie", "meadow", "wildflowers",
        "pine forest", "bamboo forest", "autumn colors", "cherry blossoms", "storm clouds",
        "sunrise", "sunset", "twilight", "starry sky", "Milky Way", "northern lights",
        "aurora borealis", "foggy morning", "misty hills", "dramatic horizon", "panoramic",
        "aerial view", "drone shot", "volcanic eruption", "lava flow", "icebergs", "coral reef",
        "desert oasis", "canyon sunset", "mountain reflection", "rolling hills", "ancient ruins",
        "farmland", "rice terraces", "vineyard"
    ],
    "Fantasy Art": [
        "dragon", "elf", "dwarf", "fairy", "goblin", "orc", "troll", "mage", "sorceress",
        "wizard", "enchanted forest", "glowing rune", "magic circle", "spellcasting", "staff",
        "enchanted sword", "armor", "shield", "griffin", "phoenix", "unicorn", "centaur",
        "mermaid", "underwater city", "castle in clouds", "flying island", "enchanted tree",
        "portal", "dimensional rift", "sorcery", "necromancer", "paladin", "bard", "knight",
        "throne", "crown", "dark lord", "enchanted crystal", "glowing eyes", "demonic wings",
        "holy light", "arcane energy", "ethereal spirit", "golem", "enchanted armor",
        "cursed object", "alchemy", "potion", "wizard's tower", "spellbook", "enchanted fire"
    ],
    "Sci-Fi Art": [
        "spaceship", "starship", "space station", "astronaut", "exosuit", "mech", "cyborg",
        "android", "futuristic city", "neon skyline", "flying car", "hover bike",
        "cybernetic implant", "robot companion", "AI interface", "hologram", "laser weapon",
        "plasma gun", "alien landscape", "terraforming", "galaxy", "wormhole", "black hole",
        "nebula", "futuristic corridor", "cryo chamber", "cloning vat", "alien ruins",
        "planetary base", "space colony", "force field", "nanotech", "biotech", "dystopian",
        "utopian", "Mars colony", "Saturn rings", "Dyson sphere", "orbital cannon",
        "drone swarm", "futuristic skyscraper", "neon streets", "galactic empire",
        "alien ambassador", "teleportation", "wormhole gate", "antimatter reactor",
        "cybernetic arm", "VR visor", "augmented reality", "hyperloop", "energy shield"
    ],
    "Animals": [
        "lion", "tiger", "leopard", "cheetah", "jaguar", "wolf", "fox", "bear", "panda",
        "koala", "kangaroo", "giraffe", "elephant", "rhino", "hippo", "crocodile", "alligator",
        "eagle", "hawk", "owl", "falcon", "sparrow", "parrot", "peacock", "flamingo", "penguin",
        "seal", "walrus", "dolphin", "whale", "shark", "turtle", "tortoise", "lizard", "snake",
        "frog", "butterfly", "bee", "beetle", "ant", "spider", "horse", "zebra", "donkey",
        "buffalo", "bison", "deer", "elk", "moose", "rabbit", "squirrel", "raccoon", "otter",
        "beaver"
    ],
    "Food Photography": [
        "gourmet dish", "fine dining", "rustic meal", "fast food", "burger", "pizza", "pasta",
        "sushi", "sashimi", "ramen", "steak", "barbecue", "dessert", "cake", "cupcake", "pie",
        "tart", "croissant", "baguette", "bread loaf", "sandwich", "taco", "burrito",
        "quesadilla", "dim sum", "dumplings", "hot pot", "curry", "soup", "salad",
        "fresh vegetables", "organic", "smoothie", "milkshake", "latte art", "cappuccino",
        "espresso", "cocktail", "wine glass", "beer mug", "cheese platter", "charcuterie board",
        "seafood platter", "lobster", "crab", "oysters", "shrimp", "fondue", "chocolate fountain",
        "fruit bowl", "pancake stack", "waffle", "ice cream cone", "popsicle"
    ],
    "Architecture": [
        "cathedral", "gothic", "baroque", "renaissance", "skyscraper", "modernist", "brutalist",
        "art deco", "Bauhaus", "futuristic dome", "glass tower", "suspension bridge",
        "cable-stayed bridge", "viaduct", "aqueduct", "pyramid", "obelisk", "ziggurat", "temple",
        "shrine", "mosque", "pagoda", "minaret", "fortress", "castle", "palace", "mansion",
        "villa", "townhouse", "cabin", "cottage", "farmhouse", "barn", "windmill", "watermill",
        "lighthouse", "observatory", "amphitheater", "coliseum", "stadium", "arena", "opera house",
        "concert hall", "museum", "library", "parliament", "capitol building", "train station",
        "airport terminal", "metro station", "underground tunnel"
    ],
    "Interior Design": [
        "living room", "sofa", "coffee table", "rug", "fireplace", "chandelier", "wall art",
        "minimalist design", "modern design", "rustic", "industrial", "farmhouse", "bohemian",
        "eclectic", "Scandinavian", "mid-century modern", "contemporary", "art deco", "luxury",
        "penthouse", "loft", "apartment", "studio", "reading nook", "office", "desk",
        "ergonomic chair", "bookshelves", "potted plant", "indoor garden", "terrarium",
        "aquarium", "smart home", "home theater", "projector", "large windows", "skylight",
        "curtains", "drapes", "marble floor", "hardwood floor", "tile floor", "patterned wallpaper",
        "accent wall", "open floor plan", "kitchen island", "breakfast nook", "bar stools",
        "dining table", "four-poster bed", "canopy bed", "walk-in closet", "vanity"
    ],
    "Concept Art": [
        "character sheet", "turnaround", "key art", "environment concept", "creature design",
        "weapon concept", "armor design", "spaceship design", "vehicle design", "costume design",
        "prop design", "mood board", "color palette", "lighting study", "silhouette", "sketch",
        "thumbnail", "storyboard", "scene composition", "digital painting", "matte painting",
        "3D concept", "ZBrush sculpt", "kitbash", "photobash", "dynamic pose", "action shot",
        "idle pose", "facial expression sheet", "orthographic view", "perspective grid",
        "world-building", "architectural sketch", "biome design", "foliage study", "skybox",
        "atmosphere", "fog effects", "particle effects", "FX layers", "ambient lighting",
        "shader test", "experimental style", "cyberpunk aesthetic", "fantasy world",
        "sci-fi landscape", "dystopian ruins", "post-apocalyptic", "alien design"
    ],
    "Anime Characters": [
        "shōnen hero", "magical girl", "chibi", "bishounen", "yokai", "mecha pilot",
        "school uniform", "sailor fuku", "katanas", "oversized sword", "glowing aura",
        "spiky hair", "pastel hair", "twin tails", "kimono", "oni mask", "fox spirit",
        "shrine maiden", "samurai armor", "ninja outfit", "dragon companion", "talking cat",
        "oversized eyes", "detailed eyelashes", "blushing", "sweat drop", "exaggerated pose",
        "transformation sequence", "floating ribbons", "giant robot", "cyberpunk city",
        "high school rooftop", "cherry blossom petals", "bubble tea", "festival yukata",
        "futuristic headset", "idol singer", "gothic lolita", "demon horns", "angel wings",
        "fox ears", "catgirl", "school bag", "magic staff", "glowing runes", "kawaii expression",
        "stoic face", "scarf fluttering", "rival character", "sidekick", "mentor"
    ],
    "Cartoons": [
        "rubber hose style", "cel shading", "bold outlines", "talking animals", "slapstick humor",
        "exaggerated expressions", "zany antics", "goofy poses", "cartoon violence",
        "bright colors", "flat shading", "Saturday morning vibe", "wacky scientist",
        "superhero parody", "villain lair", "secret base", "banana peel gag",
        "over-the-top reaction", "silly eyes", "tongue out", "bouncy animation", "stretchy limbs",
        "oversized hammer", "comical chase", "exploding pie", "toon physics", "squash and stretch",
        "talking food", "gag face", "googly eyes", "talking car", "flying house", "friendly ghost",
        "wobbly lines", "simplified forms", "kids' show aesthetic", "sidekick animal",
        "wise-cracking character", "quirky hats", "oversized shoes", "silly villain", "pratfall",
        "silly grin", "exaggerated tears", "toon explosion", "wild chase", "comedic timing",
        "playful"
    ],
    "Product Mockups": [
        "smartphone render", "laptop mockup", "tablet in hand", "smartwatch display",
        "headphone product shot", "soda can design", "beverage bottle", "cosmetic jar",
        "perfume bottle", "t-shirt mockup", "hoodie mockup", "sneaker mockup", "packaging box",
        "food wrapper", "business card", "flyer", "poster frame", "brochure", "folded pamphlet",
        "app screen", "website preview", "billboard mockup", "banner ad", "storefront signage",
        "tote bag design", "mug design", "cup sleeve", "shopping bag", "clothing tag",
        "price label", "CD cover", "vinyl record sleeve", "book cover", "magazine layout",
        "cosmetic tube", "lotion pump", "dropper bottle", "packaging pouch", "cereal box",
        "candy wrapper", "jewelry box", "candle jar", "soap bar packaging", "tech gadget",
        "AR overlay", "digital display stand", "exhibition booth", "presentation board",
        "mock store shelf", "branded pen"
    ],
    "Posters": [
        "movie poster", "retro poster", "minimalist poster", "propaganda poster",
        "vintage travel poster", "psychedelic poster", "concert poster", "gig flyer",
        "neon poster", "sports event poster", "political poster", "motivational quote",
        "bold typography", "graphic layout", "collage style", "surreal poster", "photomontage",
        "abstract poster", "festival flyer", "horror poster", "sci-fi poster", "fantasy poster",
        "blockbuster layout", "film credits", "teaser style", "headliner text",
        "dramatic composition", "art deco style", "Bauhaus style", "gig lineup", "headline banner",
        "main character center", "villain looming", "logo placement", "cinematic lighting",
        "grunge poster", "graffiti poster", "comic-style poster", "geometric shapes",
        "posterized image", "duotone effect", "limited palette", "screenprint look", "silk screen",
        "folded poster texture", "glossy finish", "matte finish", "event details", "QR code"
    ],
    "Logos": [
        "flat design", "minimalist", "abstract shape", "geometric logo", "wordmark", "lettermark",
        "emblem", "mascot", "pictorial mark", "monogram", "bold lines", "sans serif",
        "serif typography", "hand lettering", "script logo", "3D logo", "metallic logo",
        "neon logo", "gradient logo", "black-and-white", "color palette", "scalable vector",
        "circle logo", "square logo", "hexagon logo", "negative space", "hidden meaning",
        "clever design", "overlapping shapes", "symmetry", "asymmetry", "badge style",
        "retro logo", "modern logo", "corporate style", "playful logo", "luxury brand",
        "fashion logo", "sports team emblem", "tech startup", "organic shape", "eco logo",
        "medical logo", "industrial look", "minimalist icon", "abstract waves", "arrows",
        "stylized animal", "stylized tree", "futuristic look", "modern glyph", "logotype"
    ],
    "Book Covers": [
        "dust jacket", "paperback cover", "hardback design", "illustrated cover",
        "photorealistic cover", "embossed text", "foil lettering", "matte finish",
        "glossy finish", "fantasy cover", "sci-fi cover", "romance cover", "thriller cover",
        "horror cover", "YA novel", "children's book", "fairy tale style", "epic saga",
        "mythological theme", "gothic design", "minimalist cover", "abstract art", "silhouette",
        "character portrait", "symbolic imagery", "floral motif", "broken glass",
        "blood splatter", "glowing artifact", "sword on cover", "spaceship scene", "starry night",
        "misty forest", "mysterious door", "haunted house", "castle ruins", "magic circle",
        "desert dune", "futuristic skyline", "lovers embrace", "masked villain", "ancient scroll",
        "typography focus", "painted cover", "collage style", "surreal imagery",
        "dramatic lighting", "bold colors", "textured paper", "wraparound cover"
    ],
    "Album Covers": [
        "vinyl record style", "CD jewel case", "cassette tape aesthetic", "surreal art",
        "psychedelic swirl", "minimalist design", "band portrait", "moody photography",
        "concert shot", "stage lights", "neon glow", "graffiti style", "stencil art",
        "abstract shapes", "geometric cover", "black-and-white", "high contrast", "sepia tone",
        "vintage look", "holographic effect", "distorted text", "warped image", "glitch effect",
        "lo-fi vibe", "hand-drawn cover", "doodle art", "fantasy scene", "sci-fi scene",
        "gothic cover", "urban night scene", "landscape art", "illustrated band", "collage cover",
        "DIY punk aesthetic", "retro synthwave", "80s vaporwave", "90s grunge", "futuristic look",
        "cyberpunk style", "space theme", "dreamy pastel", "neon typography", "dramatic shadows",
        "silhouette band", "minimal typography", "limited palette", "bold graphic", "iconic symbol",
        "logo focus", "avant-garde art"
    ],
    "Video Game Art": [
        "character design", "hero concept", "villain design", "boss monster", "NPC",
        "environment art", "dungeon design", "level map", "item icons", "health bar",
        "HUD mockup", "dialogue box", "pixel art", "sprite sheet", "2D animation",
        "isometric map", "top-down map", "3D render", "VR scene", "battle arena", "quest hub",
        "fantasy tavern", "sci-fi ship", "stealth corridor", "horror mansion", "puzzle dungeon",
        "desert wasteland", "snowy peak", "underwater stage", "alien planet", "futuristic city",
        "castle keep", "magic forest", "battlefield", "side scroller", "platformer background",
        "FPS corridor", "RPG overworld", "skill tree", "inventory screen", "cutscene art",
        "loading screen", "promotional poster", "cinematic trailer art", "in-game UI",
        "avatar portrait", "enemy design", "power-up icon", "weapon concept", "game logo"
    ],
    "Abstract Art": [
        "geometric shapes", "spirals", "fractals", "swirls", "kaleidoscope", "concentric circles",
        "asymmetry", "cubism", "surreal abstraction", "minimalist abstraction",
        "Jackson Pollock style", "bold brushstrokes", "neon colors", "muted pastels",
        "flowing lines", "gradient blend", "splatter paint", "glitch art", "datamosh",
        "pixelated abstraction", "blocky shapes", "grids", "mosaic", "stained glass", "symmetry",
        "mandala", "sacred geometry", "ink blot", "Rorschach", "colorful haze", "blurred shapes",
        "vaporwave style", "futurist abstraction", "3D wireframe", "mesh lines", "particle swarm",
        "dynamic flow", "wave pattern", "optical illusion", "Escher style", "impossible shapes",
        "tessellation", "holographic look", "psychedelic abstraction", "dreamy blur",
        "distorted typography", "melted forms", "abstract human face", "fragmented body",
        "painterly textures", "distorted reflections"
    ],
    "Surreal Art": [
        "melting clock", "floating island", "giant hand", "oversized moon", "tiny human",
        "distorted perspective", "dreamscape", "flying fish", "walking house",
        "human-animal hybrid", "eyeball landscape", "cracked sky", "upside-down city",
        "endless staircase", "infinite hallway", "warped body", "levitating objects", "portals",
        "glowing doorway", "alternate reality", "dual suns", "mirror world", "giant fruit",
        "enormous insects", "surreal portrait", "faceless figure", "puppet strings", "hollow body",
        "shadow person", "abstract nightmare", "playful surrealism", "whimsical creatures",
        "Salvador Dalí style", "René Magritte style", "surreal collage", "photo manipulation",
        "uncanny valley", "double exposure", "dream journal style", "bizarre animals",
        "ghostly forms", "impossible structures", "dripping paint", "floating furniture",
        "liquid sky", "melting landscape", "ethereal mist", "hyper-dreamlike", "surreal composition"
    ],
    "Film Stills": [
        "cinematic shot", "widescreen aspect", "anamorphic lens", "grainy film",
        "vintage film still", "noir lighting", "golden hour", "sunset shot", "action freeze-frame",
        "dramatic close-up", "establishing shot", "long take", "silhouette", "dramatic framing",
        "dolly shot", "handheld camera feel", "POV shot", "over-the-shoulder", "tracking shot",
        "montage still", "slow motion frame", "blurry motion", "35mm film", "70mm film",
        "IMAX look", "film grain", "VHS static", "retro TV frame", "muted palette", "technicolor",
        "black-and-white still", "desaturated look", "horror movie still", "thriller vibe",
        "romance close-up", "comedy freeze", "sci-fi still", "fantasy still", "period drama",
        "western film still", "experimental cinema", "art film shot", "indie film look",
        "lens flare", "spotlight", "moody shadows", "backlit subject", "iconic scene",
        "dramatic composition", "theatrical still", "clapperboard frame"
    ],
    "Comic Panels": [
        "speech bubble", "thought bubble", "sound effect text", "action lines", "panel borders",
        "inking", "flat colors", "halftone dots", "screen tones", "exaggerated anatomy",
        "superhero costume", "cape", "mask", "villain design", "sidekick", "dynamic pose",
        "punch impact", "explosion", "laser beam", "dramatic panel", "splash page", "cover art",
        "issue number", "panel layout", "dialogue box", "narration box", "bold outlines",
        "gritty style", "noir comic", "cartoony style", "manga style", "shōnen panel",
        "shōjo style", "seinen vibe", "webtoon format", "vertical scroll", "scrolling panel",
        "zoom panel", "extreme close-up", "bird's-eye view", "worm's-eye view", "speed lines",
        "chibi panel", "parody comic", "crossover issue", "iconic logo", "superhero landing",
        "villain reveal", "final showdown", "cliffhanger ending"
    ],
    "3D Renders": [
        "high-poly model", "low-poly model", "PBR textures", "wireframe view", "clay render",
        "textured render", "photorealistic render", "Unreal Engine", "Unity engine",
        "Blender render", "Maya model", "ZBrush sculpt", "Subsurface scattering", "ray tracing",
        "ambient occlusion", "global illumination", "volumetric lighting", "particle system",
        "physics simulation", "cloth sim", "hair simulation", "rigged model", "posed render",
        "animation still", "rendered turntable", "close-up detail", "sculpted anatomy",
        "stylized model", "toon shader", "cel shading", "stylized shading", "glossy materials",
        "metallic shader", "glass shader", "subsurface material", "terrain render",
        "landscape render", "sci-fi asset", "fantasy asset", "architectural render",
        "interior render", "industrial design", "furniture model", "product render",
        "mechanical part", "CAD model", "photogrammetry", "retopology", "baked textures",
        "procedural shader"
    ],
    "Medical Illustration": [
        "skeletal system", "muscular system", "nervous system", "circulatory system",
        "digestive system", "respiratory system", "lymphatic system", "reproductive system",
        "cell structure", "mitochondria", "DNA helix", "chromosomes", "antibody", "virus particle",
        "bacteria", "red blood cell", "white blood cell", "synapse", "neuron", "axon", "dendrite",
        "brain anatomy", "heart anatomy", "lung anatomy", "kidney anatomy", "liver anatomy",
        "pancreas", "stomach", "intestines", "skeletal diagram", "cross-section",
        "anatomical chart", "medical textbook style", "vector diagram", "labeled illustration",
        "cutaway view", "3D anatomy", "surgical illustration", "hospital poster",
        "medical infographic", "X-ray style", "MRI scan", "CT scan", "ultrasound",
        "endoscope view", "prosthetic limb", "medical device", "vaccine vial", "pill illustration",
        "medical experiment"
    ],
    "Educational Diagrams": [
        "flowchart", "mind map", "organizational chart", "tree diagram", "network diagram",
        "circuit diagram", "physics formula", "chemistry reaction", "periodic table",
        "mathematical graph", "bar chart", "pie chart", "scatter plot", "line graph", "timeline",
        "infographic", "map diagram", "anatomy diagram", "cross-section", "labeled parts",
        "system overview", "block diagram", "UML diagram", "sequence diagram", "ER diagram",
        "topology map", "Venn diagram", "set diagram", "probability tree", "heatmap",
        "radar chart", "Gantt chart", "supply chain map", "process diagram", "causal loop",
        "feedback loop", "educational poster", "chalkboard diagram", "blackboard sketch",
        "simple drawing", "iconography", "infographic elements", "teacher's notes",
        "classroom whiteboard", "instructional arrows", "instructional labels", "simple schematic",
        "visual guide", "worksheet diagram", "illustrated instructions"
    ],
    "Historical Scenes": [
        "ancient Rome", "medieval castle", "renaissance painting", "baroque palace",
        "industrial revolution", "American revolution", "civil war", "world war I",
        "world war II", "trench warfare", "Napoleonic battle", "samurai duel", "Mongol horde",
        "Egyptian pharaoh", "pyramid construction", "Mayan temple", "Aztec ritual",
        "Greek philosophers", "Roman senate", "gladiator arena", "medieval feast",
        "knight's tournament", "plague doctors", "Victorian street", "colonial America",
        "sailing ships", "Viking raid", "crusades", "Byzantine empire", "Ottoman empire",
        "Persian empire", "Great Wall", "Silk Road", "discovery voyage", "printing press",
        "castle siege", "cavalry charge", "trench scene", "D-Day landing", "1920s jazz club",
        "1800s frontier town", "Cold War", "Berlin Wall", "space race", "Apollo mission",
        "historical map", "medieval manuscript", "illuminated text", "ancient scrolls"
    ],
    "Celebrity Lookalikes": [
        "red carpet pose", "award show", "glamorous dress", "tuxedo suit", "celebrity smile",
        "paparazzi shot", "press conference", "autograph signing", "fan selfie", "late night show",
        "interview chair", "stage performance", "guitar solo", "dramatic spotlight",
        "movie premiere", "sunglasses indoors", "hat and disguise", "backstage dressing room",
        "makeup artist", "fashion shoot", "modeling pose", "fragrance ad", "luxury brand ad",
        "photo booth", "headshot", "action star look", "rom-com actor", "dramatic actor",
        "singer at mic", "pop idol", "rap performance", "DJ set", "festival stage",
        "influencer selfie", "YouTube thumbnail", "Instagram shot", "reality TV vibe",
        "candid paparazzi", "bodyguard nearby", "luxury car exit", "private jet", "magazine cover",
        "tabloid headline", "high society party", "charity gala", "talk show entrance",
        "morning coffee run", "gym paparazzi shot"
    ],
    "Memes": [
        "distracted boyfriend", "doge", "shiba inu", "grumpy cat", "galaxy brain", "wojak",
        "pepe the frog", "crying wojak", "trollface", "rage comic", "advice animal",
        "bad luck Brian", "success kid", "one does not simply", "drake format", "expanding brain",
        "two buttons", "change my mind", "is this a pigeon", "surprised Pikachu", "epic handshake",
        "cat vibing", "coffin dance", "chad vs virgin", "soyjak", "me and the boys", "stonks",
        "big chungus", "bowsette", "spongebob meme", "patrick meme", "squidward meme",
        "among us sus", "impostor meme", "rickroll", "trolololo", "meme face",
        "hyperbole expression", "sarcastic caption", "deep fried meme", "ironic meme",
        "surreal meme", "absurdist humor", "photoshop battle", "shitpost", "cursed image",
        "relatable meme", "wholesome meme", "reaction image"
    ],
    "Children's Illustrations": [
        "storybook art", "fairy tale", "princess castle", "dragon friend", "magical forest",
        "talking animals", "friendly bear", "playful rabbit", "colorful bird", "smiling sun",
        "moon with face", "rainbow", "fluffy clouds", "underwater world", "treasure chest",
        "pirate ship", "knight hero", "princess gown", "enchanted garden", "candy land",
        "gingerbread house", "toy soldier", "dollhouse", "puppet show", "circus tent", "clown",
        "balloon animals", "kite flying", "playground", "sandbox", "jungle gym", "merry-go-round",
        "carousel", "train set", "toy cars", "teddy bear", "stuffed bunny", "cheerful faces",
        "wide smiles", "bedtime story", "nursery rhyme", "whimsical style", "soft pastel",
        "watercolor", "crayon style", "childlike drawing", "fantasy town", "enchanted treehouse",
        "magic lamp", "adventure map"
    ],
    "Gothic/Horror Art": [
        "haunted house", "abandoned asylum", "creepy forest", "misty graveyard", "tombstones",
        "crypt", "mausoleum", "gothic cathedral", "gargoyle", "vampire", "werewolf",
        "zombie horde", "skeleton army", "ghost apparition", "banshee", "demon", "devil horns",
        "pentagram", "occult symbols", "dark ritual", "cursed artifact", "broken mirror",
        "possessed doll", "jack-o-lantern", "scarecrow", "spider webs", "bat swarm", "black cat",
        "raven", "crow", "thunderstorm", "full moon", "blood splatter", "dripping candles",
        "cobwebbed chandelier", "rusty chains", "dungeon cell", "iron gate", "Victorian mansion",
        "plague doctor", "cloaked figure", "cult gathering", "exorcism", "eldritch horror",
        "Cthulhu", "tentacles", "Lovecraftian beast", "cursed tome", "dark spellbook",
        "shadow hands", "eerie whispers"
    ]
}


class PromptEngine:
    """Generates diverse prompts using Jinja2 templates and domain-specific pools."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.template = Template(
            "{{ general_phrases | join(', ') }}{% if general_phrases and domain_phrases %}, {% endif %}{{ domain_phrases | join(', ') }}"
        )

    def generate_prompt(self, domain: str = None) -> str:
        """Generate a single prompt with random phrases."""
        # Select random general phrases
        min_general = self.config.get('prompt_min_general_phrases', 0)
        max_general = self.config.get('prompt_max_general_phrases', 10)
        num_general = random.randint(min_general, max_general)
        general_phrases = random.sample(GENERAL_PHRASES, min(num_general, len(GENERAL_PHRASES)))

        # Select domain and domain phrases
        if domain is None:
            domain = random.choice(list(DOMAIN_PHRASES.keys()))

        domain_pool = DOMAIN_PHRASES[domain]
        min_domain = self.config.get('prompt_min_domain_phrases', 4)
        max_domain = self.config.get('prompt_max_domain_phrases', 30)
        num_domain = random.randint(min_domain, max_domain)
        domain_phrases = random.sample(domain_pool, min(num_domain, len(domain_pool)))

        # Generate prompt
        prompt = self.template.render(
            general_phrases=general_phrases,
            domain_phrases=domain_phrases
        )

        return prompt

    def generate_prompts_batch(self, count: int, domains: List[str] = None) -> List[str]:
        """Generate a batch of prompts."""
        if domains is None:
            domains = list(DOMAIN_PHRASES.keys())

        prompts = []
        for _ in range(count):
            domain = random.choice(domains)
            prompt = self.generate_prompt(domain)
            prompts.append(prompt)

        return prompts

    def generate_prompts_parallel(self, count: int, max_workers: int = 4) -> List[str]:
        """Generate prompts using parallel processing."""
        batch_size = max(1, count // max_workers)
        batches = []

        # Split work into batches
        remaining = count
        while remaining > 0:
            current_batch = min(batch_size, remaining)
            batches.append(current_batch)
            remaining -= current_batch

        # Generate in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._generate_batch_worker, batch_count)
                for batch_count in batches
            ]

            all_prompts = []
            for future in futures:
                all_prompts.extend(future.result())

        return all_prompts

    def _generate_batch_worker(self, count: int) -> List[str]:
        """Worker function for parallel prompt generation."""
        return self.generate_prompts_batch(count)

    @staticmethod
    def get_random_tags(min_count: int = 0, max_count: int = 200) -> List[str]:
        """Get random tags from the global tag pool."""
        num_tags = random.randint(min_count, max_count)
        return random.sample(GLOBAL_TAGS, min(num_tags, len(GLOBAL_TAGS)))

    @staticmethod
    def get_user_favorite_tags(min_count: int = 0, max_count: int = 10) -> List[str]:
        """Get random tags for user preferences."""
        num_tags = random.randint(min_count, max_count)
        return random.sample(GLOBAL_TAGS, min(num_tags, len(GLOBAL_TAGS)))
