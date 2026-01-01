"""Dialogic Pragmatics Inquiry Generator

This script allows the user to generate random material semantics frames and then generate inquiries of dialogic
pragmatic games from any material semantic frames.

Some comments:

in this script, I operate on indexes of sentences in the enumerated language whenever it's possible,
instead of operating on sentences as strings. Some functions, designed to be used by users, require inputting sentences
as strings. But those functions are considered as user-interface. Inside the engine, I'm always dealing with integers
as indexes of sentences.

I always work with frozensets instead of sets. I occasionally say sets for short, but it always means frozensets.

I always talk about enumerated language, which is represented as a list of strings in the script.
E.g. ['a_0', 'a_1', 'a_2'] would be an enumerated language with 3 sentences. So is ['red', 'Bob is nice', 'dsakfdsa'].

"""
import math
import random

import numpy
from prettytable import PrettyTable

from dp_common_funcs import *


########################################################################################################################
########################################################################################################################
#####################################          Some very basic functions          ######################################
########################################################################################################################
########################################################################################################################


def list_powerset_list(lst: list) -> list:
    """ This gives the power set of a given list as a list of frozensets """
    result = [frozenset()]
    for x in lst:
        result.extend([frozenset.union(subset, frozenset([x])) for subset in result])
    return result


def list_powerset(lst: list) -> frozenset:
    """ This gives the power set of a given list as a frozenset of frozensets """
    return frozenset(list_powerset_list(lst))


def list_powerset_(lst: list) -> frozenset:
    """ This gives the power set of a given list with the empty set removed, as a frozenset of frozensets """
    result = list_powerset_list(lst)
    del result[0]
    return frozenset(result)


def powerset(m: frozenset) -> frozenset:
    """ This gives the power set of a given frozenset as a frozenset of frozensets """
    return list_powerset(list(m))


def powerset_(m: frozenset) -> frozenset:
    """ This gives the power set of a given frozenset, with the empty set removed, as a frozenset of frozensets """
    return list_powerset_(list(m))


def agentswitch(x):
    """ This flips the agents: sending 'CL' to 'CR' and 'CR' to 'CL' """
    if x == 'CL':
        return 'CR'
    else:
        return 'CL'


def wrap_list(lst, items_per_line=5):
    """ This is used to display long lists. By default, it presents five elements on each line. """
    lines = list()
    for i in range(0, len(lst), items_per_line):
        chunk = lst[i:i + items_per_line]
        line = ", ".join("{!r}".format(x) for x in chunk)
        lines.append(line)
    return ",\n ".join(lines)

def stage_row(x, stage):
    """ This is used in the .show() method for MSF and inquiry, to display stages except the first stage. """
    if stage.TargetMove == None:
        x.add_row([stage.TurnNum,
               stage.Agent,
               None,
               stage.PragSig,
               stage.PrimeMove.MoveLabel,
               list(stage.FScoreSit.CL.AC),
               list(stage.FScoreSit.CL.RC),
               list(stage.FScoreSit.CL.AE),
               list(stage.FScoreSit.CL.RE),
               list(stage.FScoreSit.CR.AC),
               list(stage.FScoreSit.CR.RC),
               list(stage.FScoreSit.CR.AE),
               list(stage.FScoreSit.CR.RE)
               ])
    else:
        x.add_row([stage.TurnNum,
               stage.Agent,
               stage.TargetMove.TurnNum,
               stage.PragSig,
               stage.PrimeMove.MoveLabel,
               list(stage.FScoreSit.CL.AC),
               list(stage.FScoreSit.CL.RC),
               list(stage.FScoreSit.CL.AE),
               list(stage.FScoreSit.CL.RE),
               list(stage.FScoreSit.CR.AC),
               list(stage.FScoreSit.CR.RC),
               list(stage.FScoreSit.CR.AE),
               list(stage.FScoreSit.CR.RE)
               ])


def first_stage_row(x, stage):
    """ This is used in the .show() method for MSF and inquiry, to display the first stage """
    x.add_row([stage.TurnNum,
               stage.Agent,
               None,
               stage.PragSig,
               stage.PrimeMove.MoveLabel,
               list(stage.FScoreSit.CL.AC),
               list(stage.FScoreSit.CL.RC),
               list(stage.FScoreSit.CL.AE),
               list(stage.FScoreSit.CL.RE),
               list(stage.FScoreSit.CR.AC),
               list(stage.FScoreSit.CR.RC),
               list(stage.FScoreSit.CR.AE),
               list(stage.FScoreSit.CR.RE)
               ])


########################################################################################################################
########################################################################################################################
###############################################          Move          #################################################
########################################################################################################################
########################################################################################################################


class MoveType:
    """
    A class used to represent a move-type.
    It only records the premises, the conclusions, both as numbers, the valence (reason for or reason against)
    and the label of a move. Labels are of form: a_1, a_2, a_3 entails/excludes a_4.

    Attributes
    ----------
    Prem : frozenset
        a frozenset of numbers, each number is the index of a sentence in the list for the enumerated language
        for example, a Prem of a MoveType can be frozenset([1, 2, 4]), meaning the premise of the move is the sentences
        indexed by 1, 2, 4 in the enumerated language.
    Val : str
        it's either 'reason for' or 'reason against'
    Conc : int
        the index of a sentence in the enumerated language, as an integer
    MoveLabel : str
        a str for the name of this move-type, e.g. 'a_1, a_2, a_3 entails a_4', or 'a_2, a_5 excludes a_1'
    """
    def __init__(self, Prem, Val, Conc, MoveLabel):
        self.Prem = Prem
        self.Val = Val
        self.Conc = Conc
        self.MoveLabel = LabelMaker(MoveLabel, self.Prem, self.Val, self.Conc)
        self.ShortLabel = ShortLabelMaker(Prem = self.Prem, Val = self.Val, Conc = self.Conc)

    def show(self):
        print(self.MoveLabel)

    def to_text(self):
        if self.Val == 'reason for':
            text = str(set(self.Prem)) + '⊨' + str(self.Conc)
        else:
            text = str(set(self.Prem)) + '#' + str(self.Conc)
        return text

def LabelMaker(label, prem, val, conc):
    if label:
        return label
    else:
        label = 'a_'
        for p in prem:
            label += str(p) + ', a_'
        label = label[0:-4] # strip trailing ', a_'
        if val == 'reason for':
            label += ' entails '
        else:
            label += ' excludes '
        label += 'a_' + str(conc)
        return label


def ShortLabelMaker(Prem, Val, Conc):
    shortlable = str()
    for p in list(Prem):
        shortlable = shortlable + str(p)
    if Val == 'reason for':
        shortlable = shortlable + 'F'
    if Val == 'reason against':
        shortlable = shortlable + 'A'
    shortlable = shortlable + str(Conc)
    return shortlable

def SameMoveType(movetype_1, movetype_2):
    if movetype_1.Prem == movetype_2.Prem and movetype_1.Val == movetype_2.Val and movetype_1.Conc == movetype_2.Conc:
        return True
    else:
        return False

def flip_val(sequent: MoveType) -> MoveType:
    if sequent.Val == 'reason for':
        return MoveType(sequent.Prem, 'reason against', sequent.Conc,
                                    sequent.MoveLabel.replace('entails', 'excludes'))
    else:
        return MoveType(sequent.Prem, 'reason for', sequent.Conc,
                                    sequent.MoveLabel.replace('excludes', 'entails'))


########################################################################################################################
########################################################################################################################
################################################          MSF          #################################################
########################################################################################################################
########################################################################################################################


class MSF:
    """
    A class used to represent a material semantic frame.
    It only records the premises, the conclusions, both as numbers, the valence (reason for or reason against)
    and the label of a move. Labels are of form: a_1, a_2, a_3 entails/excludes a_4.

    Parameters
    ----------
    L : list
        The enumerated language
    IMP : frozenset
        a set of implications, each implication is a tuple, whose first element is a frozenset of integers, for indexes
        of premises and second element an integer, for the index of the conclusions.
    INC : frozenset
        a set of incoherent sets. Each member of INC is a frozenset of integers. Each integer is an index for a
        sentence in the enumerated language.

    Attributes
    ----------
    L : list
        The enumerated language
    IMP : frozenset
        a set of implications, each implication is a tuple, whose first element is a frozenset of integers, for indexes
        of premises and second element an integer, for the index of the conclusions.
    INC : frozenset
        a set of incoherent sets. Each member of INC is a frozenset of integers. Each integer is an index for a
        sentence in the enumerated language.
    EXC : dict
        a dictionary of exclusions. If \Gamma is incoherent, then for any \gamma in \Gamma, \Gamma - \gamma excludes
        \gamma. This dictionary maps the index of each sentence in the language to the set of sets of indexes of sentences
        that exclude this sentence. E.g. EXC[2] = {{1},{3,4}}.
    ForMove : frozenset
        the set of all possible for moves in this MSF. each member of the set is an object of class MoveType with its
        Val == 'reason for'. They correspond one to one with members of IMP of this MSF.
    AgainstMove : frozenset
        the set of all possible against moves in this MSF. each member of the set is an object of class MoveType with
        its Val == 'reason against'. They correspond one to one with members of EXC of this MSF.
    StrangeImp:
        the set of all implications that are strange in the sense that although the set of premises is not persistently
        incoherent, the union of premises and its conclusion is persistently incoherently. We prohibit players from
        using such implications to make moves, as asserting such implications will immediately put the player in to a
        persistenlty incoherent set of commitment.
    Code : str
        the code of a MSF can be used to regenerate the same MSF using Decode_MSF function. it's a string of form
        'len' + n + 'imp' + m + 'inc' + s, where n is the length of language, m is the code for imp, s is the code for inc.

        """
    def __init__(self, L, IMP, INC): # documented under the class
        self.L = L  # Enumerated Language, as a list of sentences
        self.IMP = IMP  # Set of Implications
        self.INC = INC  # Set of Incompatibilities
        self.ExFF = ExFF_sets(self.L, self.INC)
        self.EXC = EXC_generator(L, INC)  # Set of Exclusions
        self.ForMove = PossibleForMoves(L, IMP, INC)
        self.AgainstMove = PossibleAgainstMoves(L, INC)
        self.StrangeImp = StrangeImp(self.L, self.IMP, self.INC)
        self.Code = Code_MSF(self.L, self.IMP, self.INC)
        self.NumberOfReasons = num_reason_calculator(language = self.L, for_moves = self.ForMove, against_moves = self.AgainstMove)
        self.ReasonRatio = reason_ratio_calculator(language = self.L, for_moves= self.ForMove, against_moves = self.AgainstMove)
        self.MoveDict = move_dict_generator(self)

    def show(self):
        """
        This method prints out the MSF in a redundant and ugly way but is hopefully minimally usable for those who want
        to see what's in the MSF
        """
        print(
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^Beginning of a MSF display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print('You can retrieve this MSF using the Decode_MSF function with the following code:')
        print(self.Code)

        # First calculate pragmatically significant implications.
        imp = list()
        for i in self.ForMove:
            imp.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        imp.sort()

        # Calculate how many implications are required by ExFF. The number doesn't include those required by both ExFF
        # and CO. If an implication is required by both ExFF and CO, we consider it required by CO.
        exff_co_overlap = 0
        for i in self.ExFF:
            exff_co_overlap = exff_co_overlap + len(i)
        num_exff_required = len(self.ExFF)*len(self.L) - exff_co_overlap

        # Calculate strange implications.
        strange = list()
        for i in self.StrangeImp:
            strange.append(str(set(i[0])) + '⊨' + str(i[1]))
        strange.sort()

        print('This MSF contains in total', len(self.IMP), 'implications, among which', len(imp), 'are pragmatically',
              'significant,', len(CO_generator(self.L)), 'are required by CO,', num_exff_required, 'are required by ExFF',
              'and', len(strange), 'are strange in the sense that the premises and the conclusion are jointly persistently incoherent.')
        print('(Note that if an implication is required both by CO and ExFF, it\'s considered to be required by CO but not ExFF.)')
        print('This MSF contains', len(self.ForMove), 'pragmatically significant reasons-for with the following distribution:', self.NumberOfReasons['for'], '.')
        print('This MSF contains', len(self.AgainstMove), 'pragmatically significant reasons-against with the following distribution:', self.NumberOfReasons['against'], '.')
        print('The Reason Ratio, #reasons-for over #reasons-against, for sentences in this MSF, is as follows:', self.ReasonRatio)
        print('This MSF contains', len(self.INC), 'incoherent sets, among which', len(self.ExFF), 'are persistently incoherent.')
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")


        print('This MSF contains the following',len(imp) ,'pragmatically significant implications, i.e. implications that',
              'are not required by CO or ExFF and are not strange.')
        print(wrap_list(imp, 5))
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        print('This MSF contains the following', len(strange), 'implications',
              'that are strange in the sense that the premises and the conclusion are jointly persistently incoherent.',
              'We currently do not allow agents to use these implications as reason-fors.')
        print(wrap_list(strange, 5))
        print(
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        # Then print out pragmatic significant reason fors.
        print('Thus, this MSF has the following pragmatically significant reason-fors:')
        print(
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        for i in range(len(self.L)):
            f = list()
            for j in self.ForMove:
                if j.Conc == i:
                    f.append(str(set(j.Prem)))
            f.sort()
            print(i, 'has the following', len(f), 'pragmatically significant reasons for it:')
            print(wrap_list(f, 5))
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        # Print out incoherent sets.
        inc = list()
        for i in self.INC:
            inc.append(str(set(i)))
        inc.sort()
        print('This MSF contains the following', len(inc), 'incoherent sets:')
        print(wrap_list(inc, 5))
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        # Print out persistently incoherent sets.
        pinc = list()
        for i in ExFF_sets(self.L, self.INC):
            pinc.append(str(set(i)))
        pinc.sort()
        print('Among all incoherent sets, the following', len(pinc),' are persistently incoherent:')
        print(pinc)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        # Print out reason againsts.
        print('Thus, this MSF contains the following reasons against:')
        print(
            "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        for i in self.EXC:
            c = list()
            for j in self.EXC[i]:
                c.append(str(set(j)))
            c.sort()
            print(i, 'has the following', len(c) ,'reasons against it:')
            print(wrap_list(c, 5))
            print(
                "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        print('The universe of reasons generated by this MSF contains the following', len(self.ForMove),' (pragmatically significant) reasons-for:')
        reasons_for = list()
        for i in self.ForMove:
            reasons_for.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        reasons_for.sort()
        print(wrap_list(reasons_for, items_per_line=5))

        print('The universe of reasons generated by this MSF contains the following', len(self.AgainstMove),' (pragmatically significant) reasons-against:')
        reasons_against = list()
        for i in self.AgainstMove:
            reasons_against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        reasons_against.sort()
        print(wrap_list(reasons_against, items_per_line=5))


        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^End of a MSF display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")


def move_dict_generator(msf): # keep a map from text representations of moves to the actual MoveType objects
    move_dict = dict()
    for move in msf.ForMove:
        move_dict[move.to_text] = move
    for move in msf.AgainstMove:
        move_dict[move.to_text] = move
    return move_dict

def num_reason_calculator(language, for_moves, against_moves):
    num_reason_for = [0]*len(language)
    num_reason_against = [0]*len(language)
    for i in for_moves:
        num_reason_for[i.Conc] = num_reason_for[i.Conc] + 1
    for i in against_moves:
        num_reason_against[i.Conc] = num_reason_against[i.Conc] + 1
    dct_num_reason_for = dict()
    dct_num_reason_against = dict()
    for i in range(len(language)):
        dct_num_reason_for[i] = num_reason_for[i]
        dct_num_reason_against[i] = num_reason_against[i]
    result = dict()
    result['for'] = dct_num_reason_for
    result['against'] = dct_num_reason_against
    return result

def reason_ratio_calculator(language, for_moves, against_moves):
    num_reason_for = [0]*len(language)
    num_reason_against = [0]*len(language)
    for i in for_moves:
        num_reason_for[i.Conc] = num_reason_for[i.Conc] + 1
    for i in against_moves:
        num_reason_against[i.Conc] = num_reason_against[i.Conc] + 1
    result = dict()
    for i in range(len(language)):
        result[i] = safe_divide_for_display(num_reason_for[i], num_reason_against[i])

    return result

def Possible_IMP_Generator(language: list) -> frozenset:
    """
    Generate the set of all possible implications for a given enumerated language.
    Any set of premises with any conclusion is a potential implication.

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']

    Returns
    -------
    frozenset
        frozenset set of implications, each implication is a tuple, whose first element is a frozenset of integers and
        second element an integer
    """
    result = list()
    lst = [i for i in range(len(language))]
    for i in list_powerset_(lst):
        for j in range(len(language)):
            result.append((frozenset(i), j))
    return frozenset(result)


def CO_generator(language: list) -> frozenset:
    # This function generates the list of implications required by CO for any atomic language
    result = list()
    lst = [i for i in range(len(language))]
    for i in list_powerset_(lst):
        for j in i:
            result.append((frozenset(i), j))
    return frozenset(result)


def CO_checker(language: list, imp: frozenset):
    # This takes a set of implications and checks if that set satisfies CO in a given language
    return CO_generator(language).issubset(imp)


def Possible_non_CO_IMP_Generator(language: list) -> frozenset:
    return Possible_IMP_Generator(language = language) - CO_generator(language = language)


def RandomIMP(language: list, chance = 1/2, size = 'random') -> frozenset:
    """
    Generate a random set of implications of a given enumberated langauge by sampling from the set of all possible
    implications for a given enumerated language.
    It first generates the size of the resulting IMP, k, by generating a integer in [0, #all possible IMP] following binomial
    distribution, then sampling k elements in all possible implications without replacement.

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']

    Returns
    -------
    frozenset
        frozenset set of some implications, each implication is a tuple, whose first element is a frozenset of integers and
        second element an integer
    """
    if size != 'random':
        return frozenset.union(frozenset(random.sample(Possible_non_CO_IMP_Generator(language), size)), CO_generator(language))
    else:
        k = numpy.random.binomial(len(Possible_non_CO_IMP_Generator(language)), chance)
        return frozenset.union(frozenset(random.sample(Possible_non_CO_IMP_Generator(language), k)), CO_generator(language))


def Possible_INC_Generator(language: list) -> frozenset:
    """
    Generates all possible incoherence for a given language, namely all subsets of the language of size 2 or higher

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']

    Returns
    -------
    frozenset
        a frozenset set of sets of integers. It contains all subsets of the (indexes of the) enumerated language, except
        all singletons, since we assume singletons are always coherent.
    """
    lst = [i for i in range(len(language))]
    result = list_powerset_(lst) - frozenset([frozenset([i]) for i in lst])
    return result


def RandomINC(language: list, size = 'random', chance = 1/2) -> frozenset:
    """
    This generates a random set of sets of integers, to be interpreted as the set of all incoherent sets of sentences
    in some MSF.
    Note every single sentence is always coherent and the entire language is always incoherent.
    Like generating random implications, we first generate the size of the return set following a binomial distribution
    and then generate the return by sampling from all possible incoherent sets.

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']

    Returns
    -------
    frozenset
        A set of sets. Each set in it is a set of indexes of sentences that are jointly incoherent.
        Every single sentence is always coherent and hence is never in the output set.
        The entire language is always incoherent and hence is always in the output set.
    """
    lst = [i for i in range(len(language))]

    if size != 'random':
        result = frozenset(random.sample(Possible_INC_Generator(language) - frozenset([frozenset(lst)]), size - 1))
        return frozenset.union(result, frozenset([frozenset(lst)]))
    else:
        k = numpy.random.binomial(len(Possible_INC_Generator(language)), chance)
        result = frozenset(random.sample(Possible_INC_Generator(language), k))
        return frozenset.union(result, frozenset([frozenset(lst)]))


def ExFF_sets(language: list, inc: frozenset) -> frozenset:
    exff_sets = list()
    for gamma in inc:
        if math.pow(2, (len(language) - len(gamma))) <= len(inc):
            n = 0
            for delta in inc:
                if gamma.issubset(delta):
                    n = n + 1
            if n >= math.pow(2, (len(language) - len(gamma))):
                exff_sets.append(gamma)
    return frozenset(exff_sets)



def EXC_generator(lang: list, inc: frozenset) -> dict:
    """
    This generates a dictionary of exclusions for a language with a given INC. The return is completely decided by the
    input. However, this is no long simply a book-keeping. I have removed premises that are persistently incoherent
    from being counted as a reason against. Before, every persistently incoherent set will a reason against any sentence
    not in the set. By definition, adding anything into a persistently incoherent set doesn't make the new set coherent.
    However, if the CL happens to use such a persistently incoherent set as a reason against a sentence outside the set,
    CL will directly put himself into persistently incoherent position and the inquiry will end in two steps.
    After the fix, CL will never do that any more.

    Parameters
    ----------
    lang : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']
    inc : frozenset
        A frozenset of frozensets of intgers
        each frozenset in it is a set of indexes of sentences of the language

    Returns
    -------
    dict
        a dictionary of exclusions. If \Gamma is incoherent, then for any \gamma in \Gamma, \Gamma - \gamma excludes
        \gamma. This dictionary maps the index of each sentence in the language to the set of sets of indexes of sentences
        that exclude this sentence. E.g. EXC[2] = {{1},{3,4}}; this means that there are two and only two incoherent
        sets that contain the sentence indexe by 2, namely {1,2} and {2,3,4}
    """
    exff = ExFF_sets(lang, inc)
    result = dict()
    for i in range(len(lang)):
        against = list()
        for n in inc:
            if i in n and n - frozenset([i]) not in exff and n - frozenset([i]) != set():
                against.append(n - frozenset([i]))
        result[i] = frozenset(against)
    return result




def StrangeImp(lang, imp, inc):
    # Some implications are weird in the sense that the premises and conclusion are jointly
    # persistently in concsistent. We don't allow agents to use such IMP in a for-move.
    strangeimp = list()
    for i in imp:
        if i[0] not in ExFF_sets(lang, inc):
            if frozenset.union(i[0], frozenset([i[1]])) in ExFF_sets(lang, inc):
                strangeimp.append(i)
    return frozenset(strangeimp)


def PossibleForMoves(lang: list, imp: frozenset, inc: frozenset):
    formove = list()
    strangeimp = list()#Some implications are weird in the sense that the premises and conclusion are jointly
                       #persistently in concsistent. We don't allow agents to use such IMP in a for-move.
    for i in imp:
        if frozenset.union(i[0], frozenset([i[1]])) in ExFF_sets(lang, inc):
            strangeimp.append(i)
    pool = imp - CO_generator(lang) - ExFF_generator(lang, inc) - frozenset(StrangeImp(lang, imp, inc))
    for i in pool:
        formove.append(MoveType(Prem = i[0], Val = 'reason for', Conc = i[1], MoveLabel = str(sorted({lang[i] for i in i[0]})) + ' entails ' + lang[i[1]]))
    return frozenset(formove)


def CO_closure(language: list, imp: frozenset) -> frozenset:
    return frozenset.union(imp, CO_generator(language))




def RandomIMP_CO(language: list, size = 'random', chance = 1/2) -> frozenset:
    return CO_closure(language, RandomIMP(language = language, chance = chance, size = size))



def Code_MSF(language, imp, inc):
    """
        This function generates a code for an MSF. It's intentionally made to asks for language, imp, inc as inputs,
        instead of asking for an MSF, to avoid circularity, as we use it in initializing the .Code attribute of MSF.

        Parameters
        ----------
        language : list
            A list of strings, each string is a sentence. Namely, the enumerated language from which the original encoded MSF
            was generated and the new recovered MSF will be generated.
            e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']
        imp : frozenset
            The frozenset of all implications of the original MSF.
        inc : frozenset
            The frozenset of all incoherent sets of the original MSF.

        Returns
        -------
        str
            The function returns a string of form 'len' + n + 'imp' + m + 'inc' + s, where n is the length of language,
            m is the code for imp, s is the code for inc.
        """

    imp_code = str()
    inc_code = str()
    for i in list(Possible_IMP_Generator(language)):
        if i in imp:
            imp_code = imp_code + '1'
        else:
            imp_code = imp_code + '0'
    for i in list(Possible_INC_Generator(language)):
        if i in inc:
            inc_code = inc_code + '1'
        else:
            inc_code = inc_code + '0'
    return 'len'+str(len(language))+'imp'+str(int(imp_code, 2))+'inc'+str(int(inc_code, 2))


def Decode_MSF(language, code):
    """
    This function generates an MSF using a code for MSF.

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence. Namely, the enumerated language from which the original encoded MSF
        was generated and the new recovered MSF will be generated.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']
    code : str
        A str for coding an MSF.

    Returns
    -------
    MSF
        An MSF identical to the originally encoded MSF. Note that they are identical in the sense that all artributes of
        them are the same. But they typically do not have the same identity assigned by Python.
    """

    lang_len = int(code[3 : code.find('imp')])
    if lang_len != len(language):
        print('Error: This code only works for language with', lang_len, 'sentences.')
    else:
        inc_code_int = int(code[code.find('inc') + 3:])
        imp_code_int = int(code[code.find('imp') + 3: code.find('inc')])
        possible_imp = list(Possible_IMP_Generator(language))
        possible_inc = list(Possible_INC_Generator(language))
        imp = list()
        inc = list()
        imp_code = format(imp_code_int, '0' + str(len(possible_imp)) + 'b')
        inc_code = format(inc_code_int, '0' + str(len(possible_inc)) + 'b')
        for i in range(len(possible_imp)):
            if imp_code[i] == '1':
                imp.append(possible_imp[i])
        for i in range(len(possible_inc)):
            if inc_code[i] == '1':
                inc.append(possible_inc[i])
        return MSF(language, frozenset(imp), frozenset(inc))

def ExFF_generator(language: list, inc: frozenset) -> frozenset:
    # This generates the list of implications required by ExFF given a list of implications (IMP) and a list of
    # incoherences (INC).
    # One may have the concern that adding this generated set to an IMP doesn't always make that set closed
    # under ExFF. Perhaps, more requirements can be generated in the process of adding. That is not the case.
    # The process of adding doesn't change INC. It only changes IMP. So adding this generated set to a given IMP,
    # does make that IMP closed under ExFF relative to a INC.
    exff_sets = list()
    result = list()
    for gamma in inc:
        if math.pow(2, (len(language) - len(gamma))) <= len(inc):
            n = 0
            for delta in inc:
                if gamma.issubset(delta):
                    n = n + 1
            if n >= math.pow(2, (len(language) - len(gamma))):
                exff_sets.append(gamma)

    for gamma in exff_sets:
        for i in range(len(language)):
            result.append((gamma, i))
    return frozenset(result)


def ExFF_checker(language: list, imp: frozenset, inc: frozenset):
    # This function checks if a given a set of implications satisfy ExFF for a given set of incoherence in a given
    # language.
    return ExFF_generator(language, inc).issubset(imp)


def ExFF_closure(language: list, imp: frozenset, inc: frozenset) -> frozenset:
    return frozenset.union(imp, ExFF_generator(language, inc))

def MSF_closure(language: list, imp: frozenset, inc: frozenset):
    return MSF(L=language, IMP=ExFF_closure(language = language, imp=CO_closure(language=language, imp=imp), inc=inc),
               INC=inc)


def RandomIMP_CO_ExFF(language: list, inc: frozenset, imp_size = 'random', imp_chance = 1/2) -> frozenset:
    return ExFF_closure(language, RandomIMP_CO(language = language, size = imp_size, chance = imp_chance), inc)


def RandomIMP_CO_ExFF_with_random_INC(language: list) -> frozenset:
    # The current method used to generate a random IMP is by first randomly sampling from all possible IMPs
    # and then add all ones required by CO and ExFF (and potentially other further requirements) to the sample.
    # An alternative way to do so is to first put in all required ones and then sample from the non-required ones.
    # I now think these two ways are equivalent. It's as if you are generating a binary number of the length of all
    # possible implications relations. Suppose that there are 60 possible ones in total and 36 of them are required.
    # It's as if you are generating a binary number of 60 digits and (say) the first 36 of them (on the left) are set
    # to be 1 by fiat. It doesn't matter for the later 24 digits whether you are only generating the later 24 digits
    # and then add 36 1's in front of them or you generate 60 digits and make the first 36 of them 1.
    # Another question is whether the current procedure I use to generate these digits are faithful. What I do now is
    # first generate how many ones are there and then pick where the ones are at. I think it works well.
    return ExFF_closure(language, RandomIMP_CO(language), RandomINC(language))


def all_IMP_CO_ExFF(language: list, inc: frozenset) -> frozenset:
    # This function general all implications that satisfy CO and ExFF (given a INC) in a given langauge.
    # Actually running it will almost certainly give us a memory error.
    result = list()
    m = powerset(
        Possible_IMP_Generator(language) - frozenset.union(CO_generator(language), ExFF_generator(language, inc)))
    for x in m:
        result.append(frozenset.union(m, frozenset.union(CO_generator(language), ExFF_generator(language, inc))))
    return frozenset(result)


def PossibleAgainstMoves(lang, inc):
    againstmove = list()
    exc = EXC_generator(lang, inc)
    for i in range(len(lang)):
        for s in exc[i]:
            againstmove.append(MoveType(s, 'reason against', i, str(sorted({lang[n] for n in s})) + ' excludes ' + lang[i]))
    return frozenset(againstmove)






def RandomMSF(language, imp_size = 'random', imp_chance = 1/2, inc_size = 'random', inc_chance = 1/2):
    """
    Generate a random msf according to parameters provided.

    Parameters
    ----------
    language : list
        A list of strings, each string is a sentence.
        e.g. ['a_0', 'a_1', 'a_2'] or ['red', 'Bob is nice', 'Yao is cool']
    imp_size : 'random' or int
        This parameter controls the size of IMP directly.
        However, the resulting IMP of the MSF may not be of the exact size spcified by this parameter.
        It's kinda tricky. The current way of generating IMP is that we first randomly draw from implications that are not
        required by CO. Then add all implications required by CO. Then add all implications required by ExFF.
        This parameter sets the number of implications to be drawn from all potential implications that are not required
        CO. However, the implications so drawn may overlap with implications required by ExFF. The size of IMP equals
        imp_size + #CO required implications + #ExFF required implications - size of the overlap between drawn non-CO
        implications and ExFF required implications.
        Also note that this parameter is always larger than the number of pragmatically significant implications. Pragmatically
        significant implications form a (in most cases, proposal) subset of all non-CO implications. As some non-CO implications
        are also not pragmatically significant, e.g. they can be strange or required by ExFF (though not CO).
        This complication makes this parameter not as sharp as one may expect, since it doesn't just set the size.
        It nevertheless controls the size of IMP roughly.
        One way to use this parameter is to first randomly generate some MSFs and see how many pragmatically significant
        implications those MSFs contain. Then set and tweak this parameter.
    imp_chance : int (0 to 1)
        the chance of any potential imp, i.e. a pair of a subset of the language and a sentence, being an actual
        imp. This parameter will only make a difference if imp_size is not 'random'.
    inc_size : 'random' or int
        This parameter sets the size of INC directly. It doesn't have any complication as imp_size does.
        Note, the entire language is always incoherent. If inc_size = 9, there will be eight proper subsets of the
        language get counted as incoherent, since the entire language is always incoherent.
    inc_chance : int (0 to 1)
        the chance of any non-singleton proper subset of the language being incoherent. This parameter will only make
        a difference if inc_size is 'random'.
    Returns
    -------
    frozenset
        a frozenset set of sets of integers. It contains all subsets of the (indexes of the) enumerated language, except
        all singletons, since we assume singletons are always coherent.
    """
    inc = RandomINC(language = language, size = inc_size, chance = inc_chance)
    imp = RandomIMP_CO_ExFF(language = language, inc = inc, imp_size = imp_size, imp_chance = imp_chance)
    return MSF(language, imp, inc)




def SSMeaning(msf, object, valence = 'for'):
    # This is an implementation of Dan Kaplan's vee-function in his semantics for single succedent.
    # Note: when we calculate the vee-function, we consider all reasons, including the ones that are not pragmatically significant.
    # input msf is the msf we are operating in.
    # input 'object' should be a list of implications. For example, it can be [([2,3,4],1), ([1,3,4],5)]
    # or [([1,3,5], None), ([1,3,5], None)]. Formally, input 'object' should be a list of tuples.
    # The first element of the tuple is a list of indexes for sentences, the second element is either a number (index)
    # or None. By making the consequent None, you effectively leave it empty.
    # valence specifies whether we are trying to apply vee-function to reason-for or reason-against. It must either be 'for'
    # or 'against'.
    c = object[0][1]    # We first find out what the consequent of the implications are.
                        # For the single-succedent system, all implications of the input set must have the same consequent.
    result = list()
    finalresult = frozenset()
    display = ''
    if valence == 'for':
        if all([p[1] == c for p in object]):    # Here we check if the succedent of all reasons in the input set are the same.
            if c == None:
                for p in object:
                    count = list()
                    for i in msf.IMP:
                        if frozenset(p[0]).issubset(i[0]):
                            count.append((i[0] - frozenset(p[0]), i[1]))
                    result.append(frozenset(count))
                finalresult = frozenset.intersection(*result)
                for i in finalresult:
                    display = display + str(list(i[0])) + '⊨' + str(i[1]) + ', '
                print('Applying the vee-function to', object, 'as reasons-for gives the following set of (prima-facie) implications:')
                print('{' + display[:-2] + '}')
                return finalresult
            else:
                for p in object:
                    count = list()
                    for i in msf.IMP:
                        if i[1] == c:
                            if frozenset(p[0]).issubset(i[0]):
                                count.append((i[0] - frozenset(p[0]), None))
                    result.append(frozenset(count))
                finalresult = frozenset.intersection(*result)
                for i in finalresult:
                    display = display + str(list(i[0])) + '⊨' + str(i[1]) + ', '
                print('Applying the vee-function to', object, 'as reasons-for gives the following set of (prima-facie) implications:')
                print('{' + display[:-2] + '}')
                return finalresult

        else:
            print('For single succedent sysmtems, the second elements of ordered pairs in the input list must all be uniform'
                    'for the return to be none-empty.They can either all be None, or a particular sentence.')
    elif valence == 'against':
        if all([p[1] == c for p in object]):    # Here we check if the succedent of all reasons in the input set are the same.
            if c == None:
                rawresult = list()
                for p in object:
                    count = list()
                    for i in msf.INC:
                        if frozenset(p[0]).issubset(i):
                            count.append(i - frozenset(p[0]))
                    rawresult.append(frozenset(count))
                rawresult = frozenset.intersection(*rawresult)
                for i in rawresult:
                    for j in i:
                        result.append((i-frozenset([j]), j))
                for i in result:
                    display = display + str(list(i[0])) + '#' + str(i[1]) + ', '
                print('Applying the vee-function to', object, 'as reasons-against gives the following set of (prima-facie) implications:')
                print('{' + display[:-2] + '}')
                return result
            else:
                for p in object:
                    count = list()
                    for i in msf.INC:
                        if frozenset.union(frozenset(p[0]), frozenset([p[1]])).issubset(i):
                            count.append((i - frozenset.union(frozenset(p[0]), frozenset([p[1]])), None))
                    result.append(frozenset(count))
                finalresult = frozenset.intersection(*result)
                for i in finalresult:
                    display = display + str(list(i[0])) + '#' + str(i[1]) + ', '
                print('Applying the vee-function to', object, ' as reasons-against gives the following set of (prima-facie) implications:')
                print('{' + display[:-2] + '}')
                return finalresult
        else:
            print('For single succedent sysmtems, the second elements of ordered pairs in the input list must all be uniform'
                    'for the return to be none-empty.They can either all be None, or a particular sentence.')
    else:
        print('valence must be either \'for\' or \'against\'. If you do not specify, it is \'for\' by default. ')
        return frozenset()


########################################################################################################################
############################################          CM closure          ##############################################
########################################################################################################################

def CM_IMP_closure_once(input_IMP):
    """
    Close the input_IMP under CM once.
    CM: if \Gamma implies A and \Gamma implies B, then \Gamma, A implies B.

    Parameters
    ----------
    input_IMP : frozenset
        A frozenset of implications, where each implication is a tuple, whose first element is a frozenset of indexes of
        sentences and second element is an index of a sentence.
    Returns
    -------
    frozenset
        A frozenset set of implications. Namely, the one obtained by closing the input_IMP under CM once.
    """

    imp_unsorted = list()
    # We first change the format of the input IMP to make it earsier to sort
    for p in input_IMP:
        imp_unsorted.append(( list(p[0]), p[1] ))
    # We sort the input IMP in its new format. The point of changing format is completely for this sorting. In the old
    # format, the input_IMP will be sorted into undesired order. In the new format, all implications with the same premises
    # on the left will be sorted together.
    imp = sorted(imp_unsorted)
    i = 0
    j = 0
    # i and j are two indices we use to enumerate through imp. After the sorting, the input_IMP are in the order such that
    # implications with the same premises are adjacent. This allows us to see the input_IMP as partitioned into chunks.
    # Each chunk contains implications with the same premises. The idea is that i will be pointing to the first implication
    # in each chunk at a time and j will go through all elements in that chunk.

    # I call such a chunk "op_group", standing for "operating group", i.e. the group of implications we operate on
    # For example, if the premise set \Gamma = [1,3,5] implies and only implies 2 and 4 in the input_IMP.
    # [([1,3,5], 2), ([1,3,5], 4)] would be an op_group and for this group, op_group_rhs would be [2,4] while op_group_lhs
    # would be [1,3,5].
    # To close an IMP under CM once, we only have to, for each op_group, for any m in op_group_rhs and any k in op_group_rhs,
    # we add the implication (op_group_lhs + [m], k).
    # This procedure will generate some implications that are already in the input_IMP. But that's okay.
    op_group_rhs = list()
    new_imps = list()
    while i in range(len(imp)):
        # in each chunk at a time and j will go through all elements in that chunk.
        op_group_lhs = imp[i][0]
        while imp[i][0] == imp[j][0]:
            op_group_rhs.append(imp[j][1])
            j = j + 1
            if j not in range(len(imp)):
                break
        for k in op_group_rhs:
            for m in op_group_rhs:
                new_imps.append((frozenset.union(frozenset(op_group_lhs), frozenset([k])), m))
        op_group_rhs = list()
        i = j
    return frozenset.union(input_IMP, frozenset(new_imps))


def CM_IMP_closure(input_IMP):
    """
    Close the input_IMP under CM until the fixed point is reached.
    CM: if \Gamma implies A and \Gamma implies B, then \Gamma, A implies B.

    Parameters
    ----------
    input_IMP : frozenset
        A frozenset of implications, where each implication is a tuple, whose first element is a frozenset of indexes of
        sentences and second element is an index of a sentence.
    Returns
    -------
    frozenset
        A frozenset set of implications. Namely, the one obtained by closing the input_IMP under CM until the fixed point
        is reached.
    """
    result = CM_IMP_closure_once(input_IMP)
    while len(result) != len(CM_IMP_closure_once(result)):
        result = CM_IMP_closure_once(result)
    return result

def CM_INC_closure_once(input_IMP, input_INC):
    """
    Close the input_INC under CM, with respect to the input_IMP once.
    CM: if \Gamma implies A and \Gamma implies B, then \Gamma, A implies B.
    Let B be \bot.
    Then this means that if \Gamma implies A and \Gamma is incoherent, then \Gamma, A is incoherent.

    Parameters
    ----------
    input_IMP : frozenset
        A frozenset of implications, where each implication is a tuple, whose first element is a frozenset of indexes of
        sentences and second element is an index of a sentence.
    input_INC : frozenset
        A frozenset of incoherent frozensets, where each incoherent frozenset contains a bunch of indexes of jointly incoherent sentences.

    Returns
    -------
    frozenset
        A frozenset set of incoherent. Namely, the one obtained by closing the input_INC under CM with respect to the
        input_IMP once.
    """

    new_inc = list()
    for i in input_INC:
        for j in input_IMP:
            if j[0] == i:
                new_inc.append(frozenset.union(i , frozenset([j[1]])))
    result = frozenset.union(input_INC, frozenset(new_inc))
    return result

def CM_INC_closure(input_IMP, input_INC):
    """
    Close the input_INC under CM, with respect to the input_IMP until a fixed point is reached.
    CM: if \Gamma implies A and \Gamma implies B, then \Gamma, A implies B.
    Let B be \bot.
    Then this means that if \Gamma implies A and \Gamma is incoherent, then \Gamma, A is incoherent.

    Parameters
    ----------
    input_IMP : frozenset
        A frozenset of implications, where each implication is a tuple, whose first element is a frozenset of indexes of
        sentences and second element is an index of a sentence.
    input_INC : frozenset
        A frozenset of incoherent frozensets, where each incoherent frozenset contains a bunch of indexes of jointly incoherent sentences.

    Returns
    -------
    frozenset
        A frozenset set of incoherent. Namely, the one obtained by closing the input_INC under CM with respect to the
        input_IMP until a fixed point is reached.
    """
    result = CM_INC_closure_once(input_IMP, input_INC)
    while len(result) != len(CM_INC_closure_once(input_IMP, result)):
        result = CM_INC_closure_once(input_IMP, result)
    return result

def msf_CM_full_closure_once(frame):
    cm_imp_first_time = CM_IMP_closure(frame.IMP)
    cm_inc_first_time = CM_INC_closure_once(cm_imp_first_time, frame.INC)
    exff_imp_first_time = ExFF_closure(language= frame.L, imp= cm_imp_first_time, inc= cm_inc_first_time)
    # Notice closing the INC under CM creates more incoherent sets and hence more ExFF sets, which in turn create more
    # implications via ExFF. So we have to close the IMP under ExFF after we generate more incoherent sets.
    # We consider closing under cm_imp, cm_inc, exff in turn as closing under cm once. Strictly speaking, it doesn't
    # make too much sense of closing once, since, e.g., exff apparently creates more implications that will produce more
    # imcoherent sets under CM.
    return MSF(L = frame.L, IMP = exff_imp_first_time, INC = cm_inc_first_time)

def msf_CM_full_closure(frame):
    result = msf_CM_full_closure_once(frame)
    while len(result.IMP) != len(msf_CM_full_closure_once(result).IMP) or len(result.INC) != len(msf_CM_full_closure_once(result).INC):
        result = msf_CM_full_closure_once(result)
    return result



########################################################################################################################
############################################          CT closure          ##############################################
########################################################################################################################

def CT_IMP_closure_once(input_IMP):
    new_imp = list()
    for i in input_IMP:
        for j in input_IMP:
            if j[0] == frozenset.union(i[0], frozenset([i[1]])):
                new_imp.append((i[0], j[1]))
    output_IMP = frozenset.union(input_IMP, frozenset(new_imp))
    return output_IMP

def CT_IMP_closure(input_IMP):
    result = CT_IMP_closure_once(input_IMP)
    while len(result) != len(CT_IMP_closure_once(result)):
        result = CT_IMP_closure_once(result)
    return result


def CT_INC_closure_once(input_IMP, input_INC):
    new_inc = list()
    for i in input_IMP:
        if frozenset.union(i[0], frozenset([i[1]])) in input_INC:
            new_inc.append(i[0])
    output_INC = frozenset.union(input_INC, frozenset(new_inc))
    return output_INC

def CT_INC_closure(input_IMP, input_INC):
    result = CT_INC_closure_once(input_IMP, input_INC)
    while len(result) != len(CT_INC_closure_once(input_IMP, result)):
        result = CT_INC_closure_once(input_IMP, result)
    return result

def msf_CT_full_closure_once(frame):
    ct_imp_first_time = CT_IMP_closure(frame.IMP)
    ct_inc_first_time = CT_INC_closure_once(ct_imp_first_time, frame.INC)
    exff_imp_first_time = ExFF_closure(language= frame.L, imp= ct_imp_first_time, inc= ct_inc_first_time)
    return MSF(L = frame.L, IMP = exff_imp_first_time, INC = ct_inc_first_time)

def msf_CT_full_closure(frame):
    result = msf_CT_full_closure_once(frame)
    while len(result.IMP) != len(msf_CT_full_closure_once(result).IMP) or len(result.INC) != len(msf_CT_full_closure_once(result).INC):
        result = msf_CT_full_closure_once(result)
    return result


def UNUSED_MSF_closure(frame, close_under, times = 1):
    '''

    :param frame:
    :param close_under:
    :param times:
    :return:
    '''
    if times == 'full':
        if close_under == 'cm_imp':
            return MSF(L = frame.L, IMP = CM_IMP_closure(frame.IMP), INC = frame.INC)
        elif close_under == 'cm_inc':
            return MSF(L = frame.L, IMP = frame.IMP, INC = CM_INC_closure(frame.IMP, frame.INC))
        elif close_under == 'cm':
            return msf_CM_full_closure(frame)
        elif close_under == 'ct_imp':
            return MSF(L = frame.L, IMP = CT_IMP_closure(frame.IMP), INC = frame.INC)
        elif close_under == 'ct_inc':
            return MSF(L = frame.L, IMP = frame.IMP, INC = CT_INC_closure(frame.IMP, frame.INC))
        elif close_under == 'ct':
            return msf_CT_full_closure(frame)
        elif close_under == 'cm and ct':
            result = msf_CT_full_closure(msf_CM_full_closure(frame))
            while len(result.IMP) != len(msf_CT_full_closure(msf_CM_full_closure(result)).IMP) or len(result.INC) != len(msf_CT_full_closure(msf_CM_full_closure(result)).INC):
                result = msf_CT_full_closure(msf_CM_full_closure(result))
            return result
        else:
            print('This function requires a parameter close_under, which can take value from the following strings: '
                  '\'cm_imp\', \'cm_inc\', \'cm\', \'ct_imp\', \'ct_inc\', \'ct\', \'cm and ct\'.'
                  'By default, this function closes the input msf under the specified rule once. You can ask the function'
                  'to close multiple times by changing the parameter times, which can be any positive integer or \'full\'. If times is'
                  '\'full\', the function will close the input msf under the specified rule until a fixed point.')

    elif isinstance(times, int) and times > 0:
        if close_under == 'cm_imp':
            result = CM_IMP_closure_once(frame.IMP)
            for i in range(times - 1):
                result = CM_IMP_closure_once(result)
            return MSF(L = frame.L, IMP = result, INC = frame.INC)
        elif close_under == 'cm_inc':
            result = CM_INC_closure_once(frame.IMP, frame.INC)
            for i in range(times - 1):
                result = CM_INC_closure_once(frame.IMP, result)
            return MSF(L = frame.L, IMP = frame.IMP, INC = result)
        elif close_under == 'cm':
            result = msf_CM_full_closure_once(frame)
            for i in range(times - 1):
                result = msf_CM_full_closure_once(result)
            return result
        elif close_under == 'ct_imp':
            result = CT_IMP_closure(frame.IMP)
            for i in range(times - 1):
                result = CT_IMP_closure(result)
            return MSF(L = frame.L, IMP = result, INC = frame.INC)
        elif close_under == 'ct_inc':
            result = CT_INC_closure(frame.IMP, frame.INC)
            for i in range(times - 1):
                result = CT_INC_closure(frame.IMP, result)
            return MSF(L = frame.L, IMP = frame.IMP, INC = result)
        elif close_under == 'ct':
            result = msf_CT_full_closure_once(frame)
            for i in range(times - 1):
                result = msf_CT_full_closure_once(result)
            return result
        elif close_under == 'cm and ct':
            result = msf_CT_full_closure(msf_CM_full_closure(frame))
            for i in range(times - 1):
                result = msf_CT_full_closure(msf_CM_full_closure(result))
            return result
        else: print('This function requires a parameter close_under, which can take value from the following strings: '
                    '\'cm_imp\', \'cm_inc\', \'cm\', \'ct_imp\', \'ct_inc\', \'ct\', \'cm and ct\'.'
                    'By default, this function closes the input msf under the specified rule once. You can ask the function'
                    'to close multiple times by changing the parameter times, which can be any positive integer or \'full\'. If times is'
                    '\'full\', the function will close the input msf under the specified rule until a fixed point.')
    else: print('The parameter times specifies how many times you want the input msf closed under the rule you specified.'
                'It can either be positive integers, e.g. 1, 2, ... or string \'full\'. If it\'s set to be \'full\', it will'
                'close the input msf under the rule you specified until a fixed point.')

########################################################################################################################
########################################################################################################################
############################################          Violations          ##############################################
########################################################################################################################
########################################################################################################################
        
def find_violations(imps: frozenset) -> dict:

    prems_to_concs = dict()
    gammadelta_to_viols = dict() # result

    for i in imps: # build a dict of premise sets to sets of conclusions implied by them

        if i[0] not in prems_to_concs:
            prems_to_concs[i[0]] = frozenset({i[1]})
        else:
            prems_to_concs[i[0]] = frozenset.union(prems_to_concs[i[0]], frozenset({i[1]}))

    for gamma, c_gamma in prems_to_concs.items(): # for all premise sets gamma in IMP

        non_CO_c_gamma = frozenset.difference(c_gamma, gamma) # non-CO consequences of gamma

        for delta in powerset_(non_CO_c_gamma): # for all non-empty subsets of non-CO consequences of gamma delta

            c_gammaUdelta = prems_to_concs[frozenset.union(gamma, delta)]

            cm_viols = frozenset.difference(c_gamma, c_gammaUdelta) # CM viols are difference between C(gamma) and C(gamma U delta), the consequences lost by explicitating delta
            ct_viols = frozenset.difference(c_gammaUdelta, c_gamma) # CT viols are difference between C(gamma U delta) and C(gamma), the consequences gained by explicitating delta

            gammadelta_to_viols[(gamma, delta)] = (cm_viols, ct_viols) # ordered pair (gamma, delta) maps to ordered pair (cm_viols, ct_viols)

    return gammadelta_to_viols

def show_violations(imps: frozenset, longform : bool = True):

    gammadelta_to_viols = find_violations(imps)

    CM_viols_count = 0
    CT_viols_count = 0

    CM_violator_count = 0
    CT_violator_count = 0

    for gammadelta, viols in gammadelta_to_viols.items():

        gamma = gammadelta[0]
        delta = gammadelta[1]
        union = frozenset.union(gamma, delta)
        cm_viols = viols[0]
        ct_viols = viols[1]
        
        if len(cm_viols) != 0:
            CM_viols_count += len(cm_viols)
            CM_violator_count += 1
            if longform:
                for viol in cm_viols:
                    print('CM violation: ' + str(set(gamma)) + '⊨' + str(viol) + ' and ' + str(set(gamma)) + '⊨' + str(set(delta)) + ', but not ' + str(set(union)) + '⊨' + str(viol))
                    print('\n')

        if len(ct_viols) != 0:
            CT_viols_count += len(ct_viols)
            CT_violator_count += 1
            if longform:
                for viol in ct_viols:
                    print('CT violation: ' + str(set(gamma)) + '⊨' + str(set(delta)) + ' and ' + str(set(union)) + '⊨' + str(viol) + ', but not ' + str(set(gamma)) + '⊨' + str(viol))
                    print('\n')

    if longform:
        print(str(CM_violator_count) + ' premise sets had CM violations. There were ' + str(CM_viols_count) + ' total CM violations.')
        print(str(CT_violator_count) + ' premise sets had CT violations. There were ' + str(CT_viols_count) + ' total CT violations.')
    else:
        print(str(CM_violator_count) + ',' + str(CM_viols_count) + ',' + str(CT_violator_count) + ',' + str(CT_viols_count))
    
########################################################################################################################
########################################################################################################################
###############################################          Score          ################################################
########################################################################################################################
########################################################################################################################


class Score:
    def __init__(self, Subject, AC, RC, AE, RE):
        self.Subject = Subject
        self.AC = AC    #accept committed
        self.RC = RC    #reject committed
        self.AE = AE    #accept entitled
        self.RE = RE    #reject entitled


class ScoreSit:
    def __init__(self, CL_Score, CR_Score):
        self.CL = CL_Score
        self.CR = CR_Score
        self.CommonGround = frozenset.intersection(self.CL.AC, self.CR.AC)


EmptyScore_CL = Score('CL', frozenset(), frozenset(), frozenset(), frozenset())

EmptyScore_CR = Score('CR', frozenset(), frozenset(), frozenset(), frozenset())

EmptyScoreSit = ScoreSit(EmptyScore_CL, EmptyScore_CR)

########################################################################################################################
########################################################################################################################
####################################          Agents' Inferential Theory          ######################################
########################################################################################################################
########################################################################################################################

class InferentialTheory:
    def __init__(self, ForMove, AgainstMove):
        self.ForMove = ForMove  # the frozenset of all formoves to be used by a player with this InferentialTheory, that is all members of this frozenset are objects of class MoveType
        self.AgainstMove = AgainstMove  # the frozenset of all formoves to be used by a player with this InferentialTheory, that is all members of this frozenset are objects of class MoveType
        self.Arg = ArgGenerator(ForMove = self.ForMove, AgainstMove = self.AgainstMove)
        self.Att = AttGenerator(ForMove = self.ForMove, AgainstMove = self.AgainstMove)

    def export(self, filename):   #method for exporting an Inferential Theory as an argumentation frame in Aspartix format as a .txt file. You will have to manually change the extension of the txt file to .dl, for now.
        f = open(filename, 'w')
        f.write("% arguments\n")
        for arg in self.Arg:
            f.write('arg(' + arg + ').\n')
        f.write("\n% attack relations\n")
        for att in self.Att:
            f.write('att(' + att[0] + ',' + att[1] + ').\n')
        f.close()
    def show(self):
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^Beginning of an InferentialTheory display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        print('This inferential theory contains', len(self.ForMove), 'reasons-for, as follows:')
        reasons_for = list()
        for i in self.ForMove:
            reasons_for.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        reasons_for.sort()
        print(wrap_list(reasons_for, items_per_line=5))
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        print('This inferential theory contains', len(self.AgainstMove), 'reasons-against, as follows:')
        reasons_against = list()
        for i in self.AgainstMove:
            reasons_against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        reasons_against.sort()
        print(wrap_list(reasons_against, items_per_line=5))
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^End of an InferentialTheory display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

def UniverseOfReasons(msf):
    return InferentialTheory(ForMove = msf.ForMove, AgainstMove = msf.AgainstMove)

def ArgGenerator(ForMove, AgainstMove):
    fornodes = list()
    againstnodes = list()

    for move in ForMove:
        fornodes.append(move.ShortLabel)
    fornodes.sort()

    for move in AgainstMove:
        againstnodes.append(move.ShortLabel)
    againstnodes.sort()

    nodes = fornodes + againstnodes
    return nodes # Notice return is a list of strings, with fornodes first and then againstnodes

def AttGenerator(ForMove, AgainstMove):
    attfromformove = list()
    attfromagainstmove = list()

    for formove in ForMove:
        for againstmove in AgainstMove:
            if formove.Conc == againstmove.Conc:
                attfromformove.append((formove.ShortLabel, againstmove.ShortLabel))

    for againstmove in AgainstMove:
        for formove in ForMove:
            if againstmove.Conc in formove.Prem:
                attfromagainstmove.append((againstmove.ShortLabel, formove.ShortLabel))
            elif againstmove.Conc == formove.Conc:
                attfromagainstmove.append((againstmove.ShortLabel, formove.ShortLabel))
        for otheragainstmove in AgainstMove:
            if againstmove.Conc in otheragainstmove.Prem:
                attfromagainstmove.append((againstmove.ShortLabel, otheragainstmove.ShortLabel))

    allatt = attfromformove + attfromagainstmove
    allatt.sort()
    return allatt


def RandomInferentialTheoryGenerator(msf, for_move_size = 'random', against_move_size = 'random', for_move_chance = 1/2, against_move_chance = 1/2):

    # Part for ForMove
    if for_move_size != 'random':
        if for_move_size > len(msf.ForMove):
            print('Warning: the declared for_move_size is larger than the size of all for-moves in the universe of reasons.')
        SelectedForMove = frozenset(random.sample(msf.ForMove, for_move_size))
    else:
        k = numpy.random.binomial(len(msf.ForMove), for_move_chance)
        SelectedForMove = frozenset(random.sample(msf.ForMove, k))

    # Part for AgainstMove
    if against_move_size != 'random':
        if against_move_size > len(msf.AgainstMove):
            print('Warning: the declared against_move_size is larger than the size of all against-moves in the universe of reasons.')
        SelectedAgainstMove = frozenset(random.sample(msf.AgainstMove, against_move_size))
    else:
        k = numpy.random.binomial(len(msf.AgainstMove), against_move_chance)
        SelectedAgainstMove = frozenset(random.sample(msf.AgainstMove, k))

    return InferentialTheory(ForMove = SelectedForMove, AgainstMove = SelectedAgainstMove)




########################################################################################################################
########################################################################################################################
###############################################          Stage          ################################################
########################################################################################################################
########################################################################################################################


class Stage:
    def __init__(self, MSF, TurnNum, Agent, CL_InferentialTheory, CR_InferentialTheory, AScoreSit, TargetMove, PragSig,
                 PrimeMove, FScoreSit, LastStage, ControSet, SuffCon):
        self.MSF = MSF
        self.TurnNum = TurnNum
        self.Agent = Agent
        self.CL_InferentialTheory = CL_InferentialTheory
        self.CR_InferentialTheory = CR_InferentialTheory
        self.AScoreSit = AScoreSit
        self.TargetMove = TargetMove
        self.PragSig = PragSig
        self.PrimeMove = PrimeMove
        self.FScoreSit = FScoreSit
        self.LastStage = LastStage
        self.ControSet = ControSet
        self.SuffCon = SuffCon
        self.AvailableMove = AvailMove(self)


    def show(self):
        if self.TurnNum == 0:
            x = PrettyTable()
            x.field_names = ['TurnNum', 'Agent', 'TargetNum', 'PragSig', 'Move', 'CL_AC', 'CL_RC', 'CL_AE', 'CL_RE',
                             'CR_AC', 'CR_RC', 'CR_AE', 'CR_RE']
            first_stage_row(x,self)
            print(x)
        else:
            x = PrettyTable()
            x.field_names = ['TurnNum', 'Agent', 'TargetNum', 'PragSig', 'Move', 'CL_AC', 'CL_RC', 'CL_AE', 'CL_RE',
                             'CR_AC', 'CR_RC', 'CR_AE', 'CR_RE']
            stage_row(x,self)
            print(x)






def PrevStages(stage):
    # This gives the list of all previous stages, given a stage, in increasing order of TurnNum, i.e. the initial stage
    # has index 0, and so on.
    prevstages = list()
    s = stage
    while s.LastStage != None:
        prevstages.append(s.LastStage)
        s = s.LastStage
    prevstages.reverse()
    return prevstages


def AvailMove(stage):
    #This function is used to compute all reasons available to the next mover at a given stage.
    avail_against_move = list()
    avail_for_move = list()
    st = PrevStages(stage)+[stage]
    if stage.Agent == 'CL': #In this case, CL made a move in this stage and we should compute available moves for CR
        # We iterate through all against-moves (i.e. reason-againsts) in the msf of the stage.
        # Each against-move will pass a series of tests before it's added to a list.
        for m in stage.CR_InferentialTheory.AgainstMove:
            # Given,the move (type) under consideration is a reason-against, we first make sure that this move is
            # targeting something that CL (i.e. the opponent of the next mover CR) is entitled to.
            # And this move doesn't use the conclusion of the initial proposal of CL.
            if m.Conc in stage.FScoreSit.CL.AE and st[0].PrimeMove.Conc not in m.Prem:
                # We make sure that this move doesn't use anything that CR is committed to reject as premise and
                # the target of this reason-against isn't something that CR is committed to accept.
                if frozenset.intersection(m.Prem, stage.FScoreSit.CR.RC) == frozenset() and m.Conc not in stage.FScoreSit.CR.AC:
                    # We make sure that for every premise of this move, if CR has already committed to accept it by the
                    # end of the current stage (recall that we are computing what CR can do at next stage), CR is entitled
                    # to it. That is, making sure that CR isn't using any premise that he's not entitled.
                    if frozenset.intersection(m.Prem, stage.FScoreSit.CR.AC).issubset(stage.FScoreSit.CR.AE):
                        # We make sure that this the union of CR's current AC and the premises of this move isn't
                        # persistently incoherent. In this way, CR will never make a move that will put her into
                        # persistently incoherent AC.
                        if not frozenset.union(stage.FScoreSit.CR.AC, m.Prem) in ExFF_sets(stage.MSF.L, stage.MSF.INC):
                            # The last test checks that CR hasn't used this reason-against in previous stages.
                            if all([m != i.PrimeMove for i in PrevStages(stage)] + [m != stage.PrimeMove]):
                                # Once a move (type) passes all tests above, it's added to the list of available against
                                # moves.
                                avail_against_move.append(m)
        for j in stage.CR_InferentialTheory.ForMove: # We do the same thing for for-moves.
            if j.Conc in stage.FScoreSit.CR.AC and j.Conc not in stage.FScoreSit.CR.AE and st[0].PrimeMove.Conc not in j.Prem:
                if frozenset.intersection(j.Prem, stage.FScoreSit.CR.RC) == frozenset() and j.Conc not in stage.FScoreSit.CR.RC:
                    if frozenset.intersection(j.Prem, stage.FScoreSit.CR.AC).issubset(stage.FScoreSit.CR.AE):
                        if not frozenset.union(stage.FScoreSit.CR.AC, j.Prem, frozenset([j.Conc])) in ExFF_sets(stage.MSF.L, stage.MSF.INC):
                            if all([j != i.PrimeMove for i in PrevStages(stage)] + [j != stage.PrimeMove]):
                                avail_for_move.append(j)
        return {'agent': 'CR', 'for': frozenset(avail_for_move), 'against': frozenset(avail_against_move)}
    else:
        # In this case, CR made a move in this stage and we should compute available moves for CL.
        # The way it's checked is exactly the same as last case.
        for m in stage.CL_InferentialTheory.AgainstMove:
            if m.Conc in stage.FScoreSit.CR.AE and st[0].PrimeMove.Conc not in m.Prem:
                if frozenset.intersection(m.Prem, stage.FScoreSit.CL.RC) == frozenset() and m.Conc not in stage.FScoreSit.CL.AC:
                    if frozenset.intersection(m.Prem, stage.FScoreSit.CL.AC).issubset(stage.FScoreSit.CL.AE):
                        if not frozenset.union(stage.FScoreSit.CL.AC, m.Prem) in ExFF_sets(stage.MSF.L, stage.MSF.INC):
                            if all([m != i.PrimeMove for i in PrevStages(stage)] + [m != stage.PrimeMove]):
                                avail_against_move.append(m)
        for j in stage.CL_InferentialTheory.ForMove:
            if j.Conc in stage.FScoreSit.CL.AC and j.Conc not in stage.FScoreSit.CL.AE and st[0].PrimeMove.Conc not in j.Prem:
                if frozenset.intersection(j.Prem, stage.FScoreSit.CL.RC) == frozenset() and j.Conc not in stage.FScoreSit.CL.RC:
                    if frozenset.intersection(j.Prem, stage.FScoreSit.CL.AC).issubset(stage.FScoreSit.CL.AE):
                        if not frozenset.union(stage.FScoreSit.CL.AC, j.Prem, frozenset([j.Conc])) in ExFF_sets(stage.MSF.L, stage.MSF.INC):
                            if all([j != i.PrimeMove for i in PrevStages(stage)] + [j != stage.PrimeMove]):
                                avail_for_move.append(j)
        return {'agent': 'CL','for': frozenset(avail_for_move), 'against': frozenset(avail_against_move)}


# Make Moves as generating stages


def InitialMoveFor(frame, move, CL_InferentialTheory, CR_InferentialTheory):
    fscore = ScoreSit(Score(Subject = 'CL', AC = frozenset.union(move.Prem, frozenset([move.Conc])),
                            RC = frozenset(), AE = frozenset.union(move.Prem, frozenset([move.Conc])),
                            RE = frozenset()), EmptyScore_CR)
    scon = list()
    if move not in CL_InferentialTheory.ForMove:
        print('The given first move is not in CL\'s Inferential Theory.')
    else:
        for i in move.Prem:
            scon.append(('A', None, 'A', i))
        suffcon = [('A', move.Prem, 'A', move.Conc)] + scon
    # Here it's important to have scon second, instead of first.
        return Stage(MSF = frame, TurnNum = 0, Agent = 'CL', AScoreSit = EmptyScoreSit, TargetMove = None,
                     PragSig = 'proposal', PrimeMove = move, FScoreSit = fscore, LastStage = None,
                     ControSet = frozenset([move.Conc]), SuffCon = suffcon, CL_InferentialTheory = CL_InferentialTheory,
                     CR_InferentialTheory = CR_InferentialTheory)


def ManualInitialMoveFor(frame, proposal, CL_InferentialTheory, CR_InferentialTheory):
    if proposal not in frame.IMP:
        print('Not an eligible first reason-for move in this semantic frame')
    else:
        for m in frame.ForMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason for':
                prime = m
                break
        if prime not in CL_InferentialTheory.ForMove:
            print('The proposal is not in the player\'s inferential theory.')
        else:
            return InitialMoveFor(frame = frame, move = prime, CL_InferentialTheory = CL_InferentialTheory,
                                  CR_InferentialTheory = CR_InferentialTheory)


def FirstMoveFor(frame, premise, conclusion, CL_InferentialTheory, CR_InferentialTheory):
    proposal = (frozenset([frame.L.index(s) for s in premise]), frame.L.index(conclusion))
    return ManualInitialMoveFor(frame = frame, proposal = proposal, CL_InferentialTheory = CL_InferentialTheory,
                                  CR_InferentialTheory = CR_InferentialTheory)

def FirstMoveFor_RandomPremise(frame, conclusion, CL_InferentialTheory, CR_InferentialTheory):
    # Input conclusion as a string, e.g. 'a_2'
    pool = list()
    for i in frame.ForMove:
        if i.Conc == frame.L.index(conclusion):
            pool.append(i)
    move = random.sample(frozenset.intersection(frozenset(pool), CL_InferentialTheory.ForMove), 1)[0]
    return InitialMoveFor(frame = frame, move = move, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)


def RandomFirstMoveFor(frame, CL_InferentialTheory, CR_InferentialTheory):
    # This function draws one move out of all for-moves arbitrarily. Notice for-moves may not be equally distributed
    # over all sentences. So some sentence is more likely to be defended than others by this function
    m = random.sample(CL_InferentialTheory.ForMove, 1)[0]
    return InitialMoveFor(frame = frame, move = m, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)

def RandomFirstMoveFor_RandomConclusion(frame, CL_InferentialTheory, CR_InferentialTheory):
    # This function first randomly draws a conclusion to defend and then defend it with a randomly drawn move.
    # All sentences are equally likely to be defended by this function.
    conclusion = random.sample(frame.L, 1)[0]
    return FirstMoveFor_RandomPremise(frame = frame, conclusion = conclusion, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)



def InitialMoveAgainst(frame, move, CL_InferentialTheory, CR_InferentialTheory):
    fscore = ScoreSit(Score('CL', move.Prem, frozenset([move.Conc]), move.Prem, frozenset([move.Conc])), EmptyScore_CR)
    scon = list()
    if move not in CL_InferentialTheory.AgainstMove:
        print('The given first move is not in CL\'s Inferential Theory.')
    else:
        for i in move.Prem:
            scon.append(('A', None, 'A', i))
        suffcon = [('A', move.Prem, 'R', move.Conc)] + scon
        return Stage(MSF = frame, TurnNum = 0, Agent = 'CL', CL_InferentialTheory = CL_InferentialTheory,
                     CR_InferentialTheory = CR_InferentialTheory, AScoreSit = EmptyScoreSit, TargetMove = None,
                     PragSig = 'proposal', PrimeMove = move, FScoreSit = fscore, LastStage= None,
                     ControSet = frozenset([move.Conc]), SuffCon = suffcon)


def ManualInitialMoveAgainst(frame, proposal, CL_InferentialTheory, CR_InferentialTheory):
    if proposal[0] not in frame.EXC[proposal[1]]:
        print('Not an eligible first reason-against move in this semantic frame')
    else:
        for m in frame.AgainstMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason against':
                prime = m
                break
        if prime not in CL_InferentialTheory.AgainstMove:
            print('The given first move is not in CL\'s Inferential Theory.')
        else:
            return InitialMoveAgainst(frame = frame, move = prime, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)

def FirstMoveAgainst(frame, premise, target, CL_InferentialTheory, CR_InferentialTheory):
    proposal = (frozenset([frame.L.index(s) for s in premise]), frame.L.index(target))
    return ManualInitialMoveAgainst(frame = frame, proposal = proposal, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)

def FirstMoveAgainst_RandomPremise(frame, target, CL_InferentialTheory, CR_InferentialTheory):
    pool = list()
    for i in CL_InferentialTheory.AgainstMove:
        if i.Conc == frame.L.index(target):
            pool.append(i)
    move = random.sample(pool, 1)[0]
    return InitialMoveAgainst(frame = frame, move = move, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)


def RandomFirstMoveAgainst(frame, CL_InferentialTheory, CR_InferentialTheory):
    # This function draws one move out of all for-moves arbitrarily. Notice for-moves may not be equally distributed
    # over all sentences. So some sentence is more likely to be defended than others by this function
    m = random.sample(CL_InferentialTheory.AgainstMove, 1)[0]
    return InitialMoveAgainst(frame = frame, move = m, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)

def RandomFirstMoveAgainst_RandomTarget(frame, CL_InferentialTheory, CR_InferentialTheory):
    # This function first randomly draws a target to argue against and then defend it with a randomly drawn move.
    # All sentences are equally likely to be defended by this function.
    target = random.sample(frame.L, 1)[0]
    return FirstMoveAgainst_RandomPremise(frame = frame, target = target, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)



def InitialNextStage(last_stage, targetstage, pragsig, move):
    """
    Return next stage, which is equivalent to making a move, requiring specification of the current stage and what move
    is to be made. This is perhaps the most important function in this program.
    This function is not intended to be called manually. It requires objects of class Stage and objects of class MoveType
    as inputs, which makes it almost impossible to run manually. Instead, this function does the hardwork of making moves.
    Other functions intending to be called, requiring less demanding inputs, are defined using this function.

    Notice, since we build LastStage as an attribute of a stage. When we know what the last stage of a stage is, we
    actually have access to all previous stages. This feature is important for the operation of this function.

    This function requires inputs of what the last stage is, what the target stage is, what the pragmatic
    significance of the (move of the) next stage is, and what move is made.

    Parameters
    ----------
    last_stage : Stage
        An object of class Stage, namely the stage right before the one to be generated by this function.
    targetstage : Stage
        An object of class Stage, namely the stage targeted by the move being made.
    pragsig : str
        The pragmatic significance of the move being made.
    move : MoveType
        The move is being made.

    Returns
    -------
    Stage
        The next stage in which the move specified in the input is made.
    """
    if last_stage.Agent == 'CL' and move not in last_stage.CR_InferentialTheory.ForMove and move not in last_stage.CR_InferentialTheory.AgainstMove:
        print('Error: Attempted move is not in CL\'s Inferential Theory.')
    if last_stage.Agent == 'CR' and move not in last_stage.CL_InferentialTheory.ForMove and move not in last_stage.CL_InferentialTheory.AgainstMove:
        print('Error: Attempted move is not in CR\'s Inferential Theory.')

    frame = last_stage.MSF
    a = agentswitch(last_stage.Agent)
    if move.Val == 'reason against': # For the case where the valence of next move is reason-against.
        # To simplify the scoring process, I keep a list of controversial sentences.
        # This step updates the set of controversial claims.
        controv = frozenset.union(last_stage.ControSet, frozenset([move.Conc]))
        # The next four lines update the sufficient conditions for scoring.
        scon = list()
        for i in move.Prem:
            scon.append(('A', None, 'A', i))
        suffcon = last_stage.SuffCon + [('A', move.Prem, 'R', move.Conc)] + scon

    else:   # This is for the case where the valence of next move is reason-for.
        controv = frozenset.union(last_stage.ControSet, frozenset([move.Conc]))
        scon = list()
        for i in move.Prem:
            scon.append(('A', None, 'A', i))
        suffcon = last_stage.SuffCon + [('A', move.Prem, 'A', move.Conc)] + scon

    # The following block updates the commitments of CL and CR in different cases.
    # Updating commitments is a very simple process that has nothing to do with entitlements.
    if a == 'CL':
        if move.Val == 'reason against':
            cl_ac = frozenset.union(last_stage.FScoreSit.CL.AC, move.Prem)
            cl_rc = frozenset.union(last_stage.FScoreSit.CL.RC, frozenset([move.Conc]))
        else:
            cl_ac = frozenset.union(last_stage.FScoreSit.CL.AC, move.Prem, frozenset([move.Conc]))
            cl_rc = last_stage.FScoreSit.CL.RC
        cr_ac = last_stage.FScoreSit.CR.AC
        cr_rc = last_stage.FScoreSit.CR.RC
    else:
        if move.Val == 'reason against':
            cr_ac = frozenset.union(last_stage.FScoreSit.CR.AC, move.Prem)
            cr_rc = frozenset.union(last_stage.FScoreSit.CR.RC, frozenset([move.Conc]))
        else:
            cr_ac = frozenset.union(last_stage.FScoreSit.CR.AC, move.Prem, frozenset([move.Conc]))
            cr_rc = last_stage.FScoreSit.CR.RC
        cl_ac = last_stage.FScoreSit.CL.AC
        cl_rc = last_stage.FScoreSit.CL.RC

        #Now we are done with commitments, sufficient conditions and controversial statements. Time for entitlements!

# We first initiate lists of potential entitlements of CL and CR. E.g. p_cl_ae intended to be the set of sentences that
# the CL is potentially entitled to accept. It starts as the set of sentences CL is committed to accept.
    p_cl_ae = cl_ac
    p_cl_re = cl_rc
    p_cr_ae = cr_ac
    p_cr_re = cr_rc
    cl_ae = list()
    cl_re = list()
    cr_ae = list()
    cr_re = list()
    # First Step: make agents entitled to accept all noncontroversial sentences that they are committed to accept.
    # A sentence is not controversial if it has never appeared on the right of a turntile. This is just to simplify
    # the process of keeping track of entitlement. The tracking process still works without it, albeit slower.
    for i in cl_ac:
        if i not in controv:
            cl_ae.append(i)
    for i in cr_ac:
        if i not in controv:
            cr_ae.append(i)
    # Second Step: Iterate through all sufficient conditions accumulated so far from the latest to earliest.
    # Basically, we iterate until we find a sufficient condition, whose premises are met and conclusion has yet been
    # actualized. We then actualize it and redo the interation from the beginning. We do so until there is no further
    # sufficient condition to be actualized, i.e. for each suffcon, either its premises are not met, or its conclusion
    # has already been actualized.
    n = 0
    while n < len(suffcon):
        n = 0
        for i in reversed(suffcon):
            if i[2] == 'A':  # The case of A -> A condition
                if i[1] == None:  # The case of automatic satisfication
                    if i[3] in p_cl_ae and i[3] not in cl_ae:  # Case of CL
                        cl_ae.append(i[3])
                        p_cr_re = p_cr_re - frozenset([i[3]])
                        break
                    if i[3] in p_cr_ae and i[3] not in cr_ae:  # Case of CR
                        cr_ae.append(i[3])
                        p_cl_re = p_cl_re - frozenset([i[3]])
                        break
                elif i[1] != None:  # The case of conditional satisfication
                    if i[1].issubset(frozenset(cl_ae)) and i[3] in p_cl_ae and i[3] not in cl_ae:  # Case of CL
                        cl_ae.append(i[3])
                        p_cr_re = p_cr_re - frozenset([i[3]])
                        break
                    if i[1].issubset(frozenset(cr_ae)) and i[3] in p_cr_ae and i[3] not in cr_ae:  # Case of CR
                        cr_ae.append(i[3])
                        p_cl_re = p_cl_re - frozenset([i[3]])
                        break
            elif i[2] == 'R':  # The case of A -> R condition
                if i[1].issubset(frozenset(cl_ae)) and i[3] in p_cl_re and i[3] not in cl_re:
                    cl_re.append(i[3])
                    p_cr_ae = p_cr_ae - frozenset([i[3]])
                    break
                if i[1].issubset(frozenset(cr_ae)) and i[3] in p_cr_re and i[3] not in cr_re:
                    cr_re.append(i[3])
                    p_cl_ae = p_cl_ae - frozenset([i[3]])
                    break
            n = n + 1
    # We initiated cl_ae, cl_re, cr_ae, cr_re as lists for convenience. Now we convert them back to frozensets.
    cl_ae = frozenset(cl_ae)
    cl_re = frozenset(cl_re)
    cr_ae = frozenset(cr_ae)
    cr_re = frozenset(cr_re)
    # Creating scores for CL and CR.
    cl = Score('CL', AC = cl_ac, AE = cl_ae, RC = cl_rc, RE = cl_re)
    cr = Score('CR', AC = cr_ac, AE = cr_ae, RC = cr_rc, RE = cr_re)
    # Creating ScoreSit.
    finalscore = ScoreSit(CL_Score = cl, CR_Score = cr)
    return Stage(MSF = frame, TurnNum = last_stage.TurnNum + 1, Agent = a, CL_InferentialTheory = last_stage.CL_InferentialTheory,
                 CR_InferentialTheory = last_stage.CR_InferentialTheory, AScoreSit = last_stage.FScoreSit,
                 TargetMove = targetstage, PragSig = pragsig, PrimeMove = move, FScoreSit = finalscore,
                 LastStage=last_stage, ControSet = controv, SuffCon = suffcon)


def InitialNextStage_2(stage, prime):
    # This is the second part of InitialNextStage. Most parameters required by InitialNextStage can be inferred from the
    # move to be take. Thus this function does the inferring and reduces the number of parameters required by InitialNextStage.
    if prime.Val == 'reason for':
        for i in reversed(PrevStages(stage)+[stage]):
            if i.PragSig == 'proposal' and i.PrimeMove.Conc == prime.Conc and i.Agent != stage.Agent:
                targetstage = None
                pragsig = 'proposal'
                break
            elif i.PrimeMove.Val == 'reason against' and i.PrimeMove.Conc == prime.Conc and i.Agent == stage.Agent:
                targetstage = i
                pragsig = 'conclusion challenge'
                break
            else:
                targetstage = None
                pragsig = None
    elif prime.Val == 'reason against':
        for i in reversed(PrevStages(stage) + [stage]):
            if i.PragSig == 'proposal' and i.PrimeMove.Conc == prime.Conc and i.Agent != stage.Agent:
                targetstage = None
                pragsig = 'proposal'
                break
            elif i.PrimeMove.Val == 'reason against' and i.Agent == stage.Agent:
                if prime.Conc in i.PrimeMove.Prem:
                    targetstage = i
                    pragsig = 'premise challenge'
                    break
            elif i.PrimeMove.Val == 'reason for' and i.Agent == stage.Agent:
                if prime.Conc in i.PrimeMove.Prem:
                    targetstage = i
                    pragsig = 'premise challenge'
                    break
                elif prime.Conc == i.PrimeMove.Conc:
                    targetstage = i
                    pragsig = 'conclusion challenge'
                    break
            else:
                targetstage = None
                pragsig = None

    return InitialNextStage(last_stage = stage, targetstage = targetstage, pragsig = pragsig, move = prime)

def ManualNextStage(last_stage, targetstage, pragsig, proposal, val):
    '''
    Generate next stage with more friendly, albeit still not friendly enough, inputs. Instead of inputting an object of
    class MoveType, you only need to put in a proposal and its valence.

    Parameters
    ----------
    last_stage : Stage
        An object of class Stage, namely the stage right before the one to be generated by this function.
    targetstage : Stage
        An object of class Stage, namely the stage targeted by the move being made.
    pragsig : str
        The pragmatic significance of the move being made.
    proposal : tuple
        A 2-tuple whose first element is the frozenset of indexes of premises and the second element is an int, namely
        the index of the conlcusion. Throughout the program, we use kind of meta-typing. When a function expects a proposal
        as input, it's expecting such a tuple.
    val: str
        The valence of the move to be made. Notice proposal doesn't distinguish reason for from reason against, but only
        records premises and conclusion. This is why we need valence as a separate input. val is either 'reason for' or
        'reason against'.


    Returns
    -------
    Stage
        The next stage in which the move specified in the input is made.
    '''
    agent = agentswitch(last_stage.Agent)
    prime = None
    if val == 'reason against':
        for m in last_stage.MSF.AgainstMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason against':
                prime = m
                break
    else:
        for m in last_stage.MSF.ForMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason for':
                prime = m
                break
    if prime == None:
        print('The proposed next move is not in the given MSF.')
    elif agent == 'CL' and prime not in last_stage.CL_InferentialTheory.ForMove and prime not in last_stage.CL_InferentialTheory.AgainstMove:
        print('The proposed next move is not in the InferentialTheory of CL, who is the next agent to make a move.')
    elif agent == 'CR' and prime not in last_stage.CR_InferentialTheory.ForMove and prime not in last_stage.CR_InferentialTheory.AgainstMove:
        print('The proposed next move is not in the InferentialTheory of CR, who is the next agent to make a move.')
    else:
        return InitialNextStage(last_stage, targetstage, pragsig, prime)

def ManualNextStage_2(last_stage, targetstage, pragsig, premise, val, conclusion):
    frame = last_stage.MSF
    proposal = (frozenset([frame.L.index(s) for s in premise]), frame.L.index(conclusion))
    return ManualNextStage(last_stage = last_stage, targetstage = targetstage, pragsig = pragsig, proposal = proposal,
                           val = val)

def ManualNextStageInfer(last_stage, proposal, val):
    agent = agentswitch(last_stage.Agent)
    prime = None
    if val == 'reason against':
        for m in last_stage.MSF.AgainstMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason against':
                prime = m
                break
    else:
        for m in last_stage.MSF.ForMove:
            if m.Prem == proposal[0] and m.Conc == proposal[1] and m.Val == 'reason for':
                prime = m
                break
    if prime == None:
        print('The proposed next move is not in the given MSF.')
    elif agent == 'CL' and prime not in last_stage.CL_InferentialTheory.ForMove and prime not in last_stage.CL_InferentialTheory.AgainstMove:
        print('The proposed next move is not in the InferentialTheory of CL, who is the next agent to make a move.')
    elif agent == 'CR' and prime not in last_stage.CR_InferentialTheory.ForMove and prime not in last_stage.CR_InferentialTheory.AgainstMove:
        print('The proposed next move is not in the InferentialTheory of CR, who is the next agent to make a move.')
    else:
        return InitialNextStage_2(last_stage, prime)

def RandomNextStage(stage):
    moves = frozenset.union(stage.AvailableMove['for'], stage.AvailableMove['against'])
    prime = random.sample(moves, 1)[0]
    return InitialNextStage_2(stage = stage, prime = prime)


def NewCommitment(move, laststage):
    #Computing what the move is grossly adding.
    if move.Val == 'reason for':
        gross_new_AC = frozenset.union(move.Prem, frozenset([move.Conc]))
        gross_new_RC = frozenset()
    if move.Val == 'reason against':
        gross_new_AC = move.Prem
        gross_new_RC = frozenset([move.Conc])

    #Computing what the move's net new commitments.
    if laststage.Agent == 'CL':
        newAC = gross_new_AC - laststage.FScoreSit.CR.AC
        newRC = gross_new_RC - laststage.FScoreSit.CR.RC

    if laststage.Agent == 'CR':
        newAC = gross_new_AC - laststage.FScoreSit.CL.AC
        newRC = gross_new_RC - laststage.FScoreSit.CL.RC

    return (newAC, newRC)



def Minimize_AC_NextStage(stage):
    moves = frozenset.union(stage.AvailableMove['for'], stage.AvailableMove['against'])
    lst_new_AC_length = set()
    pool = list()
    for i in moves:
        lst_new_AC_length.add(len(NewCommitment(i, stage)[0]))
    min_new_AC_length = min(lst_new_AC_length)
    for i in moves:
        if len(NewCommitment(i,stage)[0]) == min_new_AC_length:
            pool.append(i)

    prime = random.sample(frozenset(pool), 1)[0]

    return InitialNextStage_2(stage = stage, prime = prime)

def OneStepAhead_NextStage(stage):
    moves = frozenset.union(stage.AvailableMove['for'], stage.AvailableMove['against'])
    pool = list()

    for i in moves:
        #Case for CL
        if stage.Agent == 'CL':
            if Verdict(InitialNextStage_2(stage = stage, prime = i)) == 'fail':
                pool.append(i)
        #Case for CR
        else:
            if Verdict(InitialNextStage_2(stage = stage, prime = i)) == 'sustain':
                pool.append(i)

    if len(pool) != 0:
        prime = random.sample(frozenset(pool), 1)[0]
    else:
        prime = random.sample(frozenset(moves), 1)[0]

    return InitialNextStage_2(stage = stage, prime = prime)



def NextStage(laststage, CL_strategy, CR_strategy):
    if laststage.Agent == 'CL':
        if CR_strategy == 'random':
            return RandomNextStage(stage = laststage)
        elif CR_strategy == 'minimize AC':
            return Minimize_AC_NextStage(stage = laststage)
        elif CR_strategy == 'one step ahead':
            return OneStepAhead_NextStage(stage = laststage)
        else: print('Error: Currently, CL and CR have only three strategies: \'random\', \'minimize AC\' and \'one step ahead\'.')

    elif laststage.Agent == 'CR':
        if CL_strategy == 'random':
            return RandomNextStage(stage = laststage)
        elif CL_strategy == 'minimize AC':
            return Minimize_AC_NextStage(stage = laststage)
        elif CL_strategy == 'one step ahead':
            return OneStepAhead_NextStage(stage = laststage)
        else:
            print('Error: Currently, CL and CR have only three strategies: \'random\', \'minimize AC\' and \'one step ahead\'.')

########################################################################################################################
########################################################################################################################
##############################################          Inquiry          ###############################################
########################################################################################################################
########################################################################################################################



class Inquiry:
    def __init__(self, MSF, ListOfStages, CL_InferentialTheory, CR_InferentialTheory, CL_Strategy = None, CR_Strategy = None):
        self.MSF = MSF
        self.ListOfStages = ListOfStages
        self.Verdict = Verdict(self.ListOfStages[-1])
        self.CL_InferentialTheory = CL_InferentialTheory
        self.CR_InferentialTheory = CR_InferentialTheory
        self.ICG = InferentialCommonGround(CL_InferentialTheory = self.CL_InferentialTheory,CR_InferentialTheory = self.CR_InferentialTheory)
        self.CL_Homogeneity = (len(self.ICG.ForMove) / len(self.CL_InferentialTheory.ForMove), len(self.ICG.AgainstMove) / len(self.CL_InferentialTheory.AgainstMove))
        self.CR_Homogeneity = (len(self.ICG.ForMove) / len(self.CR_InferentialTheory.ForMove), len(self.ICG.AgainstMove) / len(self.CR_InferentialTheory.AgainstMove))
        self.CL_Strategy = CL_Strategy
        self.CR_Strategy = CR_Strategy

    def table(self, NumRow):
        '''
        This method prints the table representation of an inquiry. It's not intended to be called, but rather as a common
        ground shared by .show() and .scrutinize().
        '''
        x = PrettyTable()
        x.field_names = ['TurnNum', 'Agent', 'TargetNum', 'PragSig', 'Move', 'CL_AC', 'CL_RC', 'CL_AE', 'CL_RE',
                         'CR_AC', 'CR_RC', 'CR_AE', 'CR_RE']
        first_stage_row(x, self.ListOfStages[0])
        for i in range(1, NumRow):
            stage_row(x, self.ListOfStages[i])
        print(x)

    def show_full_table(self):
        self.table(NumRow=len(self.ListOfStages))
        print()
        if self.Verdict == 'sustain':
            print('By the end of the inquiry, CL\'s proposed conclusion is sustained.')
        else:
            print('By the end of the inquiry, CL\'s proposed conclusion is rejected.')

        final_stage = self.ListOfStages[-1]

        common_ground = frozenset.intersection(final_stage.FScoreSit.CL.AC, final_stage.FScoreSit.CR.AC)

        print('The propositional common ground is', list(common_ground))

    def viewstage(self, stage):
        '''

        :param stage:
        :return:
        '''

        self.table(NumRow=stage + 1)
        # Print all available moves
        print('By the end of this stage, next player has the following',
              str(len(self.ListOfStages[stage].AvailableMove['for'])),
              'for-moves available:')
        avail_for = list()
        for i in self.ListOfStages[stage].AvailableMove['for']:
            avail_for.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        avail_for.sort()
        print(wrap_list(avail_for, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.ListOfStages[stage].AvailableMove['for']], items_per_line=5))

        print('By the end of this stage, next player has the following',
              str(len(self.ListOfStages[stage].AvailableMove['against'])),
              'against-moves available:')
        avail_against = list()
        for i in self.ListOfStages[stage].AvailableMove['against']:
            avail_against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        avail_against.sort()
        print(wrap_list(avail_against, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.ListOfStages[stage].AvailableMove['against']], items_per_line=5))

        # Verdict at this stage
        if stage == 0:
            print('By the end of this stage, CL\'s proposed conclusion is sustained.')
        else:
            if Verdict(self.ListOfStages[stage]) == 'sustain':
                print('By the end of this stage, CL\'s proposed conclusion is sustained.')
            else:
                print('By the end of this stage, CL\'s proposed conclusion is rejected.')

    def show(self, stage = 'unspecified'):

        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^Beginning of an inquiry display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print()

        print('In this inquiry, CL\'s inferential theory contains', len(self.CL_InferentialTheory.ForMove),
              'reasons-for and', len(self.CL_InferentialTheory.AgainstMove), 'reasons-against.')

        print()
        print('The Reasons-for in CL\'s inferential theory are as follows:')
        CL_IF_For = list()
        for i in self.CL_InferentialTheory.ForMove:
            CL_IF_For.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        CL_IF_For.sort()
        print(wrap_list(CL_IF_For, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.CL_InferentialTheory.ForMove], items_per_line=5))

        print()
        print('The Reasons-against in CL\'s inferential theory are as follows:')
        CL_IF_Against = list()
        for i in self.CL_InferentialTheory.AgainstMove:
            CL_IF_Against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        CL_IF_Against.sort()
        print(wrap_list(CL_IF_Against, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.CL_InferentialTheory.AgainstMove], items_per_line=5))

        print()
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print()

        print('In this inquiry, CR\'s inferential theory contains', len(self.CR_InferentialTheory.ForMove),
              'reasons-for and', len(self.CR_InferentialTheory.AgainstMove), 'reasons-against.')

        print()
        print('The Reasons-for in CR\'s inferential theory are as follows:')
        CR_IF_For = list()
        for i in self.CR_InferentialTheory.ForMove:
            CR_IF_For.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        CR_IF_For.sort()
        print(wrap_list(CR_IF_For, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.CR_InferentialTheory.ForMove], items_per_line=5))

        print()
        print('The Reasons-against in CR\'s inferential theory are as follows:')
        CR_IF_Against = list()
        for i in self.CR_InferentialTheory.AgainstMove:
            CR_IF_Against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        CR_IF_Against.sort()
        print(wrap_list(CR_IF_Against, items_per_line=5))
#        print(wrap_list([i.MoveLabel for i in self.CR_InferentialTheory.AgainstMove], items_per_line=5))

        print()
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print()

        print('In this inquiry, the inferential common ground contains', len(self.ICG.ForMove),
              'reasons-for and', len(self.ICG.AgainstMove), 'reasons-against.')

        print()
        print('The Reasons-for in the inferential common ground are as follows:')
        ICG_IF_For = list()
        for i in self.ICG.ForMove:
            ICG_IF_For.append(str(set(i.Prem)) + '⊨' + str(i.Conc))
        ICG_IF_For.sort()
        print(wrap_list(ICG_IF_For, items_per_line=5))

        print()
        print('The Reasons-against in the inferential common ground are as follows:')
        ICG_IF_Against = list()
        for i in self.ICG.AgainstMove:
            ICG_IF_Against.append(str(set(i.Prem)) + '#' + str(i.Conc))
        ICG_IF_Against.sort()
        print(wrap_list(ICG_IF_Against, items_per_line=5))

        print()

        cl_for_perc = str(round(self.CL_Homogeneity[0] * 100, 2))
        cl_agn_perc = str(round(self.CL_Homogeneity[1] * 100, 2))
        cr_for_perc = str(round(self.CR_Homogeneity[0] * 100, 2))
        cr_agn_perc = str(round(self.CR_Homogeneity[1] * 100, 2))

        print(cl_for_perc + "% of CL's reasons-for are common ground.", cl_agn_perc + "% of CL's reasons-against are common ground.")
        print(cr_for_perc + "% of CR's reasons-for are common ground.", cr_agn_perc + "% of CR's reasons-against are common ground.")

        print()
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print()

        if stage == 'unspecified':
            self.show_full_table()

        elif isinstance(stage, int):
            self.viewstage(stage = stage)

        elif stage == 'all':
            for i in range(0, len(self.ListOfStages)):
                self.viewstage(stage = i)

        else:
            print('The parameter stage can be set to \'all\' or an integer. If set to be an integer, say 7,'
                  'the method will display the inquiry up to stage 7 and provide detailed information about stage 7. '
                  'If set to \'all\', it will do that for all stages in turn. '
                  'If left unspecified, it will display the entire inquiry. ')

        print()
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^End of an inquiry display^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")



def InferentialCommonGround(CL_InferentialTheory, CR_InferentialTheory):
    return InferentialTheory(ForMove = frozenset.intersection(CL_InferentialTheory.ForMove, CR_InferentialTheory.ForMove),
                             AgainstMove = frozenset.intersection(CL_InferentialTheory.AgainstMove, CR_InferentialTheory.AgainstMove))


def Verdict(stage):     # Notice this function takes a single stage as an argument. You can use it to check the Verdict
                        # at any given stage, if you want.
    proposal = PrevStages(stage)[0].PrimeMove
    if proposal.Val == 'reason against':
        if proposal.Conc in stage.FScoreSit.CL.RE:
            return 'sustain'
        else:
            return 'fail'
    elif proposal.Val == 'reason for':
        if proposal.Conc in stage.FScoreSit.CL.AE:
            return 'sustain'
        else:
            return 'fail'


def InquiryFor(frame, target = 'random', proposal = 'undeclared', CL_strategy = 'random', CR_strategy = 'random',
               CL_InferentialTheory = 'undeclared', CR_InferentialTheory = 'undeclared'):
    if CL_InferentialTheory == 'undeclared':
        CL_InferentialTheory = UniverseOfReasons(frame)
    if CR_InferentialTheory == 'undeclared':
        CR_InferentialTheory = UniverseOfReasons(frame)
    # input conclusion as a string, e.g. 'a_2'
    if proposal != 'undeclared' and target != 'random':
        print('You can either specify proposal, of form ([1,2,3],4), or target, of form \'a_2\', but not both.')
    elif target != 'random':
        c = FirstMoveFor_RandomPremise(frame = frame, conclusion = target, CL_InferentialTheory = CL_InferentialTheory,
                                       CR_InferentialTheory = CR_InferentialTheory)
    elif proposal != 'undeclared':
        (a,b) = proposal
        c = ManualInitialMoveFor(frame = frame, proposal = (frozenset(a), b), CL_InferentialTheory = CL_InferentialTheory,
                                       CR_InferentialTheory = CR_InferentialTheory)
    else:
        c = RandomFirstMoveFor(frame = frame, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory)

    lst = [c]
    while c.AvailableMove['for'] != frozenset() or c.AvailableMove['against'] != frozenset():
        c = NextStage(laststage = c, CL_strategy = CL_strategy, CR_strategy = CR_strategy)
        lst.append(c)
    result = Inquiry(MSF = c.MSF, ListOfStages = lst, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory, CL_Strategy = CL_strategy, CR_Strategy = CR_strategy)
    return result


def InquiryAgainst(frame, target = 'random', proposal = 'undeclared', CL_strategy = 'random', CR_strategy = 'random',
               CL_InferentialTheory = 'undeclared', CR_InferentialTheory = 'undeclared'):
    if CL_InferentialTheory == 'undeclared':
        CL_InferentialTheory = UniverseOfReasons(frame)
    if CR_InferentialTheory == 'undeclared':
        CR_InferentialTheory = UniverseOfReasons(frame)
    # input conclusion as a string, e.g. 'a_2'
    if proposal != 'undeclared' and target != 'random':
        print('You can either specify proposal, of form ([1,2,3],4), or target, of form \'a_2\', but not both.')
    elif target != 'random':
        c = FirstMoveAgainst_RandomPremise(frame = frame, target = target, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)
    elif proposal != 'undeclared':
        (a,b) = proposal
        c = ManualInitialMoveAgainst(frame = frame, proposal = (frozenset(a), b), CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)
    else:
        c = RandomFirstMoveAgainst(frame = frame, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory)

    lst = [c]
    while c.AvailableMove['for'] != frozenset() or c.AvailableMove['against'] != frozenset():
        c = NextStage(laststage = c, CL_strategy = CL_strategy, CR_strategy = CR_strategy)
        lst.append(c)
    result = Inquiry(MSF = c.MSF, ListOfStages = lst, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory, CL_Strategy = CL_strategy, CR_Strategy = CR_strategy)
    return result

def InquiryFromStage(orig_inq, stage_num, next_stage = None, CL_strategy = None, CR_strategy = None):
    if not CL_strategy:
        CL_strategy = orig_inq.CL_Strategy
    if not CR_strategy:
        CR_strategy = orig_inq.CR_Strategy

    stage_list = orig_inq.ListOfStages[:stage_num]

    if next_stage:
        stage_list.append(next_stage)

    stage = stage_list[-1]

    while stage.AvailableMove['for'] != frozenset() or stage.AvailableMove['against'] != frozenset():
        stage = NextStage(laststage=stage, CL_strategy=CL_strategy, CR_strategy=CR_strategy)
        stage_list.append(stage)

    return Inquiry(MSF = stage.MSF, ListOfStages = stage_list, CL_InferentialTheory=orig_inq.CL_InferentialTheory, CR_InferentialTheory = orig_inq.CR_InferentialTheory, CL_Strategy = CL_strategy, CR_Strategy = CR_strategy)

########################################################################################################################
########################################################################################################################
##########################################          Manual Inquiry          ############################################
########################################################################################################################
########################################################################################################################


def ManualInquiry_RandomFirstMove(frame, val, target, CL_InferentialTheory, CR_InferentialTheory):
    if val == 'reason for':
        c = FirstMoveFor_RandomPremise(frame = frame, conclusion = target, CL_InferentialTheory = CL_InferentialTheory,
                                       CR_InferentialTheory = CR_InferentialTheory)
    elif val == 'reason against':
        c = FirstMoveAgainst_RandomPremise(frame = frame, target = target, CL_InferentialTheory = CL_InferentialTheory,
                          CR_InferentialTheory = CR_InferentialTheory)
    else:
        print('val must be either \'reason for\' or \'reason against\'.')
    lst = [c]
    return Inquiry(MSF = frame, ListOfStages = lst, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory)


def ManualInquiry_FirstMove(frame, premise, val, conclusion, CL_InferentialTheory, CR_InferentialTheory):
    if val == 'reason for':
        c = FirstMoveFor(frame = frame, premise = premise, conclusion = conclusion, CL_InferentialTheory = CL_InferentialTheory,
                         CR_InferentialTheory = CR_InferentialTheory)
    elif val == 'reason against':
        c = FirstMoveAgainst(frame = frame, premise = premise, target = conclusion, CL_InferentialTheory = CL_InferentialTheory,
                         CR_InferentialTheory = CR_InferentialTheory)
    else:
        print('input error')
    lst = [c]
    return Inquiry(MSF = frame, ListOfStages = lst, CL_InferentialTheory = CL_InferentialTheory, CR_InferentialTheory = CR_InferentialTheory)

def ManualInquiry_Completion_Single(inq, targetnum, pragsig, proposal, val):
    last = inq.ListOfStages[-1]
    target = inq.ListOfStages[targetnum]
    s = ManualNextStage(last_stage = last, targetstage = target, pragsig = pragsig, proposal = proposal,
                        val = val)
    return Inquiry(MSF = inq.MSF, ListOfStages = inq.ListOfStages + [s], CL_InferentialTheory = inq.CL_InferentialTheory, CR_InferentialTheory = inq.CR_InferentialTheory)


def Inquiry_Completion(inq):
    lst = inq.ListOfStages
    c = lst[-1]
    while c.AvailableMove['for'] != frozenset() or c.AvailableMove['against'] != frozenset():
        c = RandomNextStage(c)
        lst.append(c)
    result = Inquiry(MSF = c.MSF, ListOfStages = lst, CL_InferentialTheory = inq.CL_InferentialTheory, CR_InferentialTheory = inq.CR_InferentialTheory)
    return result

########################################################################################################################
########################################################################################################################
#############################################          DP2 Output          #############################################
########################################################################################################################
########################################################################################################################

def Inquiry2MSF(inquiry):
    imp = list()
    inc = list()
    for i in inquiry.AcceptedFor:
        imp.append((frozenset(i[0]), i[1]))
    for i in inquiry.AcceptedAgainst:
        inc.append(frozenset.union(frozenset(i[0]), frozenset([i[1]])))
    return MSF_closure(inquiry.Language, frozenset(imp), frozenset(inc))