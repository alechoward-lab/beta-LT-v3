"""
Hero Pairings – 2 Player Synergy

Pairings are primarily based on baseline stats (indices 0–7).
Boons and conditional bonuses may be referenced ONLY in explicit rules.
"""

# ----------------------------------------
# Tuning Variables
# ----------------------------------------
TARGET = 2
BASE_STAT_COUNT = 8

# Stat indices (global stat array)
# [0] economy
# [1] tempo
# [2] card value
# [3] survivability
# [4] villain damage
# [5] threat removal
# [6] reliability
# [7] minion control
# [8] control boon
# [9] support boon
# [10] broken builds boon
# [11] late game boon
# [12] simplicity
# [13] status cards
# [14] multiplayer consistency boon

TEMPO_INDEX = 1
SURVIVABILITY_INDEX = 3
THWART_INDEX = 5

SUPPORT_INDEX = 9          # boon
LATE_GAME_INDEX = 11       # boon

# Synergy weights
TEMPO_PAIR_BONUS = 0.25
LATE_GAME_THWART_BONUS = 0.20
BLOCKING_SUPPORT_BONUS = 0.25

POWER_DISINCENTIVE = 0.65
WEAK_PAIR_DISINCENTIVE = 0.75


# ----------------------------------------
# Imports
# ----------------------------------------
import streamlit as st
import numpy as np
from copy import deepcopy

from default_heroes import default_heroes
from hero_image_urls import hero_image_urls
from preset_options import preset_options


# ----------------------------------------
# Load hero data
# ----------------------------------------
heroes = deepcopy(default_heroes)
hero_names = list(heroes.keys())


# ----------------------------------------
# Compute GENERAL POWER (boons INCLUDED)
# ----------------------------------------
general_weights = np.array(preset_options["General Power: 2 Player"])

general_scores = {
    hero: float(np.dot(stats, general_weights))
    for hero, stats in heroes.items()
}

gp_values = np.array(list(general_scores.values()))
gp_mean = gp_values.mean()
gp_std = gp_values.std()

STRONG_HERO_THRESHOLD = gp_mean + 0.5 * gp_std
WEAK_HERO_THRESHOLD = gp_mean - 0.5 * gp_std


# ----------------------------------------
# Select primary hero
# ----------------------------------------
hero_A = st.selectbox("Select a hero to view pairings:", hero_names)

stats_A = heroes[hero_A]
base_stats_A = stats_A[:BASE_STAT_COUNT]
power_A = general_scores[hero_A]


# ----------------------------------------
# Identify Hero A weaknesses (baseline only)
# ----------------------------------------
needs = np.maximum(0, TARGET - base_stats_A)


# ----------------------------------------
# Score partner heroes
# ----------------------------------------
scores = {}

for hero_B, stats_B in heroes.items():
    if hero_B == hero_A:
        continue

    base_stats_B = stats_B[:BASE_STAT_COUNT]
    power_B = general_scores[hero_B]

    synergy_score = 0.0

    # ----------------------------------
    # 1. Weakness coverage
    # ----------------------------------
    usable_strengths = np.minimum(
        np.maximum(0, base_stats_B),
        needs
    )

    if np.sum(needs) > 0:
        synergy_score += np.dot(needs, usable_strengths) / np.sum(needs)

    # ----------------------------------
    # 2. Tempo balance (early ↔ late)
    # ----------------------------------
    tempo_mismatch = abs(
        base_stats_A[TEMPO_INDEX] - base_stats_B[TEMPO_INDEX]
    )
    synergy_score += TEMPO_PAIR_BONUS * tempo_mismatch

    # ----------------------------------
    # 3. Late-game hero + high-thwart partner
    # ----------------------------------
    if stats_A[LATE_GAME_INDEX] > TARGET:
        if base_stats_B[THWART_INDEX] > TARGET:
            synergy_score += (
                LATE_GAME_THWART_BONUS * base_stats_B[THWART_INDEX]
            )

    # ----------------------------------
    # 4. Low survivability + blocker/support
    # ----------------------------------
    if base_stats_A[SURVIVABILITY_INDEX] < TARGET:
        blocking_value = (
            max(0, base_stats_B[SURVIVABILITY_INDEX]) +
            max(0, stats_B[SUPPORT_INDEX])
        )
        synergy_score += BLOCKING_SUPPORT_BONUS * blocking_value

    # ----------------------------------
    # 5. Strong + strong disincentive
    # ----------------------------------
    if power_A >= STRONG_HERO_THRESHOLD and power_B >= STRONG_HERO_THRESHOLD:
        synergy_score *= POWER_DISINCENTIVE

    # ----------------------------------
    # 6. Weak + weak disincentive
    # ----------------------------------
    if power_A <= WEAK_HERO_THRESHOLD and power_B <= WEAK_HERO_THRESHOLD:
        synergy_score *= WEAK_PAIR_DISINCENTIVE

    scores[hero_B] = synergy_score


# ----------------------------------------
# Tiering
# ----------------------------------------
vals = np.array(list(scores.values()))
mean, std = vals.mean(), vals.std()

thr_S = mean + 1.5 * std
thr_A = mean + 0.5 * std
thr_B = mean - 0.5 * std
thr_C = mean - 1.5 * std

tiers = {"S": [], "A": [], "B": [], "C": [], "D": []}

for hero, sc in scores.items():
    if sc >= thr_S:
        tiers["S"].append(hero)
    elif sc >= thr_A:
        tiers["A"].append(hero)
    elif sc >= thr_B:
        tiers["B"].append(hero)
    elif sc >= thr_C:
        tiers["C"].append(hero)
    else:
        tiers["D"].append(hero)
