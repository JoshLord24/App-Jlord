# ---- POKER APP -------

import streamlit as st
import random
from collections import Counter
from itertools import combinations

# ----- CORE CLASSES -------

class Card:
    SUITS = ["♠", "♥", "♦", "♣"]
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

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

    def reset(self):
        self.hand = []
        self.current_bet = 0
        self.folded = False

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

    def all_players_acted(self):
        active = [p for p in self.players if not p.folded]
        return all(p.current_bet == self.current_bet for p in active)

    def advance_player(self):
        start_index = self.current_player_index

        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            player = self.players[self.current_player_index]

            if not player.folded:
                break

            if self.current_player_index == start_index:
                break


    def try_advance_phase(self):
        if self.all_players_acted():
            self.advance_phase()
            for p in self.players:
                p.current_bet = 0

            self.current_bet = 0

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

        # Straight Flush / Royal Flush
        if is_flush and is_straight:
            if high_straight == 14:
                return HandEvaluator.hand_ranks["Royal Flush"], [14]
            return HandEvaluator.hand_ranks["Straight Flush"], [high_straight]

        # Four of a Kind
        if 4 in counts.values():
            four = max(k for k, v in counts.items() if v == 4)
            kicker = max(k for k, v in counts.items() if v == 1)
            return HandEvaluator.hand_ranks["Four of a Kind"], [four, kicker]

        # Full House
        if sorted(counts.values()) == [2, 3]:
            three = max(k for k, v in counts.items() if v == 3)
            pair = max(k for k, v in counts.items() if v == 2)
            return HandEvaluator.hand_ranks["Full House"], [three, pair]

        # Flush
        if is_flush:
            return HandEvaluator.hand_ranks["Flush"], values

        # Straight
        if is_straight:
            return HandEvaluator.hand_ranks["Straight"], [high_straight]

        # Three of a Kind
        if 3 in counts.values():
            three = max(k for k, v in counts.items() if v == 3)
            kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
            return HandEvaluator.hand_ranks["Three of a Kind"], [three] + kickers

        # Two Pair
        if list(counts.values()).count(2) == 2:
            pairs = sorted((k for k, v in counts.items() if v == 2), reverse=True)
            kicker = max(k for k, v in counts.items() if v == 1)
            return HandEvaluator.hand_ranks["Two Pair"], pairs + [kicker]

        # One Pair
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

def display_hand(player_or_cards, is_human=False, label=None, reveal=False):
    if isinstance(player_or_cards, list):
        cards = player_or_cards
        name = label or "Hand"
    else:
        cards = getattr(player_or_cards, "hand", [])
        name = getattr(player_or_cards, "name", "Player") if label is None else label

    if not cards:
        st.write(f"{name} has no cards.")
        return

    if not is_human and not reveal:
        hand_str = "🂠 " * len(cards)
    else:
        hand_str = " | ".join(str(card) for card in cards)

    st.markdown(f"**{name}:** {hand_str}")

# ----- DISPLAY COMMUNITY CARDS ------
def display_community_cards():
    g = st.session_state.game
    community = g.community_cards or []
    display_hand(community, label="Community Cards")

# ----- GAME LOGIC --------

def evaluate_strength(player):
    """0 to 1 based on hand pre-flop"""
    if len(player.hand) < 2:
        return 0
    values = [Deck.rank_orders[c.rank] for c in player.hand]
    suits = [c.suit for c in player.hand]
    if values[0] == values[1]:
        return 0.7
    if suits[0] == suits[1]:
        return 0.4
    return max(values)/14 * 0.6 + 0.3

def next_player():
    g = st.session_state.game
    players = st.session_state.players
    for _ in range(len(players)):
        g.current_player_index = (g.current_player_index + 1) % len(players)
        if not players[g.current_player_index].folded:
            return

def bet(player, amount):
    g = st.session_state.game
    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet = player.current_bet + diff
    g.pot += diff
    g.current_bet = max(g.current_bet, amount)

    g.set_action(f"{player.name} bets {amount}")
    g.advance_player()

def call(player):
    g = st.session_state.game
    bet(player, g.current_bet)
    g.set_action(f"{player.name} calls")

def check(player):
    g = st.session_state.game
    g.set_action(f"{player.name} checks")
    g.advance_player()


def fold(player):
    g = st.session_state.game
    player.folded = True
    g.set_action(f"{player.name} folds")
    g.advance_player()


# ----- HAND START ------

def start_hand():
    g = st.session_state.game
    g.rotate_dealer()
    g.pot = 0
    g.current_bet = 0  # reset highest bet
    g.deck = g.new_deck()
    g.community_cards = []
    g.deal_hands()
    g.round_phase = "Preflop"
    g.small_blind_index = (g.dealer + 1) % len(g.players)
    g.big_blind_index = (g.dealer + 2) % len(g.players)


    # Post blinds
    bet(g.players[g.small_blind_index], g.small_blind_amount)
    bet(g.players[g.big_blind_index], g.big_blind_amount)

# ----- AI ACTION ------

def ai_action(player):
    if player.folded:
        return
    g = st.session_state.game
    strength = evaluate_strength(player)
    to_call = g.current_bet - player.current_bet
    pressure = to_call / max(player.chips, 1)
    aggression = random.random()
    personality = personalities
    current_bet = g.current_bet


    if player.personality == "aggressive": 
        aggression += 0.2 
    elif player.personality == "passive":
        aggression -= 0.2
    if strength > 0.8: # very strong hand
        if aggression < 0.5:
            call(player)
        else:
            bet(player, g.current_bet + int(player.chips * 0.2))
    if strength > 0.6: # strong hand
        if aggression < 0.7:
            raise_amt = g.current_bet + int(player.chips * 0.1)
            bet(player, raise_amt)
        if pressure < 0.2:
            if aggression < 0.5:
                bet(player, g.current_bet + int(player.chips * 0.1))
            else:
                call(player)
        else:
            call(player)
    if strength > 0.4: # eh hand
        if pressure < 0.1:
            call(player)
        if aggression < 0.5:
            fold(player)
        else:
            call(player)
    else: # weak hand
        if pressure > 0.1:
            fold(player)
        else:
            if aggression < 0.3:
                call(player)
            else:
                fold(player)

# ------------------ STREAMLIT UI ------------------

st.title("Poker Game")

# List of players
human_player = Player("You")

personalities = ["aggressive", "passive", "normal"]

ai_players = [
    Player(f"AI {i+1}", personality=random.choice(personalities))
    for i in range(2)
]
all_players = [human_player] + ai_players

# Initialize game if not already
if "game" not in st.session_state:
    st.session_state.game = GameState(all_players)
    st.session_state.game.deal_hands()  # initial deal

if "players" not in st.session_state:
    st.session_state.players = all_players

if "current_turn" not in st.session_state:
    st.session_state.current_turn = 0

game = st.session_state.game

for i, player in enumerate(game.players):
    if i == 0:
        display_hand(player, is_human=True)
    else:
        # Only reveal at showdown
        display_hand(player, is_human=False, reveal=(game.round_phase == "Showdown"))

g = st.session_state.game
players = st.session_state.players

col1, col2 = st.columns(2)
if col1.button("Start Hand"):
    start_hand()
if col2.button("Show Opponent Cards"):
    g.show_opponents = not g.show_opponents

g = st.session_state.game

st.header(f"Phase: {g.round_phase}")
st.subheader(f"Current Turn: {g.current_player().name}")
st.write(f"Last Action: {g.last_action}")
st.write(f"Pot: {g.pot}")

# Community cards
display_hand(g.community_cards, label="Community Cards")

# Player hands
for i, player in enumerate(g.players):
    if i == 0:
        display_hand(player, is_human=True)
    else:
        st.markdown(f"**{player.name}'s hand:** 🂠 🂠")  # hide AI hands until showdown

# Player action buttons
st.subheader("Your Actions")

current = g.current_player()

current = g.players[st.session_state.current_turn]

if current == human_player:
    cols = st.columns(4)
    if cols[0].button("Check"):
        check(human_player)
        g.try_advance_phase()
        st.session_state.current_turn = g.current_player_index
    if cols[1].button("Call"):
        call(human_player)
        g.try_advance_phase()
        st.session_state.current_turn = g.current_player_index
    if cols[2].button("Raise"):
        bet(human_player, g.current_bet + 20)
        g.try_advance_phase()
        st.session_state.current_turn = g.current_player_index
    if cols[3].button("Fold"):
        fold(human_player)
        g.try_advance_phase()
        st.session_state.current_turn = g.current_player_index
else:
    # Only act if it’s AI’s turn
    if not current.folded:
        ai_action(current)
        g.try_advance_phase()
        st.session_state.current_turn = g.current_player_index


# End condition
active = [p for p in g.players if not p.folded]
if len(active) == 1:
    st.success(f"{active[0].name} wins {g.pot}!")