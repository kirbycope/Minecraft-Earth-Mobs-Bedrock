"""Builds every mob's behavior file, spawn rule and loot tables from today's vanilla mob plus what the wiki says.

Each Earth mob is a variant of a vanilla mob (an albino cow is a cow, a bone spider is a spider), so its behavior starts
as that vanilla mob's own file from Mojang/bedrock-samples, pinned below, with the identifier and every reference to
itself (breeding partner, baby type, the properties vanilla declares) moved into the kirbycope namespace. On top of that
go the differences https://minecraft.wiki/w/Earth:Mob records for it: health, drops, the biome it lived in, how rare it
was, and the special behavior a few of them had (bone shards, lobbed rotten flesh, wall climbing, howling, flower and
mushroom trails, mud baths). Some of those need the Script API; scripts/main.js holds those parts.

The vanilla files are read from vanilla/, a sparse clone of bedrock-samples that git ignores; it is cloned on the
first run. Only what this writes is committed.

    python tools/generate_mobs.py            # writes entities/, spawn_rules/ and loot_tables/ in the behavior pack
    python tools/generate_mobs.py --check    # exits 1 if a file on disk differs from what a run would write
"""

import argparse
import copy
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "development_behavior_packs", "Minecraft-Earth-Mobs-Bedrock")
VANILLA = os.path.join(ROOT, "vanilla")
VANILLA_TAG = "v1.26.50.4"
VANILLA_PATHS = ["behavior_pack/entities", "behavior_pack/spawn_rules", "behavior_pack/loot_tables",
                 "resource_pack/entity", "resource_pack/models/entity", "resource_pack/render_controllers",
                 "resource_pack/animations", "resource_pack/animation_controllers", "resource_pack/textures/entity"]
NS = "kirbycope"

# --------------------------------------------------------------------------------------------------------------------
# What the wiki says about each mob. biome is the one its infobox names, rarity its Earth rarity. Everything else is
# a trait handled in TRAITS below.
# --------------------------------------------------------------------------------------------------------------------

COW, CHICKEN, PIG, SHEEP, RABBIT = "cow", "chicken", "pig", "sheep", "rabbit"
MOBS = {
    # cows: 10 health, leather and beef, milkable
    "albino_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "ashen_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "cookie_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "cream_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "dairy_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "pinto_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "sunset_cow": dict(base=COW, biome="plains", rarity="uncommon"),
    "moobloom": dict(base=COW, biome="plains", rarity="rare", flower="buttercup"),
    "moolip": dict(base=COW, biome="flower_forest", rarity="rare", flower="pink_daisy"),
    "wooly_cow": dict(base=COW, biome="snowy_plains", rarity="uncommon", coat="brown_wool"),
    "umbra_cow": dict(base=COW, biome="plains", rarity="uncommon", coat="black_wool"),
    # chickens: 4 health, eggs every five to ten minutes
    "amber_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "bronzed_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "gold_crested_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "midnight_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "skewbald_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "stormy_chicken": dict(base=CHICKEN, biome="plains", rarity="uncommon"),
    "fancy_chicken": dict(base=CHICKEN, biome="plains", rarity="rare", fancy=True),
    "cluckshroom": dict(base=CHICKEN, biome="forest", rarity="rare", cluckshroom=True),
    # pigs
    "mottled_pig": dict(base=PIG, biome="forest", rarity="uncommon"),
    "piebald_pig": dict(base=PIG, biome="forest", rarity="uncommon"),
    "pink_footed_pig": dict(base=PIG, biome="forest", rarity="uncommon"),
    "pale_pig": dict(base=PIG, biome="snowy_plains", rarity="uncommon"),
    "sooty_pig": dict(base=PIG, biome="dark_forest", rarity="uncommon"),
    "spotted_pig": dict(base=PIG, biome="swamp", rarity="uncommon"),
    "muddy_pig": dict(base=PIG, biome="plains", rarity="epic", mud="wet"),
    "dried_muddy_pig": dict(base=PIG, biome=None, rarity="epic", mud="dry"),
    # sheep: wool is the colour the skin shows, not a random dye; shear counts from the wiki
    "flecked_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("brown_wool", 1, 6)),
    "fuzzy_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("white_wool", 1, 6)),
    "long_nose_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("brown_wool", 1, 6)),
    "inky_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("black_wool", 1, 2)),
    "patched_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("white_wool", 1, 3)),
    "rocky_sheep": dict(base=SHEEP, biome="plains", rarity="uncommon", wool=("gray_wool", 1, 3)),
    "rainbow_sheep": dict(base=SHEEP, biome="plains", rarity="epic", wool=(f"{NS}:rainbow_wool", 3, 3)),
    "horned_sheep": dict(base=SHEEP, biome="plains", rarity="rare", wool=("white_wool", 1, 3), horned=True),
    # rabbits: 3 health
    "bold_striped_rabbit": dict(base=RABBIT, biome="plains", rarity="uncommon"),
    "freckled_rabbit": dict(base=RABBIT, biome="plains", rarity="uncommon"),
    "harelequin_rabbit": dict(base=RABBIT, biome="plains", rarity="uncommon"),
    "muddy_foot_rabbit": dict(base=RABBIT, biome="plains", rarity="uncommon"),
    "vested_rabbit": dict(base=RABBIT, biome="plains", rarity="uncommon"),
    "desert_rabbit": dict(base=RABBIT, biome="desert", rarity="common"),
    "jumbo_rabbit": dict(base=RABBIT, biome="desert", rarity="uncommon", jumbo=True),
    # the rest
    "jolly_llama": dict(base="llama", biome="snowy_plains", rarity="rare", jolly=True),
    "dyed_cat": dict(base="cat", biome=None, rarity="rare"),
    "furnace_golem": dict(base="iron_golem", biome="desert", rarity="rare", furnace=True),
    "melon_golem": dict(base="snow_golem", biome="snowy_plains", rarity="uncommon", melon=True),
    "tropical_slime": dict(base="slime", biome="jungle", rarity="rare", tropical=True),
    "bouldering_zombie": dict(base="zombie", biome="plains", rarity="rare", climber=True),
    "lobber_zombie": dict(base="zombie", biome="plains", rarity="rare", lobber=True),
    "skeleton_wolf": dict(base="wolf", biome="desert", rarity="rare", skeleton_wolf=True),
    "bone_spider": dict(base="spider", biome="dark_forest", rarity="rare", bone_spider=True),
    "viler_witch": dict(base="witch", biome="dark_forest", rarity="rare", viler=True),
}

# What each mob's kirbycope:anim property can say. The client (tools/port_earth.py) turns it into the variables
# Earth's server used to set: a witch about to cast, a mud pig rolling, a llama prancing. "none" is the resting state.
ANIM_STATES = {
    "furnace_golem": ["none", "gift", "summon"],
    "muddy_pig": ["none", "celebrate"],
    "dried_muddy_pig": ["none", "seek", "hop", "roll"],
    "horned_sheep": ["none", "prep", "ram"],
    "jolly_llama": ["none", "fern", "graze", "prance"],
    "viler_witch": ["none", "attack"],
    "melon_golem": ["none", "attack"],
    "bone_spider": ["none", "attack"],
    "lobber_zombie": ["none", "attack"],
    "bouldering_zombie": ["none", "climb_prep", "climb", "climb_exit"],
    "skeleton_wolf": ["none", "howl"],
    "wooly_cow": ["none", "shake"],
}

# Bedrock biome tags for the biomes the wiki names
BIOMES = {
    "plains": {"test": "has_biome_tag", "operator": "==", "value": "plains"},
    "forest": {"all_of": [{"test": "has_biome_tag", "operator": "==", "value": "forest"},
                          {"test": "has_biome_tag", "operator": "!=", "value": "roofed"},
                          {"test": "has_biome_tag", "operator": "!=", "value": "flower_forest"}]},
    "dark_forest": {"test": "has_biome_tag", "operator": "==", "value": "roofed"},
    "flower_forest": {"test": "has_biome_tag", "operator": "==", "value": "flower_forest"},
    "desert": {"test": "has_biome_tag", "operator": "==", "value": "desert"},
    "snowy_plains": {"test": "has_biome_tag", "operator": "==", "value": "ice_plains"},
    "swamp": {"test": "has_biome_tag", "operator": "==", "value": "swamp"},
    "jungle": {"test": "has_biome_tag", "operator": "==", "value": "jungle"},
}
SURFACE = {"desert": ["minecraft:sand"], "snowy_plains": ["minecraft:grass_block", "minecraft:snow", "minecraft:snow_layer"]}
# Spawn weight by Earth rarity. Animals sit beside vanilla's 8 to 12; monsters beside the zombie's 100 and witch's 5.
ANIMAL_WEIGHT = {"common": 10, "uncommon": 4, "rare": 2, "epic": 1}
MONSTER_WEIGHT = {"common": 40, "uncommon": 20, "rare": 10, "epic": 5}


# --------------------------------------------------------------------------------------------------------------------
# Reading vanilla
# --------------------------------------------------------------------------------------------------------------------

def ensure_vanilla():
    if os.path.isdir(os.path.join(VANILLA, "behavior_pack", "entities")): return
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--branch", VANILLA_TAG, "--filter=blob:none", "--sparse",
                    "https://github.com/Mojang/bedrock-samples.git", VANILLA], check=True)
    subprocess.run(["git", "-C", VANILLA, "sparse-checkout", "set"] + VANILLA_PATHS, check=True)


def lenient(text):
    """Mojang's JSON allows comments and trailing commas."""
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def vanilla(kind, name):
    return lenient(open(os.path.join(VANILLA, "behavior_pack", kind, name + ".json"), encoding="utf8").read())


def retarget(base, mob):
    """The vanilla base mob's file with every reference to itself, and the properties it declares, made the mob's own."""
    text = open(os.path.join(VANILLA, "behavior_pack", "entities", base + ".json"), encoding="utf8").read()
    data = lenient(text)
    props = list(data["minecraft:entity"]["description"].get("properties", {}))
    text = json.dumps(data)
    text = text.replace(f'"minecraft:{base}"', f'"{NS}:{mob}"')
    for prop in props:   # minecraft: is reserved for the game's own properties
        text = text.replace(prop, f"{NS}:" + prop.split(":", 1)[1])
    data = json.loads(text)
    desc = data["minecraft:entity"]["description"]
    desc.pop("runtime_identifier", None)
    desc["is_spawnable"] = True
    desc["is_summonable"] = True
    return data


# --------------------------------------------------------------------------------------------------------------------
# Editing a behavior file
# --------------------------------------------------------------------------------------------------------------------

class Entity:
    def __init__(self, data):
        self.data = data
        self.e = data["minecraft:entity"]
        self.e.setdefault("component_groups", {})
        self.e.setdefault("events", {})

    @property
    def components(self): return self.e["components"]

    @property
    def groups(self): return self.e["component_groups"]

    @property
    def events(self): return self.e["events"]

    def everywhere(self):
        """The base components and every component group, for edits that must reach whichever holds a component."""
        yield self.components
        yield from self.groups.values()

    def set_loot(self, table):
        for comps in self.everywhere():
            if "minecraft:loot" in comps: comps["minecraft:loot"] = {"table": table}
        if not any("minecraft:loot" in c for c in self.everywhere()): self.components["minecraft:loot"] = {"table": table}

    def set_health(self, value):
        for comps in self.everywhere():
            if "minecraft:health" in comps: comps["minecraft:health"] = {"value": value, "max": value}

    def remove(self, name):
        for comps in self.everywhere(): comps.pop(name, None)

    def family(self, add=(), remove=()):
        fam = self.components.setdefault("minecraft:type_family", {"family": []})["family"]
        for f in remove:
            if f in fam: fam.remove(f)
        for f in add:
            if f not in fam: fam.append(f)

    def add_property(self, name, spec):
        self.e["description"].setdefault("properties", {})[f"{NS}:{name}"] = spec

    def add_to_spawn(self, *groups):
        """Add component groups whenever the mob comes into the world, however it arrives."""
        for name in ("minecraft:entity_spawned", "minecraft:entity_born", "minecraft:entity_transformed"):
            event = self.events.setdefault(name, {})
            if "sequence" in event: event["sequence"].append({"add": {"component_groups": list(groups)}})
            else: self.events[name] = {"sequence": [event, {"add": {"component_groups": list(groups)}}]}

    def interactions(self, comps=None):
        comps = self.components if comps is None else comps
        return comps.setdefault("minecraft:interact", {"interactions": []}).setdefault("interactions", [])


# --------------------------------------------------------------------------------------------------------------------
# Loot tables
# --------------------------------------------------------------------------------------------------------------------

def item(name, lo=1, hi=None, chance=None, smelt=None, looting=True):
    entry = {"type": "item", "name": name if ":" in name else "minecraft:" + name, "weight": 1, "functions": []}
    if hi is None: hi = lo
    if (lo, hi) != (1, 1): entry["functions"].append({"function": "set_count", "count": {"min": lo, "max": hi}})
    if smelt: entry["functions"].append({"function": "furnace_smelt", "conditions": [{"condition": "entity_properties", "entity": "this", "properties": {"on_fire": True}}]})
    if looting and hi > 1: entry["functions"].append({"function": "looting_enchant", "count": {"min": 0, "max": 1}})
    if not entry["functions"]: del entry["functions"]
    pool = {"rolls": 1, "entries": [entry]}
    if chance is not None: pool["conditions"] = [{"condition": "random_chance", "chance": chance}]
    return pool


def table(*pools):
    return {"pools": list(pools)}


COW_DROPS = [item("leather", 0, 2), item("beef", 1, 3, smelt=True)]
CHICKEN_DROPS = [item("feather", 0, 2), item("chicken", 1, smelt=True)]
PIG_DROPS = [item("porkchop", 1, 3, smelt=True)]
RABBIT_DROPS = [item("rabbit_hide", 0, 1), item("rabbit", 0, 1, smelt=True), item("rabbit_foot", 1, chance=0.1)]
ZOMBIE_DROPS = [item("rotten_flesh", 0, 2), item("potato", 1, chance=0.025), item("carrot", 1, chance=0.025), item("iron_ingot", 1, chance=0.025)]


# --------------------------------------------------------------------------------------------------------------------
# Traits
# --------------------------------------------------------------------------------------------------------------------

def new_format(ent, version=(1, 26, 50)):
    """Files at 1.26.50 and later take some fields as lists that older ones take as strings."""
    return tuple(int(x) for x in ent.data["format_version"].split(".")[:3]) >= version


def shear_interaction(ent, event, loot, extra_filters=()):
    return {
        "on_interact": {"filters": {"all_of": [
            {"test": "has_equipment", "subject": "other", "domain": "hand", "value": "shears"},
            {"test": "is_family", "subject": "other", "value": "player"},
            {"test": "has_component", "operator": "!=", "value": "minecraft:is_baby"}] + list(extra_filters)},
            "event": event, "target": "self"},
        "use_item": False, "hurt_item": 1, "swing": True, "cooldown": 2.5,
        "spawn_items": {"table": loot}, "play_sounds": ["shear"] if new_format(ent) else "shear", "vibration": "shear",
        "interact_text": "action.interact.shear",
    }


def regrowing_coat(ent, mob, loot_full, loot_bare, shear_loot, regrow=(300, 600)):
    """A coat that can be shorn and grows back on a timer: the moobloom's flowers, the wooly cow's wool."""
    ent.add_property("sheared", {"type": "bool", "default": False, "client_sync": True})
    ent.groups[f"{NS}:coat_bare"] = {"minecraft:loot": {"table": loot_bare}, "minecraft:is_sheared": {},
                                     "minecraft:timer": {"looping": False, "randomInterval": True, "time": list(regrow),
                                                         "time_down_event": {"event": f"{NS}:coat_regrown", "target": "self"}}}
    ent.groups[f"{NS}:coat_full"] = {"minecraft:loot": {"table": loot_full}}
    ent.events[f"{NS}:sheared"] = {"set_property": {f"{NS}:sheared": True},
                                   "remove": {"component_groups": [f"{NS}:coat_full"]},
                                   "add": {"component_groups": [f"{NS}:coat_bare"]}}
    regrown = {f"{NS}:sheared": False}
    if mob in ANIM_STATES and "shake" in ANIM_STATES[mob]: regrown[f"{NS}:anim"] = "shake"   # it shakes out its new coat
    ent.events[f"{NS}:coat_regrown"] = {"set_property": regrown,
                                        "remove": {"component_groups": [f"{NS}:coat_bare"]},
                                        "add": {"component_groups": [f"{NS}:coat_full"]}}
    ent.remove("minecraft:loot")
    ent.add_to_spawn(f"{NS}:coat_full")
    filt = {"test": "bool_property", "domain": f"{NS}:sheared", "value": False}
    for comps in ent.everywhere():   # shearing goes ahead of milking in whichever list holds the bucket
        if "minecraft:interact" in comps:
            comps["minecraft:interact"]["interactions"].insert(0, shear_interaction(ent, f"{NS}:sheared", shear_loot, [filt]))
            return
    ent.interactions().insert(0, shear_interaction(ent, f"{NS}:sheared", shear_loot, [filt]))


def apply_traits(mob, spec, ent, loot):
    """Edits the vanilla file into this mob. loot collects the loot tables it needs: path -> table."""
    base = spec["base"]
    path = lambda name: f"loot_tables/entities/{NS}/{name}.json"

    if base == COW:
        loot[path(mob)] = table(*COW_DROPS)
        ent.set_loot(path(mob))
        if spec.get("flower"):
            flower = spec["flower"]
            loot[path(mob + "_shear")] = table(item(f"{NS}:{flower}", 1))
            regrowing_coat(ent, mob, path(mob), path(mob), path(mob + "_shear"))
            ent.family(add=["mooshroom_like", mob])
        if spec.get("coat"):
            wool = spec["coat"]
            loot[path(mob + "_full")] = table(*COW_DROPS, item(wool, 1))
            loot[path(mob + "_shear")] = table(item(wool, 1, 2))
            regrowing_coat(ent, mob, path(mob + "_full"), path(mob), path(mob + "_shear"))

    elif base == CHICKEN:
        drops = list(CHICKEN_DROPS)
        if spec.get("fancy"):
            drops[0] = item(f"{NS}:fancy_feather", 0, 2)
            # scared of every pig, Earth's or vanilla's
            ent.components["minecraft:behavior.avoid_mob_type"] = {"priority": 2, "entity_types": [
                {"filters": {"test": "is_family", "subject": "other", "value": "pig"}, "max_dist": 6, "walk_speed_multiplier": 1.2, "sprint_speed_multiplier": 1.5}]}
        if spec.get("cluckshroom"):
            drops.append(item("red_mushroom", 1, chance=0.5))
            loot[path(mob + "_shear")] = table(item("red_mushroom", 2, 4, looting=False))
            # it seeks the dark: out of the sun into shade, like a zombie at dawn
            ent.components["minecraft:behavior.flee_sun"] = {"priority": 2, "speed_multiplier": 1.2}
            ent.family(add=["cluckshroom"])
            # shorn, it becomes an ordinary chicken, the way a mooshroom becomes a cow
            ent.groups[f"{NS}:become_chicken"] = {"minecraft:transformation": {"into": "minecraft:chicken", "keep_level": True, "drop_equipment": True}}
            ent.events[f"{NS}:sheared"] = {"add": {"component_groups": [f"{NS}:become_chicken"]}}
            ent.interactions().insert(0, shear_interaction(ent, f"{NS}:sheared", path(mob + "_shear")))
        loot[path(mob)] = table(*drops)
        ent.set_loot(path(mob))

    elif base == PIG:
        loot[path(mob)] = table(*PIG_DROPS)
        ent.set_loot(path(mob))
        if spec.get("mud") == "wet":
            # a muddy pig dries out in five to ten minutes
            ent.groups[f"{NS}:drying"] = {"minecraft:timer": {"looping": False, "randomInterval": True, "time": [300, 600],
                                                              "time_down_event": {"event": f"{NS}:dried", "target": "self"}}}
            ent.groups[f"{NS}:dry_adult"] = {"minecraft:transformation": {"into": f"{NS}:dried_muddy_pig<minecraft:spawn_adult>", "keep_level": True}}
            ent.groups[f"{NS}:dry_baby"] = {"minecraft:transformation": {"into": f"{NS}:dried_muddy_pig<minecraft:entity_born>", "keep_level": True}}
            ent.events[f"{NS}:dried"] = {"sequence": [
                {"filters": {"test": "has_component", "value": "minecraft:is_baby"}, "add": {"component_groups": [f"{NS}:dry_baby"]}},
                {"filters": {"test": "has_component", "operator": "!=", "value": "minecraft:is_baby"}, "add": {"component_groups": [f"{NS}:dry_adult"]}}]}
            ent.add_to_spawn(f"{NS}:drying")
        if spec.get("mud") == "dry":
            # a dried muddy pig looks for mud and rolls in it
            ent.components["minecraft:behavior.move_to_block"] = {
                "priority": 4, "search_range": 16, "search_height": 4, "tick_interval": 20, "goal_radius": 0.8,
                "speed_multiplier": 1.1, "target_blocks": ["minecraft:mud"],
                "on_reach": [{"event": f"{NS}:reached_mud", "target": "self"}]}
            # scripts/main.js plays the hop and the roll, then sends found_mud
            ent.events[f"{NS}:reached_mud"] = {}
            ent.groups[f"{NS}:wet_adult"] = {"minecraft:transformation": {"into": f"{NS}:muddy_pig<minecraft:spawn_adult>", "keep_level": True}}
            ent.groups[f"{NS}:wet_baby"] = {"minecraft:transformation": {"into": f"{NS}:muddy_pig<minecraft:entity_born>", "keep_level": True}}
            ent.events[f"{NS}:found_mud"] = {"sequence": [
                {"filters": {"test": "has_component", "value": "minecraft:is_baby"}, "add": {"component_groups": [f"{NS}:wet_baby"]}},
                {"filters": {"test": "has_component", "operator": "!=", "value": "minecraft:is_baby"}, "add": {"component_groups": [f"{NS}:wet_adult"]}}]}
        if spec.get("mud"): ent.family(add=["muddy_pig"])

    elif base == SHEEP:
        wool, lo, hi = spec["wool"]
        loot[path(mob)] = table(item(wool, 1), item("mutton", 1, 2, smelt=True))
        loot[path(mob + "_shear")] = table(item(wool, lo, hi, looting=False))
        loot[path(mob + "_sheared")] = table(item("mutton", 1, 2, smelt=True))
        # the coat is the skin's: no random colour on spawn, no dye
        for name in ("minecraft:temperate_color", "minecraft:cold_color", "minecraft:warm_color"):
            if name in ent.events: ent.events[name] = {}
        for g in ent.groups.values():
            if "minecraft:is_dyeable" in g: g["minecraft:is_dyeable"] = {}
        ent.set_loot(path(mob))
        for comps in ent.everywhere():
            for inter in comps.get("minecraft:interact", {}).get("interactions", []):
                if inter.get("spawn_items", {}).get("table", "").endswith("sheep_shear.json"):
                    inter["spawn_items"]["table"] = path(mob + "_shear")
        for g in ent.groups.values():   # once shorn, no wool on death until it has eaten grass again
            if "minecraft:is_sheared" in g: g["minecraft:loot"] = {"table": path(mob + "_sheared")}
        if spec.get("horned"):
            # a horn as well, if it dies in its full coat
            loot[path(mob)] = table(item(wool, 1), item("mutton", 1, 2, smelt=True), item(f"{NS}:horn", 1, looting=False))
            # neutral: paws the ground, charges and rams whatever hurt it, and now and then another horned sheep
            ent.components["minecraft:attack"] = {"damage": 3}
            ent.components["minecraft:behavior.ram_attack"] = {
                "priority": 2, "run_speed": 0.8, "ram_speed": 1.9, "min_ram_distance": 3, "ram_distance": 8, "knockback_force": 2.0,
                "knockback_height": 0.1, "pre_ram_sound": "pre_ram", "ram_impact_sound": "ram_impact", "cooldown_range": {"min": 4, "max": 8},
                "on_start": [{"event": f"{NS}:ram_prep", "target": "self"}]}
            ent.components["minecraft:behavior.hurt_by_target"] = {"priority": 1}
            ent.components["minecraft:behavior.nearest_attackable_target"] = {"priority": 4, "must_see": True, "attack_interval": {"min": 30, "max": 60},
                "entity_types": [{"filters": {"all_of": [{"test": "is_family", "subject": "other", "value": "horned_sheep"},
                                                         {"test": "has_component", "subject": "self", "operator": "!=", "value": "minecraft:is_baby"}]},
                                  "max_dist": 8}]}
            ent.groups[f"{NS}:ram_charge"] = {"minecraft:timer": {"looping": False, "time": 1.2, "time_down_event": {"event": f"{NS}:ram_go", "target": "self"}}}
            ent.events[f"{NS}:ram_prep"] = {"set_property": {f"{NS}:anim": "prep"}, "add": {"component_groups": [f"{NS}:ram_charge"]}}
            ent.events[f"{NS}:ram_go"] = {"set_property": {f"{NS}:anim": "ram"}, "remove": {"component_groups": [f"{NS}:ram_charge"]},
                                          "add": {"component_groups": [f"{NS}:anim_reset"]}}
            ent.family(add=["horned_sheep"])

    elif base == RABBIT:
        drops = list(RABBIT_DROPS)
        if spec.get("jumbo"):
            drops[:2] = [item("rabbit_hide", 1), item("rabbit", 1, smelt=True)]
            # Earth's jumbo model is already the big one; the box is 0.7 by 1.2 blocks once the rabbit's 0.6 scale applies
            for comps in ent.everywhere():
                if "minecraft:collision_box" in comps: comps["minecraft:collision_box"] = {"width": 1.17, "height": 2.0}
            ent.family(add=["jumbo_rabbit"])
        # the wiki's coats are the skins, so the coat vanilla picks by biome does nothing; leave it
        loot[path(mob)] = table(*drops)
        ent.set_loot(path(mob))

    elif base == "llama":
        loot[path(mob)] = table(item("leather", 0, 2))
        ent.set_loot(path(mob))
        # it looks for ferns, eats one, then prances about jingling (scripts/main.js does the eating and prancing)
        ent.groups[f"{NS}:hungry"] = {"minecraft:behavior.move_to_block": {
            "priority": 5, "search_range": 12, "search_height": 3, "tick_interval": 40, "goal_radius": 1.2, "speed_multiplier": 1.0,
            "target_blocks": ["minecraft:fern", "minecraft:large_fern"], "on_reach": [{"event": f"{NS}:ate_fern", "target": "self"}]}}
        ent.groups[f"{NS}:full"] = {"minecraft:timer": {"looping": False, "randomInterval": True, "time": [60, 180],
                                                        "time_down_event": {"event": f"{NS}:hungry_again", "target": "self"}}}
        ent.events[f"{NS}:ate_fern"] = {"remove": {"component_groups": [f"{NS}:hungry"]}, "add": {"component_groups": [f"{NS}:full"]}}
        ent.events[f"{NS}:hungry_again"] = {"remove": {"component_groups": [f"{NS}:full"]}, "add": {"component_groups": [f"{NS}:hungry"]}}
        ent.add_to_spawn(f"{NS}:hungry")
        ent.family(add=["jolly_llama"])

    elif base == "cat":
        # Peanut Butter's coat is the skin; vanilla's random coat on spawn does nothing to it
        pass

    elif base == "iron_golem":
        loot[path(mob)] = table(item("coal", 1, 2), item("iron_nugget", 1, 2))
        ent.set_loot(path(mob))
        # its body is a furnace: water hurts it
        hurt = ent.components.setdefault("minecraft:hurt_on_condition", {"damage_conditions": []})["damage_conditions"]
        hurt.append({"filters": {"test": "in_water", "subject": "self", "operator": "==", "value": True}, "cause": "drowning", "damage_per_tick": 1})
        ent.components["minecraft:fire_immune"] = {}
        ent.family(add=["furnace_golem"])
        ent.add_property("lit", {"type": "bool", "default": False, "client_sync": True})
        ent.components["minecraft:inventory"] = {"container_type": "container", "inventory_size": 3, "can_be_siphoned_from": False}
        ent.remove("minecraft:behavior.offer_flower")   # it hands out torches instead (scripts/main.js)

    elif base == "snow_golem":
        loot[path(mob)] = table(item("melon_slice", 0, 15))
        ent.set_loot(path(mob))
        ent.components["minecraft:shooter"] = {"def": f"{NS}:melon_seed"}
        ra = ent.components["minecraft:behavior.ranged_attack"]
        ra.update({"burst_shots": 4, "burst_interval": 0.12, "attack_interval": {"min": 1.5, "max": 1.5}})
        # it hops about instead of walking
        ent.components["minecraft:movement.skip"] = {}
        ent.components.pop("minecraft:movement.basic", None)
        ent.components["minecraft:jump.dynamic"] = {}
        # the head is a melon, not a carved pumpkin: there is nothing to shear off
        for comps in ent.everywhere():
            if "minecraft:interact" in comps:
                comps["minecraft:interact"]["interactions"] = [i for i in comps["minecraft:interact"]["interactions"]
                                                                if "shears" not in json.dumps(i.get("on_interact", {}))]
                if not comps["minecraft:interact"]["interactions"]: del comps["minecraft:interact"]
        ent.family(add=["melon_golem"])

    elif base == "slime":
        loot[path(mob)] = table(item("tropical_fish", 1, looting=False))
        # always a medium slime that does not split
        medium = copy.deepcopy(ent.groups["minecraft:slime_medium"])
        medium["minecraft:health"] = {"value": 16, "max": 16}
        medium["minecraft:attack"] = {"damage": 2}
        medium["minecraft:loot"] = {"table": path(mob)}
        medium.pop("minecraft:area_attack", None)     # it only hurts what it is angry with
        for name in ("minecraft:slime_large", "minecraft:slime_small"): ent.groups.pop(name, None)
        ent.groups["minecraft:slime_medium"] = medium
        ent.events["minecraft:entity_spawned"] = {"trigger": "spawn_medium"}
        for name in ("spawn_small", "spawn_large"): ent.events.pop(name, None)
        # passive until provoked, and then only the slime that was hit
        ent.components.pop("minecraft:behavior.nearest_attackable_target", None)
        ent.components["minecraft:behavior.hurt_by_target"] = {"priority": 1, "alert_same_type": False}
        ent.components.pop("minecraft:despawn", None)
        ent.family(add=["tropical_slime"], remove=["monster"])
        ent.e["description"]["spawn_category"] = "creature"

    elif base == "zombie":
        loot[path(mob)] = table(*ZOMBIE_DROPS)
        ent.set_loot(path(mob))
        target_golems(ent)
        if spec.get("climber"):
            # it climbs walls like a spider when it sees a player above
            for comps in ent.everywhere():
                if "minecraft:navigation.walk" in comps:
                    comps["minecraft:navigation.climb"] = comps.pop("minecraft:navigation.walk")
            ent.family(add=["bouldering_zombie"])
        if spec.get("lobber"):
            # rotten flesh from afar, the usual swipe up close
            ent.components["minecraft:shooter"] = {"def": f"{NS}:rotten_flesh"}
            ent.components["minecraft:behavior.ranged_attack"] = {"priority": 2, "attack_interval": {"min": 2, "max": 3},
                                                                  "attack_range": {"min": 4, "max": 12}, "speed_multiplier": 1.0}
            ent.family(add=["lobber_zombie"])

    elif base == "wolf":
        make_skeleton_wolf(ent, mob, loot, path)

    elif base == "spider":
        loot[path(mob)] = table(item("string", 0, 2, chance=0.35), item("bone", 0, 2, chance=0.4), item("bone_meal", 1, 2, chance=0.25))
        ent.set_loot(path(mob))
        ent.set_health(32)
        for comps in ent.everywhere():
            if "minecraft:attack" in comps: comps["minecraft:attack"]["damage"] = 3
        # it spits bone shards from a distance
        ent.components["minecraft:shooter"] = {"def": f"{NS}:bone_shard"}
        ent.components["minecraft:behavior.ranged_attack"] = {"priority": 3, "attack_interval": {"min": 2, "max": 3},
                                                              "attack_range": {"min": 4, "max": 12}, "speed_multiplier": 1.0}
        target_golems(ent)
        ent.family(add=["bone_spider"])

    elif base == "witch":
        loot[path(mob)] = table(item("glowstone_dust", 2, looting=False), item("sugar", 2, looting=False), item("gunpowder", 2, looting=False),
                                item("redstone", 2, looting=False), item("lapis_lazuli", 2, chance=0.1, looting=False))
        ent.set_loot(path(mob))
        ent.set_health(30)
        # lingering potions of harming, and of poison for a healthy target
        ent.components["minecraft:shooter"] = {"def": "minecraft:lingering_potion", "aux_val": 23, "magic": True, "sound": "throw", "power": 0.75,
                                               "projectiles": [{"def": "minecraft:lingering_potion", "aux_val": 25, "filters": {"all_of": [
                                                   {"test": "actor_health", "subject": "other", "operator": ">=", "value": 8},
                                                   {"none_of": [{"test": "has_mob_effect", "subject": "other", "value": "poison"}]}]}}]}
        # invisibility before it attacks, healing when hurt
        potions = ent.components["minecraft:behavior.drink_potion"]["potions"]
        potions.append({"id": 7, "chance": 0.3, "filters": {"all_of": [{"test": "has_target", "subject": "self", "value": True},
                                                                       {"none_of": [{"test": "has_mob_effect", "subject": "self", "value": "invisibility"}]}]}})
        for p in potions:
            if p["id"] == 21: p["chance"] = 0.2
        # immune to poison and harming
        ent.components["minecraft:mob_effect_immunity"] = {"mob_effects": ["poison", "instant_damage"]}
        ent.family(add=["viler_witch"])


def target_golems(ent):
    """Earth's monsters went for melon and furnace golems as well as players."""
    for comps in ent.everywhere():
        nat = comps.get("minecraft:behavior.nearest_attackable_target")
        if not nat: continue
        types = nat.setdefault("entity_types", [])
        if isinstance(types, dict): types = nat["entity_types"] = [types]
        types.append({"filters": {"any_of": [{"test": "is_family", "subject": "other", "value": "furnace_golem"},
                                             {"test": "is_family", "subject": "other", "value": "melon_golem"}]}, "max_dist": 16})


def make_skeleton_wolf(ent, mob, loot, path):
    """A wolf that is undead, hostile and cannot be tamed, and howls to strengthen the skeletons around it."""
    loot[path(mob)] = table(item("bone", 1, 2))
    ent.set_loot(path(mob))
    # keep the body and the wild, angry and baby states; drop taming, collars, armour and coats
    for name in list(ent.groups):
        if not name.endswith(("_baby", "_adult", "_angry", "_wild")): del ent.groups[name]
    for g in ent.groups.values():
        for k in ("minecraft:tameable", "minecraft:rideable", "minecraft:leashable"): g.pop(k, None)
    for k in ("minecraft:behavior.beg", "minecraft:behavior.stay_while_sitting", "minecraft:healable", "minecraft:behavior.float",
              "minecraft:behavior.panic", "minecraft:balloonable"):
        ent.components.pop(k, None)
    props = ent.e["description"].get("properties", {})   # the wolf's own go; this add-on's stay
    ent.e["description"]["properties"] = {k: v for k, v in props.items() if k == f"{NS}:anim"}
    events = {}
    events["minecraft:entity_spawned"] = {"randomize": [{"weight": 9, "add": {"component_groups": ["minecraft:wolf_adult", "minecraft:wolf_wild"]}},
                                                        {"weight": 1, "add": {"component_groups": ["minecraft:wolf_baby", "minecraft:wolf_wild"]}}]}
    for name, ev in ent.events.items():
        if name in ("minecraft:ageable_grow_up", "minecraft:become_angry", "minecraft:on_calm", "minecraft:entity_born"):
            events[name] = ev
    ent.e["events"] = events
    text = json.dumps(ent.e)   # anything left that points at a removed group or a removed property goes too
    for gone in re.findall(r'"(minecraft:wolf_[a-z_]+)"', text):
        if gone not in ent.groups: text = text.replace(f'"{gone}"', '"minecraft:wolf_wild"')
    ent.e = json.loads(text); ent.data["minecraft:entity"] = ent.e
    ent.set_health(10)
    for comps in ent.everywhere():
        if "minecraft:attack" in comps: comps["minecraft:attack"]["damage"] = 4
    ent.components["minecraft:breathable"] = {"breathes_water": True, "breathes_air": True, "total_supply": 15, "suffocate_time": 0}
    ent.family(add=["skeleton_wolf", "undead", "monster", "mob"], remove=["wolf"])
    # hostile to players and to jumbo rabbits, never to skeletons
    ent.components["minecraft:behavior.nearest_attackable_target"] = {"priority": 3, "must_see": True, "reselect_targets": True, "entity_types": [
        {"filters": {"any_of": [{"test": "is_family", "subject": "other", "value": "player"}]}, "max_dist": 16},
        {"filters": {"test": "is_family", "subject": "other", "value": "jumbo_rabbit"}, "max_dist": 12},
        {"filters": {"any_of": [{"test": "is_family", "subject": "other", "value": "furnace_golem"},
                                {"test": "is_family", "subject": "other", "value": "melon_golem"}]}, "max_dist": 16}]}
    ent.components["minecraft:behavior.hurt_by_target"] = {"priority": 1, "entity_types": {"filters": {"test": "is_family", "subject": "other", "operator": "!=", "value": "skeleton"}}}
    # while hunting it howls every so often, and the skeletons around it (not itself) hit harder
    ent.groups[f"{NS}:howling"] = {"minecraft:timer": {"looping": True, "randomInterval": True, "time": [12, 24],
                                                       "time_down_event": {"event": f"{NS}:howl", "target": "self"}}}
    ent.components["minecraft:on_target_acquired"] = {"event": f"{NS}:hunting", "target": "self"}
    ent.components["minecraft:on_target_escape"] = {"event": f"{NS}:resting", "target": "self"}
    ent.events[f"{NS}:hunting"] = {"add": {"component_groups": [f"{NS}:howling"]}}
    ent.events[f"{NS}:resting"] = {"remove": {"component_groups": [f"{NS}:howling"]}}
    ent.events[f"{NS}:howl"] = {"set_property": {f"{NS}:anim": "howl"}, "add": {"component_groups": [f"{NS}:anim_reset"]}, "queue_command": {"command": [
        "playsound mob.wolf.howl @a ~ ~ ~ 2 0.7",
        "effect @e[family=skeleton,r=16] strength 10 0",
        "effect @e[family=skeleton_wolf,r=16,rm=0.5] strength 10 0",
        "particle minecraft:villager_angry ~ ~1.2 ~"]}}
    ent.e["description"]["spawn_category"] = "monster"
    ent.components["minecraft:despawn"] = {"despawn_from_distance": {}}


# --------------------------------------------------------------------------------------------------------------------
# Spawn rules
# --------------------------------------------------------------------------------------------------------------------

def spawn_rule(mob, spec):
    base = spec["base"]
    try: vanilla_rule = vanilla("spawn_rules", base)["minecraft:spawn_rules"]
    except FileNotFoundError: vanilla_rule = None
    conds = (vanilla_rule or {}).get("conditions") or []
    monster = (vanilla_rule or {}).get("description", {}).get("population_control") == "monster"
    if base == "slime": monster = False      # the tropical slime is neutral and out in the day
    if base == "wolf": monster = True        # the skeleton wolf is a night hunter
    cond = copy.deepcopy(conds[0]) if conds else {}
    for k in ("minecraft:permute_type", "minecraft:biome_filter", "minecraft:spawns_on_block_filter", "minecraft:spawns_underground",
              "minecraft:spawns_on_block_prevented_filter", "minecraft:spawn_event", "minecraft:is_persistent"):
        cond.pop(k, None)
    cond["minecraft:spawns_on_surface"] = {}
    cond["minecraft:biome_filter"] = BIOMES[spec["biome"]]
    if monster:
        cond["minecraft:brightness_filter"] = {"min": 0, "max": 7, "adjust_for_weather": True}
        cond.setdefault("minecraft:difficulty_filter", {"min": "easy", "max": "hard"})
        cond["minecraft:weight"] = {"default": MONSTER_WEIGHT[spec["rarity"]] // (5 if base == "witch" else 1)}
        if spec["biome"] == "dark_forest": cond["minecraft:spawns_underground"] = {}   # the bone spider hides in caves too
    else:
        cond["minecraft:brightness_filter"] = {"min": 7, "max": 15, "adjust_for_weather": False}
        cond["minecraft:spawns_on_block_filter"] = SURFACE.get(spec["biome"], ["minecraft:grass_block"])
        cond["minecraft:weight"] = {"default": ANIMAL_WEIGHT[spec["rarity"]]}
        cond.pop("minecraft:difficulty_filter", None)
    if base in ("iron_golem", "snow_golem"): cond["minecraft:herd"] = {"min_size": 1, "max_size": 1}
    cond.setdefault("minecraft:herd", {"min_size": 1, "max_size": 2})
    return {"format_version": "1.8.0", "minecraft:spawn_rules": {
        "description": {"identifier": f"{NS}:{mob}", "population_control": "monster" if monster else "animal"},
        "conditions": [cond]}}


# --------------------------------------------------------------------------------------------------------------------
# Hand-written additions merged into a generated mob: the furnace golem keeps its furnace this way
# --------------------------------------------------------------------------------------------------------------------

def build():
    out = {}
    loot = {}
    for mob, spec in MOBS.items():
        ent = Entity(retarget(spec["base"], mob))
        if mob in ANIM_STATES:
            ent.add_property("anim", {"type": "enum", "values": ANIM_STATES[mob], "default": "none", "client_sync": True})
            # any state other than none settles back after a moment
            ent.groups[f"{NS}:anim_reset"] = {"minecraft:timer": {"looping": False, "time": 2.5, "time_down_event": {"event": f"{NS}:anim_none", "target": "self"}}}
            ent.events[f"{NS}:anim_none"] = {"set_property": {f"{NS}:anim": "none"}, "remove": {"component_groups": [f"{NS}:anim_reset"]}}
        apply_traits(mob, spec, ent, loot)
        if mob in ANIM_STATES and "shake" in ANIM_STATES[mob] and f"{NS}:coat_regrown" in ent.events:
            ent.events[f"{NS}:coat_regrown"].setdefault("add", {}).setdefault("component_groups", []).append(f"{NS}:anim_reset")
        out[f"entities/{mob}.json"] = ent.data
        if spec["biome"]: out[f"spawn_rules/{mob}.json"] = spawn_rule(mob, spec)
    out.update(loot)
    out.update(extras())
    return out


# --------------------------------------------------------------------------------------------------------------------
# The projectiles, items and blocks Earth's mobs need
# --------------------------------------------------------------------------------------------------------------------

def projectile(name, damage, gravity, power):
    return {"format_version": "1.21.0", "minecraft:entity": {
        "description": {"identifier": f"{NS}:{name}", "is_spawnable": False, "is_summonable": True},
        "components": {
            "minecraft:type_family": {"family": ["projectile", name]},
            "minecraft:collision_box": {"width": 0.25, "height": 0.25},
            "minecraft:physics": {}, "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
            "minecraft:projectile": {"anchor": "eye_height", "offset": [0, -0.1, 0], "gravity": gravity, "power": power, "angle_offset": 0.0,
                                     "on_hit": {"impact_damage": {"damage": damage, "knockback": True, "destroy_on_hit": True},
                                                "remove_on_hit": {}}}}}}


def flower(name):
    return {"format_version": "1.21.40", "minecraft:block": {
        "description": {"identifier": f"{NS}:{name}", "menu_category": {"category": "nature", "group": "itemGroup.name.flower"}},
        "components": {
            "minecraft:geometry": "minecraft:geometry.cross",
            "minecraft:material_instances": {"*": {"texture": f"{NS}_{name}", "render_method": "alpha_test", "face_dimming": False, "ambient_occlusion": False}},
            "minecraft:collision_box": False,
            "minecraft:selection_box": {"origin": [-5, 0, -5], "size": [10, 10, 10]},
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 0},
            "minecraft:flammable": {"catch_chance_modifier": 60, "destroy_chance_modifier": 100},
            "minecraft:light_dampening": 0,
            "minecraft:placement_filter": {"conditions": [{"allowed_faces": ["up"], "block_filter": [
                "minecraft:grass_block", "minecraft:dirt", "minecraft:coarse_dirt", "minecraft:podzol", "minecraft:moss_block", "minecraft:mud", "minecraft:rooted_dirt"]}]}}}}


def extras():
    out = {
        "entities/melon_seed.json": projectile("melon_seed", 1, 0.03, 1.4),
        "entities/bone_shard.json": projectile("bone_shard", {"range_min": 2, "range_max": 6}, 0.02, 1.6),
        "entities/rotten_flesh.json": projectile("rotten_flesh", 1, 0.05, 1.1),
        "blocks/buttercup.json": flower("buttercup"),
        "blocks/pink_daisy.json": flower("pink_daisy"),
        "blocks/rainbow_wool.json": {"format_version": "1.21.40", "minecraft:block": {
            "description": {"identifier": f"{NS}:rainbow_wool", "menu_category": {"category": "construction", "group": "itemGroup.name.wool"}},
            "components": {
                "minecraft:material_instances": {"*": {"texture": f"{NS}_rainbow_wool"}},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.2},
                "minecraft:flammable": {"catch_chance_modifier": 30, "destroy_chance_modifier": 60},
                "minecraft:map_color": "#d65f8a"}}},
    }
    for name in ("fancy_feather", "horn"):
        out[f"items/{name}.json"] = {"format_version": "1.21.40", "minecraft:item": {
            "description": {"identifier": f"{NS}:{name}", "menu_category": {"category": "items"}},
            "components": {"minecraft:icon": f"{NS}_{name}", "minecraft:max_stack_size": 64}}}
    return out


def render(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    ensure_vanilla()
    files = build()
    stale = []
    for rel, data in sorted(files.items()):
        dest = os.path.join(BP, rel)
        text = render(data)
        if args.check:
            if not os.path.exists(dest) or open(dest, encoding="utf8").read() != text: stale.append(rel)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf8", newline="\n") as f: f.write(text)
    if args.check:
        for rel in stale: print("stale:", rel)
        sys.exit(1 if stale else 0)
    # the old hand-copied melon golem file is replaced by the generated one
    old = os.path.join(BP, "entities", "melon_golem.behavior.json")
    if os.path.exists(old): os.remove(old)
    print(f"wrote {len(files)} files")


if __name__ == "__main__":
    main()
