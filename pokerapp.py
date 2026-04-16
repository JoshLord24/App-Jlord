# ---- POKER APP -------

from unicodedata import name

import streamlit as st
import random
from collections import Counter
from itertools import combinations
import streamlit.components.v1 as components

# ----- CORE CLASSES -------

class Card:
    SUITS = ["♠️", "♥️", "♦️", "♣️"]
    RANKS = ["𝟐", "𝟑", "𝟒", "𝟓", "𝟔", "𝟕", "𝟖", "𝟗", "𝟏𝟎", "𝐉", "𝐐", "𝐊", "𝐀"]

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Player:
    def __init__(self, name, chips=1000, personality="normal"):
        self.name = name
        self.hand = []
        self.chips = chips
        self.current_bet = 0
        self.folded = False
        self.personality = personality
        self.has_acted = False

    def reset(self):
        self.hand = []
        self.current_bet = 0
        self.folded = False
        self.has_acted = False

class Deck:
    rank_orders = {r: i+2 for i, r in enumerate(Card.RANKS)}

    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num):
        return [self.cards.pop() for _ in range(num)]

class GameState:
    def __init__(self, players, small_blind=10, big_blind=20):
        self.players = players
        self.pot = 0
        self.community_cards = []
        self.dealer = 0
        self.current_player_index = 0
        self.last_action = "Hand Started"
        self.round_phase = "Preflop"
        self.betting_round_complete = False
        self.deck = self.new_deck()

        self.small_blind_amount = small_blind
        self.big_blind_amount = big_blind
        self.small_blind_index = (self.dealer + 1) % len(self.players)
        self.big_blind_index = (self.dealer + 2) % len(self.players)

        self.current_bet = 0

    def new_deck(self):
        deck = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]
        random.shuffle(deck)
        return deck

    def deal_hands(self):
        for player in self.players:
            player.hand = [self.deck.pop(), self.deck.pop()]
            player.current_bet = 0
            player.folded = False

    def deal_community(self, num):
        for _ in range(num):
            self.community_cards.append(self.deck.pop())

    def rotate_dealer(self):
        self.dealer = (self.dealer + 1) % len(self.players)
        self.small_blind_index = (self.dealer + 1) % len(self.players)
        self.big_blind_index = (self.dealer + 2) % len(self.players)
        self.current_player_index = (self.dealer + 1) % len(self.players)

    def current_player(self):
        return self.players[self.current_player_index]

    def set_action(self, text):
        self.last_action = text

    def next_player(self):
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if not self.players[self.current_player_index].folded:
                return

    def all_players_acted(self):
        active = [p for p in self.players if not p.folded]
        bets_equal = all(p.current_bet == self.current_bet for p in active)
        all_acted = all(p.has_acted for p in active)
        if self.round_phase == "Preflop" and bets_equal and not all_acted:
            return False
        return all_acted and bets_equal

    def try_advance_phase(self):
        if self.all_players_acted():
            self.advance_phase()
            for p in self.players:
                p.current_bet = 0
                p.has_acted = False
            self.current_bet = 0
            self.current_player_index = self.dealer % len(self.players)
            self.next_player()
        else:
            self.next_player()

    def advance_phase(self):
        phases = ["Preflop", "Flop", "Turn", "River", "Showdown"]
        next_index = phases.index(self.round_phase) + 1
        if next_index < len(phases):
            self.round_phase = phases[next_index]
            if self.round_phase == "Flop":
                self.deal_community(3)
            elif self.round_phase in ["Turn", "River"]:
                self.deal_community(1)
        else:
            self.round_phase = "Showdown"

# ----- HAND EVALUATOR ------

class HandEvaluator:
    hand_ranks = {
        "High Card": 1,
        "One Pair": 2,
        "Two Pair": 3,
        "Three of a Kind": 4,
        "Straight": 5,
        "Flush": 6,
        "Full House": 7,
        "Four of a Kind": 8,
        "Straight Flush": 9,
        "Royal Flush": 10
    }

    @staticmethod
    def evaluate_5(cards):
        values = sorted([Deck.rank_orders[c.rank] for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        counts = Counter(values)
        is_flush = len(set(suits)) == 1
        is_straight, high_straight = HandEvaluator.is_straight(values)

        if is_flush and is_straight:
            if high_straight == 14:
                return HandEvaluator.hand_ranks["Royal Flush"], [14]
            return HandEvaluator.hand_ranks["Straight Flush"], [high_straight]
        if 4 in counts.values():
            four = max(k for k, v in counts.items() if v == 4)
            kicker = max(k for k, v in counts.items() if v == 1)
            return HandEvaluator.hand_ranks["Four of a Kind"], [four, kicker]
        if sorted(counts.values()) == [2, 3]:
            three = max(k for k, v in counts.items() if v == 3)
            pair = max(k for k, v in counts.items() if v == 2)
            return HandEvaluator.hand_ranks["Full House"], [three, pair]
        if is_flush:
            return HandEvaluator.hand_ranks["Flush"], values
        if is_straight:
            return HandEvaluator.hand_ranks["Straight"], [high_straight]
        if 3 in counts.values():
            three = max(k for k, v in counts.items() if v == 3)
            kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
            return HandEvaluator.hand_ranks["Three of a Kind"], [three] + kickers
        if list(counts.values()).count(2) == 2:
            pairs = sorted((k for k, v in counts.items() if v == 2), reverse=True)
            kicker = max(k for k, v in counts.items() if v == 1)
            return HandEvaluator.hand_ranks["Two Pair"], pairs + [kicker]
        if 2 in counts.values():
            pair = max(k for k, v in counts.items() if v == 2)
            kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
            return HandEvaluator.hand_ranks["One Pair"], [pair] + kickers
        return HandEvaluator.hand_ranks["High Card"], values

    @staticmethod
    def is_straight(values):
        unique_values = sorted(set(values), reverse=True)
        if len(unique_values) < 5:
            return False, None
        for i in range(len(unique_values) - 4):
            if unique_values[i] - unique_values[i + 4] == 4:
                return True, unique_values[i]
        if set([14, 2, 3, 4, 5]).issubset(set(values)):
            return True, 5
        return False, None

    @staticmethod
    def best_hand(cards7):
        best = None
        best_score = None
        for combo in combinations(cards7, 5):
            score = HandEvaluator.evaluate_5(combo)
            if best_score is None or score > best_score:
                best_score = score
                best = combo
        return best_score, best

def get_hand_name(score):
    rank_value = score[0]
    for name, val in HandEvaluator.hand_ranks.items():
        if val == rank_value:
            return name

# ----- CARD DISPLAY -----

def display_hand(player_or_cards, is_human=False, label=None, reveal=False, is_community=False):
    if isinstance(player_or_cards, list):
        cards = player_or_cards
        name = label or "Community Cards"
    else:
        cards = getattr(player_or_cards, "hand", [])
        name = getattr(player_or_cards, "name", "Player") if label is None else label
 
    if not cards:
        placeholder = "—" if is_community else "*(no cards)*"
        st.markdown(f"**{name}:** {placeholder}", unsafe_allow_html=True)
        return
 
    if is_community or is_human or reveal:
        cards_str = " | ".join(str(c) for c in cards)
        st.markdown(f"**{name}:** {cards_str}", unsafe_allow_html=True)
    else:
        cards_str = " | ".join("🂠" for _ in cards)
        st.markdown(f"**{name}:** {cards_str}", unsafe_allow_html=True)

# ----- GAME LOGIC --------

def evaluate_strength(player):
    if len(player.hand) < 2:
        return 0
    values = sorted([Deck.rank_orders[c.rank] for c in player.hand])
    suits = [c.suit for c in player.hand]
    high_card = values[1]
    low_card = values[0]
    is_pair = values[0] == values[1]
    is_suited = suits[0] == suits[1]

    if is_pair:
        return 0.50 + (high_card - 2) / 12 * 0.45
    
    base = (high_card * .7 + low_card * .3) / 14
    # Adds a boost for suited cards
    suited_bonus = 0.05 * (high_card / 14) if is_suited else 0
    # Adds a boost for connectors (cards touching in rank)
    connected_bonus = 0.03 if (high_card - low_card) <= 2 else 0.0
    return base + suited_bonus + connected_bonus


def bet(player, amount):
    g = st.session_state.game
    amount = min(amount, player.chips + player.current_bet)  
    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet = amount
    g.pot += diff
    g.current_bet = max(g.current_bet, amount)
    player.has_acted = True
    g.set_action(f"{player.name} bets {amount}")

def call(player):
    g = st.session_state.game
    amount = min(g.current_bet, player.chips + player.current_bet)
    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet = amount
    g.pot += diff
    player.has_acted = True
    g.set_action(f"{player.name} calls")

def check(player):
    g = st.session_state.game
    player.has_acted = True
    g.set_action(f"{player.name} checks")

def fold(player):
    g = st.session_state.game
    player.folded = True
    player.has_acted = True
    g.set_action(f"{player.name} folds")

def all_in(player):
    g = st.session_state.game
    amount = player.chips + player.current_bet
    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet = amount
    g.pot += diff
    g.current_bet = max(g.current_bet, amount)
    player.has_acted = True
    g.set_action(f"{player.name} goes ALL IN with {amount}")

# ----- HAND START ------

def post_blind(player, amount):
    g = st.session_state.game
    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet += diff
    g.pot += diff
    g.current_bet = max(g.current_bet, amount)

def start_hand():
    g = st.session_state.game
    g.rotate_dealer()
    g.pot = 0
    g.current_bet = 0
    g.deck = g.new_deck()
    g.community_cards = []
    g.round_phase = "Preflop"
    g.small_blind_index = (g.dealer + 1) % len(g.players)
    g.big_blind_index = (g.dealer + 2) % len(g.players)

    for p in g.players:
        p.current_bet = 0
        p.folded = False
        p.has_acted = False

    g.deal_hands()
    post_blind(g.players[g.small_blind_index], g.small_blind_amount)
    post_blind(g.players[g.big_blind_index], g.big_blind_amount)

    g.current_player_index = (g.big_blind_index + 1) % len(g.players)

# ----- AI ACTION ------

def ai_action(player):
    if player.folded:
        return
    g = st.session_state.game
    strength = evaluate_strength(player)
    to_call = g.current_bet - player.current_bet
    pressure = to_call / max(player.chips, 1)
    aggression = random.random()
 
    if player.personality == "aggressive":
        aggression = min(aggression + 0.15, 1.0)
    elif player.personality == "passive":
        aggression = max(aggression - 0.15, 0.0)
 
    if strength >= 0.8:
        # Premium hand — raise 50%, otherwise call
        if aggression >= 0.50:
            bet(player, g.current_bet + int(player.chips * 0.20))
        else:
            call(player)
 
    elif strength >= 0.65:
        # Strong hand — call freely; only raise with high aggression
        if aggression >= 0.8:
            bet(player, g.current_bet + int(player.chips * 0.10))
        else:
            call(player)
 
    elif strength >= 0.5:
        # Decent hand — call if cheap; fold under pressure
        if pressure <= 0.15:
            call(player)
        elif aggression >= 0.75:
            call(player)
        else:
            fold(player)
 
    else:
        # Weak hand — fold unless it's very cheap to call or AI is very aggressive
        if to_call == 0:
            check(player)
        elif pressure <= 0.05:
            call(player)
        else:
            fold(player)


# ------ Table and Card Display ------

def card_html(card, size="sm"):
    w, h, fs = ("36px", "52px", "15px") if size == "sm" else ("44px", "64px", "18px")
    suit = str(card.suit)
    red = "♥" in suit or "♦" in suit
    color = "#c0392b" if red else "#1a1a1a"
    return (f'<div style="width:{w};height:{h};background:#fff;border-radius:5px;'
            f'border:1px solid #ccc;display:flex;align-items:center;justify-content:center;'
            f'font-size:{fs};font-weight:500;color:{color};box-shadow:0 1px 3px rgba(0,0,0,0.3);">'
            f'{card.rank}{card.suit}</div>')

def back_card_html(size="sm"):
    w, h = ("36px", "52px") if size == "sm" else ("44px", "64px")
    return (f'<div style="width:{w};height:{h};background:#2c5aa0;border-radius:5px;'
            f'border:1px solid #1a3d75;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>')

def build_table_html(g, players, show_opponents):
    # Phase pills
    phases = ["Preflop", "Flop", "Turn", "River", "Showdown"]
    phase_pills = "".join(
        f'<div style="font-size:11px;padding:3px 12px;border-radius:20px;'
        f'background:{"rgba(0,100,220,0.15)" if p == g.round_phase else "transparent"};'
        f'border:0.5px solid {"rgba(0,100,220,0.4)" if p == g.round_phase else "rgba(128,128,128,0.2)"};'
        f'color:{"#1a6bd4" if p == g.round_phase else "#888"};">{p}</div>'
        for p in phases
    )

    # Community cards
    community_html = "".join(
        card_html(c) for c in g.community_cards
    ) + "".join(
        back_card_html() for _ in range(5 - len(g.community_cards))
    )

    # AI seats (players[1:]) — positions around the oval
    seat_positions = [
        "top:-68px;left:50%;transform:translateX(-50%)",   # top center
        "top:-24px;right:-48px",                           # top right
        "bottom:-24px;right:-88px",                        # bot right
        "top:-24px;left:-48px",                            # top left
        "bottom:-24px;left:-68px",                         # bot left
        "bottom:-68px;left:25%;transform:translateX(-50%)", # bot left-center (6+ players)
        "bottom:-68px;left:75%;transform:translateX(-50%)", # bot right-center
    ]

    ai_seats = ""
    for idx, player in enumerate(players[1:]):
        pos = seat_positions[idx % len(seat_positions)]
        is_current = (g.current_player() == player)
        is_folded = player.folded

        # Role badge
        i = players.index(player)
        role = ""
        if i == g.dealer: role = "D"
        elif i == g.small_blind_index: role = "SB"
        elif i == g.big_blind_index: role = "BB"

        # Cards
        if is_folded:
            cards_html = back_card_html() + back_card_html()
            opacity = "0.4"
        elif show_opponents:
            cards_html = "".join(card_html(c) for c in player.hand)
            opacity = "1"
        else:
            cards_html = back_card_html() + back_card_html()
            opacity = "1"

        name_bg = "rgba(0,120,255,0.35)" if is_current else "rgba(0,0,0,0.45)"
        status = " ⬅" if is_current else (" 🚫" if is_folded else "")
        badge = f'<span style="font-size:9px;color:#ffd700;margin-left:4px;">{role}</span>' if role else ""

        ai_seats += f'''
        <div style="position:absolute;{pos};display:flex;flex-direction:column;
                    align-items:center;gap:4px;min-width:110px;opacity:{opacity};">
          <div style="display:flex;gap:4px;">{cards_html}</div>
          <div style="font-size:11px;font-weight:500;color:rgba(255,255,255,0.9);
                      background:{name_bg};border-radius:12px;padding:2px 10px;white-space:nowrap;">
            {player.name}{badge}{status}
          </div>
          <div style="font-size:10px;color:rgba(255,255,255,0.55);">
            chips: {player.chips} | bet: {player.current_bet}
          </div>
        </div>'''

    # Human player cards
    human = players[0]
    human_role = ""
    if 0 == g.dealer: human_role = "  DEALER"
    elif 0 == g.small_blind_index: human_role = " (SB)"
    elif 0 == g.big_blind_index: human_role = " (BB)"
    human_cards_html = "".join(
        f'<div style="width:44px;height:64px;background:#fff;border-radius:6px;'
        f'border:1px solid #ccc;display:flex;align-items:center;justify-content:center;'
        f'font-size:18px;font-weight:500;color:{"#c0392b" if "♥" in c.suit or "♦" in c.suit else "#1a1a1a"};'
        f'box-shadow:0 2px 6px rgba(0,0,0,0.2);">{c.rank}{c.suit}</div>'
        for c in human.hand
    ) if human.hand else "<span style='color:#888;font-size:13px;'>No cards yet</span>"

    return f"""
    <div style="font-family:sans-serif;display:flex;flex-direction:column;align-items:center;padding:1rem;">
      <div style="display:flex;gap:6px;margin-bottom:10px;">{phase_pills}</div>
      <div style="font-size:12px;color:#888;margin-bottom:8px;">Last action: {g.last_action}</div>

      <div style="position:relative;width:580px;height:320px;margin:80px 0 100px;">
        <div style="width:100%;height:100%;background:#1a6b3c;border-radius:150px;
                    border:8px solid #8B5E2A;outline:4px solid #5a3a10;
                    display:flex;align-items:center;justify-content:center;">
          <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
            <div style="font-size:10px;color:rgba(255,255,255,0.5);letter-spacing:.08em;">COMMUNITY CARDS</div>
            <div style="display:flex;gap:6px;">{community_html}</div>
            <div style="font-size:11px;color:rgba(255,255,255,0.6);margin-top:2px;">Pot</div>
            <div style="font-size:17px;font-weight:500;color:#ffd700;"> {g.pot}</div>
          </div>
        </div>
        {ai_seats}
      </div>

      <div style="display:flex;flex-direction:column;align-items:center;gap:8px;
                  padding:12px 24px;border:0.5px solid #ddd;border-radius:12px;width:400px;">
        <div style="font-size:13px;font-weight:500;">You{human_role} — chips: {human.chips} | bet: {human.current_bet}</div>
        <div style="display:flex;gap:8px;">{human_cards_html}</div>
      </div>
    </div>
    """


# ------ STREAMLIT UI --------

st.title("♥️♠️ Texas Hold'em ♣️♦️")


# ----- SIDEBAR SETTINGS -----
with st.sidebar:
    st.header("⚙️ Game Settings")
    num_ai = st.number_input("Number of AI players", min_value=1, max_value=7, value=3, step=1)
    starting_chips = st.number_input("Starting chips", min_value=100, max_value=100000, value=1000, step=100)
    small_blind = st.number_input("Small blind", min_value=1, max_value=10000, value=10, step=10)
    big_blind = st.number_input("Big blind", min_value=2, max_value=10000, value=20, step=20)
 
    if st.button("🆕 New Game", use_container_width=True):
        human = Player("You", chips=int(starting_chips))
        ais = [
            Player(f"AI {i+1}", chips=int(starting_chips),
                   personality=random.choice(["aggressive", "passive", "normal"]))
            for i in range(int(num_ai))
        ]
        st.session_state.players = [human] + ais
        st.session_state.game = GameState(
            st.session_state.players,
            small_blind=int(small_blind),
            big_blind=int(big_blind),
        )
        st.session_state.show_opponents = False
        st.rerun()

if "players" not in st.session_state:
    human_player = Player("You")
    ai_players = [
        Player(f"AI {i+1}", chips=1000,
               personality=random.choice(["aggressive", "passive", "normal"]))
        for i in range(3)
    ]
    st.session_state.players = [human_player] + ai_players

if "game" not in st.session_state:
    st.session_state.game = GameState(st.session_state.players)

if "show_opponents" not in st.session_state:
    st.session_state.show_opponents = False

g = st.session_state.game

if g is None:
    st.error("Game not initialized")
    st.stop()

players = st.session_state.players
human_player = players[0]


# Controls to start hand and toggle opponent card visibility
col1, col2 = st.columns(2)
if col1.button("▶ Start Hand", use_container_width=True):
    start_hand()
    st.rerun()
if col2.button("👁️ Toggle Opponent Cards", use_container_width=True):
    st.session_state.show_opponents = not st.session_state.show_opponents
    st.rerun()

components.html(build_table_html(g, g.players, st.session_state.show_opponents), height=720)

# End condition/Showdown — check before prompting for actions
active = [p for p in players if not p.folded]
if len(active) == 1:
    st.success(f"{active[0].name} wins {g.pot}!")
    st.stop()

if g.round_phase == "Showdown":
    st.subheader("Showdown!")
    results = []
    for p in active:
        score, best = HandEvaluator.best_hand(p.hand + g.community_cards)
        results.append((p, score, best))
    results.sort(key=lambda x: x[1], reverse=True)
    winner = results[0][0]
    winner.chips += g.pot
    for p, score, best in results:
        hand_name = get_hand_name(score)
        cards_str = " | ".join(str(c) for c in best)
        st.write(f"**{p.name}**: {hand_name} — {cards_str}")
    st.success(f"🏆 {winner.name} wins {g.pot} chips!")
    st.stop()

current = g.current_player()

if current != human_player:
    while g.current_player() != human_player:
        ai = g.current_player()
        if not ai.folded:
            ai_action(ai)
        g.try_advance_phase()
        # Break early if the hand is over or we've reached showdown
        active_check = [p for p in players if not p.folded]
        if len(active_check) == 1 or g.round_phase == "Showdown":
            break
    st.rerun()

# Player buttons
st.subheader("Your Actions")
to_call = g.current_bet - human_player.current_bet
can_raise = human_player.chips > to_call


cols = st.columns(5)

can_check = to_call == 0
if cols[0].button("Check", disabled=not can_check):
    check(human_player)
    g.try_advance_phase()
    st.rerun()

if cols[1].button(f"Call {to_call}", disabled=to_call == 0):
    call(human_player)
    g.try_advance_phase()
    st.rerun()

if can_raise:
    min_raise = g.big_blind_amount
    max_raise = human_player.chips
    default_raise = min(g.big_blind_amount * 2, max_raise)  # clamp default to max

    raise_amount = st.number_input(
        "Raise amount",
        min_value=min_raise,
        max_value=max_raise,
        value=default_raise,
        step=g.big_blind_amount,
        key="raise_input"
    )
    if cols[2].button(f"Raise to {raise_amount}", use_container_width=True):
        bet(human_player, raise_amount)
        g.try_advance_phase()
        st.rerun()
else:
    cols[2].button("Raise", disabled=True, use_container_width=True)

if cols[3].button("Fold"):
    fold(human_player)
    g.try_advance_phase()
    st.rerun()

if cols[4].button(" All In", disabled=human_player.chips == 0):
    all_in(human_player)
    g.try_advance_phase()
    st.rerun()