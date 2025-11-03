import random
from itertools import combinations
import streamlit as st
import pathlib

# ====== Load CSS ======
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/styles.css")
load_css(css_path)

# ----------------------------
NUM_PLAYERS = 10
HERO = 7  # index uman (1-based)
SEED = None
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
def card_vals(cards): return sorted([RANK_VAL[c[:-1]] for c in cards], reverse=True)

def is_flush(cards):
    suits = [c[-1] for c in cards]
    for s in SUITS:
        if suits.count(s) == 5: return True, s
    return False, None

def is_straight(vals):
    u = sorted(set(vals), reverse=True)
    if 14 in u: u.append(1)
    for i in range(len(u) - 4):
        seq = u[i:i+5]
        if seq[0] - seq[4] == 4:
            return True, seq[0]
    return False, 0

def evaluate_5(cards):
    vals = card_vals(cards)
    freq = {}
    for v in vals: freq[v] = freq.get(v, 0) + 1
    groups = sorted(freq.items(), key=lambda x: (x[1], x[0]), reverse=True)
    counts = [g[1] for g in groups]
    flush, flush_suit = is_flush(cards)
    straight, top_st = is_straight(vals)

    if flush:
        flush_vals = card_vals([c for c in cards if c[-1] == flush_suit])
        sf, sf_top = is_straight(flush_vals)
        if sf: return (8, sf_top)
    if 4 in counts:
        four = groups[0][0]
        kicker = max([v for v in vals if v != four]) if any(v != four for v in vals) else 0
        return (7, four, kicker)
    if 3 in counts and 2 in counts:
        trips = [v for v, c in groups if c == 3][0]
        pair  = [v for v, c in groups if c == 2][0]
        return (6, trips, pair)
    if flush: return (5, sorted(vals, reverse=True))
    if straight: return (4, top_st)
    if 3 in counts:
        trips = [v for v, c in groups if c == 3][0]
        kickers = [v for v in vals if v != trips][:2]
        return (3, trips, kickers)
    pairs = [v for v, c in groups if c == 2]
    if len(pairs) >= 2:
        top2 = pairs[:2]
        kicker = [v for v in vals if v not in top2][0]
        return (2, top2, kicker)
    if 2 in counts:
        pair = [v for v, c in groups if c == 2][0]
        kickers = [v for v in vals if v != pair][:3]
        return (1, pair, kickers)
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
    3: "Trei de un fel (Three of a Kind)",
    2: "Două perechi (Two Pair)",
    1: "O pereche (One Pair)",
    0: "Carte mare (High Card)",
}

def to_rank_str(v): return VAL_RANK[v]
def straight_str(topv): return "5–A" if topv == 5 else "–".join(to_rank_str(topv - i) for i in range(5))

def describe_score(score):
    t = score[0]
    if t == 8: return f"{HAND_NAMES[t]} – {straight_str(score[1])}"
    if t == 7: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} cu kicker {to_rank_str(score[2])}"
    if t == 6: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])} peste {to_rank_str(score[2])}"
    if t == 5: return f"{HAND_NAMES[t]} – " + " ".join(to_rank_str(v) for v in score[1][:5])
    if t == 4: return f"{HAND_NAMES[t]} – {straight_str(score[1])}"
    if t == 3: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])}"
    if t == 2:
        p1, p2 = to_rank_str(score[1][0]), to_rank_str(score[1][1])
        return f"{HAND_NAMES[t]} – {p1} și {p2}, kicker {to_rank_str(score[2])}"
    if t == 1: return f"{HAND_NAMES[t]} – {to_rank_str(score[1])}"
    return f"{HAND_NAMES[0]} – " + " ".join(to_rank_str(v) for v in score[1][:5])

# ===== UI helpers =====
def card_html(card, big=False, highlight=False, border=False):
    rank, suit = card[:-1], card[-1]
    color = "#d00" if suit in RED_SUITS else "#111"
    bg = "#d9ffd9" if highlight else "#fff"
    pad = "8px 10px" if big else "4px 8px"
    font = "700 26px/1.0 'Segoe UI'" if big else "700 16px/1.0 'Segoe UI'"
    border_css = "2px solid #2e7d32" if border else "1px solid #bbb"
    return f"<span style='display:inline-block;margin:2px;padding:{pad};background:{bg};color:{color};border:{border_css};border-radius:6px'>{rank}{suit}</span>"

def hidden_html(big=False):
    pad = "8px 10px" if big else "4px 8px"
    return f"<span style='display:inline-block;margin:2px;padding:{pad};background:#fff;color:#111;border:1px solid #bbb;border-radius:6px'>🂠</span>"

# ===== Streamlit app =====
st.set_page_config(page_title="Texas Hold'em – 10 jucători", layout="wide")

if "state" not in st.session_state: st.session_state.state = {}
if "seed" not in st.session_state: st.session_state.seed = SEED

def new_hand():
    rng = random.Random(st.session_state.seed)
    deck = make_deck()
    riffle_shuffle(deck, rng)
    dealer = rng.randrange(NUM_PLAYERS)
    hands = deal_hole_cards(deck, NUM_PLAYERS, dealer)
    flop, turn, river = deal_board(deck)
    st.session_state.state = {
        "dealer": dealer + 1,
        "hands": hands,
        "flop": flop,
        "turn": turn,
        "river": river,
        "stage": "flop",
        "winners": [],
        "show": False
    }

def progress_step():
    s = st.session_state.state
    if s["stage"] == "flop": s["stage"] = "turn"
    elif s["stage"] == "turn": s["stage"] = "river"
    elif s["stage"] == "river": s["stage"] = "show"; s["show"] = True

# HEADER
st.title("Texas Hold'em")
seed_in = st.text_input("Seed (opțional, pentru repetabilitate)", value=str(st.session_state.seed or ""))
st.session_state.seed = int(seed_in) if seed_in.strip().isdigit() else None

if not st.session_state.state:
    new_hand()
s = st.session_state.state
stage, show = s["stage"], s["show"]

# BOARD
row_left, row_center, row_right = st.columns([1,6,1])
with row_left:
    if st.button("🃏 Mână nouă", key="btn_new_board", use_container_width=True):
        new_hand(); st.rerun()
with row_center:
    st.markdown("<h3 style='text-align:center;margin:0.5rem 0'>Board</h3>", unsafe_allow_html=True)

    # pregătim cărțile
    parts = []
    for c in s["flop"]:
        parts.append(card_html(c, big=True))
    if stage in ("turn","river","show"):
        parts.append(card_html(s["turn"], big=True))
    else: parts.append(hidden_html(big=True))
    if stage in ("river","show"):
        parts.append(card_html(s["river"], big=True))
    else: parts.append(hidden_html(big=True))

    # MASA OVALĂ
    st.markdown(
        f"""
        <div class="table-wrap">
          <div class="poker-table">
            <div class="table-logo">Texas Hold'em</div>
            <div class="board-cards">{' '.join(parts)}</div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )
with row_right:
    label = "Arată Turn" if stage=="flop" else "Arată River" if stage=="turn" else "Arată cărțile"
    if st.button(label, key="btn_prog_board", disabled=show, use_container_width=True):
        progress_step(); st.rerun()

# HERO
hero_cards = s["hands"][HERO-1]
st.subheader("Mâna ta – Jucătorul 7")
st.markdown(" ".join(card_html(c, big=True) for c in hero_cards), unsafe_allow_html=True)
