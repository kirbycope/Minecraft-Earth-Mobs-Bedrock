![Minecraft-Earth-Mobs-Bedrock](/Minecraft-Earth-Mobs-Bedrock.png)

# Minecraft-Earth-Mobs-Bedrock
All the mobs from Minecraft Earth in Minecraft Bedrock Edition.

## Installation
1. Download the [mcaddon](https://github.com/kirbycope/Minecraft-Earth-Mobs-Bedrock/releases/latest/download/Minecraft-Earth-Mobs-Bedrock.mcaddon)
1. Double-click the mcaddon file
1. Load the Resource and Behaviour packs for your world/save. No experiments are needed (Minecraft Bedrock 1.26.0 or newer).

### Mobs
Every mob from the [Minecraft Earth mob list](https://minecraft.wiki/w/Earth:Mob) that is not already in Minecraft, plus Peanut Butter, the
dyed cat. Each looks the way it did in Earth and lives the way the wiki says it did: its health, drops, biome, rarity and habits.

| Mob | Built on | Spawns in | Earth rarity | What it does |
| --- | --- | --- | --- | --- |
| Albino Cow | cow | Plains | Uncommon | as the cow it is built on |
| Ashen Cow | cow | Plains | Uncommon | as the cow it is built on |
| Cookie Cow | cow | Plains | Uncommon | as the cow it is built on |
| Cream Cow | cow | Plains | Uncommon | as the cow it is built on |
| Dairy Cow | cow | Plains | Uncommon | as the cow it is built on |
| Pinto Cow | cow | Plains | Uncommon | as the cow it is built on |
| Sunset Cow | cow | Plains | Uncommon | as the cow it is built on |
| Moobloom | cow | Plains | Rare | shear for a buttercup (grows back); leaves dandelions and sunflowers behind it |
| Moolip | cow | Flower Forest | Rare | shear for a pink daisy (grows back); leaves alliums, lilacs and peonies behind it |
| Wooly Cow | cow | Snowy Plains | Uncommon | shear for brown wool; it grows back and the cow shakes out its new coat |
| Umbra Cow | cow | Plains | Uncommon | shear for black wool; it grows back |
| Amber Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Bronzed Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Gold Crested Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Midnight Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Skewbald Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Stormy Chicken | chicken | Plains | Uncommon | as the chicken it is built on |
| Fancy Chicken | chicken | Plains | Rare | drops fancy feathers; runs from pigs |
| Cluckshroom | chicken | Forest | Rare | shear it for mushrooms and it turns into a chicken; keeps out of the sun, leaves mushrooms in the dark |
| Mottled Pig | pig | Forest | Uncommon | as the pig it is built on |
| Piebald Pig | pig | Forest | Uncommon | as the pig it is built on |
| Pink Footed Pig | pig | Forest | Uncommon | as the pig it is built on |
| Pale Pig | pig | Snowy Plains | Uncommon | as the pig it is built on |
| Sooty Pig | pig | Dark Forest | Uncommon | as the pig it is built on |
| Spotted Pig | pig | Swamp | Uncommon | as the pig it is built on |
| Muddy Pig | pig | Plains | Epic | dries out into a dried muddy pig after five to ten minutes; any pig that walks into mud becomes one |
| Dried Muddy Pig | pig | does not spawn | Epic | looks for mud, hops in and rolls until it is a muddy pig again |
| Flecked Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Fuzzy Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Long Nosed Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Inky Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Patched Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Rocky Sheep | sheep | Plains | Uncommon | as the sheep it is built on |
| Rainbow Sheep | sheep | Plains | Epic | sheared for 3 rainbow wool |
| Horned Sheep | sheep | Plains | Rare | neutral: paws the ground and rams whatever hurts it; drops a horn |
| Bold Striped Rabbit | rabbit | Plains | Uncommon | as the rabbit it is built on |
| Freckled Rabbit | rabbit | Plains | Uncommon | as the rabbit it is built on |
| Harelequin Rabbit | rabbit | Plains | Uncommon | as the rabbit it is built on |
| Muddy Foot Rabbit | rabbit | Plains | Uncommon | as the rabbit it is built on |
| Vested Rabbit | rabbit | Plains | Uncommon | as the rabbit it is built on |
| Desert Rabbit | rabbit | Desert | Common | as the rabbit it is built on |
| Jumbo Rabbit | rabbit | Desert | Uncommon | Earth's big rabbit; skeleton wolves hunt it |
| Jolly Llama | llama | Snowy Plains | Rare | finds ferns, eats them, then prances about jingling |
| Dyed Cat | cat | does not spawn | Rare | Peanut Butter; never spawned in Earth either |
| Furnace Golem | iron golem | Desert | Rare | a working furnace in its chest; sets what it hits on fire, hands out torches, hurt by water |
| Melon Golem | snow golem | Snowy Plains | Uncommon | fires bursts of four melon seeds; hops instead of walking; its melon head cannot be sheared |
| Tropical Slime | slime | Jungle | Rare | neutral until hit, never splits, drops a tropical fish; the fish inside swim |
| Bouldering Zombie | zombie | Plains | Rare | climbs walls |
| Lobber Zombie | zombie | Plains | Rare | throws rotten flesh from range |
| Skeleton Wolf | wolf | Desert | Rare | hostile, cannot be tamed; howls to make nearby skeletons stronger |
| Bone Spider | spider | Dark Forest | Rare | spits bone shards; 32 health |
| Viler Witch | witch | Dark Forest | Rare | lingering potions of harming and poison, drinks invisibility; immune to poison and harming |

Vanilla mobs Earth also had (pig, cow, chicken, white sheep, glow squid, squid, ocelot, parrot, salmon, tropical fish, polar bear, skeleton,
zombie, creeper, spider, slime, witch) are left to the game, as is Mob of Me, which was the player's own character.

#### Where they come from

* **Looks**: Minecraft Earth's own resource pack ([andiricum2/MC-Earth-Resourcepack](https://github.com/andiricum2/MC-Earth-Resourcepack)),
  ported by `tools/port_earth.py`: each mob's model, skin, animations (blinking, the witch's cast, the mud pig's roll, the llama's prance, the
  horned sheep's charge), render controllers and particles. That pack is cloned into `java/`, which git ignores; only what the port writes is
  committed. Earth's models are rewritten into the current geometry format, which is what makes them render, and Earth's animated textures are
  cut into frames.
* **Behavior**: today's vanilla mob from [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) v1.26.50.4, with the differences
  the wiki records layered on, written by `tools/generate_mobs.py` (also the spawn rules, loot tables, projectiles, the buttercup, pink daisy and
  rainbow wool blocks, and the fancy feather and horn items). It clones bedrock-samples into `vanilla/`, also git ignored.
* **Habits** a behavior file cannot express (trails, mud baths, fern hunting, wall climbing, the animation each Earth model expects at the right
  moment) live in `scripts/behaviors.js`; the Furnace Golem's in `scripts/furnace_golem.js`.

Spawn weights follow Earth's rarity: animals at 10 (common), 4 (uncommon), 2 (rare) and 1 (epic) beside vanilla's 8 to 12, monsters at 40, 20,
10 and 5 beside the zombie's 100. Monsters spawn in the dark on the surface, and the bone spider in caves too.

    python tools/generate_mobs.py     # behavior pack: entities, spawn rules, loot tables, items, blocks
    python tools/port_earth.py        # resource pack: models, skins, animations, render controllers, particles

The skins that came from Planet Minecraft (and one bug report there, from Asher_SweetDream: the skeleton wolf's missing texture, the viler
witch's hat and the desert rabbit's eyes) are replaced by Earth's own; all three render properly now.

### Furnace Golem
The Furnace Golem's chest is a working furnace.

- **Open it** by using the golem with an empty hand (holding an iron ingot still repairs it). It opens a furnace screen: what to smelt goes in the top cell, fuel in the bottom one, and the result comes out of the large cell on the right. Fuel dropped into the top cell, by a shift-click for example, is moved down to the fuel cell for you.
- **It smelts like a furnace**: 10 seconds an item, every vanilla furnace recipe, the same fuels burning for the same time (a lava bucket leaves its bucket behind), XP orbs as items finish, and fuel that keeps burning down once lit. It only smelts while the golem is in a loaded chunk, and what is inside stays with the golem; it drops if the golem dies.
- **The furnace on its chest burns while it works**: the flames across its chest light up, flame and smoke puff out of it and it crackles. When the fuel runs out they go out again. The same flames show, with its eyes, whenever it is fighting.

How it is built, since Bedrock has no furnace container for entities:

| Part | Where |
| --- | --- |
| A three-slot inventory (`container`, 0 smelt, 1 fuel, 2 result) and the client-synced `kirbycope:lit` property | `development_behavior_packs/.../entities/furnace_golem.json`, written by `tools/generate_mobs.py` |
| The smelting, run every half second for every loaded golem | `development_behavior_packs/.../scripts/furnace_golem.js` (Script API, `@minecraft/server` 2.6.0) |
| The vanilla furnace recipes, generated from [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) 1.26.50.4 | `development_behavior_packs/.../scripts/furnace_recipes.js` |
| The furnace screen: an override of the chest screen's top half that lays the slots out as a furnace's whenever the container is a single row, which no vanilla chest, barrel, chest minecart or chest boat is | `development_resource_packs/.../ui/chest_screen.json` |
| Earth's own model, with its chest flames lit while the furnace burns, and flame, smoke and a crackle from a `furnace_mouth` locator | `tools/port_earth.py`, `animations/furnace_golem.animation.json`, `animation_controllers/`, `particles/` |

The furnace screen is drawn for the desktop ("Classic") UI layout. With the Pocket UI layout the golem opens the plain chest grid instead; it still works, with its first three cells as the three slots. The arrow and the flame on the screen do not fill in as a furnace's do, because a custom container has no progress for them to show; the golem's chest shows whether it is burning.

## Releasing
Pushing a tag that starts with `v` (for example `git tag v1.0.0 && git push origin v1.0.0`) runs the Release workflow in `.github/workflows/release.yml`, which builds the add-on and attaches `Minecraft-Earth-Mobs-Bedrock.mcaddon` to a GitHub Release.

To build it locally, run `python tools/build_addon.py`. It writes `build/Minecraft-Earth-Mobs-Bedrock.mcaddon`, which git ignores, and leaves the committed `Minecraft-Earth-Mobs-Bedrock.mcaddon` as it is.
