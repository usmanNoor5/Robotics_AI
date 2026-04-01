import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";

const canvas = document.getElementById("game");
const playerHealthEl = document.getElementById("playerHealth");
const enemyHealthEl = document.getElementById("enemyHealth");
const messageEl = document.getElementById("message");
const restartBtn = document.getElementById("restartBtn");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b1020);

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  200
);

// -----------------------------
// Arena + collision setup
// -----------------------------
const arenaHalf = 10;
const wallThickness = 0.5;
const wallHeight = 3;
const arenaY = 0;

const obstacleMeshes = [];
const colliderRadius = 0.42;
const pillarRadius = 1.15;

function addWall(x, z, sx, sz) {
  const geo = new THREE.BoxGeometry(sx, wallHeight, sz);
  const mat = new THREE.MeshStandardMaterial({ color: 0x1f2a44, roughness: 0.9 });
  const wall = new THREE.Mesh(geo, mat);
  wall.position.set(x, wallHeight / 2 + arenaY, z);
  scene.add(wall);
  obstacleMeshes.push(wall);
}

function addPillar() {
  const geo = new THREE.CylinderGeometry(pillarRadius, pillarRadius, wallHeight, 24);
  const mat = new THREE.MeshStandardMaterial({ color: 0x24314f, roughness: 0.95 });
  const pillar = new THREE.Mesh(geo, mat);
  pillar.position.set(0, wallHeight / 2 + arenaY, 0);
  scene.add(pillar);
  obstacleMeshes.push(pillar);
}

function buildArena() {
  scene.clear();
  obstacleMeshes.length = 0;

  const hemi = new THREE.HemisphereLight(0x7dd3fc, 0x0b1020, 1.1);
  scene.add(hemi);
  const dir = new THREE.DirectionalLight(0xffffff, 0.7);
  dir.position.set(8, 12, 6);
  scene.add(dir);

  const floorGeo = new THREE.PlaneGeometry(arenaHalf * 2, arenaHalf * 2);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x0d1833,
    roughness: 1.0,
    metalness: 0.0
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, arenaY, 0);
  scene.add(floor);

  // Border walls (no interior walls besides pillar)
  addWall(0, -(arenaHalf - wallThickness / 2), arenaHalf * 2, wallThickness);
  addWall(0, arenaHalf - wallThickness / 2, arenaHalf * 2, wallThickness);
  addWall(-(arenaHalf - wallThickness / 2), 0, wallThickness, arenaHalf * 2);
  addWall(arenaHalf - wallThickness / 2, 0, wallThickness, arenaHalf * 2);

  // Central obstacle
  addPillar();
}

// -----------------------------
// Player + enemy
// -----------------------------
const player = {
  x: -6,
  z: 0,
  yaw: Math.PI / 2,
  pitch: 0,
  speed: 5.5,
  eyeHeight: 1.6,
  radius: colliderRadius,
  health: 100,
  alive: true,
  nextShotMs: 0,
  shootCooldownMs: 250,
  mesh: null
};

const enemy = {
  x: 6,
  z: 0,
  yaw: -Math.PI / 2,
  speed: 4.7,
  eyeHeight: 1.45,
  radius: 0.45,
  health: 100,
  alive: true,
  nextShotMs: 0,
  shootCooldownMs: 450,
  mesh: null
};

function makeAvatar(color) {
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.6, 1.6, 0.6),
    new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.05 })
  );
  body.position.y = 0.8 + arenaY;
  return body;
}

function rebuildCharacters() {
  const toRemove = [];
  for (const child of scene.children) {
    if (child.userData && child.userData.kind === "actor") toRemove.push(child);
  }
  for (const m of toRemove) scene.remove(m);

  player.health = 100;
  enemy.health = 100;
  player.alive = true;
  enemy.alive = true;

  player.mesh = makeAvatar(0x38bdf8);
  player.mesh.userData.kind = "actor";
  player.mesh.position.set(player.x, 0.8 + arenaY, player.z);
  scene.add(player.mesh);

  enemy.mesh = makeAvatar(0xfb7185);
  enemy.mesh.userData.kind = "actor";
  enemy.mesh.position.set(enemy.x, 0.8 + arenaY, enemy.z);
  scene.add(enemy.mesh);
}

// -----------------------------
// Visual FX
// -----------------------------
const tracers = [];
function addTracer(from, to, color) {
  const points = [from.clone(), to.clone()];
  const geo = new THREE.BufferGeometry().setFromPoints(points);
  const mat = new THREE.LineBasicMaterial({ color });
  const line = new THREE.Line(geo, mat);
  scene.add(line);
  tracers.push({ line, life: 0.12 });
}

// -----------------------------
// Controls
// -----------------------------
const keys = new Set();
let pointerLocked = false;

function setMessage(text) {
  messageEl.textContent = text;
}

function lockHint() {
  // Only show the "click to start" hint while the game is still running.
  if (!pointerLocked && player.alive && enemy.alive) {
    setMessage("Click to start (pointer lock)");
  }
}

window.addEventListener("keydown", (e) => {
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(e.code)) {
    e.preventDefault();
  }

  keys.add(e.code);
  if (e.code === "Space") attemptPlayerShoot();
});

window.addEventListener("keyup", (e) => {
  keys.delete(e.code);
});

canvas.addEventListener("click", () => {
  if (!pointerLocked) canvas.requestPointerLock?.();
});

document.addEventListener("pointerlockchange", () => {
  pointerLocked = document.pointerLockElement === canvas;
  if (pointerLocked) setMessage("");
  else lockHint();
});

window.addEventListener("mousemove", (e) => {
  if (!pointerLocked) return;

  const sensitivity = 0.0022;
  player.yaw -= e.movementX * sensitivity;
  player.pitch -= e.movementY * sensitivity;
  player.pitch = Math.max(-1.25, Math.min(1.25, player.pitch));
});

// -----------------------------
// Shooting + ray tests
// -----------------------------
const raycaster = new THREE.Raycaster();
const clock = new THREE.Clock();
const maxShootRange = 22;
const playerHitRadius = 0.55;

function getPlayerEye() {
  return new THREE.Vector3(player.x, player.eyeHeight, player.z);
}

function getEnemyEye() {
  return new THREE.Vector3(enemy.x, enemy.eyeHeight, enemy.z);
}

function shoot(rayOrigin, rayDir, targets, obstacleOnly) {
  raycaster.set(rayOrigin, rayDir.normalize());
  raycaster.far = maxShootRange;

  const shootables = [];
  if (targets?.length) shootables.push(...targets);
  if (!obstacleOnly && obstacleMeshes.length) shootables.push(...obstacleMeshes);

  // Intersect sorted by distance; first hit wins.
  const hits = raycaster.intersectObjects(shootables, false);
  if (!hits.length) return null;
  return hits[0];
}

function attemptPlayerShoot() {
  if (!player.alive) return;
  if (!pointerLocked) return;
  const now = performance.now();
  if (now < player.nextShotMs) return;
  player.nextShotMs = now + player.shootCooldownMs;

  const origin = getPlayerEye();
  const dir = new THREE.Vector3();
  camera.getWorldDirection(dir);

  raycaster.set(origin, dir.normalize());
  raycaster.far = maxShootRange;

  // First intersect among enemy + obstacles.
  const shootables = [enemy.mesh, ...obstacleMeshes];
  const hits = raycaster.intersectObjects(shootables, false);

  let endPoint = origin.clone().add(dir.clone().multiplyScalar(maxShootRange));
  if (hits.length) endPoint = hits[0].point.clone();
  addTracer(origin, endPoint, 0x60a5fa);

  if (!hits.length) return;
  if (hits[0].object === enemy.mesh) {
    applyPlayerDamage(18);
  }
}

function applyPlayerDamage(amount) {
  if (!enemy.alive) return;
  enemy.health = Math.max(0, enemy.health - amount);
  updateHUD();
  if (enemy.health <= 0) {
    enemy.alive = false;
    setMessage("You win! Enemy eliminated.");
    pointerLocked = false;
    restartBtn.style.display = "inline-block";
    document.exitPointerLock?.();
  }
}

function applyEnemyDamage(amount) {
  if (!player.alive) return;
  player.health = Math.max(0, player.health - amount);
  updateHUD();
  if (player.health <= 0) {
    player.alive = false;
    setMessage("Game over! You were eliminated.");
    pointerLocked = false;
    restartBtn.style.display = "inline-block";
    document.exitPointerLock?.();
  }
}

function enemyShouldShoot() {
  if (!enemy.alive || !player.alive) return false;
  const dx = player.x - enemy.x;
  const dz = player.z - enemy.z;
  const dist = Math.hypot(dx, dz);
  if (dist > 18) return false;

  // Aim cone check.
  const aimYaw = Math.atan2(dx, dz);
  const yawDiff = Math.atan2(Math.sin(aimYaw - enemy.yaw), Math.cos(aimYaw - enemy.yaw));
  if (Math.abs(yawDiff) > 0.55) return false;

  // Line of sight check: if obstacle is hit before player, no shot.
  const origin = getEnemyEye();
  const targetPoint = getPlayerEye();
  const dir = targetPoint.clone().sub(origin).normalize();
  raycaster.set(origin, dir);
  raycaster.far = maxShootRange;

  const shootables = [player.mesh, ...obstacleMeshes];
  const hits = raycaster.intersectObjects(shootables, false);
  if (!hits.length) return false;
  if (hits[0].object !== player.mesh) return false;

  const now = performance.now();
  return now >= enemy.nextShotMs;
}

function enemyShoot() {
  enemy.nextShotMs = performance.now() + enemy.shootCooldownMs;

  const origin = getEnemyEye();
  const dir = getPlayerEye().sub(origin).normalize();

  raycaster.set(origin, dir);
  raycaster.far = maxShootRange;

  const shootables = [player.mesh, ...obstacleMeshes];
  const hits = raycaster.intersectObjects(shootables, false);

  let endPoint = origin.clone().add(dir.clone().multiplyScalar(maxShootRange));
  if (hits.length) endPoint = hits[0].point.clone();

  addTracer(origin, endPoint, 0xfb7185);

  if (hits.length && hits[0].object === player.mesh) {
    applyEnemyDamage(15);
  }
}

// -----------------------------
// Movement + collision
// -----------------------------
const safeHalf = arenaHalf - wallThickness - player.radius;

function clampToArena(entity, radius) {
  entity.x = Math.max(-safeHalf, Math.min(safeHalf, entity.x));
  entity.z = Math.max(-safeHalf, Math.min(safeHalf, entity.z));

  // Pillar collision push-out in XZ plane.
  const px = entity.x;
  const pz = entity.z;
  const dist = Math.hypot(px, pz);
  const minDist = pillarRadius + radius;
  if (dist < minDist) {
    const pushDir = new THREE.Vector2(px, pz);
    if (pushDir.lengthSq() < 1e-8) pushDir.set(1, 0);
    pushDir.normalize();
    entity.x = pushDir.x * minDist;
    entity.z = pushDir.y * minDist;
  }
}

function updatePlayer(dt) {
  if (!player.alive) return;
  // If pointer not locked, don't move.
  if (!pointerLocked) return;

  let forward = 0;
  let strafe = 0;
  if (keys.has("ArrowUp")) forward += 1;
  if (keys.has("ArrowDown")) forward -= 1;
  if (keys.has("ArrowRight")) strafe += 1;
  if (keys.has("ArrowLeft")) strafe -= 1;

  const len = Math.hypot(forward, strafe);
  if (len > 0) {
    forward /= len;
    strafe /= len;
  }

  const sin = Math.sin(player.yaw);
  const cos = Math.cos(player.yaw);
  const forwardVec = new THREE.Vector3(-sin, 0, -cos);
  const rightVec = new THREE.Vector3(cos, 0, -sin);

  const move = forwardVec.multiplyScalar(forward).add(rightVec.multiplyScalar(strafe));
  player.x += move.x * player.speed * dt;
  player.z += move.z * player.speed * dt;
  clampToArena(player, player.radius);

  player.mesh.position.set(player.x, 0.8 + arenaY, player.z);
  player.mesh.rotation.y = player.yaw;
}

function updateEnemy(dt) {
  if (!enemy.alive || !player.alive) return;

  const dx = player.x - enemy.x;
  const dz = player.z - enemy.z;
  const dist = Math.hypot(dx, dz);

  // Face the player.
  enemy.yaw = Math.atan2(dx, dz);
  enemy.mesh.rotation.y = enemy.yaw;

  // Move toward player, keep a bit of distance.
  const wantDist = 3.2;
  let moveMag = 1;
  if (dist < wantDist) moveMag = (dist / wantDist) * 0.45;

  const sin = Math.sin(enemy.yaw);
  const cos = Math.cos(enemy.yaw);
  const forwardVec = new THREE.Vector3(-sin, 0, -cos);
  enemy.x += forwardVec.x * enemy.speed * moveMag * dt;
  enemy.z += forwardVec.z * enemy.speed * moveMag * dt;

  // Add small perpendicular strafe to reduce wall hugging.
  const perp = new THREE.Vector3(cos, 0, -sin);
  enemy.x += perp.x * enemy.speed * 0.25 * dt * Math.sign(Math.sin(performance.now() / 600));
  enemy.z += perp.z * enemy.speed * 0.25 * dt * Math.sign(Math.sin(performance.now() / 600));

  clampToArena(enemy, enemy.radius);
  enemy.mesh.position.set(enemy.x, 0.8 + arenaY, enemy.z);

  // Shoot decision.
  if (enemyShouldShoot()) enemyShoot();
}

// -----------------------------
// HUD
// -----------------------------
function updateHUD() {
  const pPct = (player.health / 100) * 100;
  const ePct = (enemy.health / 100) * 100;
  playerHealthEl.style.width = `${Math.max(0, pPct)}%`;
  enemyHealthEl.style.width = `${Math.max(0, ePct)}%`;
}

// -----------------------------
// Game init / loop
// -----------------------------
function resetGame() {
  buildArena();
  rebuildCharacters();
  for (const t of tracers) scene.remove(t.line);
  tracers.length = 0;

  player.x = -6;
  player.z = 0;
  player.yaw = Math.PI / 2;
  player.pitch = 0;

  enemy.x = 6;
  enemy.z = 0;
  enemy.yaw = -Math.PI / 2;

  player.mesh.position.set(player.x, 0.8 + arenaY, player.z);
  enemy.mesh.position.set(enemy.x, 0.8 + arenaY, enemy.z);

  updateHUD();
  restartBtn.style.display = "none";
  setMessage("Click to start (pointer lock)");
  document.exitPointerLock?.();
  pointerLocked = false;
}

restartBtn.addEventListener("click", () => resetGame());

buildArena();
rebuildCharacters();
updateHUD();
restartBtn.style.display = "none";
setMessage("Click to start (pointer lock)");

function updateCameraTransform() {
  // Camera is positioned from the player's eye and rotated by yaw/pitch.
  camera.position.set(player.x, player.eyeHeight, player.z);
  camera.rotation.order = "YXZ";
  camera.rotation.y = player.yaw;
  camera.rotation.x = player.pitch;
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.033); // avoid huge jumps when tab resumes

  // Update camera always; game freeze handled by alive checks.
  updateCameraTransform();

  updatePlayer(dt);
  updateEnemy(dt);

  // Update tracer life.
  for (let i = tracers.length - 1; i >= 0; i--) {
    const t = tracers[i];
    t.life -= dt;
    if (t.life <= 0) {
      scene.remove(t.line);
      tracers.splice(i, 1);
    }
  }

  renderer.render(scene, camera);
}

animate();

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

