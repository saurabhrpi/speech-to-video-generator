from dataclasses import dataclass, field
from typing import Dict, List, Optional


ROOM_TYPES: List[Dict[str, str]] = [
    {"value": "staircase", "label": "Staircase"},
    {"value": "bathroom", "label": "Bathroom"},
    {"value": "living_room", "label": "Living Room"},
    {"value": "kitchen", "label": "Kitchen"},
    {"value": "bedroom", "label": "Bedroom"},
    {"value": "patio", "label": "Patio / Outdoor"},
    {"value": "office", "label": "Home Office"},
    {"value": "dining_room", "label": "Dining Room"},
    {"value": "hallway", "label": "Hallway / Entryway"},
    {"value": "closet", "label": "Walk-in Closet"},
    {"value": "garage", "label": "Garage"},
    {"value": "basement", "label": "Basement"},
]

STYLES: List[Dict[str, str]] = [
    {"value": "modern", "label": "Modern"},
    {"value": "modern_luxury", "label": "Modern Luxury"},
    {"value": "minimalist", "label": "Minimalist"},
    {"value": "scandinavian", "label": "Scandinavian"},
    {"value": "industrial", "label": "Industrial"},
    {"value": "farmhouse", "label": "Farmhouse"},
    {"value": "bohemian", "label": "Bohemian"},
    {"value": "coastal", "label": "Coastal"},
    {"value": "mid_century_modern", "label": "Mid-Century Modern"},
    {"value": "art_deco", "label": "Art Deco"},
    {"value": "japanese_zen", "label": "Japanese Zen"},
    {"value": "rustic", "label": "Rustic"},
    {"value": "contemporary", "label": "Contemporary"},
    {"value": "traditional", "label": "Traditional"},
]

LIGHTING_OPTIONS: List[Dict[str, str]] = [
    {"value": "warm", "label": "Warm"},
    {"value": "cool", "label": "Cool"},
    {"value": "dramatic", "label": "Dramatic"},
    {"value": "natural", "label": "Natural Daylight"},
    {"value": "ambient", "label": "Soft Ambient"},
    {"value": "warm_led", "label": "Warm LED"},
    {"value": "golden_hour", "label": "Golden Hour"},
    {"value": "moody", "label": "Moody / Low-key"},
]

CAMERA_OPTIONS: List[Dict[str, str]] = [
    {"value": "slow_pan", "label": "Cinematic Slow Pan"},
    {"value": "static", "label": "Static / Locked"},
    {"value": "dolly", "label": "Dolly Push-in"},
    {"value": "orbit", "label": "Slow Orbit"},
    {"value": "crane_up", "label": "Crane / Rise Up"},
    {"value": "tracking", "label": "Tracking Shot"},
]

PROGRESSION_TYPES: List[Dict[str, str]] = [
    {"value": "construction", "label": "Construction (empty shell \u2192 finished)"},
    {"value": "transformation", "label": "Transformation (old \u2192 new)"},
    {"value": "reveal", "label": "Reveal (dark \u2192 lit / hidden \u2192 shown)"},
]

SUGGESTED_FEATURES: List[str] = [
    "glass panels",
    "waterfall feature",
    "river pebbles",
    "LED underlighting",
    "floating shelves",
    "accent wall",
    "marble countertop",
    "open shelving",
    "freestanding tub",
    "skylight",
    "exposed brick",
    "vaulted ceiling",
    "fireplace",
    "indoor plants",
    "statement chandelier",
    "built-in cabinetry",
    "floor-to-ceiling windows",
    "herringbone flooring",
    "waterfall island",
    "barn door",
]

SUGGESTED_MATERIALS: List[str] = [
    "glass",
    "marble",
    "wood",
    "concrete",
    "stone",
    "brass",
    "steel",
    "ceramic tile",
    "granite",
    "oak",
    "walnut",
    "bamboo",
    "rattan",
    "leather",
    "terrazzo",
    "quartz",
    "copper",
    "travertine",
]


@dataclass
class TimelapseRequest:
    room_type: str
    style: str
    features: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    lighting: str = "natural"
    duration: int = 10
    camera_motion: str = "slow_pan"
    progression: str = "construction"
    freeform_description: str = ""


_CAMERA_LABEL_MAP = {item["value"]: item["label"].lower() for item in CAMERA_OPTIONS}
_STYLE_LABEL_MAP = {item["value"]: item["label"].lower() for item in STYLES}
_LIGHTING_LABEL_MAP = {item["value"]: item["label"].lower() for item in LIGHTING_OPTIONS}

_PROGRESSION_NARRATIVES = {
    "construction": (
        "Scene starts with an empty concrete interior shell. "
        "Construction progresses phase by phase: structural framework appears, "
        "then primary surfaces and materials are installed, "
        "then {feature_narrative} "
        "then {lighting_desc} lighting activates and finishing details appear. "
        "Final shot: completed {style_label} {room_label} interior, polished surfaces, "
        "soft reflections, photorealistic detail."
    ),
    "transformation": (
        "Scene starts with a dated, worn-out {room_label} interior. "
        "The space transforms step by step: old surfaces dissolve away, "
        "fresh materials emerge in their place, "
        "then {feature_narrative} "
        "then {lighting_desc} lighting shifts to reveal the new atmosphere. "
        "Final shot: fully renovated {style_label} {room_label}, pristine and inviting."
    ),
    "reveal": (
        "Scene starts in complete darkness inside a {room_label}. "
        "A soft glow begins to illuminate the space from one edge, "
        "progressively revealing {feature_narrative} "
        "then {lighting_desc} lighting sweeps across the room. "
        "Final shot: the fully lit {style_label} {room_label} is revealed in all its detail, "
        "dramatic and cinematic."
    ),
}


def _build_feature_narrative(features: List[str]) -> str:
    if not features:
        return "key design elements take shape, "
    if len(features) == 1:
        return f"{features[0]} is installed, "
    parts = ", then ".join(features[:-1]) + f", and finally {features[-1]} are added, "
    return parts


def compose_timelapse_prompt(req: TimelapseRequest) -> str:
    style_label = _STYLE_LABEL_MAP.get(req.style, req.style.replace("_", " "))
    room_label = req.room_type.replace("_", " ")
    camera_label = _CAMERA_LABEL_MAP.get(req.camera_motion, req.camera_motion.replace("_", " "))
    lighting_desc = _LIGHTING_LABEL_MAP.get(req.lighting, req.lighting.replace("_", " "))
    feature_narrative = _build_feature_narrative(req.features)

    material_clause = ""
    if req.materials:
        material_clause = f" using {', '.join(req.materials)}"

    narrative_template = _PROGRESSION_NARRATIVES.get(
        req.progression, _PROGRESSION_NARRATIVES["construction"]
    )
    narrative = narrative_template.format(
        room_label=room_label,
        style_label=style_label,
        feature_narrative=feature_narrative,
        lighting_desc=lighting_desc,
    )

    freeform_clause = ""
    if req.freeform_description.strip():
        freeform_clause = f" Additional creative direction: {req.freeform_description.strip()}"

    prompt = (
        f"Create a hyper-realistic {req.duration} second cinematic timelapse video "
        f"of building a {style_label} {room_label}{material_clause}. "
        f"{narrative} "
        f"Camera: {camera_label}. "
        f"Architectural visualization style, high detail, photorealistic rendering."
        f"{freeform_clause}"
    )
    return prompt


def get_all_options() -> Dict:
    return {
        "room_types": ROOM_TYPES,
        "styles": STYLES,
        "lighting_options": LIGHTING_OPTIONS,
        "camera_options": CAMERA_OPTIONS,
        "progression_types": PROGRESSION_TYPES,
        "suggested_features": SUGGESTED_FEATURES,
        "suggested_materials": SUGGESTED_MATERIALS,
    }
