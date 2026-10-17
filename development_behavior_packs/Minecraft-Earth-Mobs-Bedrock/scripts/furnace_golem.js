// The Furnace Golem. Its chest is a working furnace (an addition of this add-on; Earth's golem only looked like one),
// and as in Earth it sets what it fights on fire and now and then hands a player a torch.
//
// The furnace: its inventory is three slots, laid out like a furnace's by the
// resource pack's chest_screen.json: 0 is what to smelt, 1 the fuel and 2 the result. Bedrock has no furnace
// container for entities, so the smelting itself happens here, at a furnace's own pace: 200 ticks an item, fuel
// burning for the same number of ticks it lasts in a furnace block. While fuel burns the golem's kirbycope:lit
// property is true, which lights the flames on its chest and puffs flame and smoke from it.

import { ItemStack, system, world } from "@minecraft/server";
import { FURNACE_RECIPES, FURNACE_TAG_RECIPES } from "./furnace_recipes.js";

const GOLEM = "kirbycope:furnace_golem";
const LIT = "kirbycope:lit";
const INPUT = 0;
const FUEL = 1;
const OUTPUT = 2;
const INTERVAL = 10;      // ticks between updates; every timer below counts in ticks too
const COOK_TICKS = 200;   // one item, as in a furnace block
const DIMENSIONS = ["overworld", "nether", "the_end"];

// Burn time in ticks, as a furnace block gives it.
const FUEL_TICKS = {
  "minecraft:lava_bucket": 20000,
  "minecraft:coal_block": 16000,
  "minecraft:dried_kelp_block": 4000,
  "minecraft:blaze_rod": 2400,
  "minecraft:coal": 1600,
  "minecraft:charcoal": 1600,
  "minecraft:bow": 300,
  "minecraft:crossbow": 300,
  "minecraft:fishing_rod": 300,
  "minecraft:crafting_table": 300,
  "minecraft:chest": 300,
  "minecraft:trapped_chest": 300,
  "minecraft:barrel": 300,
  "minecraft:bookshelf": 300,
  "minecraft:chiseled_bookshelf": 300,
  "minecraft:lectern": 300,
  "minecraft:jukebox": 300,
  "minecraft:noteblock": 300,
  "minecraft:loom": 300,
  "minecraft:cartography_table": 300,
  "minecraft:fletching_table": 300,
  "minecraft:smithing_table": 300,
  "minecraft:composter": 300,
  "minecraft:daylight_detector": 300,
  "minecraft:ladder": 300,
  "minecraft:wooden_door": 200,
  "minecraft:trapdoor": 300,
  "minecraft:fence_gate": 300,
  "minecraft:wooden_button": 100,
  "minecraft:wooden_pressure_plate": 300,
  "minecraft:wooden_sword": 200,
  "minecraft:wooden_pickaxe": 200,
  "minecraft:wooden_axe": 200,
  "minecraft:wooden_shovel": 200,
  "minecraft:wooden_hoe": 200,
  "minecraft:stick": 100,
  "minecraft:bowl": 100,
  "minecraft:dead_bush": 100,
  "minecraft:mangrove_propagule": 100,
  "minecraft:bamboo": 50,
  "minecraft:scaffolding": 50,
};

// The wooden pieces whose ids follow <wood>_<piece>, and how long each burns.
const WOODS = /^minecraft:(oak|spruce|birch|jungle|acacia|dark_oak|mangrove|cherry|bamboo|pale_oak)_/;
const WOOD_PIECES = { _planks: 300, _stairs: 300, _fence: 300, _fence_gate: 300, _trapdoor: 300, _pressure_plate: 300,
  _door: 200, _sign: 200, _hanging_sign: 200, _slab: 150, _button: 100 };

// Experience a smelt gives, by result; anything not listed gives 0.1, as most furnace recipes do.
const XP = {
  "minecraft:iron_ingot": 0.7, "minecraft:copper_ingot": 0.7, "minecraft:gold_ingot": 1, "minecraft:diamond": 1,
  "minecraft:emerald": 1, "minecraft:netherite_scrap": 2, "minecraft:redstone": 0.7, "minecraft:lapis_lazuli": 0.2,
  "minecraft:quartz": 0.2, "minecraft:coal": 0.1,
};
const COOKED_XP = 0.35;

function smeltResult(item) {
  const result = FURNACE_RECIPES[item.typeId];
  if (result) return result;
  for (const [tag, tagResult] of Object.entries(FURNACE_TAG_RECIPES)) if (item.hasTag(tag)) return tagResult;
  return undefined;
}

function fuelTicks(item) {
  const id = item.typeId;
  if (FUEL_TICKS[id]) return FUEL_TICKS[id];
  if (id.includes("crimson") || id.includes("warped")) return 0;   // nether wood does not burn
  if (item.hasTag("minecraft:logs_that_burn")) return 300;
  if (id.endsWith("_boat") || id.endsWith("_raft")) return 1200;
  if (id.endsWith("_sapling")) return 100;
  if (id.endsWith("_wool")) return 100;
  if (id.endsWith("_carpet") && id !== "minecraft:moss_carpet") return 67;
  if (id.endsWith("_banner") || id === "minecraft:banner") return 300;
  if (WOODS.test(id)) for (const [piece, ticks] of Object.entries(WOOD_PIECES)) if (id.endsWith(piece)) return ticks;
  return 0;
}

function xpFor(result) {
  if (XP[result] !== undefined) return XP[result];
  return result.includes("cooked_") || result === "minecraft:baked_potato" || result === "minecraft:dried_kelp" ? COOKED_XP : 0.1;
}

function fits(output, result) {
  return !output || (output.typeId === result && output.amount < output.maxAmount);
}

function take(container, slot, item) {
  if (item.amount > 1) {
    item.amount -= 1;
    container.setItem(slot, item);
  } else {
    container.setItem(slot, undefined);
  }
}

// A plain container sends a shift-clicked stack to its first free slot, so coal lands where the ore goes.
// Move fuel that cannot be smelted down to the fuel slot, as a furnace would have sorted it.
function sortFuel(container) {
  const input = container.getItem(INPUT);
  if (!input || smeltResult(input) || !fuelTicks(input)) return;
  const fuel = container.getItem(FUEL);
  if (!fuel) {
    container.setItem(FUEL, input);
    container.setItem(INPUT, undefined);
  } else if (fuel.isStackableWith(input)) {
    const moved = Math.min(input.amount, fuel.maxAmount - fuel.amount);
    if (moved <= 0) return;
    fuel.amount += moved;
    container.setItem(FUEL, fuel);
    if (moved === input.amount) {
      container.setItem(INPUT, undefined);
    } else {
      input.amount -= moved;
      container.setItem(INPUT, input);
    }
  }
}

function update(golem) {
  const container = golem.getComponent("minecraft:inventory")?.container;
  if (!container) return;
  sortFuel(container);

  let burn = golem.getDynamicProperty("kirbycope:burn") ?? 0;
  let cook = golem.getDynamicProperty("kirbycope:cook") ?? 0;
  const input = container.getItem(INPUT);
  const result = input ? smeltResult(input) : undefined;
  const canSmelt = result !== undefined && fits(container.getItem(OUTPUT), result);

  if (burn <= 0 && canSmelt) {
    const fuel = container.getItem(FUEL);
    const ticks = fuel ? fuelTicks(fuel) : 0;
    if (ticks > 0) {
      burn = ticks;
      if (fuel.typeId === "minecraft:lava_bucket") container.setItem(FUEL, new ItemStack("minecraft:bucket"));
      else take(container, FUEL, fuel);
    }
  }

  if (burn > 0) {
    burn = Math.max(0, burn - INTERVAL);
    if (canSmelt) {
      cook += INTERVAL;
      if (cook >= COOK_TICKS) {
        cook = 0;
        take(container, INPUT, input);
        const output = container.getItem(OUTPUT);
        if (output) {
          output.amount += 1;
          container.setItem(OUTPUT, output);
        } else {
          container.setItem(OUTPUT, new ItemStack(result));
        }
        dropXp(golem, xpFor(result));
      }
    } else {
      cook = 0;
    }
  } else {
    cook = Math.max(0, cook - 2 * INTERVAL);   // a furnace that goes out loses its progress twice as fast
  }

  golem.setDynamicProperty("kirbycope:burn", burn);
  golem.setDynamicProperty("kirbycope:cook", cook);
  const lit = burn > 0;
  if (golem.getProperty(LIT) !== lit) golem.setProperty(LIT, lit);
}

// Smelting XP is fractional, so it is banked on the golem and paid out an orb at a time.
function dropXp(golem, amount) {
  let xp = (golem.getDynamicProperty("kirbycope:xp") ?? 0) + amount;
  for (; xp >= 1; xp -= 1) golem.dimension.spawnEntity("minecraft:xp_orb", golem.location);
  golem.setDynamicProperty("kirbycope:xp", xp);
}

system.runInterval(() => {
  for (const id of DIMENSIONS) {
    for (const golem of world.getDimension(id).getEntities({ type: GOLEM })) {
      if (golem.isValid) update(golem);
    }
  }
}, INTERVAL);

// ---- in a fight: whatever it hits catches fire, and now and then it calls up flames around its target -------------

world.afterEvents.entityHurt.subscribe(({ hurtEntity, damageSource }) => {
  const golem = damageSource.damagingEntity;
  if (!golem?.isValid || golem.typeId !== GOLEM || !hurtEntity.isValid) return;
  hurtEntity.setOnFire(4, true);
  if (Math.random() < 0.2 && world.gameRules.mobGriefing) {
    golem.setProperty("kirbycope:anim", "summon");
    golem.dimension.playSound("mob.blaze.shoot", golem.location, { pitch: 0.7 });
    system.runTimeout(() => {
      if (!hurtEntity.isValid) return;
      const at = hurtEntity.dimension.getBlock({ x: Math.floor(hurtEntity.location.x), y: Math.floor(hurtEntity.location.y), z: Math.floor(hurtEntity.location.z) });
      if (at?.isAir && at.below() && !at.below().isAir) at.setType("minecraft:fire");
    }, 10);
    system.runTimeout(() => { if (golem.isValid) golem.setProperty("kirbycope:anim", "none"); }, 30);
  }
});

// ---- gifts: like an iron golem's poppy, a torch for a player who catches its eye ----------------------------------

const lastGift = new Map();   // golem id -> tick of its last gift

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const seen = player.getEntitiesFromViewDirection({ maxDistance: 8 })[0]?.entity;
    if (!seen?.isValid || seen.typeId !== GOLEM || seen.target) continue;
    if (system.currentTick - (lastGift.get(seen.id) ?? -1e9) < 20 * 60 || Math.random() > 0.15) continue;
    lastGift.set(seen.id, system.currentTick);
    seen.setProperty("kirbycope:anim", "gift");
    system.runTimeout(() => {
      if (!seen.isValid) return;
      const from = seen.location, to = player.location;
      const len = Math.hypot(to.x - from.x, to.z - from.z) || 1;
      seen.dimension.spawnItem(new ItemStack("minecraft:torch"), { x: from.x + (to.x - from.x) / len, y: from.y + 1.2, z: from.z + (to.z - from.z) / len });
      seen.dimension.playSound("random.pop", from);
    }, 20);
    system.runTimeout(() => { if (seen.isValid) seen.setProperty("kirbycope:anim", "none"); }, 45);
  }
}, 40);
