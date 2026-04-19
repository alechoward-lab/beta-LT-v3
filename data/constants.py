"""
Shared constants used across the app.
Single source of truth for stat names, tier colors, and default weights.
"""

STAT_NAMES = [
    "Economy",
    "Tempo",
    "Card Value",
    "Survivability",
    "Villain Damage",
    "Threat Removal",
    "Reliability",
    "Minion Control",
    "Control Boon",
    "Support Boon",
    "Unique Broken Builds Boon",
    "Late Game Power Boon",
    "Simplicity",
    "Stun/Confuse Boon",
    "Multiplayer Consistency Boon",
]

TIER_COLORS = {
    "S": "#FF69B4",
    "A": "#9B59B6",
    "B": "#3CB371",
    "C": "#FF8C00",
    "D": "#E74C3C",
}

DEFAULT_WEIGHTS = {
    "Economy": 4,
    "Tempo": 2,
    "Card Value": 2,
    "Survivability": 2,
    "Villain Damage": 1,
    "Threat Removal": 2,
    "Reliability": 3,
    "Minion Control": 1,
    "Control Boon": 2,
    "Support Boon": 2,
    "Unique Broken Builds Boon": 1,
    "Late Game Power Boon": 1,
    "Simplicity": 0,
    "Stun/Confuse Boon": 0,
    "Multiplayer Consistency Boon": 0,
}
