#Apophenia Support Group

from random import shuffle
from networkx import Graph
import networkx as nx
#import pyglet as gl

class Dealer(dict):

    def shuffle(self,pile_name):
        shuffle(self[pile_name])
        
    def add_players(self,*names):
        for name in names:
            new_player_pile = Pile("%s's cards" % name)
            self[name] = new_player_pile
    
    def add_deck(self,deckname):
    
        deck_dict = {
                     "tarot": TarotCards,
                     "playing": PlayingCards
                    }
        
        if deckname in deck_dict:
            deckobj = deck_dict[deckname]()
        else:
            raise Exception("Do not recognise deck type %s" % deckname)
            
        #make new pile
        new_deck = Pile(deckobj.name)
        
        #default to 'stock', else add index to name
        if "stock" not in self.keys():
            new_deck_name = "stock"
        else:
            new_deck_index = len([x for x in self.piles.keys() if "stock" in x])
            new_deck_name = "stock %s" % new_deck_index
            
        #add empty pile to dealer dictionary
        self[ new_deck_name ] = new_deck
        #populate with contents of deck
        new_deck.init_deck(deckobj)
        #shuffle it to initialise
        shuffle(self[new_deck_name])
    
    def add_spread(self,name,spread_type,*places,**places2):
    
        spread_dict = {
                       "unlinked": Spread,
                       "line": LineSpread,
                       "cycle": CycleSpread,
                       "grid" : GridSpread,
                       "cross": CrossSpread,
                      }
        if spread_type in spread_dict:
            spread_obj = spread_dict[spread_type]
        else:
            raise Exception("Do not recognise spread type %s" % spread_type)
        
        new_spread = spread_obj(name,*places,**places2)
        
        if name not in self.spreads.keys():
            self.spreads[name] = new_spread
        else:
            exceptstr = "Spread called %s already exists!" % name
            raise Exception(exceptstr)

    def get_spread(self,name):
        return self.spreads[name]
                    
    def add_places_to_spread(self,name,*places):
        our_spread = self.spreads[name]
        for place in places:
            our_spread.add_place(place)
        our_spread.empty_places()
            
                   
    def deal_some(self,frompile,topile,n=1):
        '''deal n cards from the first pile given, to the second'''
        if len(self[frompile]) < n:
            exceptstr = "Cannot take %s cards from pile, only %s therein." % (n, len(self[frompile]))
            raise Exception(exceptstr)
        for i in range(n):
            c = self[frompile].pop(0)
            self[topile].add_cards(c)

    def deal_new_player(self,playername,n,pilefrom="stock"):
        '''add a new player playername, and deal n cards to them
           from pilefrom (defaults to "stock"'''
           
        self.add_players(playername)
        self.deal_some(pilefrom,playername,n)
    
    def spread_new_player(self,playername,spread_type, *names, **names2):

        if len(names2):
            dealout = sum([len(x) for x in names2.values()])
        else:
            dealout = len(names)
            
        self.deal_new_player(playername,dealout)
        self.add_spread("%s spread" % playername,spread_type,*names, **names2)
        self.spread_pile(playername,"%s spread" % playername)
        
    def spread_pile(self,frompile,tospread):
        '''spread out the cards from the pile in the spread
           sizes should match'''
           
        our_spread = self.spreads[tospread]
        
        spread_size = our_spread.get_size()
        
        pile_size = len(self[frompile])
        
        if pile_size != spread_size:
            exceptstr = "Spread has %s slots, %s cards given." % (spread_size, pile_size)
            raise Exception(exceptstr)
        else:
            cards = self[frompile]
            our_spread.add_cards(*cards)
            del( self[frompile][:] )

    def describe_spread(self,spread):
        our_spread = self.spreads[spread]
        print("This is the spread '%s'." % our_spread)
        
        shapedict = {"unlinked": "a haphazard spread of %s cards.",
                     "line": "a line of %s cards.",
                     "cycle": "%s cards arranged in a circle.",
                     "grid": "%s cards arranged in a %s x %s grid.",
                     "cross": "%s cards arranged in a cross.",
                    }
        composestring = shapedict[our_spread.type_name]
        if our_spread.type_name != "grid":
            print("It is composed of " + composestring % our_spread.get_size() )
        else:
            n,m = our_spread.xs, our_spread.ys 
            print("It is composed of " + composestring % (our_spread.get_size(), n, m) )
        
        print("The cards are as follows:")
        for i,place in enumerate(our_spread.nodes(data=True)):
            this_num = place[0]
            if our_spread.type_name == "cross":
                for key in our_spread.branch_dict:
                    if i+1 in our_spread.branch_dict[key]:
                        this_num = "%s (%s)" % (this_num, key)
                        
            this_name = place[1]["name"]
            try:
                this_card = place[1]["card"].get_name()
            except AttributeError:
                this_card = "No card"
            
            if i+1 < our_spread.get_size():
                punct = ","
            else:
                punct = "."
                
            print("At position %s '%s': %s%s" % (this_num, this_name, this_card, punct))
                
    def return_spread(self,fromspread,topile="stock"):
        '''return all cards in spread to a pile, default "stock"'''
        
        our_spread, our_pile = self.spreads[fromspread], self[topile]
        
        card_vals = nx.get_node_attributes(our_spread,"card").values()
        cards_in_spread = [c for c in card_vals]
        
        our_pile.add_cards(cards_in_spread)
        our_spread.empty_places()
    
    def inspect_pile(self,pile):
        our_pile = self[pile]
        return our_pile.inspect()

    def inspect_next_in_pile(self,pile):
        our_pile = self[pile]
        return our_pile.inspect_next()
                   
    def __init__(self):
        #create some default piles
        discard = Pile("discard")
        self["discard"] = discard
        
        #initialise spread dictionary
        self.spreads = dict()
    
    
class Pile(list):

    def set_name(self,name):
        self.name = name
    
    def add_cards(self,*card_objs):
        for card in card_objs:
            self.insert(0,card)
        
    def init_deck(self,deck_obj):
        '''if the pile is empty, add all cards in deck_obj to it'''
        if len(self) == 0:
            for card in deck_obj:
                self += [card]

    def set_stack(self):
        self.is_stack = not self.is_stack

    def get(self):
        if self.is_stack:
            raise Exception("%s is a stack, no peeking!" % name)
        else:
            return [x for x in self]
               
    def get_next(self):
        return self[0]
        
    def inspect(self):
        '''returns the names of the cards in the pile, unless it is a stack'''
        if self.is_stack:
            raise Exception("%s is a stack, no peeking!" % name)
        else:
            return [x.get_name() for x in self]
    
    def inspect_next(self):
        '''returns the name of card object at the top of a pile,
           does not alter anything'''
        return self.get_next().get_name()
           
    def __init__(self,name):
        self.name = name
        self.is_stack = False
    
        
class Deck(set):
    def add_cards(self,*cards):
        for card in cards:
            self.add(card)

    def remove_card(self):
        pass
            
    def add_suit(self,suit_name,value_list,**kwargs):
        '''takes name of suit and ordered list of value name strings
           kwargs take extra properties and values thereof'''
        for i, value in enumerate(value_list):
            this_card = self.card_type()
            this_card.set_suit(suit_name)
            this_card.set_value(i+1)
            this_card.set_value_name(value)
            
            for name,value in kwargs.items():
                this_card.add_quality(name,value)
                
            self.add_cards(this_card)   
    
    def get_from_suit(self,suit_name):
        return {card for card in self if card.suit == suit_name}
    
    def get_from_value_name(self,value_name):
        return {card for card in self if card.value_name == value_name}
    
    def get_from_property(self,cat,qual):
        return {card for card in self if qual in card.quality[cat]}
    
    def __init__(self):
    
        #overload this to allow type-matching of different cards
        self.card_type = Card
        
class Card(object):
        
    def set_value(self, value):
        '''integer value of card'''
        self.value = value
    
    def set_value_name(self, value_name):
        '''string name of card value'''
        self.value_name = value_name
        
    def set_suit(self, suit):
        '''suit string'''
        self.suit = suit

    def set_name(self,name):
        '''card name string'''
        self.name = name

    def get_name(self):
        return self.name
    
    def add_quality(self,cat,qual):
        try:
            self.quality[cat] += [qual]
        except AttributeError:
            self.quality = {}
            self.quality[cat] = [qual]
            
    def __init__(self):
        pass

               
class PlayingCard(Card):

    def get_name(self):
        return "The %s of %s" % (self.value_name.title(), self.suit.title())
    
     
class PlayingCards(Deck):
    
    def pick_playing_card(self,value_name,suit):
        '''return the unique [b/c playing cards] card with value name and suit
        '''
        your_card = self.get_from_value_name(value_name) & self.get_from_suit(suit)
        return list(your_card)[0]
        
    def __init__(self):
    
        self.name = "Playing cards"

        #overload PlayingCard for PlayingCard special funcs to check
        self.card_type = PlayingCard
        
        self.suits = ["spades","clubs","hearts","diamonds"]
        self.suit_symbols = "♠♣♥♦"
        self.colours = ["black", "black", "red", "red"]
        self.values = ["ace"] + [str(i) for i in range(2,11)] + ["jack", "queen", "king"]
        
        for colour, suit in zip(self.colours,self.suits):
            self.add_suit(suit,self.values, colour = colour)

class Spread(Graph):
    '''a networkx graph
       should have similar interface to pile
       
       nodes are sites, with cards as attribute "card"
       
       default spread is disconnected'''

    def empty_places(self):
        nx.set_node_attributes(self, "card", None)
                
    def set_name(self,name):
        self.name = name
        
    def add_cards(self,*cards):
        card_dic = {i+1: card for i,card in enumerate(cards)}
        nx.set_node_attributes(self, "card", card_dic)
            
    def add_place(self,name):
        num = self.number_of_nodes()
        self.add_node(num + 1, name = name)
    
    def get_size(self):
        return self.number_of_nodes()
    
    def add_link(self,place_a,place_b):
        self.add_edge(place_a,place_b)
        
    def __init__(self,name,*places,**no):
        super().__init__()
        self.name = name
        self.type_name = "unlinked"
        self.is_stack = False
        
        for place in places:
            self.add_place(place)
        
        self.empty_places()


class LineSpread(Spread):
    def __init__(self,name,*places,**no):
        super().__init__(name)
        self.type_name = "line"
        
        for place in places:
            self.add_place(place)
        
        for i,j in zip( range(len(places)), range(len(places)-1 ) ):
            a,b = i+1,j+2
            self.add_link(a,b)      

        self.empty_places()
        
        
class CycleSpread(Spread):
    def __init__(self,name,*places):
        super().__init__(name)
        self.type_name = "cycle"
        
        for place in places:
            self.add_place(place)
        
        for i,j in zip( range(len(places)), range(len(places)-1 ) ):
            a,b = i+1,j+2
            self.add_link(a,b)      
        self.add_link(len(places),1)

        self.empty_places()

        
class CrossSpread(Spread):
    
    def __init__(self,name,*no,**places_dict):
        super().__init__(name)
        self.type_name = "cross"
        
        #initialise branch dictionary to store which cards are where
        #dict[branch] gives list of numbers-of-cards in branch
        
        self.branch_dict = {}
        centre_cards = places_dict["centre"]
        
        #add central card
        self.add_place(centre_cards[0])
        self.branch_dict["centre"] = [self.nodes()[0]]
        
        #if there are additional cards stacked in the centre
        if len(centre_cards) > 1:
            for card in centre_cards[1:]:
                self.add_place(card)
                self.branch_dict["centre"] += [self.nodes()[-1]]

        for direction in ["right","bottom","left","top"]:
            if direction in places_dict:
                self.branch_dict[direction] = []
                these_cards = places_dict[direction]
                for card in these_cards:
                    self.add_place(card)
                    self.branch_dict[direction] += [self.nodes()[-1]]

        #TODO add links

        self.empty_places()
        
class GridSpread(Spread):
    def __init__(self,name,*placelists,**no):
        super().__init__(name)
        self.type_name = "grid"        
        
        self.ys = len(placelists)
        self.xs = len(placelists[0])
        
        for placelist in placelists:
            for place in placelist:
                self.add_place(place)
        
        #add horizontal edges
        for y in range(self.ys):
            for i,j in zip( range(self.xs), range(self.xs-1) ):
                a,b = (i+1) + self.xs*y, (j+2) + self.xs*y
                self.add_link(a,b)   
        
        #add vertical edges   
        for y in range(self.ys-1):
            for i,j in zip( range(self.xs), range(self.xs) ):
                a,b = (i+1) + y*self.xs, (i+1) + (y+1)*self.xs
                self.add_link(a,b)

        self.empty_places()
            
            
class TarotCard(Card):
    def get_name(self):
        if self.quality["arcana"] == ["minor"]:
            return "The %s of %s" % (self.value_name.title(), self.suit.title())
        else:
            if self.value_name in {"justice","strength","death","temperance","judgement"}:
                det = ""
            else:
                det = "the "
                
            return (det + self.value_name).title()
    
class TarotCards(Deck):

    def __init__(self):
    
        self.name = "Tarot cards"
        
        self.card_type = TarotCard
        
        self.minor_suits = ["swords","wands","pentacles","cups"]
        
        self.minor_values = [str(i) for i in range(1,11)] + ["page","knight",
                                                            "queen","king"]
                                                            
        self.major_values = ["fool","magician","high priestess","empress",
                             "emperor","hierophant","lovers","chariot",
                             "justice","hermit","wheel of fortune",
                             "strength","hanged man","death","temperance",
                             "devil","tower","star","moon","sun","judgement",
                             "world"]
        
        for suit in self.minor_suits:
            self.add_suit(suit,self.minor_values, arcana = "minor")
        
        for i, major in enumerate(self.major_values):
            self.add_suit("trumps",[major], arcana = "major")
                      
dealer = Dealer()

dealer.add_deck("tarot")

spread_places = ["the Past","the Present","the Future"]

grid_places = [["card %s" % x for x in range(1,8)],
               ["card %s" % x for x in range(8,15)],
               ["card %s" % x for x in range(15,22)]
              ]

cross_places = {
                "centre": ["Ego", "Alter Ego"],
                "top": ["Superego"],
                "right": ["Immediate Effect","Ultimate Effect"],
                "bottom": ["Id"],
                "left": ["Immediate Cause","Original Cause"],
               }
               
#dealer.spread_new_player("alice", "line", *spread_places)
dealer.spread_new_player("bob", "cross", **cross_places)
dealer.describe_spread("bob spread")
