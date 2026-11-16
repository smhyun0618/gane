
import streamlit as st
import streamlit.components.v1 as components
import json

# --------------------------------
# 1. 게임 기본 설정 (리스트)
# --------------------------------

st.set_page_config(
    page_title="RETRO STRIKE",
    page_icon="🎮",
    layout="wide"
)

mission_plan = [
    {"name": "MISSION 1 - TRAINING", "enemy_count": 2},
    {"name": "MISSION 2 - DARK HALL", "enemy_count": 3},
    {"name": "MISSION 3 - LAST BATTLE", "enemy_count": 4}
]

# 적의 위치
enemy_positions = [
    [7.5, 1.5],
    [7.5, 6.5],
    [5.5, 3.5],
    [2.5, 6.5]
]

# --------------------------------
# 2. 함수
# --------------------------------

def build_missions():

    game_missions = []

    for index, mission in enumerate(mission_plan):

        if index == 0:
            difficulty = "EASY"
        elif index == 1:
            difficulty = "NORMAL"
        else:
            difficulty = "HARD"

        enemies = []

        for i in range(mission["enemy_count"]):

            enemies.append({
                "x": enemy_positions[i][0],
                "y": enemy_positions[i][1],
                "hp": 1
            })

        game_missions.append({
            "name": mission["name"],
            "difficulty": difficulty,
            "enemies": enemies
        })

    return game_missions


# --------------------------------
# 3. 웹 화면
# --------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #101014;
    color: white;
}
h1, h2, h3, p {
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🎮 RETRO STRIKE")
st.subheader("LAST MISSION")
st.caption("RETRO FPS ARCADE GAME")

st.write(
    "어두운 기지를 탐험하고 로봇 적들을 상대하세요. "
    "모든 미션을 완료하면 게임에서 승리합니다."
)

st.info(
    "WASD: 이동 | 마우스: 시점 회전 | 클릭: 에너지 공격"
)

# --------------------------------
# 4. 미션 데이터 생성
# --------------------------------

missions = build_missions()

# --------------------------------
# 5. 게임 화면 구현
# --------------------------------

game_html = r"""
<!DOCTYPE html>
<html>
<head>
<style>
body {
    margin: 0;
    background: #090909;
    color: white;
    font-family: monospace;
    overflow: hidden;
}

canvas {
    width: 100%;
    height: auto;
    display: block;
    background: black;
    cursor: crosshair;
    border: 2px solid #555;
}

.info {
    display: flex;
    justify-content: space-between;
    padding: 10px;
    font-size: 15px;
    color: #00ff99;
    background: #111;
}

#message {
    text-align: center;
    color: #ffcc00;
    font-size: 17px;
    padding: 8px;
}
</style>
</head>

<body>

<div class="info">
    <span id="mission">MISSION 1</span>
    <span id="health">HP: 100</span>
    <span id="score">SCORE: 0</span>
</div>

<canvas id="game" width="960" height="540"></canvas>

<div id="message">
    CLICK TO START
</div>

<script>

// --------------------------------
// 게임 데이터
// --------------------------------

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const W = canvas.width;
const H = canvas.height;

const MAP = [
    "##########",
    "#........#",
    "#..#.....#",
    "#........#",
    "#....#...#",
    "#........#",
    "#..#.....#",
    "#........#",
    "##########"
];

const MISSIONS = __MISSION_DATA__;

let missionIndex = 0;
let player = {
    x: 1.5,
    y: 1.5,
    angle: 0,
    hp: 100
};

let enemies = [];
let score = 0;
let keys = {};
let lastShot = 0;
let clearTime = 0;
let gameOver = false;
let gameWon = false;
let started = false;

const FOV = Math.PI / 3;
const depthBuffer = new Array(W).fill(10);

// --------------------------------
// 미션 시작 함수
// --------------------------------

function startMission() {

    player.x = 1.5;
    player.y = 1.5;
    player.angle = 0;

    enemies = MISSIONS[missionIndex].enemies.map(
        e => ({
            x: e.x,
            y: e.y,
            hp: e.hp,
            alive: true
        })
    );

    document.getElementById("mission").innerText =
        MISSIONS[missionIndex].name;

    clearTime = 0;
}

// --------------------------------
// 벽 충돌 확인 함수
// --------------------------------

function isWall(x, y) {

    let mapX = Math.floor(x);
    let mapY = Math.floor(y);

    if (
        mapY < 0 || mapY >= MAP.length ||
        mapX < 0 || mapX >= MAP[0].length
    ) {
        return true;
    }

    return MAP[mapY][mapX] === "#";
}

// --------------------------------
// 플레이어 이동 함수
// --------------------------------

function movePlayer(dt) {

    const speed = 2.5 * dt;

    let dx = 0;
    let dy = 0;

    if (keys["w"]) {
        dx += Math.cos(player.angle) * speed;
        dy += Math.sin(player.angle) * speed;
    }

    if (keys["s"]) {
        dx -= Math.cos(player.angle) * speed;
        dy -= Math.sin(player.angle) * speed;
    }

    if (keys["a"]) {
        dx += Math.cos(player.angle - Math.PI / 2) * speed;
        dy += Math.sin(player.angle - Math.PI / 2) * speed;
    }

    if (keys["d"]) {
        dx += Math.cos(player.angle + Math.PI / 2) * speed;
        dy += Math.sin(player.angle + Math.PI / 2) * speed;
    }

    if (!isWall(player.x + dx, player.y)) {
        player.x += dx;
    }

    if (!isWall(player.x, player.y + dy)) {
        player.y += dy;
    }

    // 적과 가까워지면 체력 감소
    for (let enemy of enemies) {

        if (!enemy.alive) continue;

        let distance = Math.hypot(
            player.x - enemy.x,
            player.y - enemy.y
        );

        if (distance < 0.55) {
            player.hp -= 12 * dt;
        }
    }
}

// --------------------------------
// 공격 함수
// --------------------------------

function shoot() {

    if (!started || gameOver || gameWon) return;

    const now = performance.now();

    if (now - lastShot < 300) return;

    lastShot = now;

    let target = null;
    let minDistance = Infinity;

    for (let enemy of enemies) {

        if (!enemy.alive) continue;

        let dx = enemy.x - player.x;
        let dy = enemy.y - player.y;

        let distance = Math.hypot(dx, dy);

        let angle = Math.atan2(dy, dx);
        let difference = Math.atan2(
            Math.sin(angle - player.angle),
            Math.cos(angle - player.angle)
        );

        if (
            Math.abs(difference) < 0.12 &&
            distance < minDistance &&
            distance < 8
        ) {
            target = enemy;
            minDistance = distance;
        }
    }

    if (target !== null) {

        target.hp -= 1;

        if (target.hp <= 0) {
            target.alive = false;
            score += 100;
        }
    }
}

// --------------------------------
// 3D 벽 그리기 함수
// --------------------------------

function drawWalls() {

    ctx.fillStyle = "#24202a";
    ctx.fillRect(0, 0, W, H / 2);

    ctx.fillStyle = "#35302c";
    ctx.fillRect(0, H / 2, W, H / 2);

    const strip = 4;

    for (let x = 0; x < W; x += strip) {

        let rayAngle =
            player.angle - FOV / 2 +
            (x / W) * FOV;

        let distance = 0;
        let hit = false;

        while (distance < 12 && !hit) {

            distance += 0.025;

            let rx = player.x +
                Math.cos(rayAngle) * distance;

            let ry = player.y +
                Math.sin(rayAngle) * distance;

            if (isWall(rx, ry)) {
                hit = true;
            }
        }

        let correctedDistance =
            distance * Math.cos(rayAngle - player.angle);

        correctedDistance = Math.max(
            0.1,
            correctedDistance
        );

        let wallHeight = Math.min(
            H,
            H / correctedDistance
        );

        let shade = Math.max(
            25,
            180 - correctedDistance * 18
        );

        ctx.fillStyle =
            `rgb(${shade}, ${Math.floor(shade * 0.65)}, ${Math.floor(shade * 0.55)})`;

        ctx.fillRect(
            x,
            H / 2 - wallHeight / 2,
            strip,
            wallHeight
        );

        for (let i = x; i < x + strip; i++) {
            depthBuffer[i] = correctedDistance;
        }
    }
}

// --------------------------------
// 적 캐릭터 그리기 함수
// --------------------------------

function drawEnemies() {

    let visibleEnemies = enemies.filter(
        enemy => enemy.alive
    );

    visibleEnemies.sort((a, b) => {

        let da = Math.hypot(
            a.x - player.x,
            a.y - player.y
        );

        let db = Math.hypot(
            b.x - player.x,
            b.y - player.y
        );

        return db - da;
    });

    for (let enemy of visibleEnemies) {

        let dx = enemy.x - player.x;
        let dy = enemy.y - player.y;

        let distance = Math.hypot(dx, dy);

        let angle = Math.atan2(dy, dx);

        let difference = Math.atan2(
            Math.sin(angle - player.angle),
            Math.cos(angle - player.angle)
        );

        if (Math.abs(difference) > FOV / 2) continue;

        let screenX =
            W / 2 + (difference / FOV) * W;

        let size = Math.min(
            250,
            H / distance * 0.7
        );

        let left = screenX - size / 2;
        let top = H / 2 - size / 2;

        let column = Math.max(
            0,
            Math.min(W - 1, Math.floor(screenX))
        );

        if (depthBuffer[column] < distance) continue;

        // 로봇 몸체
        ctx.fillStyle = "#8d2929";
        ctx.fillRect(
            left + size * 0.2,
            top + size * 0.35,
            size * 0.6,
            size * 0.55
        );

        // 로봇 머리
        ctx.fillStyle = "#b5b5b5";
        ctx.fillRect(
            left + size * 0.28,
            top + size * 0.12,
            size * 0.44,
            size * 0.3
        );

        // 눈
        ctx.fillStyle = "#ff3333";

        ctx.fillRect(
            left + size * 0.36,
            top + size * 0.23,
            size * 0.1,
            size * 0.06
        );

        ctx.fillRect(
            left + size * 0.55,
            top + size * 0.23,
            size * 0.1,
            size * 0.06
        );

        // 다리
        ctx.fillStyle = "#444";

        ctx.fillRect(
            left + size * 0.28,
            top + size * 0.85,
            size * 0.15,
            size * 0.15
        );

        ctx.fillRect(
            left + size * 0.57,
            top + size * 0.85,
            size * 0.15,
            size * 0.15
        );
    }
}

// --------------------------------
// 조준점
// --------------------------------

function drawCrosshair() {

    ctx.strokeStyle = "#00ff99";
    ctx.lineWidth = 2;

    ctx.beginPath();

    ctx.moveTo(W / 2 - 12, H / 2);
    ctx.lineTo(W / 2 + 12, H / 2);

    ctx.moveTo(W / 2, H / 2 - 12);
    ctx.lineTo(W / 2, H / 2 + 12);

    ctx.stroke();
}

// --------------------------------
// 게임 상태 확인 함수
// --------------------------------

function checkGame() {

    let aliveCount = enemies.filter(
        enemy => enemy.alive
    ).length;

    if (player.hp <= 0) {
        gameOver = true;
        return;
    }

    if (aliveCount === 0) {

        if (clearTime === 0) {
            clearTime = performance.now();
        }

        if (performance.now() - clearTime > 1500) {

            if (missionIndex < MISSIONS.length - 1) {

                missionIndex++;
                startMission();

            } else {

                gameWon = true;
            }
        }
    }
}

// --------------------------------
// 화면 출력
// --------------------------------

function drawHUD() {

    document.getElementById("health").innerText =
        "HP: " + Math.max(0, Math.floor(player.hp));

    document.getElementById("score").innerText =
        "SCORE: " + score;

    let aliveCount = enemies.filter(
        enemy => enemy.alive
    ).length;

    if (gameOver) {

        document.getElementById("message").innerText =
            "GAME OVER - REFRESH TO RESTART";

    } else if (gameWon) {

        document.getElementById("message").innerText =
            "MISSION COMPLETE! FINAL SCORE: " + score;

    } else if (clearTime > 0) {

        document.getElementById("message").innerText =
            "MISSION CLEAR!";

    } else {

        document.getElementById("message").innerText =
            "ROBOTS REMAINING: " + aliveCount;
    }
}

// --------------------------------
// 게임 메인 반복 함수
// --------------------------------

let previousTime = performance.now();

function gameLoop() {

    const now = performance.now();

    let dt = Math.min(
        (now - previousTime) / 1000,
        0.05
    );

    previousTime = now;

    if (started && !gameOver && !gameWon) {

        if (clearTime === 0) {
            movePlayer(dt);
        }

        checkGame();
    }

    if (started) {

        drawWalls();
        drawEnemies();
        drawCrosshair();
        drawHUD();

    } else {

        ctx.fillStyle = "#111";
        ctx.fillRect(0, 0, W, H);

        ctx.fillStyle = "#00ff99";
        ctx.font = "bold 36px monospace";
        ctx.textAlign = "center";

        ctx.fillText(
            "RETRO STRIKE",
            W / 2,
            H / 2 - 20
        );

        ctx.font = "20px monospace";

        ctx.fillText(
            "CLICK TO START",
            W / 2,
            H / 2 + 35
        );
    }

    requestAnimationFrame(gameLoop);
}

// --------------------------------
// 키보드 조작
// --------------------------------

document.addEventListener("keydown", function(e) {

    let key = e.key.toLowerCase();

    if (["w", "a", "s", "d"].includes(key)) {
        keys[key] = true;
        e.preventDefault();
    }
});

document.addEventListener("keyup", function(e) {

    keys[e.key.toLowerCase()] = false;
});

// --------------------------------
// 마우스 조작
// --------------------------------

canvas.addEventListener("click", function() {

    if (!started) {

        started = true;
        startMission();

        if (canvas.requestPointerLock) {
            canvas.requestPointerLock();
        }

    } else {

        if (
            document.pointerLockElement !== canvas &&
            canvas.requestPointerLock
        ) {
            canvas.requestPointerLock();
        }

        shoot();
    }
});

document.addEventListener("mousemove", function(e) {

    if (
        document.pointerLockElement === canvas &&
        started &&
        !gameOver &&
        !gameWon
    ) {

        player.angle += e.movementX * 0.0025;
    }
});

// 게임 실행
gameLoop();

</script>
</body>
</html>
"""

# --------------------------------
# 6. Python 데이터를 JavaScript에 전달
# --------------------------------

mission_json = json.dumps(missions)

game_html = game_html.replace(
    "__MISSION_DATA__",
    mission_json
)

components.html(
    game_html,
    height=650,
    scrolling=False
)

st.caption(
    "RETRO STRIKE | 3 MISSIONS | ROBOT ARCADE GAME"
)
