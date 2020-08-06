from typing import Tuple
from Levenshtein import distance, hamming, median

# -*- coding: utf-8 -*-


class TrieNode(object):
    
    def __init__(self, char: str):
        self.char = char
        self.children = []
        # Is it the last character of the word.`
        self.word_finished = False
        # How many times this character appeared in the addition process
        self.counter = 1
    

def add(root, word: str):
    """
    Adding a word in the trie structure
    """
    node = root
    for char in word:
        found_in_child = False
        # Search for the character in the children of the present `node`
        for child in node.children:
            if child.char == char:
                # We found it, increase the counter by 1 to keep track that another
                # word has it as well
                child.counter += 1
                # And point the node to the child that contains this char
                node = child
                found_in_child = True
                break
        # We did not find it so add a new chlid
        if not found_in_child:
            new_node = TrieNode(char)
            node.children.append(new_node)
            # And then point node to the new child
            node = new_node
    # Everything finished. Mark it as the end of a word.
    node.word_finished = True


def find_prefix(root, prefix: str) -> Tuple[bool, int]:
    
    """
    Check and return 
      1. If the prefix exists in any of the words we added so far
      2. If yes then how may words actually have the prefix
    """
    node = root
    res=''
    # If the root node has no children, then return False.
    # Because it means we are trying to search in an empty trie
    if not root.children:
        print('Empty trie') 
    for char in prefix:
        char_not_found = True
        # Search through all the children of the present `node`
        for child in node.children:
            if child.char == char:
                # We found the char existing in the child.
                char_not_found = False
                # Assign node as the child containing the char and break
                node = child
                res+=node.char
                if node.word_finished==True and res==prefix:
                    return res
                break
        # Return False anyway when we did not find a char.
    return 'Not found'
    # Well, we are here means we have found the prefix. Return true to indicate that
    # And also the counter of the last node. This indicates how many words have this
    # prefix

    
def letter_missing(root,query2,level,one_dist_list,word):
    dist=0
    if not root.children:
        res=''
        query2[level]='*'
        for i in range(len(query2)):
            res+=query2[i]
        for i in range(len(res)):
            if res[i]=='*':
                result=res[:i]
                break
        dist=distance(result,word)
        if dist==1:
            one_dist_list.append(result)
    for i in range(len(root.children)):
        if root.children[i]:
            query2[level]=root.children[i].char
            letter_missing(root.children[i],query2,level+1,one_dist_list,word)


            
def lev_dist(root,word):
    node=root
    query1=word
    dist=0
    query2=''
    one_distance_list=[]
    parent=None
    if not root.children:
        print('Empty trie')
    for char in word:
        char_not_found = True
        # Search through all the children of the present `node`
        for child in node.children:
            if child.char == char:
                # We found the char existing in the child.
                # Assign node as the child containing the char and break
                node = child
                query2=query2+node.char
                dist=distance(query1,query2)
                if(dist==1) and node.word_finished==True:
                    one_distance_list.append(query2)
                parent=node

    for child in parent.children:
        parent= child
        query2=query2+parent.char
        dist=distance(query1,query2)
        if(dist==1)and node.word_finished==True:
            one_distance_list.append(query2)
        parent=child
    if len(one_distance_list)==0:
        letter_missing(root,['*']*40,0,one_distance_list,word)
    if len(one_distance_list)==0:
        return None
    return one_distance_list


def startcheck(user_input_list,no_of_correct, no_of_wrong):
    root = TrieNode('*')
    f=open("flaskblog/data.txt", "r", encoding="utf-8")
    contents=f.read()
    words_list=contents.split()
    for word in words_list:
        word=''.join(c for c in word if c not in '.,?!')
        add(root,word)
    is_wrong=False
    f.close()
    l=[]
    #user_input_list=input('Enter text\n')
    text_list=user_input_list.split()
    tokenize_list=[]
    for word in text_list:
        word=''.join(c for c in word if c not in '.,?!')
        tokenize_list.append(word)
        if find_prefix(root,word)=='Not found' or find_prefix(root,word)!=word:
            #print(word)
            no_of_wrong+=1
            is_wrong=True
        else:
            is_wrong=False
            no_of_correct+=1
            
        if is_wrong==True:
            #print('Pick from the below list')
            l.append(lev_dist(root,word))
    print(l)
    return l,no_of_correct,no_of_wrong,is_wrong
    #print('WRONG:',no_of_wrong)
    #print('CORRECT:',no_of_correct)
    
    
        
        


    
