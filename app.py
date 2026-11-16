
import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="RETRO STRIKE",
    page_icon="🎮",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #101018;
    color: white;
}
h1 {
    color: #00e5ff;
}
</style>
""", unsafe_allow_html=True)

st.title("🎮 RETRO STRIKE: LAST MISSION")
st.write("모든 미션을 클리어하고 최종 임무를 완수하세요!")

# 미션 데이터
def build_missions():
    return [
        {
            "name": "MISSION 01 - TRAINING BASE",
            "map": [
                "1111111111",
                "1000000001",
                "1020000001",
                "1000100001",
                "1000102001",
                "1000000001",
                "1000010001",
                "1000000001",
                "1000000001",
                "1111111111"
            ],
            "enemies": [[5.5, 2.5], [7.5, 5.5]],
            "ammo": [[3.5, 2.5], [6.5, 7.5]]
        },
        {
            "name": "MISSION 02 - DARK FACTORY",
            "map": [
                "1111111111",
                "1000000001",
                "1020102001",
                "1000100001",
                "1000000001",
                "1000200001",
                "1000100001",
                "1000000001",
                "1000000001",
                "1111111111"
            ],
            "enemies": [[5.5, 1.5], [7.5, 3.5], [2.5, 6.5]],
            "ammo": [[2.5, 2.5], [7.5, 7.5]]
        },
        {
            "name": "MISSION 03 - FINAL BATTLE",
            "map": [
                "1111111111",
                "1000000001",
                "1020102001",
                "1000000001",
                "1000100001",
                "1000000001",
                "1020102001",
                "1000000001",
                "1000000001",
                "1111111111"
            ],
            "enemies": [
                [5.5, 1.5],
                [7.5, 3.5],
                [2.5, 5.5],
                [5.5, 7.5]
            ],
            "ammo": [[2.5, 2.5], [7.5, 7.5]]
        }
    ]


missions = json.dumps(build_missions())

# 게임 화면
html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: #080810;
    color: white;
    font-family: monospace;
    overflow: hidden;
}

#info {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px;
    color: #00e5ff;
    font-size: 16px;
}

canvas {
    display: block;
    width: 100%;
    height: auto;
    border: 3px solid #00e5ff;
    outline: none;
    background: black;
}

#message {
    color: #ffdf5d;
    text-align: center;
    font-size: 18px;
    min-height: 28px;
    padding: 8px;
}

button {
    background: #00bcd4;
    color: black;
    border: none;
    padding: 10px 18px;
    margin: 5px;
    font-weight: bold;
    cursor: pointer;
}

#help {
    color: #aaa;
    text-align: center;
    font-size: 13px;
    padding: 8px;
}
</style>
</head>

<body>
<div id="info">
    <span id="mission"></span>
    <span id="health"></span>
    <span id="ammo"></span>
    <span id="score"></span>
    <span id="enemy-count"></span>
</div>

<canvas id="game" width="900" height="520" tabindex="0"></canvas>

<div id="message">게임 화면을 클릭하고 시작하세요!</div>

<div style="text-align:center">
    <button onclick="togglePause()">PAUSE / RESUME</button>
    <button onclick="restartGame()">RESTART</button>
</div>

<div id="help">
WASD: 이동 | ← →: 시야 회전 | SPACE: 사격 | R: 재장전 | P: 일시정지
</div>

<script>
const missions = __MISSIONS__;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const W = canvas.width;
const H = canvas.height;

let missionIndex = 0;
let player;
let enemies = [];
let ammoItems = [];
let score = 0;
let paused = false;
let gameOver = false;
let missionClear = false;
let keys = {};
let lastTime = 0;
let attackFlash = 0;
let message = "";

const FOV = Math.PI / 2.8;
const MAX_DISTANCE = 12;

function startMission(index) {
    missionIndex = index;
    const data = missions[index];

    player = {
        x: 1.5,
        y: 1.5,
        angle: 0,
        hp: 100,
        ammo: 20,
        maxAmmo: 20,
        lastHit: 0
    };

    enemies = data.enemies.map((p, i) => ({
        x: p[0],
        y: p[1],
        hp: 2,
        alive: true,
        id: i,
        attackTimer: 0
    }));

    ammoItems = data.ammo.map(p => ({
        x: p[0],
        y: p[1],
        collected: false
    }));

    paused = false;
    gameOver = false;
    missionClear = false;
    keys = {};

    message = data.name + " - MISSION START!";
    updateHUD();
}

function currentMap() {
    return missions[missionIndex].map;
}

function isWall(x, y) {
    const map = currentMap();
    const mx = Math.floor(x);
    const my = Math.floor(y);

    if (
        my < 0 || my >= map.length ||
        mx < 0 || mx >= map[0].length
    ) return true;

    return map[my][mx] === "1" ||
           map[my][mx] === "2";
}

function movePlayer(dt) {
    if (keys["arrowleft"]) player.angle -= 2.2 * dt;
    if (keys["arrowright"]) player.angle += 2.2 * dt;

    const speed = 2.5 * dt;
    let forward = 0;
    let side = 0;

    if (keys["w"]) forward += speed;
    if (keys["s"]) forward -= speed;
    if (keys["a"]) side -= speed;
    if (keys["d"]) side += speed;

    const dx = Math.cos(player.angle) * forward
             - Math.sin(player.angle) * side;
    const dy = Math.sin(player.angle) * forward
             + Math.cos(player.angle) * side;

    if (!isWall(player.x + dx, player.y)) player.x += dx;
    if (!isWall(player.x, player.y + dy)) player.y += dy;

    enemies.forEach(enemy => {
        if (!enemy.alive) return;

        const distance = Math.hypot(
            player.x - enemy.x,
            player.y - enemy.y
        );

        if (distance < 0.55) {
            player.x -= dx * 1.5;
            player.y -= dy * 1.5;
        }
    });

    ammoItems.forEach(item => {
        if (item.collected) return;

        if (Math.hypot(
            player.x - item.x,
            player.y - item.y
        ) < 0.5) {
            item.collected = true;
            player.ammo = Math.min(40, player.ammo + 10);
            message = "AMMO +10";
        }
    });
}

function shoot() {
    if (paused || gameOver || missionClear) return;

    if (player.ammo <= 0) {
        message = "NO AMMO! PRESS R TO RELOAD";
        return;
    }

    player.ammo--;
    attackFlash = 0.12;

    let target = null;
    let closest = Infinity;

    enemies.forEach(enemy => {
        if (!enemy.alive) return;

        const dx = enemy.x - player.x;
        const dy = enemy.y - player.y;
        const distance = Math.hypot(dx, dy);

        let angle = Math.atan2(dy, dx) - player.angle;
        angle = Math.atan2(Math.sin(angle), Math.cos(angle));

        if (Math.abs(angle) < 0.16 &&
            distance < closest &&
            !rayBlocked(player.x, player.y, enemy.x, enemy.y)) {
            target = enemy;
            closest = distance;
        }
    });

    if (target) {
        target.hp--;

        if (target.hp <= 0) {
            target.alive = false;
            score += 100;
            message = "ENEMY DEFEATED! +100";
        } else {
            message = "HIT!";
        }
    } else {
        message = "MISS!";
    }

    checkGame();
    updateHUD();
}

function reload() {
    if (paused || gameOver || missionClear) return;

    if (player.ammo < player.maxAmmo) {
        player.ammo = player.maxAmmo;
        message = "RELOADED!";
        updateHUD();
    }
}

function rayBlocked(x1, y1, x2, y2) {
    const distance = Math.hypot(x2 - x1, y2 - y1);
    const steps = Math.ceil(distance * 15);

    for (let i = 1; i < steps; i++) {
        const t = i / steps;

        if (isWall(
            x1 + (x2 - x1) * t,
            y1 + (y2 - y1) * t
        )) return true;
    }

    return false;
}

function drawWalls() {
    const columns = 180;
    const columnWidth = W / columns;

    for (let i = 0; i < columns; i++) {
        const cameraAngle =
            player.angle - FOV / 2 + FOV * (i / columns);

        let distance = 0;
        let hit = false;

        while (distance < MAX_DISTANCE && !hit) {
            distance += 0.025;

            const x = player.x + Math.cos(cameraAngle) * distance;
            const y = player.y + Math.sin(cameraAngle) * distance;

            if (isWall(x, y)) hit = true;
        }

        const corrected = distance *
            Math.cos(cameraAngle - player.angle);

        const wallHeight = Math.min(
            H,
            H / Math.max(corrected, 0.1)
        );

        const shade = Math.max(
            25,
            190 - corrected * 18
        );

        const map = currentMap();
        const mx = Math.floor(
            player.x + Math.cos(cameraAngle) * distance
        );
        const my = Math.floor(
            player.y + Math.sin(cameraAngle) * distance
        );

        const wallType = map[my]?.[mx] || "1";

        if (wallType === "2") {
            ctx.fillStyle = `rgb(${shade},${shade * 0.35},30)`;
        } else {
            ctx.fillStyle = `rgb(${shade * 0.25},${shade * 0.75},${shade})`;
        }

        ctx.fillRect(
            i * columnWidth,
            H / 2 - wallHeight / 2,
            columnWidth + 1,
            wallHeight
        );
    }
}

function drawFloor() {
    const gradient = ctx.createLinearGradient(0, H/2, 0, H);
    gradient.addColorStop(0, "#25252d");
    gradient.addColorStop(1, "#080810");

    ctx.fillStyle = gradient;
    ctx.fillRect(0, H/2, W, H/2);
}

function drawEnemies() {
    const visible = enemies
        .filter(e => e.alive)
        .map(e => ({
            ...e,
            distance: Math.hypot(e.x-player.x, e.y-player.y)
        }))
        .sort((a,b) => b.distance-a.distance);

    visible.forEach(enemy => {
        const dx = enemy.x - player.x;
        const dy = enemy.y - player.y;

        const angle = Math.atan2(dy,dx)-player.angle;
        const normalized = Math.atan2(
            Math.sin(angle),
            Math.cos(angle)
        );

        if (Math.abs(normalized) > FOV/2 + 0.2) return;

        const screenX = W/2 + normalized/FOV*W;
        const size = Math.min(
            300,
            H / Math.max(enemy.distance,0.3)
        );

        const screenY = H/2-size/2;

        if (rayBlocked(player.x,player.y,enemy.x,enemy.y)) return;

        ctx.fillStyle = "#1b1b1b";
        ctx.fillRect(screenX-size/2,screenY,size,size);

        ctx.fillStyle = "#d52c37";
        ctx.fillRect(screenX-size*0.3,screenY+size*0.18,size*0.6,size*0.35);

        ctx.fillStyle = "#ffeb3b";
        ctx.fillRect(screenX-size*0.22,screenY+size*0.28,size*0.12,size*0.08);
        ctx.fillRect(screenX+size*0.10,screenY+size*0.28,size*0.12,size*0.08);

        ctx.fillStyle = "#555";
        ctx.fillRect(screenX-size*0.35,screenY+size*0.55,size*0.7,size*0.35);
    });
}

function drawAmmo() {
    ammoItems.forEach(item => {
        if (item.collected) return;

        const dx = item.x-player.x;
        const dy = item.y-player.y;
        const angle = Math.atan2(dy,dx)-player.angle;
        const normalized = Math.atan2(Math.sin(angle),Math.cos(angle));

        if (Math.abs(normalized)>FOV/2) return;

        const distance = Math.hypot(dx,dy);
        if (rayBlocked(player.x,player.y,item.x,item.y)) return;

        const x = W/2 + normalized/FOV*W;
        const size = Math.min(35,H/distance*0.12);

        ctx.fillStyle = "#00ff77";
        ctx.fillRect(x-size/2,H/2-size/2,size,size);
    });
}

function drawCrosshair() {
    ctx.strokeStyle = attackFlash > 0 ? "#ffdf5d" : "white";
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(W/2-12,H/2);
    ctx.lineTo(W/2+12,H/2);
    ctx.moveTo(W/2,H/2-12);
    ctx.lineTo(W/2,H/2+12);
    ctx.stroke();
}

function drawWeapon() {
    ctx.fillStyle = "#333";
    ctx.fillRect(W/2-55,H-105,110,105);

    ctx.fillStyle = "#777";
    ctx.fillRect(W/2-30,H-130,60,70);

    ctx.fillStyle = "#00e5ff";
    ctx.fillRect(W/2-8,H-135,16,20);
}

function drawMiniMap() {
    const map = currentMap();
    const scale = 10;
    const x0 = W-125;
    const y0 = 15;

    ctx.fillStyle = "rgba(0,0,0,0.7)";
    ctx.fillRect(x0-5,y0-5,110,110);

    map.forEach((row,y) => {
        [...row].forEach((cell,x) => {
            ctx.fillStyle = cell === "1" ? "#00aabb" :
                            cell === "2" ? "#aa7733" : "#222";

            ctx.fillRect(x0+x*scale,y0+y*scale,scale-1,scale-1);
        });
    });

    enemies.forEach(enemy => {
        if (!enemy.alive) return;

        ctx.fillStyle = "#ff3333";
        ctx.fillRect(
            x0+enemy.x*scale-2,
            y0+enemy.y*scale-2,
            5,5
        );
    });

    ctx.fillStyle = "#ffff00";
    ctx.beginPath();
    ctx.arc(
        x0+player.x*scale,
        y0+player.y*scale,
        4,0,Math.PI*2
    );
    ctx.fill();
}

function draw() {
    ctx.fillStyle = "#111";
    ctx.fillRect(0,0,W,H/2);

    drawFloor();
    drawWalls();
    drawAmmo();
    drawEnemies();
    drawWeapon();
    drawCrosshair();
    drawMiniMap();

    if (attackFlash > 0) {
        ctx.fillStyle = "rgba(255,220,80,0.3)";
        ctx.fillRect(0,0,W,H);
    }

    if (paused || gameOver || missionClear) {
        ctx.fillStyle = "rgba(0,0,0,0.75)";
        ctx.fillRect(0,0,W,H);

        ctx.textAlign = "center";
        ctx.font = "bold 42px monospace";
        ctx.fillStyle = gameOver ? "#ff4444" : "#00e5ff";

        ctx.fillText(
            gameOver ? "GAME OVER" :
            missionClear ? "MISSION CLEAR!" :
            "PAUSED",
            W/2,H/2
        );
    }
}

function checkGame() {
    if (player.hp <= 0) {
        gameOver = true;
        message = "GAME OVER - PRESS RESTART";
        return;
    }

    if (enemies.every(e => !e.alive)) {
        missionClear = true;

        if (missionIndex === missions.length-1) {
            message = "ALL MISSIONS COMPLETE! FINAL SCORE: " + score;
        } else {
            message = "MISSION CLEAR! PRESS ENTER FOR NEXT MISSION";
        }
    }
}

function updateHUD() {
    document.getElementById("mission").textContent =
        missions[missionIndex].name;

    document.getElementById("health").textContent =
        "HP: " + player.hp;

    document.getElementById("ammo").textContent =
        "AMMO: " + player.ammo;

    document.getElementById("score").textContent =
        "SCORE: " + score;

    document.getElementById("enemy-count").textContent =
        "ENEMIES: " + enemies.filter(e=>e.alive).length;

    document.getElementById("message").textContent = message;
}

function togglePause() {
    if (gameOver || missionClear) return;
    paused = !paused;
    message = paused ? "PAUSED" : "MISSION IN PROGRESS";
    updateHUD();
}

function restartGame() {
    score = 0;
    startMission(0);
    canvas.focus();
}

function gameLoop(timestamp) {
    const dt = Math.min((timestamp-lastTime)/1000 || 0,0.04);
    lastTime = timestamp;

    if (!paused && !gameOver && !missionClear) {
        movePlayer(dt);

        enemies.forEach(enemy => {
            if (!enemy.alive) return;

            enemy.attackTimer += dt;

            const distance = Math.hypot(
                enemy.x-player.x,
                enemy.y-player.y
            );

            if (distance < 4 && enemy.attackTimer > 1.2) {
                if (!rayBlocked(player.x,player.y,enemy.x,enemy.y)) {
                    player.hp -= 5;
                    enemy.attackTimer = 0;
                    message = "WARNING! ENEMY ATTACK!";
                }
            }
        });

        attackFlash = Math.max(0,attackFlash-dt);
        checkGame();
        updateHUD();
    }

    draw();
    requestAnimationFrame(gameLoop);
}

// 키보드 조작
document.addEventListener("keydown",function(e) {
    const key = e.key.toLowerCase();

    if (["w","a","s","d","arrowleft","arrowright"," "].includes(key)) {
        e.preventDefault();
    }

    if (key === " " && !keys[" "]) {
        shoot();
        keys[" "] = true;
    } else if (key === "p" && !e.repeat) {
        togglePause();
    } else if (key === "r" && !e.repeat) {
        reload();
    } else if (key === "enter" && missionClear &&
               missionIndex < missions.length-1) {
        startMission(missionIndex+1);
    } else {
        keys[key] = true;
    }
});

document.addEventListener("keyup",function(e) {
    keys[e.key.toLowerCase()] = false;
});

canvas.addEventListener("click",function() {
    canvas.focus();
});

startMission(0);
requestAnimationFrame(gameLoop);

</script>
</body>
</html>
"""

html = html.replace("__MISSIONS__", missions)

components.html(
    html,
    height=680,
    scrolling=False
)
