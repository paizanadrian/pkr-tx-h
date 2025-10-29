import random
from itertools import combinations
import streamlit as st

# ----------------------------
NUM_PLAYERS = 10
HERO = 7  # index uman (1-based)
SEED = None  # pune un număr (ex. 42) pentru joc repetabil
# ----------------------------

RANKS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
SUITS = "♣♦♥♠"
RED_SUITS = {"♦", "♥"}
RANK_VAL = {r: i for i, r in enumerate(RANKS, start=2)}
VAL_RANK = {v: r for r, v in RANK_VAL.items()}

# ===== util deck =====
def make_deck():
    return [r + s for r in RANKS for s in SUITS]

def riffle_shuffle(deck, rng, times=5):
    for _ in range(times):
        cut = rng.randint(18, 34)
        left, right = deck[:cut], deck[cut:]
        inter = []
        while left or right:
            tl = rng.randint(1, 3); tr = rng.randint(1, 3)
            inter.extend(left[:tl]); left = left[tl:]
            inter.extend(right[:tr]); right = right[tr:]
        deck[:] = inter
        k = rng.randint(5, 15)
        deck[:] = deck[-k:] + deck[:-k]

def burn(deck):
    if deck: deck.pop(0)

def seat_order(dealer_pos):
    return [(dealer_pos + 1 + i) % NUM_PLAYERS for i in range(NUM_PLAYERS)]

def deal_hole_cards(deck, num_players, dealer_pos):
    hands = [[] for _ in range(num_players)]
    order = seat_order(dealer_pos)
    for p in order: hands[p].append(deck.pop(0))
    for p in order: hands[p].append(deck.pop(0))
    return hands

def deal_board(deck):
    burn(deck); flop = [deck.pop(0) for _ in range(3)]
    burn(deck); turn = deck.pop(0)
    burn(deck); river = deck.pop(0)
    return flop, turn, river

# ===== evaluare =====
def card_vals(cards):
    return sorted([RANK_VAL[c[:-1]] for c in cards], reverse=True)

def is_flush(cards):
    suits = [c[-1] for c in cards]
    for s in SUITS:
        if suits.count(s) == 5:
            return True, s
    return False, None

def is_straight(vals):
    u = sorted(set(vals), reverse=True)
    if 14 in u: u.append(1)  # A low
    for i in range(len(u) - 4):
        seq = u[i:i+5]
        if seq[0] - seq[4] == 4:
            return True, seq[0]
    return False, 0

# score tuple: (class, ...)  8=SF,7=Four,6=Full,5=Flush,4=Straight,3=Trips,2=TwoPair,1=Pair,0=High
def evaluate_5(cards):
    vals = card_vals(cards)
    freq = {}
    for v in vals: freq[v] = freq.get(v, 0) + 1
    groups = sorted(freq.items(), key=lambda x: (x[1], x[0]), reverse=True)
    counts = [g[1] for g in groups]

    flush, flush_suit = is_flush(cards)
    straight, top_st = is_straight(vals)

    # straight flush
    if flush:
        flush_vals = card_vals([c for c in cards if c[-1] == flush_suit])
        sf, sf_top = is_straight(flush_vals)
        if sf: return (8, sf_top)

    # four
    if 4 in counts:
        four = groups[0][0]
        kicker = max([v for v in vals if v != four]) if any(v != four for v in vals) else 0
        return (7, four, kicker)

    # full
    if 3 in counts and 2 in counts:
        trips = [v for v, c in groups if c == 3][0]
        pair  = [v for v, c in groups if c == 2][0]
        return (6, trips, pair)

    # flush
    if flush:
        return (5, sorted(vals, reverse=True))

    # straight
    if straight:
        return (4, top_st)

    # trips
    if 3 in counts:
        trips = [v for v, c in groups if c == 3][0]
        kickers = [v for v in vals if v != trips][:2]
        return (3, trips, kickers)

    # two pair
    pairs = [v for v, c in groups if c == 2]
    if len(pairs) >= 2:
        top2 = pairs[:2]
        kicker = [v for v in vals if v not in top2][0]
        return (2, top2, kicker)

    # pair
    if 2 in counts:
        pair = [v for v, c in groups if c == 2][0]
        kickers = [v for v in vals if v != pair][:3]
        return (1, pair, kickers)

    # high
    return (0, vals)

def best_of_seven(cards7):
    best = None
    for combo in combinations(cards7, 5):
        score = evaluate_5(combo)
        if (best is None) or (score > best):
            best = score
    return best

def best_of_seven_with_combo(cards7):
    best_score, best_combo = None, None
    for combo in combinations(cards7, 5):
        score = evaluate_5(combo)
        if (best_score is None) or (score > best_score):
            best_score, best_combo = score, combo
    return best_score, list(best_combo)

HAND_NAMES = {
    8: "Chintă de culoare (Straight Flush)",
    7: "Careu (Four of a Kind)",
    6: "Full (Full House)",
    5: "Culoare (Flush)",
    4: "Chintă (Straight)",
    3: "Trei de un fel / Trips (Three of a Kind)",
    2: "Două perechi (Two Pair)",
    1: "O pereche (One Pair)",
    0: "Carte mare (High Card)",
}

def to_rank_str(v): return VAL_RANK[v]

def straight_str(topv):
    if topv == 5: return "5–A"
    return "–".join(to_rank_str(topv - i) for i in range(5))

def describe_score(score):
    t = score[0]
    if t == 8: return f"{HAND_NAMES[t]} – {straight_str(score[1])}"
    if t == 7: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} cu kicker {to_rank_str(score[2])}"
    if t == 6: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} peste {to_rank_str(score[2])}"
    if t == 5: return f"{HAND_NAMES[t]} – " + " ".join(to_rank_str(v) for v in score[1][:5])
    if t == 4: return f"{HAND_NAMES[t]} – {straight_str(score[1])}"
    if t == 3: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} cu kicker(e) " + " ".join(to_rank_str(v) for v in score[2])
    if t == 2:
        p1, p2 = to_rank_str(score[1][0]), to_rank_str(score[1][1])
        return f"{HAND_NAMES[t]} – {p1} și {p2}, kicker {to_rank_str(score[2])}"
    if t == 1: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} cu kicker(e) " + " ".join(to_rank_str(v) for v in score[2])
    return f"{HAND_NAMES[0]} – " + " ".join(to_rank_str(v) for v in score[1][:5])

def winner_details_with_combos(hands, board5):
    scored, combos, best = [], [], None
    for h in hands:
        s, combo = best_of_seven_with_combo(h + board5)
        scored.append(s); combos.append(combo)
        if best is None or s > best: best = s
    winners = [i for i, s in enumerate(scored) if s == best]
    desc = [describe_score(scored[i]) for i in winners]
    winner_combos = [combos[i] for i in winners]
    return winners, desc, winner_combos

# ===== mapări legendă =====
# 1=Royal, 2=StraightFlush, 3=Four, 4=Full, 5=Flush, 6=Straight, 7=Trips, 8=TwoPair, 9=Pair, 10=High
LEGEND_TEXT = {
    1: "Chintă roială (Royal Flush)",
    2: "Chintă de culoare (Straight Flush)",
    3: "Careu (Four of a Kind)",
    4: "Full (Full House)",
    5: "Culoare (Flush)",
    6: "Chintă (Straight)",
    7: "Trei de un fel / Trips (Three of a Kind)",
    8: "Două perechi (Two Pair)",
    9: "O pereche (One Pair)",
    10:"Carte mare (High Card)",
}

def score_to_legend_ids(score):
    ids = set()
    cls = score[0]
    if cls == 8:
        top = score[1]
        ids.add(1 if top == 14 else 2)
    elif cls == 7: ids.add(3)
    elif cls == 6: ids.add(4)
    elif cls == 5: ids.add(5)
    elif cls == 4: ids.add(6)
    elif cls == 3: ids.add(7)
    elif cls == 2: ids.add(8)
    elif cls == 1: ids.add(9)
    elif cls == 0: ids.add(10)
    return ids

def legend_possibles_on_river(board5):
    deck = make_deck()
    remaining = [c for c in deck if c not in board5]
    found = set()
    n = len(remaining)  # 47
    for a in range(n):
        for b in range(a+1, n):
            hole = [remaining[a], remaining[b]]
            sc = best_of_seven(board5 + hole)
            found |= score_to_legend_ids(sc)
            if len(found) == 10:
                return sorted(found)
    return sorted(found)

# ===== UI helpers (HTML) =====
def card_html(card, big=False, highlight=False, border=False):
    rank, suit = card[:-1], card[-1]
    color = "#d00" if suit in RED_SUITS else "#111"
    bg = "#d9ffd9" if highlight else "#fff"
    pad = "8px 10px" if big else "4px 8px"
    font = "700 26px/1.0 'Segoe UI', system-ui" if big else "700 16px/1.0 'Segoe UI', system-ui"
    border_css = "2px solid #2e7d32" if border else "1px solid #bbb"
    # font e definit dar nu-l folosim explicit în style (browser-ul aplică fontul paginii)
    return f"<span style='display:inline-block;margin:2px;padding:{pad};background:{bg};color:{color};border:{border_css};border-radius:6px'>{rank}{suit}</span>"

def hidden_html(big=False):
    pad = "8px 10px" if big else "4px 8px"
    font = "700 26px/1.0 'Segoe UI', system-ui" if big else "700 16px/1.0 'Segoe UI', system-ui"
    return f"<span style='display:inline-block;margin:2px;padding:{pad};background:#fff;color:#111;border:1px solid #bbb;border-radius:6px'>🂠</span>"

def legend_lines(ids):
    if not ids: return "—"
    return "\n".join(f"{i}) {LEGEND_TEXT[i]}" for i in range(1, 11) if i in ids)

# ====== Streamlit app ======
st.set_page_config(page_title="Texas Hold'em – 10 jucători", layout="wide")

# init state
if "state" not in st.session_state:
    st.session_state.state = {}
if "seed" not in st.session_state:
    st.session_state.seed = SEED

def new_hand():
    rng = random.Random(st.session_state.seed)
    deck = make_deck()
    riffle_shuffle(deck, rng)
    dealer = rng.randrange(NUM_PLAYERS)
    hands = deal_hole_cards(deck, NUM_PLAYERS, dealer)
    flop, turn, river = deal_board(deck)
    st.session_state.state = {
        "dealer": dealer + 1,  # 1-based
        "hands": hands,
        "flop": flop,
        "turn": turn,
        "river": river,
        "stage": "flop",
        "winners": [],
        "winner_combos": [],
        "possible_river": None,
        "show": False
    }

def progress_step():
    s = st.session_state.state
    stage = s["stage"]
    if stage == "flop":
        s["stage"] = "turn"
    elif stage == "turn":
        s["stage"] = "river"
        board5 = s["flop"] + [s["turn"], s["river"]]
        s["possible_river"] = legend_possibles_on_river(board5)
    elif stage == "river":
        s["stage"] = "show"
        s["show"] = True
        board5 = s["flop"] + [s["turn"], s["river"]]
        winners, descriptions, winner_combos = winner_details_with_combos(s["hands"], board5)
        s["winners"] = winners
        s["winner_combos"] = winner_combos
        s["winner_descriptions"] = descriptions

# Header (fără butoane ca să evităm dublurile)
left, mid, right = st.columns([1, 2, 1])
with left:
    pass
with mid:
    st.title("Texas Hold'em – masă cu 10 jucători")
    seed_in = st.text_input("Seed (adauga un numar, opțional, pentru repetabilitate)",
                            value=str(st.session_state.seed) if st.session_state.seed is not None else "")
    if seed_in.strip() == "":
        st.session_state.seed = None
    else:
        try:
            st.session_state.seed = int(seed_in)
        except ValueError:
            st.info("Seed-ul trebuie să fie un număr întreg sau gol.")
with right:
    pass

# Ensure state exists
if not st.session_state.state:
    new_hand()

s = st.session_state.state
stage = s["stage"]
show = s["show"]
winners = set(s.get("winners", []))
winner_combos = s.get("winner_combos", [])

st.caption(f"**Buton (Dealer):** Jucătorul {s['dealer']} • **HERO:** Jucătorul {HERO}")

# ==================== BOARD (centrat) + butoane pe același rând ====================
# pregătim label-ul pentru butonul din dreapta
label = (
    "Arată Turn" if stage == "flop" else
    ("Arată River" if stage == "turn" else
     ("Arată cărțile" if stage == "river" else "Final"))
)
disabled = stage == "show"

row_left, row_center, row_right = st.columns([1, 6, 1], gap="small")

with row_left:
    if st.button("🃏 Mână nouă", key="btn_new_board", use_container_width=True):
        new_hand()
        st.rerun()

with row_center:
    # titlu centrat
    st.markdown(
        "<h3 style='text-align:center;margin:0.5rem 0'>Board (Flop • Turn • River)</h3>",
        unsafe_allow_html=True
    )

    # cărțile de pe board (cu highlight dacă fac parte din combo câștigător)
    parts = []
    board_highlight_set = set()
    if show and winner_combos:
        all_board = s["flop"] + [s["turn"], s["river"]]
        for combo in winner_combos:
            for c in combo:
                if c in all_board:
                    board_highlight_set.add(c)

    # Flop
    for c in s["flop"]:
        parts.append(card_html(
            c, big=True,
            highlight=show and c in board_highlight_set,
            border=show and c in board_highlight_set
        ))

    # Turn
    if stage in ("turn", "river", "show"):
        c = s["turn"]
        parts.append(card_html(
            c, big=True,
            highlight=show and c in board_highlight_set,
            border=show and c in board_highlight_set
        ))
    else:
        parts.append(hidden_html(big=True))

    # River
    if stage in ("river", "show"):
        c = s["river"]
        parts.append(card_html(
            c, big=True,
            highlight=show and c in board_highlight_set,
            border=show and c in board_highlight_set
        ))
    else:
        parts.append(hidden_html(big=True))

    # rand de cărți centrat
    st.markdown(
        f"<div style='text-align:center'>{' '.join(parts)}</div>",
        unsafe_allow_html=True
    )

with row_right:
    if st.button(label, key="btn_prog_board", disabled=disabled, use_container_width=True):
        progress_step()
        st.rerun()

st.divider()
# ================================================================================

# HERO
is_hero_winner = (HERO-1) in winners
hero_combo_set = set()
if show and winner_combos and is_hero_winner:
    for w_i, w_idx in enumerate(s["winners"]):
        if w_idx == HERO-1:
            hero_combo_set = set(s["winner_combos"][w_i]); break

st.subheader("Mâna ta – Jucătorul 7 (TU)" + (" 🏆" if is_hero_winner else ""))
hero_cards = s["hands"][HERO-1]
st.markdown(" ".join(card_html(c, big=True, highlight=(show and c in hero_combo_set) or is_hero_winner) for c in hero_cards), unsafe_allow_html=True)

st.divider()

# OTHERS – afișare pe 5 coloane (2 rânduri pentru 10 jucători)
st.subheader("Ceilalți jucători")

cols = st.columns(5, gap="small")

def render_player(idx, column):
    is_winner = (stage == "show") and (idx in winners)
    combo_set = set()
    if show and is_winner:
        for w_i, w_idx in enumerate(s["winners"]):
            if w_idx == idx:
                combo_set = set(s["winner_combos"][w_i])
                break

    title = f"Jucător {idx+1}" + (" (Dealer)" if (idx+1) == s["dealer"] else "")
    if is_winner:
        title += " – 🏆"

    with column:
        st.markdown(f"**{title}**")
        if stage == "show":
            cards_html = " ".join(
                card_html(c, highlight=(c in combo_set) or is_winner)
                for c in s["hands"][idx]
            )
        else:
            cards_html = " ".join(hidden_html() for _ in range(2))
        st.markdown(cards_html, unsafe_allow_html=True)
        st.write("")

# parcurgem toți jucătorii, dar îl sărim pe HERO
visible_indices = [i for i in range(NUM_PLAYERS) if i != (HERO - 1)]
for n, idx in enumerate(visible_indices):
    col = cols[n % 5]  # distribuție pe 5 coloane
    render_player(idx, col)

# Rezultate la SHOW
if stage == "show":
    # obținem scorul (clasa 0-8) pentru fiecare câștigător
    board5 = s["flop"] + [s["turn"], s["river"]]
    scores = [best_of_seven(s["hands"][w] + board5) for w in s["winners"]]
    hand_ids = [list(score_to_legend_ids(sc))[0] for sc in scores]

    if len(s["winners"]) == 1:
        who = s["winners"][0] + 1
        title = f"🏆 **Câștigător: Jucătorul {who}** — {hand_ids[0]}) {LEGEND_TEXT[hand_ids[0]]}"
        st.success(title)
    else:
        st.success("🏆 **Câștigători:**")
        for i, w in enumerate(s["winners"]):
            st.write(f"• Jucătorul {w+1} — {hand_ids[i]}) {LEGEND_TEXT[hand_ids[i]]}")

    st.info("\n".join(f"• Jucătorul {w + 1} — {desc}" for w, desc in zip(s["winners"], s.get("winner_descriptions", []))))

# Bottom: legendă + posibil doar la River
left, right = st.columns(2)
with left:
    st.markdown("### Ordinea mâinilor câștigătoare (de la cea mai puternică la cea mai slabă)")
    legend_txt = (
        "1) Chintă roială (Royal Flush) – A-K-Q-J-10, toate de aceeași culoare\n"
        "2) Chintă de culoare (Straight Flush)\n"
        "3) Careu (Four of a Kind)\n"
        "4) Full (Full House)\n"
        "5) Culoare (Flush)\n"
        "6) Chintă (Straight)\n"
        "7) Trei de un fel / Trips (Three of a Kind)\n"
        "8) Două perechi (Two Pair)\n"
        "9) O pereche (One Pair)\n"
        "10) Carte mare (High Card)"
    )
    st.text(legend_txt)
with right:
    st.markdown("### Combinații posibile câștigătoare (doar la River)")
    if s.get("possible_river"):
        st.text(legend_lines(s["possible_river"]))
    else:
        st.text("—")
