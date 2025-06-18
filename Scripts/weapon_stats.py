# weapon_stats.py

# Store offset as a list [x, y] for easy definition
# Store melee attack sprites as a pattern and count

WEAPON_STATS = {
    'starter_sword': {
        'type': 'melee',
        'offset': [20, 10], 
        'scale': 2,
        'idle_sprite_name': "Weapons/MeleeWeapons/StarterSword/starter_sword_idle",
        'attack_sprite_pattern': "Weapons/MeleeWeapons/StarterSword/starter_sword_attack_{}",
        'attack_sprite_count': 6, # Number of attack frames (1 to 6)
        'damage': 50,
        'attack_range': 50,
        'cooldown': 1.0,
        'repulsion': 1.5, 
        'frame_duration': 0.1,
        'attack_arc': 120
    },
    'pistol': {
        'type': 'range',
        'offset': [15, 10],
        'scale': 2,
        'weapon_idle_sprite': "Weapons/RangeWeapons/Pistol/pistol_idle", # Corrected key name
        'projectile_speed': 600,
        'projectile_sprite_name': "Weapons/bullet",
        'damage': 30,
        'cooldown': 0.5,
        'accuracy': 5,
        'repulsion': 0.6,
        'mana_cost': 5,
        'close_quarters_range': 20, # The radius for the point-blank melee check
        'close_quarters_arc': 60   # The arc in degrees for the check
    },
    'rifle': {
        'type': 'range',
        'offset': [5, 5], 
        'weapon_idle_sprite': "Weapons/RangeWeapons/Rifle/rifle_idle", # Assume idle sprite exists
        'projectile_speed': 800,
        'projectile_sprite_name': "Weapons/rifle_bullet",
        'damage': 12,
        'cooldown': 0.2,
        'accuracy': 2,
        'repulsion': 0.2 
    }
}
