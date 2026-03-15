// 游戏状态
let gameState = {
    hp: 100, maxHp: 100, gold: 0, items: [], level: 1, currentScene: 'start'
};

// 所有场景（剧情数据，易扩展）
const scenes = {
    start: {
        text: "你从昏迷中醒来，发现自己被锁在失落王国的阴冷监狱里。门外有守卫的脚步声。你该怎么办？",
        choices: [
            { text: "偷钥匙逃跑", next: 'stealKey' },
            { text: "攻击守卫", next: 'fightGuard' },
            { text: "假装生病求救", next: 'fakeSick' }
        ]
    },
    stealKey: {
        text: "你小心翼翼地偷到钥匙！但守卫发现了！快速选择：",
        choices: [
            { text: "逃向森林", next: 'forest', chance: 0.7 }, // 70%成功
            { text: "反击守卫", next: 'fightGuard' }
        ]
    },
    fightGuard: {
        text: "战斗开始！守卫HP:50，你的攻击力:" + (Math.floor(Math.random()*10)+gameState.level*5),
        choices: [{ text: "继续战斗", action: 'battle', enemy: {hp:50, dmg:8} }]
    },
    fakeSick: {
        text: "守卫开门查看，你趁机逃出！获得5金币。你跑到森林边缘。",
        choices: [
            { text: "探索森林", next: 'forest' },
            { text: "回监狱找物品", next: 'prisonItem' }
        ],
        onChoose: () => { gameState.gold += 5; updateStatus(); }
    },
    forest: {
        text: "森林幽暗潮湿，你遇到一只狼！战斗或逃？",
        choices: [
            { text: "战斗狼", next: 'fightWolf' },
            { text: "扔食物逃跑（需物品）", next: 'escapeWolf', reqItem: 'food' },
            { text: "去村庄", next: 'village' }
        ]
    },
    fightWolf: {
        text: "狼HP:30，撕咬你！",
        choices: [{ text: "战斗", action: 'battle', enemy: {hp:30, dmg:12} }]
    },
    village: {
        text: "村庄里有个老者，他说：'帮我找世界之树种子，就能推翻国王！' 给你食物和伤药。",
        choices: [
            { text: "接受任务", next: 'seedQuest', giveItem: 'food' },
            { text: "抢劫村民", next: 'robVillage', chance: 0.5 }
        ],
        onChoose: () => {
            if (!gameState.items.includes('food')) gameState.items.push('food');
            if (!gameState.items.includes('伤药')) gameState.items.push('伤药');
            updateStatus();
        }
    },
    seedQuest: {
        text: "你找到种子！老者给你剑，提升等级！现在去城堡打国王。",
        choices: [{ text: "挑战国王", next: 'kingFight' }],
        onChoose: () => { gameState.level++; gameState.items.push('sword'); updateStatus(); }
    },
    kingFight: {
        text: "最终BOSS！国王HP:100",
        choices: [{ text: "决战", action: 'battle', enemy: {hp:100, dmg:15} }]
    },
    // 结局场景（简化）
    victory: { text: "🎉 你推翻国王，成为英雄！王国重生。GOOD END", choices: [{ text: "重玩", next: 'start', reset: true }] },
    gameover: { text: "💀 你死了... GAME OVER", choices: [{ text: "重玩", next: 'start', reset: true }] },
    neutral: { text: "😐 你逃亡一生，无人知晓。NEUTRAL END", choices: [{ text: "重玩", next: 'start', reset: true }] }
    // 可以继续加更多场景...
};

// 初始化
function init() {
    updateStory(scenes.start);
    document.getElementById('save').onclick = saveGame;
    document.getElementById('load').onclick = loadGame;
    document.getElementById('reset').onclick = resetGame;
}

// 更新故事（打字动画）
function updateStory(scene) {
    const storyEl = document.getElementById('story');
    storyEl.innerHTML = scene.text;
    // 简单打字效果
    storyEl.style.opacity = 0;
    setTimeout(() => {
        storyEl.style.transition = 'opacity 1s';
        storyEl.style.opacity = 1;
    }, 100);

    const choicesEl = document.getElementById('choices');
    choicesEl.innerHTML = '';
    scene.choices.forEach((choice, i) => {
        const btn = document.createElement('button');
        btn.textContent = choice.text;
        btn.onclick = () => handleChoice(choice, i);
        choicesEl.appendChild(btn);
    });
    // 如果有可用食物或伤药，显示使用按钮
    if (gameState.items.includes('food')) {
        const btn = document.createElement('button');
        btn.textContent = '吃食物恢复HP';
        btn.onclick = () => handleChoice({ action: 'useFood' });
        choicesEl.appendChild(btn);
    }
    if (gameState.items.includes('伤药')) {
        const btn = document.createElement('button');
        btn.textContent = '使用伤药恢复HP';
        btn.onclick = () => handleChoice({ action: 'usePotion' });
        choicesEl.appendChild(btn);
    }
}

// 处理选择
function handleChoice(choice, index) {
    // 随机事件
    if (choice.chance && Math.random() > choice.chance) {
        updateStory({ text: "失败了！守卫抓住你。", choices: [{ text: "重玩", next: 'start', reset: true }] });
        gameState.hp = 0;
        return;
    }

    // 给物品
    if (choice.giveItem) gameState.items.push(choice.giveItem);

    // 执行回调
    if (choice.onChoose) choice.onChoose();

    // 战斗
    if (choice.action === 'battle') {
        battle(choice.enemy);
        return;
    }
    // 逃跑
    if (choice.action === 'escapeBattle') {
        // 根据敌人类型跳转
        let nextScene = 'forest';
        if (choice.enemy && choice.enemy.dmg === 12) nextScene = 'village'; // 狼
        if (choice.enemy && choice.enemy.dmg === 15) nextScene = 'neutral'; // BOSS
        gameState.currentScene = nextScene;
        updateStory(scenes[nextScene]);
        updateStatus();
        return;
    }

    // 使用伤药
    if (choice.action === 'usePotion') {
        if (gameState.items.includes('伤药')) {
            gameState.hp = Math.min(gameState.maxHp, gameState.hp + 30);
            // 消耗伤药
            gameState.items = gameState.items.filter(item => item !== '伤药');
            updateStory({ text: `你使用了伤药，HP恢复30！当前HP: ${gameState.hp}`, choices: [{ text: "继续", next: gameState.currentScene }] });
            updateStatus();
        } else {
            updateStory({ text: "你没有伤药！", choices: [{ text: "继续", next: gameState.currentScene }] });
        }
        return;
    }

    // 使用食物
    if (choice.action === 'useFood') {
        if (gameState.items.includes('food')) {
            gameState.hp = Math.min(gameState.maxHp, gameState.hp + 20);
            // 消耗食物
            gameState.items = gameState.items.filter(item => item !== 'food');
            updateStory({ text: `你吃了食物，HP恢复20！当前HP: ${gameState.hp}`, choices: [{ text: "继续", next: gameState.currentScene }] });
            updateStatus();
        } else {
            updateStory({ text: "你没有食物！", choices: [{ text: "继续", next: gameState.currentScene }] });
        }
        return;
    }

    // 切换场景
    gameState.currentScene = choice.next;
    const nextScene = scenes[choice.next] || scenes.gameover;
    if (choice.reset) resetGame();
    updateStory(nextScene);
    updateStatus();

    // 检查胜负
    checkWinLose();
}

// 战斗系统（简单骰子）
function battle(enemy) {
    let playerDmg = Math.floor(Math.random() * 10) + gameState.level * 5;
    let enemyDmg = Math.floor(Math.random() * 5) + enemy.dmg;
    gameState.hp -= enemyDmg;
    enemy.hp -= playerDmg;

    // 战斗描述
    let battleDesc = `<span class='battle-desc'>你造成 <b>${playerDmg}</b> 伤害！敌人造成 <b>${enemyDmg}</b> 伤害。</span>`;
    // HP显示
    let hpInfo = `<span class='hp-info'>你的HP: <b>${gameState.hp}</b>　敌人HP: <b>${enemy.hp}</b></span>`;
    let battleText = `${battleDesc}<br>${hpInfo}`;
    if (enemy.hp <= 0) {
        gameState.gold += 10;
        battleText += "<br><span class='battle-win'>敌人倒下！你获得10金币。</span>";
        // 判断敌人类型，推进剧情
        let nextScene = 'forest';
        if (enemy.dmg === 12) nextScene = 'village'; // 狼
        if (enemy.dmg === 15) nextScene = 'victory'; // BOSS
        gameState.currentScene = nextScene;
        let choices = [{ text: "继续冒险", next: nextScene }];
        // 战斗胜利后可用伤药
        if (gameState.items.includes('伤药')) {
            choices.unshift({ text: "使用伤药", action: 'usePotion' });
        }
        updateStory({ text: battleText, choices });
    } else if (gameState.hp <= 0) {
        // 死亡时直接跳转到gameover场景
        gameState.currentScene = 'gameover';
        updateStory(scenes.gameover);
    } else {
        // 传递当前enemy的hp，防止重置
        let choices = [{ text: "再战一回合", action: 'battle', enemy: { ...enemy } }];
        // 增加逃跑按钮
        choices.push({ text: "逃跑", action: 'escapeBattle', enemy });
        // 战斗中可用伤药
        if (gameState.items.includes('伤药')) {
            choices.unshift({ text: "使用伤药", action: 'usePotion' });
        }
        updateStory({ text: battleText, choices });
    }
    updateStatus();
}

// BOSS战（简化）
function bossBattle() {
    // 类似battle，但HP翻倍等
    battle({hp:100, dmg:15});
}

// 检查胜负
function checkWinLose() {
    if (gameState.hp <= 0) {
        updateStory(scenes.gameover);
        return;
    }
    if (gameState.currentScene === 'victory' || gameState.gold > 50 && gameState.items.includes('sword')) {
        updateStory(scenes.victory);
    }
}

// 更新状态
function updateStatus() {
    document.getElementById('hp').textContent = Math.max(0, gameState.hp);
    document.getElementById('gold').textContent = gameState.gold;
    // 物品显示优化
    document.getElementById('items').textContent = gameState.items.length ? gameState.items.join(', ') : '无';
    document.getElementById('level').textContent = gameState.level;
}

// 存档/读档/重玩
function saveGame() { localStorage.setItem('textRPG', JSON.stringify(gameState)); }
function loadGame() {
    const saved = localStorage.getItem('textRPG');
    if (saved) {
        gameState = JSON.parse(saved);
        updateStory(scenes[gameState.currentScene] || scenes.start);
        updateStatus();
    }
}
function resetGame() {
    gameState = { hp: 100, maxHp: 100, gold: 0, items: [], level: 1, currentScene: 'start' };
    updateStory(scenes.start);
    updateStatus();
}

// 音效（浏览器beep）
function playSound() {
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAo'); // 简单beep
    audio.play().catch(() => {});
}

// 点击按钮加音效
document.addEventListener('click', playSound, { once: false });

init(); // 启动游戏