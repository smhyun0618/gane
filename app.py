
import streamlit as st
import streamlit.components.v1 as components
import random
import json

# =====================================
# 1. 기본 설정
# =====================================

st.set_page_config(
    page_title="RETRO STRIKE",
    page_icon="🎮",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #101014;
    color: white;
}
h1, h2, h3, p, label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# =====================================
# 2. 게임 데이터 (리스트)
# =====================================

mission_plan = [
    {"name": "MISSION 1 : TRAINING", "enemy_count": 2},
    {"name": "MISSION 2 : DARK HALL", "enemy_count": 3},
    {"name": "MISSION 3 : LAST BATTLE", "enemy_count": 4}
]

spawn_positions = [
    [7.5, 1.5],
    [7.5, 6.5],
    [5.5, 3.5],
    [2.5, 6.5]
]


# =====================================
# 3. 미션 생성 함수
# =====================================

def build_missions():

    game_missions = []

    for index, mission in enumerate(mission_plan):

        if index == 0:
            difficulty = "EASY"
        elif index == 1:
            difficulty = "NORMAL"
        else:
            difficulty = "HARD"

        # 적의 위치를 무작위로 선택
        selected_positions = random.sample(
            spawn_positions,
            mission["enemy_count"]
        )

        enemies = []

        for position in selected_positions:

            enemies.append({
                "x": position[0],
                "y": position[1],
                "hp": 1
            })

        game_missions.append({
            "name": mission["name"],
            "difficulty": difficulty,
            "enemies": enemies
        })

    return game_missions


# =====================================
# 4. 게임 제목 및 안내
# =====================================

st.title("🎮 RETRO STRIKE")
st.subheader("LAST MISSION")

st.markdown("""
**RETRO FPS ARCADE GAME**

어두운 기지에 침입한 로봇들을 상대하세요.
모든 적을 처치하고 최종 미션을 완료하세요!
""")

st.info("""
↑ ↓ : 전진 / 후진
| ← → : 시야 회전
| W A S D : 이동
| 마우스 클릭 : 공격
""")

# =====================================
# 5. 게임 데이터 전달
# =====================================

missions = build_missions()

game_html = r"""
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">

<style>

body {
    margin: 0;
    padding: 0;
    background: #090909;
    color: white;
    font-family: monospace;
}

.info {
    display: flex;
    justify-content: space-around;
    padding: 12px;
    background: #151515;
    color: #00ff99;
    font-size: 16px;
    border: 1px solid #444;
}

canvas {
    display: block;
    width: 100%;
    height: auto;
    background: black;
    border: 2px solid #555;
    cursor: crosshair;
    outline: none;
}

#message {
    text-align: center;
    color: #ffcc00;
    font-size: 18px;
    padding: 12px;
    background: #151515;
}

</style>
</head>

<body>

<div class="info">
    <span id="mission">MISSION 1</span>
    <span id="health">HP: 100</span>
    <span id="score">SCORE: 0</span>
</div>

<canvas id="game" width="960" height="540" tabindex="0"></canvas>

<div id="message">
    CLICK TO START
</div>

<script>

// =====================================
// 1. 게임 기본 데이터
// =====================================

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

let started = false;
let gameOver = false;
let gameWon = false;

let lastShot = 0;
let clearTime = 0;

const FOV = Math.PI / 3;
const depthBuffer = new Array(W).fill(10);


// =====================================
// 2. 미션 시작 함수
// =====================================

function startMission() {

    player.x = 1.5;
    player.y = 1.5;
    player.angle = 0;

    enemies = MISSIONS[missionIndex].enemies.map(
        enemy => ({
            x: enemy.x,
            y: enemy.y,
            hp: enemy.hp,
            alive: true
        })
    );

    clearTime = 0;

    document.getElementById("mission").innerText =
        MISSIONS[missionIndex].name;
}


// =====================================
// 3. 게임 초기화 함수
// =====================================

function resetGame() {

    missionIndex = 0;

    player.hp = 100;
    player.x = 1.5;
    player.y = 1.5;
    player.angle = 0;

    score = 0;

    gameOver = false;
    gameWon = false;
    started = true;

    keys = {};

    startMission();
}


// =====================================
// 4. 벽 충돌 확인 함수
// =====================================

function isWall(x, y) {

    let mapX = Math.floor(x);
    let mapY = Math.floor(y);

    if (
        mapY < 0 ||
        mapY >= MAP.length ||
        mapX < 0 ||
        mapX >= MAP[0].length
    ) {
        return true;
    }

    return MAP[mapY][mapX] === "#";
}


// =====================================
// 5. 플레이어 이동 함수
// =====================================

function movePlayer(dt) {

    const speed = 2.5 * dt;

    let dx = 0;
    let dy = 0;

    // 앞으로 이동
    if (keys["w"] || keys["arrowup"]) {

        dx += Math.cos(player.angle) * speed;
        dy += Math.sin(player.angle) * speed;

    }

    // 뒤로 이동
    if (keys["s"] || keys["arrowdown"]) {

        dx -= Math.cos(player.angle) * speed;
        dy -= Math.sin(player.angle) * speed;

    }

    // 왼쪽 이동
    if (keys["a"]) {

        dx += Math.cos(player.angle - Math.PI / 2) * speed;
        dy += Math.sin(player.angle - Math.PI / 2) * speed;

    }

    // 오른쪽 이동
    if (keys["d"]) {

        dx += Math.cos(player.angle + Math.PI / 2) * speed;
        dy += Math.sin(player.angle + Math.PI / 2) * speed;

    }

    // 벽 충돌 검사
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
            player.hp -= 20 * dt;
        }

    }
}


// =====================================
// 6. 공격 함수
// =====================================

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

        // 조준 범위 확인
        if (
            Math.abs(difference) < 0.12 &&
            distance < minDistance &&
            distance < 8
        ) {

            // 벽 뒤에 있는 적은 공격할 수 없음
            let blocked = false;

            for (let d = 0.1; d < distance; d += 0.1) {

                let checkX = player.x +
                    Math.cos(angle) * d;

                let checkY = player.y +
                    Math.sin(angle) * d;

                if (isWall(checkX, checkY)) {
                    blocked = true;
                    break;
                }
            }

            if (!blocked) {
                target = enemy;
                minDistance = distance;
            }

        }

    }

    // 공격 성공
    if (target !== null) {

        target.hp -= 1;

        if (target.hp <= 0) {

            target.alive = false;
            score += 100;

        }

    }

}


// =====================================
// 7. 3D 벽 그리기 함수
// =====================================

function drawWalls() {

    // 천장
    ctx.fillStyle = "#24202a";
    ctx.fillRect(0, 0, W, H / 2);

    // 바닥
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
            distance * Math.cos(
                rayAngle - player.angle
            );

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


// =====================================
// 8. 적 캐릭터 그리기 함수
// =====================================

function drawEnemies() {

    let visibleEnemies = enemies.filter(
        enemy => enemy.alive
    );

    // 먼 적부터 그리기
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

        if (Math.abs(difference) > FOV / 2) {
            continue;
        }

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

        if (depthBuffer[column] < distance) {
            continue;
        }

        // 몸체
        ctx.fillStyle = "#8d2929";

        ctx.fillRect(
            left + size * 0.2,
            top + size * 0.35,
            size * 0.6,
            size * 0.55
        );

        // 머리
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


// =====================================
// 9. 조준점 그리기
// =====================================

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


// =====================================
// 10. 게임 상태 확인
// =====================================

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


// =====================================
// 11. HUD 표시 함수
// =====================================

function drawHUD() {

    document.getElementById("health").innerText =
        "HP: " + Math.max(
            0,
            Math.floor(player.hp)
        );

    document.getElementById("score").innerText =
        "SCORE: " + score;

    let aliveCount = enemies.filter(
        enemy => enemy.alive
    ).length;

    if (gameOver) {

        document.getElementById("message").innerText =
            "GAME OVER - PRESS R TO RESTART";

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


// =====================================
// 12. 메인 게임 반복 함수
// =====================================

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


// =====================================
// 13. 키보드 조작
// =====================================

window.addEventListener("keydown", function(e) {

    let key = e.key.toLowerCase();

    // 이동 키
    if (
        ["w", "a", "s", "d",
         "arrowup", "arrowdown",
         "arrowleft", "arrowright"].includes(key)
    ) {
        e.preventDefault();
        keys[key] = true;
    }

    // 좌우 시야 회전
    if (key === "arrowleft") {
        player.angle -= 0.08;
    }

    if (key === "arrowright") {
        player.angle += 0.08;
    }

    // 게임 재시작
    if (key === "r" && (gameOver || gameWon)) {
        resetGame();
    }

});

window.addEventListener("keyup", function(e) {

    keys[e.key.toLowerCase()] = false;

});

window.addEventListener("blur", function() {

    keys = {};

});


// =====================================
// 14. 마우스 공격
// =====================================

canvas.addEventListener("click", function() {

    canvas.focus();

    if (!started) {

        started = true;
        startMission();

        return;

    }

    if (!gameOver && !gameWon) {
        shoot();
    }

});


// =====================================
// 15. 게임 실행
// =====================================

gameLoop();

</script>

</body>
</html>
"""

# Python 데이터를 JavaScript로 전달
mission_json = json.dumps(missions)

game_html = game_html.replace(
    "__MISSION_DATA__",
    mission_json
)

# 게임 화면 출력
components.html(
    game_html,
    height=650,
    scrolling=False
)

st.caption(
    "RETRO STRIKE | 3 MISSIONS | ARCADE FPS"
)
