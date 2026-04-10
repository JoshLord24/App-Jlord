# ---- POKER APP -------

from unicodedata import name

import streamlit as st
import random
from collections import Counter
from itertools import combinations

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
        return (
            all(p.has_acted for p in active)
            and all(p.current_bet == self.current_bet for p in active)
        )

    def try_advance_phase(self):
        if self.all_players_acted():
            self.advance_phase()
            for p in self.players:
                p.current_bet = 0
                p.has_acted = False
            self.current_bet = 0
            self.current_player_index = self.dealer
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
 
    # Community cards are ALWAYS shown face-up; human cards always shown;
    # AI cards hidden unless reveal=True
    if is_community or is_human or reveal:
        hand_str = "  ".join(Card(c) for c in cards)
        st.markdown(f"**{name}:** {hand_str}", unsafe_allow_html=True)
    else:
        st.markdown(f"**{name}:** {'🂠 ' * len(cards)}")

# ----- GAME LOGIC --------

def evaluate_strength(player):
    if len(player.hand) < 2:
        return 0
    values = [Deck.rank_orders[c.rank] for c in player.hand]
    suits = [c.suit for c in player.hand]
    if values[0] == values[1]:
        return 0.7
    if suits[0] == suits[1]:
        return 0.4
    return max(values) / 14 * 0.6 + 0.3


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

    # Preflop action starts with player after big blind
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
        # Premium hand — raise ~50%, otherwise call
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

# ------ STREAMLIT UI --------

st.title("🃏 Poker Game")


# ----- SIDEBAR SETTINGS -----
with st.sidebar:
    st.header("⚙️ Game Settings")
    num_ai = st.number_input("Number of AI players", min_value=1, max_value=7, value=3, step=1)
    starting_chips = st.number_input("Starting chips", min_value=100, max_value=100000, value=1000, step=100)
    small_blind = st.number_input("Small blind", min_value=1, max_value=10000, value=10, step=5)
    big_blind = st.number_input("Big blind", min_value=2, max_value=10000, value=20, step=5)
 
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
if col1.button("▶️ Start Hand", use_container_width=True):
    start_hand()
    st.rerun()
if col2.button("👁️ Toggle Opponent Cards", use_container_width=True):
    st.session_state.show_opponents = not st.session_state.show_opponents
    st.rerun()

st.header(f"Phase: {g.round_phase}")
st.write(f"Last Action: {g.last_action}")
st.write(f"Pot: {g.pot}")

display_hand(g.community_cards, label="Community Cards", is_community=True)
 
st.divider()
 
# Player hands
for i, player in enumerate(players):
    status = ""
    if player.folded:
        status = " 🚫 FOLDED"
    elif g.current_player() == player:
        status = " ⬅ current turn"
    label = f"{player.name}{status} — chips: {player.chips}  |  bet: {player.current_bet}"
    if i == 0:
        display_hand(player, is_human=True, label=label)
    else:
        display_hand(player, is_human=False, label=label,
                     reveal=st.session_state.show_opponents)
 
st.divider()

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
st.subheader(f"Current Turn: {current.name}")

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

# Player action buttons
st.subheader("Your Actions")
to_call = g.current_bet - human_player.current_bet
cols = st.columns(4)

can_check = to_call == 0
if cols[0].button("Check", disabled=not can_check):
    check(human_player)
    g.try_advance_phase()
    st.rerun()

if cols[1].button(f"Call {to_call}", disabled=to_call == 0):
    call(human_player)
    g.try_advance_phase()
    st.rerun()

if cols[2].button("Raise"):
    raise_amount = input("Raise Amount", value=20, step=10)
    bet(human_player, g.current_bet + raise_amount)
    g.try_advance_phase()
    st.rerun()

if cols[3].button("Fold"):
    fold(human_player)
    g.try_advance_phase()
    st.rerun()