import networkx as nx
import matplotlib.pyplot as plt
from globalVariables import *

# generate adjacency list from blocktree
def graphFromBlockTree(tree):
    ids = sorted(list(tree.keys()))
    mapping = {} # stores mapping of block ID to node number
    for i in range(len(ids)):
        mapping[ids[i]] = i
    graph = [[] for id in ids]
    for id in ids:
        block = tree[id][0]
        # if block has a parent, add edge from parent to block
        if block.parent is not None:
            graph[mapping[block.parent]].append(mapping[id])
    
    return graph, mapping

# returns mapping of node number to block ID
def getNodeLabels(tree):
    ids = sorted(list(tree.keys()))
    labels = {}
    for i in range(len(ids)):
        labels[i] = ids[i]
    return labels

# returns colors used for visualization, longest chain is red and branches are blue
def getNodeColors(tree, mapping, leaf):
    ids = sorted(list(tree.keys()))
    colors = ['#1f78b4' for id in ids]
    curr = leaf
    while curr is not None:
        colors[mapping[curr]] = '#ff0000'
        curr = tree[curr][0].parent
    return colors

# generate visualization for blocktree, networkx library is used for this purpose
def drawGraph(tree, leaf, filename):
    graph, mapping = graphFromBlockTree(tree)
    labels = getNodeLabels(tree)
    colors = getNodeColors(tree, mapping, leaf)
    
    nxG = nx.Graph()
    for i in range(len(graph)):
        for j in graph[i]:
            nxG.add_edge(i,j)
    plt.figure(figsize=(12,10))
    nx.draw_kamada_kawai(nxG, nodelist=list(range(len(graph))),labels=labels, node_color=colors, node_size = 90, font_size = 7)
    plt.savefig(filename)
    plt.close()

# To visualize how peers are connected
def plotPeerGraph(graph):
    nxG = nx.Graph()
    labels = {}
    for i in range(len(graph)):
        for j in graph[i]:
            nxG.add_edge(i,j)
        labels[i] = i
    plt.figure()
    nx.draw_kamada_kawai(nxG, nodelist=list(range(len(graph))), labels=labels)
    plt.show()