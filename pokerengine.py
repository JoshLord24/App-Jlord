import streamlit as st
import random
import pandas as pd
from collections import Counter
from itertools import combinations

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
def pretty_card(card):
    suit_symbols = {
        "Hearts": "♥",
        "Diamonds": "♦",
        "Clubs": "♣",
        "Spades": "♠"
    }
    symbol = suit_symbols[card.suit]
    color = "red" if card.suit in ["Hearts", "Diamonds"] else "black"
    return f"<span style='color:{color}; font-size:20px;'>{card.rank} {symbol}</span>"

def display_hand(player, is_human):
    game = st.session_state.game

    st.markdown(f"**{player.name}:**", unsafe_allow_html=True)

    visible = (
        is_human or
        game.show_opponents or
        GameState.phases[game.phase_index] == "Showdown"
    )

    cols = st.columns(len(player.hand))
    for col, card in zip(cols, player.hand):
        if visible:
            col.markdown(pretty_card(card), unsafe_allow_html=True)
        else:
            col.markdown("🂠")

def display_cards(label, cards):
    st.markdown(f"**{label}:**", unsafe_allow_html=True)
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        col.markdown(pretty_card(card), unsafe_allow_html=True)

def ai_action(player):
    if player.folded:
        return

    game = st.session_state.game

    # Very basic AI - Develop more later
    if game.current_bet == 0:
        action = random.choice(["check", "check", "fold"])
    else:
        action = random.choice(["call", "fold"])

    if action == "check":
        check(player)
    elif action == "call":
        call(player)
    elif action == "fold":
        fold(player)
    
def run_betting_round():
    game = st.session_state.game
    players = st.session_state.players

    active_players = [p for p in players if not p.folded]

    if len(active_players) == 1:
        game.phase = "showdown"
        return

    current = players[game.active_player_index]

    # AI turns
    if current.name != "You":
        ai_action(current)
        return

class Deck:
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    rank_orders = {r: i+2 for i, r in enumerate(ranks)}

    def __init__(self):
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def shuffle(self):
        random.shuffle(self.cards)  

    def deal(self, n=1):
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt
    def to_dataframe(self):
        return pd.DataFrame({
            "Rank": [card.rank for card in self.cards],
            "Suit": [card.suit for card in self.cards],
            "Card": [str(card) for card in self.cards]
        })

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.folded = False
        self.current_bet = 0
        self.chips = 1000
        self.best_score = None

    def reset(self):
        self.hand = []
        self.folded = False
        self.current_bet = 0
        self.best_score = None

class GameState:
    phases = ["Preflop", "Flop", "Turn", "River", "Showdown"]
    
    def __init__(self):
        self.phase_index = 0
        self.show_opponents = False
        self.pot = 0
        self.current_bet = 0
        self.active_player_index = 0
        self.betting_round_active = False
    
    def __init__(self):
        self.phase_index = 0
        self.show_opponents = False
        self.pot = 0
        self.current_bet = 0
        self.active_player_index = 0
        self.betting_round_active = False
    
    def advance_game(self):
        game = st.session_state.game
        deck = st.session_state.deck

        if game.phase_index == 0:  # Pre-Flop
            deck.shuffle()
            for player in st.session_state.players:
                player.receive_cards(deck.deal(2))
            game.phase_index += 1
        elif game.phase_index == 1:  # Flop
            deck.deal(1)  # burn
            game.community_cards.extend(deck.deal(3))  # flop
            game.phase_index += 1
        elif game.phase_index == 2:  # Turn
            deck.deal(1)  # burn
            game.community_cards.extend(deck.deal(1))  # turn
            game.phase_index += 1
        elif game.phase_index == 3:  # River
            deck.deal(1)  # burn
            game.community_cards.extend(deck.deal(1))  # river
            game.phase_index += 1
        elif game.phase_index == 4:  # Showdown
            for player in st.session_state.players:                
                player.evaluate(game.community_cards)
            game.phase_index += 1


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
        
        #One Pair
        if 2 in counts.values():
            pair = max(k for k, v in counts.items() if v == 2)
            kickers = sorted((k for k, v in counts.items() if v == 1), reverse=True)
            return HandEvaluator.hand_ranks["One Pair"], [pair] + kickers
        
        # High Card
        return HandEvaluator.hand_ranks["High Card"], values
    
    @staticmethod
    def is_straight(values):
        unique_values = sorted(set(values), reverse=True)
        if len(unique_values) < 5:
            return False, None
        for i in range(len(unique_values) - 4):
            if unique_values[i] - unique_values[i + 4] == 4:
                return True, unique_values[i]
        # Check for Ace-low straight (A-2-3-4-5)
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
    
# Game Logic

def next_player():
    game = st.session_state.game
    players = st.session_state.players

    if all(p.folded for p in st.session_state.players):        
        return

    while True:
        game.active_player_index = (game.active_player_index + 1) % len(players)
        if not players[game.active_player_index].folded:
            break

def bet(player, amount):
    g = st.session_state.game

    diff = amount - player.current_bet
    player.chips -= diff
    player.current_bet = amount
    g.pot += diff
    g.current_bet = max(g.current_bet, amount)

    next_player()

def check(player):
    next_player()
    check_betting_complete()

def call(player):
    game = st.session_state.game
    to_call = game.current_bet - player.current_bet

    player.chips -= to_call
    player.current_bet += to_call
    game.pot += to_call

    next_player()
    check_betting_complete()

def fold(player):
    player.folded = True
    next_player()
    check_betting_complete()

def check_betting_complete():
    game = st.session_state.game
    players = [p for p in st.session_state.players if not p.folded]

    bets = [p.current_bet for p in players]

    if len(set(bets)) == 1:
        game.betting_round_active = False
    
def start_hand():
    st.session_state.deck = Deck()
    st.session_state.deck.shuffle()

    g = st.session_state.game
    players = st.session_state.players

    for p in players:
        p.reset()

    g.phase_index = 0
    g.pot = 0
    g.current_bet = 0

    # move dealer
    g.dealer = (g.dealer + 1) % len(players)

    # blinds
    sb = (g.dealer + 1) % len(players)
    bb = (g.dealer + 2) % len(players)

    bet(players[sb], g.small_blind)
    bet(players[bb], g.big_blind)

    g.active_player = (bb + 1) % len(players)

    # deal
    for p in players:
        p.hand = st.session_state.deck.deal(2)

    g.betting_active = True


# User Interface (UI Display)

st.title("Poker Simulator")


num_players = st.number_input("Number of Players", min_value=2, max_value=9, value=2, step=1)
if st.button("Create Players", key="create_players"):
    st.session_state.players = [Player("You")] + [
        Player(f"AI {i}") for i in range(1, num_players)
    ]

if "deck" not in st.session_state:
    st.session_state.deck = Deck()
if "game" not in st.session_state:
    st.session_state.game = GameState()
if "players" not in st.session_state:
    st.session_state.players = []

# Controls

col1, col2 = st.columns(2)

if col1.button("Start Hand"):
    start_hand()


# Display
st.subheader(f"Pot: {st.session_state.game.pot}")

for i, p in enumerate(st.session_state.players):
    st.write(f"{p.name} | Chips: {p.chips} {'(Folded)' if p.folded else ''}")


def deal_player_hands():
    deck = st.session_state.deck
    for player in st.session_state.players:
        player.receive_cards(st.session_state.deck.deal(2))

def advance_game():
    game = st.session_state.game
    deck = st.session_state.deck

    if game.betting_round_active:
        st.warning("Finish Betting Round")
        return
    if all(p.folded for p in player):
        return
    if game.phase_index == 0:  # Pre-Flop
        deck.shuffle()
        for player in game.players:
            player.receive_cards(deck.deal(2))
            game.phase_index += 1
            game.betting_round_active = True
            game.current_bet = 0
            for player in st.session_state.players:
                player.current_bet = 0
    elif game.phase_index == 1:  # Flop
        deck.deal(1)  # burn
        game.community_cards.extend(deck.deal(3))  # flop
        game.phase_index += 1
        game_phase = GameState.phases[game.phase_index]
        game.betting_round_active = True
        game.current_bet = 0
        for player in st.session_state.players:
            player.current_bet = 0
        st.write(f"{game_phase}")
    elif game.phase_index == 2:  # Turn
        deck.deal(1)  # burn
        game.community_cards.extend(deck.deal(1))  # turn
        game.phase_index += 1
        game.betting_round_active = True
        game.current_bet = 0
        for player in st.session_state.players:
            player.current_bet = 0
        st.write(f"{GameState.phases[game.phase_index]}")
    elif game.phase_index == 3:  # River
        deck.deal(1)  # burn
        game.community_cards.extend(deck.deal(1))  # river
        game.phase_index += 1
        game.betting_round_active = True
        game.current_bet = 0
        for player in st.session_state.players:
            player.current_bet = 0
        st.write(f"{GameState.phases[game.phase_index]}")
    elif game.phase_index == 4:  # Showdown
        for player in game.players:
            player.evaluate(game.community_cards)
        game.phase_index += 1
        st.write("Showdown!")

def new_hand():
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.deck.shuffle()
    st.session_state.community_cards = []
    for player in st.session_state.players:
        player.hand = []
        player.folded = False
        player.current_bet = 0
    st.session_state.community_cards = []
    st.session_state.game.phase_index = 0
    game = st.session_state.game
    game.pot = 0
    game.current_bet = 0
    game.active_player_index = 0
    game.betting_round_active = True





