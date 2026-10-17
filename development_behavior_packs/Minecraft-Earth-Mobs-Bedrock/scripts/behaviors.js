// What Earth's server did for its mobs that a behavior file cannot: telling the client which animation to play (the
// kirbycope:anim property each Earth model reads, see tools/port_earth.py), and the mobs' habits in the world: flower
// and mushroom trails, mud baths, a llama's fern hunt, a zombie climbing a wall.

import { BlockPermutation, system, world } from "@minecraft/server";

const DIMENSIONS = ["overworld", "nether", "the_end"];
const ANIM = "kirbycope:anim";

function each(type, fn) {
  for (const id of DIMENSIONS) {
    for (const entity of world.getDimension(id).getEntities({ type })) {
      if (entity.isValid) fn(entity);
    }
  }
}

function setAnim(entity, state, ticks) {
  if (!entity.isValid) return;
  try { entity.setProperty(ANIM, state); } catch { return; }
  if (ticks) system.runTimeout(() => { if (entity.isValid && entity.getProperty(ANIM) === state) entity.setProperty(ANIM, "none"); }, ticks);
}

function griefing() {
  return world.gameRules.mobGriefing;
}

function blockAt(dimension, location, dy = 0) {
  try { return dimension.getBlock({ x: Math.floor(location.x), y: Math.floor(location.y) + dy, z: Math.floor(location.z) }); } catch { return undefined; }
}

function pick(weights) {
  let roll = Math.random() * weights.reduce((sum, [, w]) => sum + w, 0);
  for (const [value, w] of weights) { if ((roll -= w) < 0) return value; }
  return weights[0][0];
}

// ---- attacks: every Earth ranged attacker played its throw or spit as the projectile left -------------------------

const SHOOTERS = {
  "kirbycope:melon_seed": "kirbycope:melon_golem",
  "kirbycope:bone_shard": "kirbycope:bone_spider",
  "kirbycope:rotten_flesh": "kirbycope:lobber_zombie",
  "minecraft:lingering_potion": "kirbycope:viler_witch",
};

world.afterEvents.entitySpawn.subscribe(({ entity }) => {
  if (!entity.isValid) return;
  const shooter = SHOOTERS[entity.typeId];
  if (shooter) {
    const owner = entity.getComponent("minecraft:projectile")?.owner;
    if (owner?.isValid && owner.typeId === shooter) setAnim(owner, "attack", 30);
  }
  if (entity.typeId === "kirbycope:muddy_pig") setAnim(entity, "celebrate", 30);   // fresh out of the mud
});

// ---- the bouldering zombie: crouches, climbs, swings over the top ----------------------------------------------------

system.runInterval(() => {
  each("kirbycope:bouldering_zombie", (zombie) => {
    const rising = !zombie.isOnGround && zombie.getVelocity().y > 0.08;
    const state = zombie.getProperty(ANIM);
    if (rising && state === "none") { setAnim(zombie, "climb_prep"); system.runTimeout(() => { if (zombie.isValid && zombie.getProperty(ANIM) === "climb_prep") setAnim(zombie, "climb"); }, 6); }
    else if (!rising && (state === "climb" || state === "climb_prep")) setAnim(zombie, "climb_exit", 12);
  });
}, 4);

// ---- mud pigs: a dried muddy pig smells mud, walks to it, hops in and rolls until it is muddy again -----------------

function findBlock(dimension, around, types, radius, height) {
  const cx = Math.floor(around.x), cy = Math.floor(around.y), cz = Math.floor(around.z);
  let best, bestDist = Infinity;
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dz = -radius; dz <= radius; dz++) {
      for (let dy = -height; dy <= height; dy++) {
        let block;
        try { block = dimension.getBlock({ x: cx + dx, y: cy + dy, z: cz + dz }); } catch { continue; }
        if (!block || !types.includes(block.typeId)) continue;
        const dist = dx * dx + dy * dy + dz * dz;
        if (dist < bestDist) { best = block; bestDist = dist; }
      }
    }
  }
  return best;
}

system.runInterval(() => {
  each("kirbycope:dried_muddy_pig", (pig) => {
    if (pig.getProperty(ANIM) !== "none" && pig.getProperty(ANIM) !== "seek") return;
    const mud = findBlock(pig.dimension, pig.location, ["minecraft:mud"], 8, 3);
    setAnim(pig, mud ? "seek" : "none");
  });
  // an ordinary pig that wanders into mud comes out a muddy pig
  each("minecraft:pig", (pig) => {
    const under = blockAt(pig.dimension, pig.location, -1), at = blockAt(pig.dimension, pig.location);
    if (under?.typeId !== "minecraft:mud" && at?.typeId !== "minecraft:mud") return;
    if (pig.getComponent("minecraft:is_saddled") || pig.getComponent("minecraft:leashable")?.isLeashed) return;
    const baby = !!pig.getComponent("minecraft:is_baby");
    const muddy = pig.dimension.spawnEntity(baby ? "kirbycope:muddy_pig<minecraft:entity_born>" : "kirbycope:muddy_pig<minecraft:spawn_adult>", pig.location);
    muddy.setRotation(pig.getRotation());
    if (pig.nameTag) muddy.nameTag = pig.nameTag;
    pig.remove();
  });
}, 60);

world.afterEvents.dataDrivenEntityTrigger.subscribe(({ entity, eventId }) => {
  if (!entity.isValid) return;
  if (eventId === "kirbycope:reached_mud" && entity.getProperty(ANIM) !== "hop" && entity.getProperty(ANIM) !== "roll") {
    setAnim(entity, "hop");
    entity.dimension.playSound("mob.pig.say", entity.location);
    system.runTimeout(() => {
      if (!entity.isValid) return;
      setAnim(entity, "roll");
      entity.dimension.playSound("bucket.fill_lava", entity.location, { pitch: 0.6, volume: 0.6 });
      system.runTimeout(() => { if (entity.isValid) entity.triggerEvent("kirbycope:found_mud"); }, 50);
    }, 20);
  }
  if (eventId === "kirbycope:ate_fern") eatFern(entity);
});

// ---- the jolly llama: spots a fern, eats it, then prances about jingling ---------------------------------------------

const FERNS = ["minecraft:fern", "minecraft:large_fern"];
const llamaFull = new Map();   // entity id -> tick it may hunt again

system.runInterval(() => {
  each("kirbycope:jolly_llama", (llama) => {
    const state = llama.getProperty(ANIM);
    if (state === "graze" || state === "prance") return;
    if ((llamaFull.get(llama.id) ?? 0) > system.currentTick) { if (state === "fern") setAnim(llama, "none"); return; }
    const fern = findBlock(llama.dimension, llama.location, FERNS, 6, 2);
    if (fern && state !== "fern") { setAnim(llama, "fern"); llama.dimension.playSound("mob.llama.idle", llama.location, { pitch: 1.4 }); }
    if (!fern && state === "fern") setAnim(llama, "none");
  });
}, 20);

function eatFern(llama) {
  const fern = findBlock(llama.dimension, llama.location, FERNS, 2, 2);
  if (fern && griefing()) {
    const above = fern.above();
    if (fern.typeId === "minecraft:large_fern" && above?.typeId === "minecraft:large_fern") above.setType("minecraft:air");
    const below = fern.below();
    if (fern.typeId === "minecraft:large_fern" && below?.typeId === "minecraft:large_fern") below.setType("minecraft:air");
    fern.setType("minecraft:air");
  }
  llamaFull.set(llama.id, system.currentTick + 20 * (60 + Math.floor(Math.random() * 120)));
  setAnim(llama, "graze");
  llama.dimension.playSound("mob.llama.eat", llama.location);
  system.runTimeout(() => {
    if (!llama.isValid) return;
    setAnim(llama, "prance", 120);
    for (let hop = 0; hop < 8; hop++) {
      system.runTimeout(() => {
        if (!llama.isValid || !llama.isOnGround) return;
        llama.applyImpulse({ x: (Math.random() - 0.5) * 0.3, y: 0.42, z: (Math.random() - 0.5) * 0.3 });
        llama.dimension.playSound("note.bell", llama.location, { pitch: 1.4 + Math.random() * 0.6, volume: 0.6 });
      }, 10 + hop * 14);
    }
  }, 40);
}

// ---- trails: mooblooms leave buttercup-yellow flowers, moolips pink ones, cluckshrooms mushrooms in the dark --------

const FLOWERS = {
  "kirbycope:moobloom": [["minecraft:dandelion", 80], ["minecraft:sunflower", 20]],
  "kirbycope:moolip": [["minecraft:allium", 40], ["minecraft:lilac", 40], ["minecraft:peony", 20]],
};
const TALL = new Set(["minecraft:sunflower", "minecraft:lilac", "minecraft:peony"]);
const SOIL = new Set(["minecraft:grass_block", "minecraft:dirt", "minecraft:podzol", "minecraft:coarse_dirt", "minecraft:moss_block"]);

function plant(dimension, location, type) {
  const at = blockAt(dimension, location), below = blockAt(dimension, location, -1);
  if (!at || !below || !at.isAir || !SOIL.has(below.typeId)) return false;
  if (TALL.has(type)) {
    const above = at.above();
    if (!above?.isAir) return false;
    at.setPermutation(BlockPermutation.resolve(type, { upper_block_bit: false }));
    above.setPermutation(BlockPermutation.resolve(type, { upper_block_bit: true }));
  } else {
    at.setType(type);
  }
  return true;
}

function dark(dimension, location) {
  try { return dimension.getLightLevel(location) < 8; } catch { /* older API: judge by the clock and the sky */ }
  const time = world.getTimeOfDay();
  const night = time > 13000 && time < 23000;
  const covered = !blockAt(dimension, location, 1)?.isAir;
  return night || covered;
}

system.runInterval(() => {
  if (!griefing()) return;
  for (const [type, flowers] of Object.entries(FLOWERS)) {
    each(type, (cow) => {
      if (cow.getComponent("minecraft:is_baby") || Math.random() > 0.05) return;
      plant(cow.dimension, cow.location, pick(flowers));
    });
  }
  each("kirbycope:cluckshroom", (chicken) => {
    if (Math.random() > 0.04 || !dark(chicken.dimension, chicken.location)) return;
    const at = blockAt(chicken.dimension, chicken.location), below = blockAt(chicken.dimension, chicken.location, -1);
    if (!at?.isAir || !below || below.isAir || below.isLiquid) return;
    at.setType(Math.random() < 0.7 ? "minecraft:red_mushroom" : "minecraft:brown_mushroom");
    chicken.dimension.playSound("random.pop", chicken.location, { pitch: 0.8 });
  });
}, 40);
