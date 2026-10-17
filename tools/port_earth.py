"""Ports each mob's look from Minecraft Earth's own resource pack: model, skin, animations, render controllers, particles.

Earth was built on the Bedrock engine, so its client files are already Bedrock's: a client entity, geometry,
animations and animation controllers per mob, under mobs/<kind>/<mob>/ in andiricum2/MC-Earth-Resourcepack. That pack
is cloned into java/, which git ignores; this reads it and writes the resource pack's files, which are committed.

What changes on the way:

* identifiers move to kirbycope:, and every geometry, animation, controller and particle Earth defines gets a
  kirbycope. prefix, so Earth's animation.quadruped.walk never replaces vanilla's for every other mob in the world;
* skins are written as PNG under textures/entity/earth/, converted from TGA where Earth shipped TGA;
* materials only Earth's engine had are swapped for the nearest vanilla one;
* the variables Earth's server pushed to the client (a witch about to cast, a mud pig rolling, a llama prancing) are
  set from the mob's kirbycope:anim property, which the behavior pack and scripts/main.js drive, and the few values
  Bedrock's engine fills in only for its own mobs (wing flap, jump angle, golem attack swing) are worked out in Molang.

    python tools/port_earth.py
"""

import glob
import json
import os
import re
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EARTH = os.path.join(ROOT, "java")
RP = os.path.join(ROOT, "development_resource_packs", "Minecraft-Earth-Mobs-Bedrock")
NS = "kirbycope"
OUT_TEX = "textures/entity/earth"

# our mob -> Earth client entity
PORT = {
    "albino_cow": "cow/albino_cow/albino_cow", "ashen_cow": "cow/ashen_cow/ashen_cow", "cookie_cow": "cow/cookie_cow/cookie_cow",
    "cream_cow": "cow/cream_cow/cream_cow", "dairy_cow": "cow/dairy_cow/dairy_cow", "moobloom": "cow/moo_bloom/moo_bloom",
    "moolip": "cow/moolip/moolip", "pinto_cow": "cow/pinto_cow/pinto_cow", "sunset_cow": "cow/sunset_cow/sunset_cow",
    "umbra_cow": "cow/umbra_cow/umbra_cow", "wooly_cow": "cow/wooly_cow/wooly_cow",
    "amber_chicken": "chicken/amber_chicken/amber_chicken", "bronzed_chicken": "chicken/bronzed_chicken/bronzed_chicken",
    "cluckshroom": "chicken/cluck_shroom/cluck_shroom", "fancy_chicken": "chicken/fancy_chicken/fancy_chicken",
    "gold_crested_chicken": "chicken/gold_crested_chicken/gold_crested_chicken", "midnight_chicken": "chicken/midnight_chicken/midnight_chicken",
    "skewbald_chicken": "chicken/skewbald_chicken/skewbald_chicken", "stormy_chicken": "chicken/stormy_chicken/stormy_chicken",
    "mottled_pig": "pig/mottled_pig/mottled_pig", "muddy_pig": "pig/mud_pig/mud_pig", "dried_muddy_pig": "pig/mud_pig/mud_pig",
    "pale_pig": "pig/pale_pig/pale_pig", "piebald_pig": "pig/piebald_pig/piebald_pig", "pink_footed_pig": "pig/pink_footed_pig/pink_footed_pig",
    "sooty_pig": "pig/sooty_pig/sooty_pig", "spotted_pig": "pig/spotted_pig/spotted_pig",
    "bold_striped_rabbit": "rabbit/bold_striped/bold_striped", "desert_rabbit": "rabbit/genoa_rabbit/genoa_rabbit",
    "freckled_rabbit": "rabbit/freckled/freckled", "harelequin_rabbit": "rabbit/harelequin/harelequin",
    "jumbo_rabbit": "rabbit/jumbo_rabbit/jumbo_rabbit", "muddy_foot_rabbit": "rabbit/muddy_foot/muddy_foot", "vested_rabbit": "rabbit/vested/vested",
    "flecked_sheep": "sheep/flecked/flecked", "fuzzy_sheep": "sheep/fuzzy/fuzzy", "horned_sheep": "sheep/horned_sheep/horned_sheep",
    "inky_sheep": "sheep/inky/inky", "long_nose_sheep": "sheep/long_nosed/long_nosed", "patched_sheep": "sheep/patched/patched",
    "rainbow_sheep": "sheep/rainbow_sheep/rainbow_sheep", "rocky_sheep": "sheep/rocky/rocky",
    "furnace_golem": "iron_golem/furnace_golem/furnace_golem", "jolly_llama": "llama/jolly_llama/jolly_llama",
    "tropical_slime": "slime/tropical_slime/tropical_slime", "melon_golem": "snow_golem/melon_golem/melon_golem",
    "melon_seed": "snow_golem/melon_golem/melon_golem_projectile", "bone_spider": "spider/bone_spider/bone_spider",
    "bone_shard": "spider/bone_spider/bone_shard", "viler_witch": "witch/viler/viler_witch", "skeleton_wolf": "wolf/skeleton_wolf/skeleton_wolf",
    "bouldering_zombie": "zombie/bouldering/bouldering_zombie", "lobber_zombie": "zombie/lobber/lobber_zombie",
    "rotten_flesh": "zombie/lobber/rotten_flesh_projectile",
}

# materials Earth's engine had and vanilla does not
MATERIALS = {"furnace_golem": "entity_emissive_alpha", "jolly_llama": "entity_alphatest", "tropical_slime": "slime"}

# Values Bedrock works out only for its own mobs, and what Earth's server told the client, as Molang. Each list is
# added to the mob's pre_animation; anim is the mob's kirbycope:anim property, which the behavior pack sets.
ANIM = "query.property('kirbycope:anim')"
CHICKEN = ["variable.wing_flap = query.is_on_ground ? 0 : ((math.sin(query.life_time * 1700) + 1) * 0.5);"]
RABBIT = ["variable.jump_rotation = math.clamp(query.vertical_speed / 8, -1, 1);"]
EXTRA = {
    "furnace_golem": [
        "variable.attack_animation_tick = (variable.attack_time ?? 0) > 0 ? 10 * (1 - variable.attack_time) : 0;",
        f"variable.offer_gift_tick = {ANIM} == 'gift' ? 40 : 0;",
        f"variable.summon = {ANIM} == 'summon';",
    ],
    "muddy_pig": [
        "variable.muddy = 1;", "variable.is_muddy = 1;",
        f"variable.celebrate_mud = {ANIM} == 'celebrate';",
    ],
    "dried_muddy_pig": [
        "variable.muddy = 0;", "variable.is_muddy = 0;",
        f"variable.seek_mud = {ANIM} == 'seek';",
        f"variable.hop_into_mud = {ANIM} == 'hop';",
        f"variable.mud_rolling = {ANIM} == 'roll';",
    ],
    "horned_sheep": [
        f"variable.prepare_ram = {ANIM} == 'prep';",
        f"variable.ramming = {ANIM} == 'ram';",
        "variable.grazing = query.is_grazing;",
    ],
    "jolly_llama": [
        f"variable.fern_detected = {ANIM} == 'fern';",
        f"variable.grazing = {ANIM} == 'graze';",
        f"variable.prancing = {ANIM} == 'prance';",
    ],
    "viler_witch": [f"variable.cast_preparing = {ANIM} == 'attack';", "variable.isholdingitem = query.is_item_equipped;"],
    "melon_golem": [f"variable.shots_fired = {ANIM} == 'attack';"],
    "bone_spider": [f"variable.start_shooting_animation = {ANIM} == 'attack';"],
    "lobber_zombie": [f"variable.shots_preparing = {ANIM} == 'attack';"],
    "bouldering_zombie": [
        f"variable.climb_prep = {ANIM} == 'climb_prep';",
        f"variable.climb = {ANIM} == 'climb';",
        f"variable.climb_exit = {ANIM} == 'climb_exit';",
    ],
    "skeleton_wolf": [f"variable.is_howling = {ANIM} == 'howl';"],
    "wooly_cow": [f"variable.is_shaking = {ANIM} == 'shake';"],
}

# Earth's art for the items and blocks the mobs drop: our texture name -> Earth file
ITEM_TEXTURES = {"fancy_feather": "textures/items/fancy_feather", "horn": "textures/items/horn"}
BLOCK_TEXTURES = {"buttercup": "textures/blocks/flower_buttercup", "pink_daisy": "textures/blocks/flower_pink_daisy",
                  "rainbow_wool": "textures/blocks/wool_colored_rainbow"}
NAMES = {
    "item.kirbycope:fancy_feather": "Fancy Feather", "item.kirbycope:horn": "Horn",
    "tile.kirbycope:buttercup.name": "Buttercup", "tile.kirbycope:pink_daisy.name": "Pink Daisy",
    "tile.kirbycope:rainbow_wool.name": "Rainbow Wool",
    "entity.kirbycope:horned_sheep.name": "Horned Sheep", "item.spawn_egg.entity.kirbycope:horned_sheep.name": "Spawn Horned Sheep",
    "entity.kirbycope:melon_seed.name": "Melon Seed", "entity.kirbycope:bone_shard.name": "Bone Shard",
    "entity.kirbycope:rotten_flesh.name": "Rotten Flesh",
}

# The Earth skins replace these hand-made ones; anything here that no client entity uses any more is removed.
OLD_FILES = ["models/entity/cluckshroom.geo.json", "models/entity/melon_golem.geo.json", "models/entity/furnace_golem.geo.json",
             "animations/melon_golem.animation.json", "render_controllers/furnace_golem.render_controllers.json"]

# Earth's folder -> the vanilla mob the behavior is built on, and the render scale vanilla's client gives that mob to
# undo the scale its behavior file sets (a rabbit is 0.6 in the world and drawn at 1/0.6).
BASES = {"rabbit": "rabbit"}
VANILLA_SCALE = {"rabbit": "query.is_baby ? (1 / 0.4) : (1 / 0.6)"}

# spawn egg colours, base and spots
EGGS = {
    "horned_sheep": ("#d8cfc0", "#6b4b33"),
}


def lenient(text):
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def load(path):
    return lenient(open(path, encoding="utf8", errors="ignore").read())


class Earth:
    """Every definition in Earth's pack, by identifier."""

    def __init__(self):
        self.where = {}     # id -> source file
        self.parent = {}    # old-format geometry -> the geometry it inherits from
        for path in glob.glob(os.path.join(EARTH, "**", "*.json"), recursive=True):
            try: data = load(path)
            except Exception: continue
            if not isinstance(data, dict): continue
            for key, value in data.items():
                if key.startswith("geometry."):
                    name, _, parent = key.partition(":")
                    self.where.setdefault(name, path)
                    if parent: self.parent.setdefault(name, parent)
                if key == "minecraft:geometry":
                    for g in value: self.where.setdefault(g["description"]["identifier"], path)
                if key in ("animations", "animation_controllers", "render_controllers") and isinstance(value, dict):
                    for i in value: self.where.setdefault(i, path)
                if key == "particle_effect": self.where.setdefault(value["description"]["identifier"], path)

    def has(self, ident): return ident in self.where


def rename(ident):
    """kirbycope's name for an id Earth defines."""
    for prefix in ("controller.animation.", "controller.render.", "animation.", "geometry."):
        if ident.startswith(prefix):
            rest = ident[len(prefix):]
            rest = rest[len("genoa."):] if rest.startswith("genoa.") else rest
            return f"{prefix}{NS}.{rest}"
    if ":" in ident: return f"{NS}:" + ident.split(":", 1)[1].replace("genoa_", "")
    return ident


class Port:
    def __init__(self):
        self.earth = Earth()
        self.files = {}          # source file -> set of ids to port from it
        self.textures = {}       # earth texture path (no extension) -> our path

    def need(self, ident):
        if not self.earth.has(ident): return ident
        self.files.setdefault(self.earth.where[ident], set()).add(ident)
        return rename(ident)

    def texture(self, earth_path):
        rel = earth_path[len("mobs/"):] if earth_path.startswith("mobs/") else earth_path
        ours = f"{OUT_TEX}/{rel}"
        self.textures[earth_path] = ours
        return ours

    def entity(self, mob, earth_file):
        desc = load(os.path.join(EARTH, "mobs", earth_file + ".ent.json"))["minecraft:client_entity"]["description"]
        out = {"identifier": f"{NS}:{mob}"}
        out["materials"] = {k: MATERIALS.get(v, v) for k, v in desc.get("materials", {}).items()}
        out["textures"] = {k: self.texture(v) for k, v in desc.get("textures", {}).items()}
        out["geometry"] = {k: self.geometry(v) for k, v in desc.get("geometry", {}).items()}
        if "animations" in desc: out["animations"] = {k: self.need(v) for k, v in desc["animations"].items()}
        if "animation_controllers" in desc:
            out["animation_controllers"] = [{k: self.need(v) for k, v in c.items()} for c in desc["animation_controllers"]]
        if "particle_effects" in desc: out["particle_effects"] = {k: self.need(v) for k, v in desc["particle_effects"].items()}
        if "sound_effects" in desc: out["sound_effects"] = desc["sound_effects"]
        scripts = json.loads(json.dumps(desc.get("scripts", {})).replace("query.muddy", "variable.muddy"))
        if "initialization" in scripts: scripts["initialize"] = scripts.pop("initialization")   # Earth's name for it
        extra = list(EXTRA.get(mob, []))
        text = json.dumps(desc)
        if "wing_flap" in text or "chicken" in earth_file: extra = CHICKEN + extra
        if "rabbit" in earth_file: extra = RABBIT + extra
        if extra: scripts["pre_animation"] = scripts.get("pre_animation", []) + extra
        base = BASES.get(earth_file.split("/")[0])
        if base and "scale" not in scripts and base in VANILLA_SCALE:
            scripts["scale"] = VANILLA_SCALE[base]   # the behavior pack keeps the vanilla mob's own scale, so undo it the same way
        if scripts: out["scripts"] = scripts
        rcs = []
        for rc in desc.get("render_controllers", []):
            if isinstance(rc, str): rcs.append(self.need(rc))
            else: rcs.append({self.need(k): v.replace("query.muddy", "variable.muddy") for k, v in rc.items()})
        out["render_controllers"] = rcs
        return out

    def geometry(self, ident):
        if not self.earth.has(ident): return ident
        self.need(ident)
        if ident in self.earth.parent: self.geometry(self.earth.parent[ident])
        return rename(ident)

    def write(self):
        written = []
        for src, idents in sorted(self.files.items()):
            data = load(src)
            out = {"format_version": data.get("format_version", "1.8.0")}
            if any(k.startswith("geometry.") for k in data): out["format_version"] = "1.12.0"
            for key, value in data.items():
                if key == "minecraft:geometry":
                    geos = []
                    for g in value:
                        if g["description"]["identifier"] in idents:
                            g = json.loads(json.dumps(g)); g["description"]["identifier"] = rename(g["description"]["identifier"])
                            geos.append(g)
                    if geos: out["minecraft:geometry"] = geos
                elif key.startswith("geometry."):
                    name, _, parent = key.partition(":")
                    if name in idents:
                        out.setdefault("minecraft:geometry", []).append(self.modern_geometry(name, value, parent))
                elif key in ("animations", "animation_controllers", "render_controllers"):
                    part = {rename(i): self.fix(v) for i, v in value.items() if i in idents}
                    if part: out[key] = part
                elif key == "particle_effect" and value["description"]["identifier"] in idents:
                    v = json.loads(json.dumps(value)); v["description"]["identifier"] = rename(v["description"]["identifier"])
                    tex = v["description"].get("basic_render_parameters", {}).get("texture", "")
                    if tex.startswith("mobs/"): v["description"]["basic_render_parameters"]["texture"] = self.texture(tex)
                    out["particle_effect"] = v
            rel = os.path.relpath(src, EARTH).replace("\\", "/")
            if "minecraft:geometry" in out or any(k.startswith("geometry.") for k in out): folder = "models/entity/earth"
            elif "animations" in out: folder = "animations/earth"
            elif "animation_controllers" in out: folder = "animation_controllers/earth"
            elif "render_controllers" in out: folder = "render_controllers/earth"
            elif "particle_effect" in out: folder = "particles/earth"
            else: continue
            name = re.sub(r"\.(geo|anim|acon|rcon|fx|ent)$", "", os.path.basename(rel)[:-len(".json")]).replace(".", "_")
            dest = os.path.join(RP, folder, f"{name}.json")
            if dest in written:   # two sources with one name: name it by its folder too
                dest = os.path.join(RP, folder, os.path.dirname(rel).split("/")[-1] + "_" + name + ".json")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf8", newline="\n") as f: f.write(json.dumps(out, indent=2) + "\n")
            written.append(dest)
        for earth_path, ours in sorted(self.textures.items()):
            src = next((os.path.join(EARTH, earth_path + ext) for ext in (".png", ".tga") if os.path.exists(os.path.join(EARTH, earth_path + ext))), None)
            if not src: print("no texture", earth_path); continue
            dest = os.path.join(RP, ours + ".png")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if src.endswith(".png"): shutil.copyfile(src, dest)
            else: Image.open(src).save(dest, optimize=True)
        return written

    def modern_geometry(self, name, value, parent):
        """Earth kept its models in the 1.8 layout, which Bedrock reads without the poly_mesh its models are made of.
        The same bones in the 1.12 layout render, so each model is rewritten that way, with any model it inherits from
        folded in, since the 1.12 layout has no inheritance."""
        bones = {b["name"]: b for b in value.get("bones", [])}
        width, height = value.get("texturewidth"), value.get("textureheight")
        bounds = {k: value[k] for k in ("visible_bounds_width", "visible_bounds_height", "visible_bounds_offset") if k in value}
        while parent:
            pname, _, grand = parent, None, None
            src = self.earth.where.get(pname)
            if not src: break
            pdata = load(src)
            pkey = next((k for k in pdata if k.split(":")[0] == pname), None)
            if not pkey: break
            pval = pdata[pkey]
            for b in pval.get("bones", []): bones.setdefault(b["name"], b)
            width = width or pval.get("texturewidth"); height = height or pval.get("textureheight")
            for k in ("visible_bounds_width", "visible_bounds_height", "visible_bounds_offset"):
                if k in pval: bounds.setdefault(k, pval[k])
            parent = pkey.partition(":")[2]
        desc = {"identifier": rename(name), "texture_width": width or 64, "texture_height": height or 64}
        desc.update(bounds)
        desc.setdefault("visible_bounds_width", 3); desc.setdefault("visible_bounds_height", 3); desc.setdefault("visible_bounds_offset", [0, 1.5, 0])
        for b in bones.values():
            b.pop("neverRender", None)
        return {"description": desc, "bones": list(bones.values())}

    def fix(self, value):
        """Earth-only queries inside an animation or controller, made Bedrock's."""
        text = json.dumps(value).replace("query.muddy", "variable.muddy")
        text = text.replace("query.health_percent", "(query.health / math.max(query.max_health, 1))")
        return json.loads(text)


def furnace_golem(desc):
    """Earth's golem already burns: flames across its chest and eyes while it has a target, animated by uv_anim. The
    chest flames also show while its furnace is smelting (kirbycope:lit, set by scripts/main.js), and flame, smoke
    and a crackle come out of the furnace mouth then, from animations/furnace_golem.animation.json."""
    desc["materials"]["aggro_flames"] = "entity_beam_additive"   # glows, and the flame texture's clear pixels add nothing
    desc["animations"]["fire"] = "animation.furnace_golem.fire"
    desc["animations"]["fire_controller"] = "controller.animation.furnace_golem.fire"
    desc["scripts"]["animate"].append("fire_controller")
    desc["particle_effects"] = {"flame": "kirbycope:furnace_golem_flame", "smoke": "kirbycope:furnace_golem_smoke"}
    desc["sound_effects"] = dict(desc.get("sound_effects", {}), crackle="block.furnace.lit")


def furnace_golem_files():
    rc_path = os.path.join(RP, "render_controllers", "earth", "furnace_golem.json")
    rc = json.load(open(rc_path, encoding="utf8"))
    aggro = rc["render_controllers"]["controller.render.kirbycope.furnace_golem_aggro"]
    aggro["part_visibility"] = [{"aggro_eyes": "query.has_target"},
                                {"aggro_chest": "query.has_target || query.property('kirbycope:lit')"}]
    json.dump(rc, open(rc_path, "w", encoding="utf8", newline="\n"), indent=2)
    geo_path = os.path.join(RP, "models", "entity", "earth", "furnace_golem.json")
    geo = json.load(open(geo_path, encoding="utf8"))
    for g in geo["minecraft:geometry"]:
        if g["description"]["identifier"] == "geometry.kirbycope.furnace_golem":
            for b in g["bones"]:
                if b["name"] == "chest": b["locators"] = {"furnace_mouth": [0, 25, -7]}
    json.dump(geo, open(geo_path, "w", encoding="utf8", newline="\n"), indent=2)


def tropical_slime():
    """Earth animated the fish inside the slime by sliding a uv_anim window down a strip of 48 frames. Bedrock does not
    apply uv_anim to a poly_mesh model, which squeezes every frame into the cube at once, so the strip is cut into its
    48 frames here and the render controller steps through them at Earth's 17 frames a second."""
    folder = os.path.join(RP, OUT_TEX, "slime", "tropical_slime")
    strip_path = os.path.join(folder, "tropical_slime.png")
    strip = Image.open(strip_path).convert("RGBA")
    frames = 48
    h = strip.height // frames
    names = []
    for i in range(frames):
        name = f"tropical_slime_{i:02d}"
        strip.crop((0, i * h, strip.width, (i + 1) * h)).save(os.path.join(folder, name + ".png"), optimize=True)
        names.append(name)
    os.remove(strip_path)
    ent_path = os.path.join(RP, "entity", "tropical_slime.entity.json")
    ent = json.load(open(ent_path, encoding="utf8"))
    tex = ent["minecraft:client_entity"]["description"]["textures"]
    del tex["default"]
    for name in names: tex[name] = f"{OUT_TEX}/slime/tropical_slime/{name}"
    json.dump(ent, open(ent_path, "w", encoding="utf8", newline="\n"), indent=2)
    rc_path = os.path.join(RP, "render_controllers", "earth", "tropical_slime.json")
    rc = json.load(open(rc_path, encoding="utf8"))
    inner = rc["render_controllers"]["controller.render.kirbycope.tropical_slime"]
    inner.pop("uv_anim", None)
    inner["arrays"] = {"textures": {"Array.frames": [f"Texture.{n}" for n in names]}}
    inner["textures"] = [f"Array.frames[math.mod(math.floor(query.life_time * 17), {frames})]"]
    rc["render_controllers"]["controller.render.kirbycope.tropical_slime_shell"].pop("uv_anim", None)
    json.dump(rc, open(rc_path, "w", encoding="utf8", newline="\n"), indent=2)


def dyed_cat():
    """Peanut Butter has no Earth model (the dyed cat was never in the game), so it keeps its skin on the vanilla cat,
    with the values Bedrock's engine fills in only for its own cats worked out here instead."""
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": f"{NS}:dyed_cat",
        "materials": {"default": "cat"},
        "textures": {"default": "textures/entity/dyed_cat"},
        "geometry": {"default": "geometry.cat"},
        "animations": {"sneak": "animation.cat.sneak", "walk": "animation.cat.walk", "sprint": "animation.cat.sprint", "sit": "animation.cat.sit",
                       "look_at_target": "animation.common.look_at_target", "lie_down": "animation.cat.lie_down",
                       "look_at_controller": "controller.animation.cat.look_at_target", "move_controller": "controller.animation.cat.move"},
        "scripts": {
            "animate": ["look_at_controller", "move_controller"],
            "pre_animation": [
                "variable.state = query.is_sitting ? 2 : (query.is_sneaking ? 0 : (query.modified_move_speed > 0.8 ? 1 : 3));",
                "variable.liedownamount = query.is_sleeping ? 1 : 0;",
                "variable.liedownamounttail = query.is_sleeping ? 1 : 0;",
                "variable.lieonplayer = 0;"],
            "scale": "1.25"},   # the behavior pack scales a cat to 0.8, a kitten to 0.4
        "render_controllers": ["controller.render.default"],
        "spawn_egg": {"base_color": "#7d5aa6", "overlay_color": "#3b2a52"}}}}


def items_and_blocks():
    item_atlas = {"resource_pack_name": "kirbycope", "texture_name": "atlas.items", "texture_data": {}}
    terrain_atlas = {"resource_pack_name": "kirbycope", "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4, "texture_data": {}}
    for name, src in ITEM_TEXTURES.items():
        ours = f"textures/items/{name}"
        shutil.copyfile(os.path.join(EARTH, src + ".png"), os.path.join(RP, ours + ".png"))
        item_atlas["texture_data"][f"{NS}_{name}"] = {"textures": ours}
    for name, src in BLOCK_TEXTURES.items():
        ours = f"textures/blocks/{name}"
        shutil.copyfile(os.path.join(EARTH, src + ".png"), os.path.join(RP, ours + ".png"))
        terrain_atlas["texture_data"][f"{NS}_{name}"] = {"textures": ours}
    json.dump(item_atlas, open(os.path.join(RP, "textures", "item_texture.json"), "w", encoding="utf8", newline="\n"), indent=2)
    json.dump(terrain_atlas, open(os.path.join(RP, "textures", "terrain_texture.json"), "w", encoding="utf8", newline="\n"), indent=2)
    lang_path = os.path.join(RP, "texts", "en_US.lang")
    lines = [l for l in open(lang_path, encoding="utf8").read().splitlines() if l.split("=", 1)[0] not in NAMES]
    lines += [f"{k}={v}" for k, v in NAMES.items()]
    open(lang_path, "w", encoding="utf8", newline="\n").write("\n".join(lines) + "\n")


def main():
    for folder in ("textures/items", "textures/blocks"): os.makedirs(os.path.join(RP, folder), exist_ok=True)
    port = Port()
    old = {}
    for path in glob.glob(os.path.join(RP, "entity", "*.entity.json")):
        try: old[os.path.basename(path)[:-len(".entity.json")]] = load(path)["minecraft:client_entity"]["description"]
        except Exception: pass
    shutil.rmtree(os.path.join(RP, OUT_TEX), ignore_errors=True)
    for folder in ("models/entity/earth", "animations/earth", "animation_controllers/earth", "render_controllers/earth", "particles/earth"):
        shutil.rmtree(os.path.join(RP, folder), ignore_errors=True)
    for mob, earth_file in PORT.items():
        desc = port.entity(mob, earth_file)
        if mob == "furnace_golem": furnace_golem(desc)
        egg = old.get(mob, {}).get("spawn_egg")
        if mob in EGGS: egg = {"base_color": EGGS[mob][0], "overlay_color": EGGS[mob][1]}
        if egg: desc["spawn_egg"] = egg
        data = {"format_version": "1.10.0", "minecraft:client_entity": {"description": desc}}
        with open(os.path.join(RP, "entity", f"{mob}.entity.json"), "w", encoding="utf8", newline="\n") as f:
            f.write(json.dumps(data, indent=2) + "\n")
    written = port.write()
    furnace_golem_files()
    tropical_slime()
    with open(os.path.join(RP, "entity", "dyed_cat.entity.json"), "w", encoding="utf8", newline="\n") as f:
        f.write(json.dumps(dyed_cat(), indent=2) + "\n")
    items_and_blocks()
    used = set()
    for path in glob.glob(os.path.join(RP, "entity", "*.entity.json")):
        used.update(load(path)["minecraft:client_entity"]["description"].get("textures", {}).values())
    for png in glob.glob(os.path.join(RP, "textures", "entity", "*.png")):
        if "textures/entity/" + os.path.basename(png)[:-4] not in used: os.remove(png)
    for rel in OLD_FILES:
        if os.path.exists(os.path.join(RP, rel)): os.remove(os.path.join(RP, rel))
    print(f"ported {len(PORT)} entities, {len(written)} definition files, {len(port.textures)} textures")


if __name__ == "__main__":
    main()
