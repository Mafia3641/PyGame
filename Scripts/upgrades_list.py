# Dictionary of available upgrades
# Keys are unique identifiers, values are dictionaries with upgrade details.

UPGRADES = {
    'hp_boost_1': {
        'title': "Vitality Boost",
        'description': "Slightly increases your maximum health.",
        'icon': "Sprites/Upgrades/Upgrade_icons/heart.png",
        'stats': {'max_hp': 20} # Stat to change: Amount
    },
    'damage_boost_1': {
        'title': "Sharpened Edge",
        'description': "Increases your base weapon damage.",
        'icon': "Sprites/Upgrades/Upgrade_icons/upgrade_physical_damage.png",
        'stats': {'damage': 5}
    },
    'speed_boost_1': {
        'title': "Fleet Footed",
        'description': "Increases your movement speed.",
        'icon': "Sprites/Upgrades/Upgrade_icons/upgrade_speed.png",
        'stats': {'speed': 30} # Assuming player has a 'speed' attribute
    },
    'xp_gain_boost_1': {
        'title': "Quick Learner",
        'description': "Gain slightly more experience from defeating enemies.",
        'icon': "Sprites/Upgrades/Upgrade_icons/book.png",
        'stats': {'xp_multiplier': 0.1} # Example: +10% XP gain
    },
     'attack_speed_boost_1': {
        'title': "Rapid Strikes",
        'description': "Increases your attack speed slightly.",
        'icon': "Sprites/Upgrades/Upgrade_icons/glove.png", 
        # Needs modification in Weapon stats, e.g., decreasing cooldown
        'stats': {'attack_cooldown_mult': 0.95} # Example: 5% reduction
    },
    'max_mana_boost_1': {
        'title': "Arcane Reserves",
        'description': "Increases your maximum mana by 20%.",
        'icon': "Sprites/Upgrades/Upgrade_icons/upgrade_max_mana.png",
        'stats': {'max_mana_mult': 1.20} # Increase by 20%
    },
}

def get_upgrade_data(upgrade_name):
    """Safely retrieves upgrade data by name."""
    return UPGRADES.get(upgrade_name)

def get_all_upgrade_names():
    """Returns a list of all available upgrade names."""
    return list(UPGRADES.keys())



