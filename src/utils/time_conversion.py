def convert_ms_to_hh_mm_ss(ms: int) -> tuple[int, int, int]:
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return h, m, s
