# weapon_stats.py

# Store offset as a list [x, y] for easy definition
# Store melee attack sprites as a pattern and count

WEAPON_STATS = {
    'starter_sword': {
        'type': 'melee',
        'offset': [5, 2], 
        'idle_sprite_name': "Weapons/MeleeWeapons/StarterSword/starter_sword_idle",
        'attack_sprite_pattern': "Weapons/MeleeWeapons/StarterSword/starter_sword_attack{}",
        'attack_sprite_count': 4, # Number of attack frames (1 to 4)
        'damage': 10,
        'attack_range': 40,
        'cooldown': 0.5,
        'repulsion': 1.0, 
        'frame_duration': 0.1
    },
    'pistol': {
        'type': 'range',
        'offset': [5, 5], 
        'weapon_idle_sprite': "Weapons/RangeWeapons/Pistol/pistol_idle", # Corrected key name
        'projectile_speed': 600,
        'projectile_sprite_name': "Weapons/bullet",
        'damage': 8,
        'cooldown': 0.3,
        'accuracy': 5,
        'repulsion': 0.6 
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
