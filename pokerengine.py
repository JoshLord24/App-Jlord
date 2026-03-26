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
    
    
class Deck:
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    rank_orders = {"2": 2, 
                   "3": 3, 
                   "4": 4, 
                   "5": 5, 
                   "6": 6,
                   "7": 7, 
                   "8": 8, 
                   "9": 9, 
                   "10": 10,
                   "Jack": 11, 
                   "Queen": 12, 
                   "King": 13, 
                   "Ace": 14
            }

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
    
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.best_hand = None
        self.best_score = None
    
    def receive_cards(self, cards):
        self.hand = cards
    
    def evaluate(self, community_cards):
        all_cards = self.hand + community_cards
        self.best_score, self.best_hand = HandEvaluator.best_hand(all_cards)


st.title("Poker Engine")
st.write("This is a simple Streamlit app to display poker data.")

num_players = st.number_input("Number of Players", min_value=2, max_value=9, value=2, step=1)
if st.button("Create Players", key="create_players"):
    st.session_state.players = [Player(f"Player {i+1}") for i in range(num_players)]

if "deck" not in st.session_state:
    st.session_state.deck = Deck()
if "player_hand" not in st.session_state:
    st.session_state.player_hand = []
if "community_cards" not in st.session_state:
    st.session_state.community_cards = []
if "players" not in st.session_state:
    st.session_state.players = []

# ------ Buttons on Streamlit ------

col1, col2, col3, col4, col5 = st.columns(5)

if col1.button("Shuffle Deck", key="shuffle"):
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.deck.shuffle()
    st.session_state.player_hand = []
    st.session_state.community_cards = []
    st.write("Deck shuffled!")

if col2.button("Deal Other Hands", key="deal_all"):
    for player in st.session_state.players:
        player.receive_cards(st.session_state.deck.deal(2))
    st.success("Dealt 2 cards to each player")
if col2.button("Deal Player Hand"):
    if len(st.session_state.player_hand) == 0:
        st.session_state.player_hand = st.session_state.deck.deal(2)
        st.success("Player hand dealt")
    else:
        st.warning("Player hand already dealt")

if col3.button("Burn + Turn", key="burn_turn"):
    if len(st.session_state.community_cards) == 0:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(3))  # flop
        st.success("Flop dealt")
    elif len(st.session_state.community_cards) == 3:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(1))  # turn
        st.success("Turn dealt")
    elif len(st.session_state.community_cards) == 4:
        st.session_state.deck.deal(1)  # burn
        st.session_state.community_cards.extend(st.session_state.deck.deal(1))  # river
        st.success("River dealt")
    else:
        st.warning("All community cards already dealt")

if col4.button("Show Best Hands", key="show_hands"):
    if st.session_state.players and st.session_state.community_cards:
        for player in st.session_state.players:
            player.evaluate(st.session_state.community_cards)

        # sort players by best_score (hand rank + tiebreakers)
        ranked = sorted(
            st.session_state.players,
            key=lambda p: p.best_score,
            reverse=True
        )
        winner = ranked[0]

        rank_name = [name for name, val in HandEvaluator.hand_ranks.items() if val == winner.best_score[0]][0]

        st.subheader(f"{winner.name} is the winner with {rank_name}!")
        st.write(f"{winner.name}: {rank_name} with best hand {[str(c) for c in winner.best_hand]}")
    else:
        st.warning("Deal player hands and community cards first")

if col5.button("Reset Game", key="reset"):
    st.session_state.deck = Deck()  # Reset the deck
    st.session_state.player_hand = []
    st.session_state.community_cards = []
    st.write("Game reset.")

# ------ Display ------
st.subheader("Player Hand")
if st.session_state.player_hand:
    for card in st.session_state.player_hand:
        st.write(str(card))
else:
    st.write("No cards in player hand.")

st.subheader("Community Cards")
if st.session_state.community_cards:
    for card in st.session_state.community_cards:
        st.write(str(card))
else:    
    st.write("No community cards dealt yet.")

st.subheader("Best Possible Hand")
for player in st.session_state.players:
    if player.best_hand:
        st.write(f"**{player.name}:** {[str(c) for c in player.best_hand]} (Score: {player.best_score})")
    else:
        st.write(f"**{player.name}:** No hand evaluated yet.")

st.subheader("Player Hands")
def pretty_card(card):
    suit_symbols = {
        "Hearts": "♥",
        "Diamonds": "♦",
        "Clubs": "♣",
        "Spades": "♠"
    }
    symbol = suit_symbols[card.suit]
    color = "red" if card.suit in ["Hearts", "Diamonds"] else "black"
    return f"<span style='color:{color}'>{card.rank} {symbol}</span>"

st.markdown(f"**{player.name}:**", unsafe_allow_html=True)
for card in player.hand:
    st.markdown(pretty_card(card), unsafe_allow_html=True)

    if player.best_hand:
        st.write(f"Best 5: {[str(c) for c in player.best_hand]}")
        st.write(f"Score: {player.best_score}")
        st.write(f"Hand: {[name for name, val in HandEvaluator.hand_ranks.items() if val == player.best_score[0]][0]}")

if st.session_state.player_hand and st.session_state.community_cards:
    all_cards = st.session_state.player_hand + st.session_state.community_cards
    score, best5 = HandEvaluator.best_hand(all_cards)

    rank_name = [name for name, val in HandEvaluator.hand_ranks.items() if val == score[0]][0]

    st.write(f"**Hand Rank:** {rank_name}")
    st.write(f"**Best 5 Cards:** {[str(c) for c in best5]}")
    st.write(f"**Score Details:** {score}")
else:
    st.write("Deal player hand and community cards to evaluate.")


st.subheader("Remaining Deck")
st.dataframe(st.session_state.deck.to_dataframe())
