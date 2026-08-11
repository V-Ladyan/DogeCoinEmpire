let gameState = {
    coins: 0,
    totalCoins: 0,
    clicks: 0,
    autoClickPower: 0,
    multiplier: 1.0,
    active_skin: 'default',
    skin_bonus: 1.0
};

let autoClickInterval = null;
let activeBoost = null;
let boostTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    loadGame();
    setupEventListeners();
    startAutoClicker();
});

async function loadGame() {
    try {
        const response = await fetch('/api/game-state');
        const data = await response.json();
        
        gameState = data.user;
        updateUI(data);
        renderUpgrades(data.available_upgrades);
        renderMonetization(data.stage_id);
        updateBackground(data.stage_id);
        loadMonetizationStatus();
        
        if (gameState.active_skin && gameState.active_skin !== 'default') {
            updateDogeSkin({id: gameState.active_skin, bonus: gameState.skin_bonus});
        }
    } catch (error) {
        console.error('Ошибка загрузки игры:', error);
    }
}

function setupEventListeners() {
    const dogeEmoji = document.getElementById('dogeEmoji');
    const dogeButton = document.getElementById('dogeButton');
    
    if (dogeEmoji) {
        dogeEmoji.addEventListener('click', handleClick);
    }
    
    if (dogeButton) {
        dogeButton.addEventListener('click', handleClick);
    }
    
    document.addEventListener('selectstart', (e) => {
        if (e.target.closest('.doge-emoji, .doge-button, .upgrade-card, .monetization-btn')) {
            e.preventDefault();
        }
    });
}

async function handleClick(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const target = e.currentTarget;
    target.style.transform = 'scale(0.9)';
    setTimeout(() => {
        target.style.transform = '';
    }, 100);
    
    try {
        const response = await fetch('/api/click', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        gameState.coins = data.coins;
        gameState.totalCoins = data.total_coins;
        gameState.clicks = data.clicks;
        
        updateStats();
        showClickEffect(data.coins_earned, data.crit_type);
        
        if (data.event) {
            showEvent(data.event);
        }
        
        if (data.stage_up) {
            showStageUp(data.new_stage);
            await loadGame();
        }
        
        updateUpgradeAvailability();
    } catch (error) {
        console.error('Ошибка клика:', error);
    }
}

function showClickEffect(amount, critType) {
    const effect = document.getElementById('clickEffect');
    if (!effect) return;
    
    let text = '+' + amount.toFixed(1);
    
    if (critType === true) {
        text += ' 💥CRIT!';
        effect.style.color = '#ff6b6b';
        effect.style.fontSize = '2em';
    } else if (critType === 'quantum') {
        text += ' ⚛️QUANTUM!';
        effect.style.color = '#4ecdc4';
        effect.style.fontSize = '2em';
    } else {
        effect.style.color = '#f2a900';
        effect.style.fontSize = '1.5em';
    }
    
    effect.textContent = text;
    effect.style.animation = 'none';
    effect.offsetHeight;
    effect.style.animation = 'clickFloat 1s ease-out forwards';
}

function updateStats() {
    const coinsEl = document.getElementById('coins');
    const totalCoinsEl = document.getElementById('totalCoins');
    const clicksEl = document.getElementById('clicks');
    
    if (coinsEl) coinsEl.textContent = gameState.coins.toFixed(1);
    if (totalCoinsEl) totalCoinsEl.textContent = gameState.total_coins.toFixed(1);
    if (clicksEl) clicksEl.textContent = gameState.clicks;
}

function updateUI(data) {
    const stageName = document.getElementById('stageName');
    const stageDesc = document.getElementById('stageDesc');
    const autoClickPower = document.getElementById('autoClickPower');
    
    if (stageName) stageName.textContent = data.current_stage.name;
    if (stageDesc) stageDesc.textContent = data.current_stage.description;
    if (autoClickPower) autoClickPower.textContent = data.user.auto_click_power.toFixed(1);
    
    updateStats();
}

function renderUpgrades(upgrades) {
    const grid = document.getElementById('upgradesGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    for (const [id, upgrade] of Object.entries(upgrades)) {
        const card = document.createElement('div');
        card.className = 'upgrade-card';
        card.setAttribute('data-upgrade-id', id);
        
        if (upgrade.level >= (upgrade.max_level || 10)) {
            card.classList.add('max-level');
        }
        
        const canAfford = gameState.coins >= upgrade.cost;
        if (!canAfford && upgrade.level < (upgrade.max_level || 10)) {
            card.classList.add('locked');
        }
        
        card.innerHTML = 
            '<div class="upgrade-level">Ур. ' + upgrade.level + '/10</div>' +
            '<div class="upgrade-name">' + upgrade.name + '</div>' +
            '<div class="upgrade-desc">' + upgrade.description + '</div>' +
            '<div class="upgrade-flavor">' + upgrade.flavor + '</div>' +
            '<div class="upgrade-cost">💰 ' + upgrade.cost.toFixed(0) + ' DogeCoin</div>';
        
        card.addEventListener('click', () => buyUpgrade(id));
        grid.appendChild(card);
    }
}

async function buyUpgrade(upgradeId) {
    try {
        const response = await fetch('/api/buy-upgrade/' + upgradeId, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if (data.success) {
            gameState.coins = data.coins;
            updateStats();
            
            showEvent({
                name: 'Покупка!',
                message: data.message,
                type: 'bonus'
            });
            
            await loadGame();
        } else {
            showEvent({
                name: 'Ошибка',
                message: data.message,
                type: 'penalty'
            });
        }
    } catch (error) {
        console.error('Ошибка покупки:', error);
    }
}

function updateUpgradeAvailability() {
    const cards = document.querySelectorAll('.upgrade-card');
    cards.forEach(card => {
        const costText = card.querySelector('.upgrade-cost');
        if (!costText) return;
        
        const costTextContent = costText.textContent;
        const cost = parseFloat(costTextContent.replace(/[^0-9.]/g, ''));
        
        if (gameState.coins >= cost && !card.classList.contains('max-level')) {
            card.classList.remove('locked');
        } else if (!card.classList.contains('max-level')) {
            card.classList.add('locked');
        }
    });
}

function showEvent(eventData) {
    const toast = document.getElementById('eventToast');
    if (!toast) return;
    
    const icon = toast.querySelector('.event-icon');
    const text = toast.querySelector('.event-text');
    
    if (icon) {
        switch(eventData.type) {
            case 'bonus':
                icon.textContent = '🎉';
                break;
            case 'crisis':
                icon.textContent = '⚠️';
                break;
            case 'penalty':
                icon.textContent = '💀';
                break;
            default:
                icon.textContent = '📢';
        }
    }
    
    if (text) {
        text.innerHTML = '<strong>' + eventData.name + '</strong><br>' + eventData.message;
    }
    
    toast.style.display = 'block';
    toast.classList.add('show');
    toast.style.animation = 'none';
    toast.offsetHeight;
    toast.style.animation = 'slideIn 0.5s ease-out';
    
    setTimeout(() => {
        toast.style.display = 'none';
        toast.classList.remove('show');
    }, 4000);
}

function showStageUp(newStage) {
    const eventData = {
        name: '🚀 Новый этап!',
        message: newStage.name + '<br>' + newStage.description,
        type: 'bonus'
    };
    showEvent(eventData);
    updateBackground(getStageIdByName(newStage.name));
}

function getStageIdByName(stageName) {
    const stages = {
        '🖥️ Домашний майнер': 1,
        '🏭 Гаражная ферма': 2,
        '🏢 Промышленный майнинг': 3,
        '🌕 Lunar Doge Station': 4,
        '🚀 Межгалактический хайп': 5
    };
    return stages[stageName] || 1;
}

function updateBackground(stageId) {
    const backgrounds = {
        1: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        2: 'linear-gradient(135deg, #2c3e50 0%, #3498db 50%, #2c3e50 100%)',
        3: 'linear-gradient(135deg, #0f3460 0%, #533483 50%, #0f3460 100%)',
        4: 'linear-gradient(135deg, #1a1a2e 0%, #4a0e4e 50%, #1a1a2e 100%)',
        5: 'linear-gradient(135deg, #e94560 0%, #533483 50%, #0f3460 100%)'
    };
    
    document.body.style.background = backgrounds[stageId] || backgrounds[1];
}

function startAutoClicker() {
    if (autoClickInterval) {
        clearInterval(autoClickInterval);
    }
    
    autoClickInterval = setInterval(() => {
        if (gameState.auto_click_power > 0) {
            const boostMultiplier = activeBoost ? activeBoost.multiplier : 1;
            const autoCoins = gameState.auto_click_power * gameState.multiplier * boostMultiplier;
            gameState.coins += autoCoins;
            gameState.total_coins += autoCoins;
            updateStats();
            updateUpgradeAvailability();
        }
    }, 1000);
}

async function resetGame() {
    if (confirm('Точно хочешь начать заново? Весь прогресс будет потерян!')) {
        try {
            await fetch('/api/reset', { method: 'POST' });
            window.location.reload();
        } catch (error) {
            console.error('Ошибка сброса:', error);
        }
    }
}

function renderMonetization(stageId) {
    const existingPanel = document.querySelector('.monetization-panel');
    if (existingPanel) existingPanel.remove();
    
    const upgradesZone = document.querySelector('.upgrades-zone');
    if (!upgradesZone) return;
    
    const monetizationDiv = document.createElement('div');
    monetizationDiv.className = 'monetization-panel';
    monetizationDiv.innerHTML = 
        '<h3>💎 Монетизация</h3>' +
        '<div class="monetization-buttons">' +
            '<button class="monetization-btn" onclick="claimDailyReward()">🎁 Ежедневный бонус</button>' +
            '<button class="monetization-btn" onclick="activateAdBoost()">📺 Реклама (x2 буст)</button>' +
        '</div>' +
        '<div class="skins-panel" id="skinsPanel"></div>' +
        '<div class="boost-display" id="boostDisplay"></div>';
    
    upgradesZone.appendChild(monetizationDiv);
}

async function loadMonetizationStatus() {
    try {
        const response = await fetch('/api/monetization/skins');
        const data = await response.json();
        renderSkins(data.skins);
    } catch (error) {
        console.error('Ошибка загрузки монетизации:', error);
    }
}

async function claimDailyReward() {
    try {
        const response = await fetch('/api/monetization/daily-reward', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            gameState.coins += data.reward;
            updateStats();
            showEvent({
                name: '🎁 Ежедневная награда!',
                message: data.message,
                type: 'bonus'
            });
        } else {
            showEvent({
                name: '⏰ Подожди',
                message: data.message,
                type: 'penalty'
            });
        }
    } catch (error) {
        console.error('Ошибка получения награды:', error);
    }
}

async function activateAdBoost() {
    try {
        const response = await fetch('/api/monetization/ad-boost', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            activeBoost = {
                multiplier: data.multiplier,
                endTime: Date.now() + (data.duration * 1000)
            };
            
            updateBoostTimer();
            showEvent({
                name: '📺 Реклама просмотрена!',
                message: data.message,
                type: 'bonus'
            });
        } else {
            showEvent({
                name: '⏰ Реклама недоступна',
                message: data.message,
                type: 'penalty'
            });
        }
    } catch (error) {
        console.error('Ошибка активации буста:', error);
    }
}

function updateBoostTimer() {
    if (boostTimer) clearInterval(boostTimer);
    
    boostTimer = setInterval(() => {
        if (!activeBoost) {
            clearInterval(boostTimer);
            updateBoostDisplay(0);
            return;
        }
        
        const remaining = Math.max(0, (activeBoost.endTime - Date.now()) / 1000);
        updateBoostDisplay(remaining);
        
        if (remaining <= 0) {
            activeBoost = null;
            clearInterval(boostTimer);
        }
    }, 100);
}

function updateBoostDisplay(remaining) {
    const display = document.getElementById('boostDisplay');
    if (display) {
        if (activeBoost && remaining > 0) {
            display.textContent = '🔥 Буст x2: ' + remaining.toFixed(1) + 'с';
            display.style.display = 'block';
        } else {
            display.style.display = 'none';
        }
    }
}

async function buySkin(skinId) {
    try {
        const response = await fetch('/api/monetization/buy-skin/' + skinId, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            gameState.coins = data.coins;
            gameState.active_skin = skinId;
            updateStats();
            updateDogeSkin(data.skin);
            showEvent({
                name: '🎨 Новый скин!',
                message: data.message,
                type: 'bonus'
            });
        } else {
            showEvent({
                name: '❌ Ошибка',
                message: data.message,
                type: 'penalty'
            });
        }
    } catch (error) {
        console.error('Ошибка покупки скина:', error);
    }
}

function updateDogeSkin(skin) {
    const dogeEmoji = document.getElementById('dogeEmoji');
    if (!dogeEmoji) return;
    
    const skinEmojis = {
        'golden_doge': '🦊',
        'cyber_doge': '🤖',
        'cosmic_doge': '🌌',
        'default': '🐕'
    };
    
    dogeEmoji.textContent = skinEmojis[skin.id] || '🐕';
    
    dogeEmoji.style.filter = 'none';
    if (skin.id === 'golden_doge') {
        dogeEmoji.style.filter = 'drop-shadow(0 0 20px rgba(255, 215, 0, 0.8))';
    } else if (skin.id === 'cyber_doge') {
        dogeEmoji.style.filter = 'drop-shadow(0 0 20px rgba(0, 255, 255, 0.8)) hue-rotate(90deg)';
    } else if (skin.id === 'cosmic_doge') {
        dogeEmoji.style.filter = 'drop-shadow(0 0 30px rgba(138, 43, 226, 0.8))';
    }
}

function renderSkins(skins) {
    const skinsPanel = document.getElementById('skinsPanel');
    if (!skinsPanel) return;
    
    skinsPanel.innerHTML = '<h4>🎨 Скины Doge</h4>';
    
    for (const [id, skin] of Object.entries(skins)) {
        const skinCard = document.createElement('div');
        skinCard.className = 'skin-card';
        skinCard.innerHTML = 
            '<span class="skin-name">' + skin.name + '</span>' +
            '<span class="skin-bonus">x' + skin.bonus + ' к кликам</span>' +
            '<span class="skin-cost">💰 ' + skin.cost.toLocaleString() + '</span>';
        skinCard.addEventListener('click', () => buySkin(id));
        skinsPanel.appendChild(skinCard);
    }
}