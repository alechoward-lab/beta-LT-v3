import numpy as np
preset_options = {  #                                 e, t, cv,s, d, th,re,mi,c, su,br,lg,si,sc,mu
    "General Power: 2 Player":               np.array([4, 2, 2, 2, 1, 2, 3, 1, 2, 2, 2, 1, 0, 0, 1, 0]),
    "Multiplayer: 3 Player":                 np.array([4, 1, 2, 2, 1, 5, 2, 3, 1, 7, 2, 5, 0, 0, 6, 0]),
    "Multiplayer: 4 Player":                 np.array([4, 1, 2, 2, 1, 5, 2, 3, 1, 7, 2, 7, 0, 0, 10, 0]),
    "Solo (No Rush)":                       np.array([8, 3, 2, 4, 2, 3, 4, 1, 2, 0, 2, 3, 0, 4, -5, 0]),
    "Solo: Rush":                            np.array([0, 5, 0, 2, 5, 0, 0, 0, 0, 0, 0,-3, 0, 0, 0, 0]),
    "Solo: Final Boss Steady/Stalwart":      np.array([10,1, 3, 6, 2, 3, 2, 1, 3, 0, 2, 2, 0, -7, -7, 0]),
    "Beginner Friendly Heroes":             np.array([2, 1, 0, 1, 0, 0, 5, 0, 0, 0, 0, -1, 10, 1, 0, 0])
}