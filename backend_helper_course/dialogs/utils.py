import numpy as np


def centered(v):
    arr = np.array(v, dtype=float)
    return arr - arr.mean()


def similarity(u, v, alpha=0.5):
    u_clean = [1 if x is None else x for x in u]
    v_clean = [1 if x is None else x for x in v]
    u_arr = np.array(u_clean, dtype=float)
    v_arr = np.array(v_clean, dtype=float)
    u0 = u_arr - u_arr.mean()
    v0 = v_arr - v_arr.mean()
    cos = np.dot(u0, v0) / (np.linalg.norm(u0) * np.linalg.norm(v0) + 1e-8)
    eu = np.linalg.norm(u_arr - v_arr)
    maxd = np.linalg.norm(np.array([1.0] * len(u_arr)))
    lvl = 1.0 - eu / (maxd + 1e-8)
    return alpha * cos + (1 - alpha) * lvl
