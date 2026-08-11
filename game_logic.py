import random
import math
import time

# ============ ЭТАПЫ ИГРЫ ============
STAGES = {
    1: {
        'name': '🖥️ Домашний майнер',
        'description': 'Ты майнишь DogeCoin на своём ноутбуке. Мама жалуется на счета за электричество.',
        'threshold': 0,
        'background': '#1a1a2e'
    },
    2: {
        'name': '🏭 Гаражная ферма',
        'description': 'Ты арендовал гараж и заставил его видеокартами. Соседи думают, что это обогреватель.',
        'threshold': 500,
        'background': '#16213e'
    },
    3: {
        'name': '🏢 Промышленный майнинг',
        'description': 'Твой ЦОД охлаждается ветром с гор. DogeCoin стал серьёзным бизнесом.',
        'threshold': 5000,
        'background': '#0f3460'
    },
    4: {
        'name': '🌕 Lunar Doge Station',
        'description': 'Ты перенёс майнинг на Луну. Низкая температура = идеальное охлаждение!',
        'threshold': 50000,
        'background': '#533483'
    },
    5: {
        'name': '🚀 Межгалактический хайп',
        'description': 'Ты майнишь на чёрных дырах. Илон Маск ретвитнул твой прогресс.',
        'threshold': 500000,
        'background': '#e94560'
    }
}

# ============ УЛУЧШЕНИЯ ============
UPGRADES = {
    'better_gpu': {
        'name': '🎮 Игровая видеокарта',
        'description': '+1 к силе клика',
        'base_cost': 10,
        'cost_multiplier': 1.5,
        'effect_type': 'click_power',
        'effect_value': 1,
        'stage_required': 1,
        'flavor': 'Куплена на сэкономленные карманные деньги'
    },
    'energy_drink': {
        'name': '⚡ Энергетик "Doge Fuel"',
        'description': 'Критический клик: 10% шанс x3',
        'base_cost': 50,
        'cost_multiplier': 1.8,
        'effect_type': 'crit_chance',
        'effect_value': 0.10,
        'stage_required': 1,
        'flavor': 'Содержит экстракт луны и вау-эффект'
    },
    'auto_clicker': {
        'name': '🤖 Автокликер',
        'description': 'Автоматический клик каждую секунду',
        'base_cost': 100,
        'cost_multiplier': 1.4,
        'effect_type': 'auto_click',
        'effect_value': 0.5,
        'stage_required': 2,
        'flavor': 'Написан твоим другом на Python за пиццу'
    },
    'meme_magic': {
        'name': '✨ Магия мема',
        'description': 'Множитель всех доходов x2',
        'base_cost': 300,
        'cost_multiplier': 2.0,
        'effect_type': 'multiplier',
        'effect_value': 1.0,
        'stage_required': 2,
        'flavor': 'Чем смешнее мем, тем дороже монета'
    },
    'quantum_miner': {
        'name': '💎 Квантовый майнер',
        'description': 'Клики дают в 10 раз больше, но с вероятностью 50%',
        'base_cost': 1000,
        'cost_multiplier': 1.6,
        'effect_type': 'quantum',
        'effect_value': 10,
        'stage_required': 3,
        'flavor': 'Кот Шрёдингера одобряет этот майнинг'
    },
    'doge_army': {
        'name': '🐕 Армия Doge',
        'description': 'Тысячи сиба-ину майнят для тебя',
        'base_cost': 5000,
        'cost_multiplier': 1.3,
        'effect_type': 'auto_click',
        'effect_value': 50,
        'stage_required': 4,
        'flavor': 'Such mining, much profit, wow!'
    },
    'time_dilation': {
        'name': '⏰ Временная аномалия',
        'description': 'Замедляет время (ускоряет автоклик x3 на 10 сек)',
        'base_cost': 2000,
        'cost_multiplier': 2.5,
        'effect_type': 'active_skill',
        'effect_value': 3,
        'stage_required': 3,
        'flavor': '1 секунда здесь = 3 секунды майнинга'
    }
}

# ============ СОБЫТИЯ ============
EVENTS = [
    {
        'id': 'elon_tweet',
        'name': '🐦 Илон Маск твитнул!',
        'description': 'Elon Musk: "Doge to the moon!" 🚀',
        'effect': lambda user: {'coins': user['coins'] * 0.3, 'message': 'Курс взлетел! +30% к балансу!'},
        'type': 'bonus',
        'chance': 0.15
    },
    {
        'id': 'china_ban',
        'name': '🇨🇳 Китай запретил майнинг',
        'description': 'Все азиатские фермы отключились... Но твоя работает!',
        'effect': lambda user: {'coins': -user['coins'] * 0.15, 'message': 'Сложность упала! Но курс просел на 15%'},
        'type': 'crisis',
        'chance': 0.10
    },
    {
        'id': 'meme_viral',
        'name': '🔥 Твой мем стал вирусным!',
        'description': 'Твой Doge-мем попал в топ Reddit!',
        'effect': lambda user: {'coins': user['coins'] * 0.5, 'multiplier_bonus': 2.0, 'message': 'Мега-хайп! x2 монет на 30 секунд!'},
        'type': 'bonus',
        'chance': 0.08,
        'duration': 30
    },
    {
        'id': 'hacker_attack',
        'name': '👾 Хакерская атака',
        'description': 'Хакеры пытаются украсть твои DogeCoin!',
        'effect': lambda user: {'coins': -user['coins'] * 0.25, 'message': 'О нет! Украдено 25% монет! Нужен файрвол!'},
        'type': 'penalty',
        'chance': 0.12
    },
    {
        'id': 'mystery_box',
        'name': '🎁 Таинственный сундук',
        'description': 'Ты нашёл старый жёсткий диск с DogeCoin!',
        'effect': lambda user: {'coins': max(user['coins'] * 0.1, 100), 'message': 'Джекпот! Найден клад!'},
        'type': 'bonus',
        'chance': 0.05
    }
]

# ============ МОНЕТИЗАЦИЯ ============
MONETIZATION = {
    'ad_boost': {
        'id': 'ad_boost',
        'name': '📺 Рекламный буст',
        'description': 'Посмотри рекламу и получи x2 монет на 30 секунд',
        'type': 'ad',
        'cooldown': 300,
        'duration': 30,
        'multiplier': 2.0,
        'flavor': 'Реклама корма "Doge Chow" - such taste, much wow!',
        'real_world': 'Доход от рекламы (AdMob, Yandex Ads)'
    },
    'daily_reward': {
        'id': 'daily_reward',
        'name': '🎁 Ежедневный бонус',
        'description': 'Заходи каждый день и получай награду! Серия дней увеличивает бонус',
        'type': 'retention',
        'cooldown': 86400,
        'base_reward': 50,
        'streak_multiplier': 1.5,
        'flavor': 'Doge ждал тебя весь день!',
        'real_world': 'Удержание пользователей (Retention)'
    },
    'premium_skin': {
        'id': 'premium_skin',
        'name': '🎨 Премиум скины',
        'description': 'Особые скины для Doge за просмотр специальных предложений',
        'type': 'cosmetic',
        'skins': {
            'golden_doge': {'name': '🦊 Golden Doge', 'cost': 5000, 'bonus': 1.1},
            'cyber_doge': {'name': '🤖 Cyber Doge', 'cost': 10000, 'bonus': 1.2},
            'cosmic_doge': {'name': '🌌 Cosmic Doge', 'cost': 25000, 'bonus': 1.5}
        },
        'flavor': 'Выделяйся среди других майнеров!',
        'real_world': 'Платные косметические предметы (In-App Purchases)'
    }
}

STAGES_MONETIZATION = {
    1: ['ad_boost'],
    2: ['ad_boost', 'daily_reward'],
    3: ['ad_boost', 'daily_reward', 'premium_skin'],
    4: ['ad_boost', 'daily_reward', 'premium_skin'],
    5: ['ad_boost', 'daily_reward', 'premium_skin']
}

def calculate_upgrade_cost(upgrade_id, level):
    upgrade = UPGRADES[upgrade_id]
    return math.floor(upgrade['base_cost'] * (upgrade['cost_multiplier'] ** level))

def get_current_stage(coins):
    current_stage = 1
    for stage_id in sorted(STAGES.keys()):
        if coins >= STAGES[stage_id]['threshold']:
            current_stage = stage_id
    return current_stage

def calculate_click_value(user, upgrades):
    base = user['click_power']
    
    if random.random() < user['crit_chance']:
        base *= user['crit_multiplier']
        return base, True
    
    if upgrades.get('quantum_miner', 0) > 0:
        if random.random() < 0.5:
            base *= 10
            return base, 'quantum'
    
    return base, False

def check_event():
    roll = random.random()
    cumulative = 0
    for event in EVENTS:
        cumulative += event['chance']
        if roll <= cumulative:
            return event
    return None

def get_available_monetization(stage_id):
    available = {}
    for monetization_id in STAGES_MONETIZATION.get(stage_id, []):
        if monetization_id in MONETIZATION:
            available[monetization_id] = MONETIZATION[monetization_id]
    return available

def calculate_daily_reward(streak_days):
    base = MONETIZATION['daily_reward']['base_reward']
    multiplier = MONETIZATION['daily_reward']['streak_multiplier'] ** min(streak_days - 1, 7)
    return int(base * multiplier)

def apply_ad_boost(user):
    current_time = time.time()
    boost_end = current_time + MONETIZATION['ad_boost']['duration']
    return {
        'multiplier': MONETIZATION['ad_boost']['multiplier'],
        'boost_end': boost_end,
        'message': 'Рекламный буст активирован! x2 монет на 30 секунд!'
    }

def buy_premium_skin(user_id, skin_id):
    skin = MONETIZATION['premium_skin']['skins'].get(skin_id)
    if not skin:
        return None
    return {
        'skin': skin,
        'message': f'Скин "{skin["name"]}" куплен! Бонус к кликам: x{skin["bonus"]}'
    }