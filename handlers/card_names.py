import os

TYPE_LABELS = {
    "akatsuki": "🟥 Акацуки",
    "biju": "🟨 Биджу",
}

def pretty_card_name(filename: str) -> str:
    """
    akatsuki_itachi_2.jpg -> Итачи (🟥 Акацуки) II
    biju_kyuubi.jpg -> Кьюби (🟨 Биджу)
    naruto.jpg -> Наруто
    """
    base = os.path.splitext(os.path.basename(filename))[0]  # akatsuki_itachi_2

    level2 = False
    if base.endswith("_2"):
        level2 = True
        base = base[:-2]  # akatsuki_itachi

    card_type = None
    for prefix in TYPE_LABELS.keys():
        if base.startswith(prefix + "_"):
            card_type = prefix
            base = base[len(prefix) + 1:]  # itachi
            break

    # имя: itachi -> Itachi, shikamaru_nara -> Shikamaru Nara
    name = base.replace("_", " ").strip()
    if name:
        name = name[0].upper() + name[1:]

    # добавляем метку типа и уровень
    suffix_parts = []
    if card_type:
        suffix_parts.append(f"({TYPE_LABELS[card_type]})")
    if level2:
        suffix_parts.append("II")

    if suffix_parts:
        return f"{name} {' '.join(suffix_parts)}"
    return name
