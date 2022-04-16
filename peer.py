from block import Block
from globalVariables import *

# Genesis Block is included in the blocktree of every peer during initialization
# It is the first block being created, so it's ID is 0
genesisBlock = Block(None, [], 0)

class Peer:
    def __init__(self, id, neighbors):
        self.id = id # unique id of each peer
        self.neighbors = neighbors # The ids of neighbors of this peer
        self.invalidTxnProb = 0.1
        self.localTrustValues = [0 for i in range(number_of_peers)]

        self.numValidTxns = [0 for i in range(number_of_peers)]
        self.numInvalidTxns = [0 for i in range(number_of_peers)]
        
        # Each node maintains balances of each peer
        self.allBalances = [0 for id in range(number_of_peers)]

        # Dictionary of the form txnID: (usedFlag, txn), where usedFlag is 1 if txn is used in the longest 
        # chain of the block and 0 if it's not
        self.txnpool = {}

        # blocktree stores all accepted blocks received or mined by this peer. Format is
        # blkID: (Block, arrivalTime), where arrivalTime is the time at which the peer received this block
        self.blocktree = {0: (genesisBlock, 0)}

        self.longestChainLeaf = 0 # the blkID of the leaf in the longest chain of this peer
        self.longestChainLength = 0 # length of longest chain
        
        # We may receive blocks whose parent is not yet present in the blocktree. They are stored as 
        # parentBlkID: [(Block_1, arrivalTime_1), (Block_2, arrivalTime_2), ...]
        self.pendingBlocks = {}
    
    # Given list of txns in a block, update balances stored by the peer
    def updateBalances(self, txns):
        for txn in txns[:-1]:
            tmp = txn.split()
            sender, reciever, amount = int(tmp[1]), int(tmp[3]), int(tmp[4])
            self.allBalances[sender] -= amount
            self.allBalances[reciever] += amount
        # Last Txn is coinbase so updated seperately
        self.allBalances[int(txns[-1].split()[1])] += 50
    
    # If block is attaching to the leaf of longest chain, it can be verified using this function
    def verifyBlock(self, block):
        balances = self.allBalances[:] # Create a copy so original values do not get changed if block is invalid
        txnpool = self.txnpool.copy() # Create a copy so original values do not get changed if block is invalid
        
        # No need to verify coinbase as it only increments balance of a peer
        for txn in block.txns[:-1]:
            tmp = txn.split()
            txnID, sender, receiver, amount = int(tmp[0][:-1]), int(tmp[1]), int(tmp[3]), int(tmp[4])
            if sender < 0 or sender >= number_of_peers or receiver < 0 or receiver >= number_of_peers or txnID < 0 or amount < 0:
                return False
            # if txn is already present in longest chain, discard the block
            elif txnID in txnpool and txnpool[txnID][0] == 1:
                return False
            # if sender is trying to pay more than balance, discard the block
            elif balances[sender] < amount:
                return False
            else:
                txnpool[txnID] = (1, txn) # mark txn as used in txnpool
                balances[sender] -= amount # deduct amount from sender's balance
                balances[receiver] += amount # add amount in receiver's balance
        return True

# Add peers to nodeList
for p in range(number_of_peers):
    peer = Peer(p, G[p])
    nodeList.append(peer)
    global_trust_values.append(1/number_of_peers)