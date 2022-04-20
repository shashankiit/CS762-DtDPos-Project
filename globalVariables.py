from itertools import count
import numpy as np
from queue import PriorityQueue

rng = np.random.default_rng(0) # seed for the simulation is specified here
unique = count() # the event id, used for distinguishing between events which occur at the same time
number_of_peers = 20 # number of peer nodes in the network
roundNumBlocks = 50 # number of block per election cycle
numWitnessNodes = 10 # number of witness nodes per election cycle
witnessNodes = [] # set of witness nodes
numElectionCycles = 5
peerSleepBeta = 0.2 # mean of interarrival time of transactions
timeforVote = 20 # Per block in election cycle
parNextBlock = None # Parent of next block to be generated
# meanT_k = [10 for i in range(number_of_peers)]
loggingTxn = False
loggingBlock = False
block_Votes = 0 # votes for the current block in circulation

# Do DFS on a undirected graph given as adjacency list
def DFS(v, G, visited):
    visited[v] = True
    for u in G[v]:
        if not visited[u]:
            DFS(u, G, visited)

# As the given graph is undirected, it is connected if we are able to reach all nodes from any one chosen node
def isConnected(G, n):
    visited = [False for i in range(n)]
    DFS(0, G, visited) # Here we start from node 0
    return all(visited)

# Used for generating random P2P network
def generateRandomGraph(n):
    p = np.log(n)/n # Probability of each edge is log(n)/n
    # We randomly generate graphs until we get a connected graph
    while True:
        G = [[] for i in range(n)]
        for i in range(n):
            for j in range(i):
                if rng.random() < p:
                    G[i].append(j)
                    G[j].append(i)
        if isConnected(G, n):
            return G

G = generateRandomGraph(number_of_peers) # Peer Graph
nodeList = [] # Stores all the Peers
global_trust_values = [] # Stores global trust values
pq = PriorityQueue() # The Event Queue
fout = open("log.txt","w") # log file