from block import Block
from globalVariables import *
from events import *

class Peer:
    def __init__(self, id, neighbors, genesisBlock):
        self.id = id # unique id of each peer
        self.neighbors = neighbors # The ids of neighbors of this peer
        self.invalidTxnProb = 0.1
        
        # Each node maintains balances of each peer
        self.allBalances = [10 for id in range(number_of_peers)]

        # Dictionary of the form txnID: (usedFlag, txn), where usedFlag is 1 if txn is used in the longest 
        # chain of the block and 0 if it's not
        self.txnpool = {}

        # blocktree stores all accepted blocks received or mined by this peer. Format is
        # blkID: (Block, arrivalTime), where arrivalTime is the time at which the peer received this block
        self.blocktree = {0: (genesisBlock, 0)}

        self.longestChainLeaf = 0 # the blkID of the leaf in the longest chain of this peer
        # self.longestChainLength = 0 # length of longest chain
        
        # We may receive blocks whose parent is not yet present in the blocktree. They are stored as 
        # parentBlkID: [(Block_1, arrivalTime_1), (Block_2, arrivalTime_2), ...]
        self.pendingBlocks = {}
    

    def getBalance(self):
        return self.allBalances[self.id]

    # Broadcast txn to neighbors of a peer
    def broadcastTxnToNeighbors(self, time, txn):
        for p in self.neighbors:
            neighbor = nodeList[p]

            # latency generated as described in problem statement, |m| = 1 KB = 8*1024 bits as size of txn is fixed
            c_ij = 100
            d_ij = rng.exponential(96/(1024*c_ij))
            latency = rho_ij + 8/(1024*c_ij) + d_ij

            recTime = time + latency 
            pq.put((recTime, next(unique), ReceiveTransaction(recTime, neighbor.id, txn)))

    # Broadcast block to neighbors of a peer
    def broadcastBlockToNeighbors(self, time, block):
        for p in self.neighbors:
            neighbor = nodeList[p]

            # latency generated as described in problem statement, |m| = numTxns * 1KB = numTxns*8*1024 bits as size of txn is fixed
            c_ij = 100
            d_ij = rng.exponential(96/(1024*c_ij))
            latency = rho_ij + 8*len(block.txns)/(1024*c_ij) + d_ij

            recTime = time + latency
            pq.put((recTime, next(unique), ReceiveBlock(recTime, neighbor.id, block, self.id)))
            
    # Given list of txns in a block, update balances stored by the peer
    def updateBalances(self, txns):
        for txn in txns[:-1]:
            tmp = txn.split()
            try:
                sender, reciever, amount = int(tmp[1]), int(tmp[3]), int(tmp[4])
            except Exception as e:
                print(e, txn)
            self.allBalances[sender] -= amount
            self.allBalances[reciever] += amount
        # Last Txn is coinbase so updated seperately
        self.allBalances[int(txns[-1].split()[1])] += 50
    
    # Verify the block if block.parent is accepted; adds the block in the chain
    def VerifyAddBlock(self, block, arrivalTime):
        assert(self.blocktree[block.parent][0].accepted)

        allBalances = self.allBalances[:] # Create a copy so original values do not get changed if block is invalid
        txnpool = self.txnpool.copy() # Create a copy so original values do not get changed if block is invalid

        if block.parent != self.longestChainLeaf:
            chain = [] # This will store the chain
            currBlock = self.blocktree[block.parent][0]
            while currBlock.id != 0: # run loop until we reach genesis block
                chain.append(currBlock) # add block to chain
                currBlock = self.blocktree[currBlock.parent][0] # set currBlock to parent of currBlock
            chain = list(reversed(chain)) # we need to reverse it as we were adding child earlier than parent
            
            for txnID in txnpool:
                txnpool[txnID] = (0, txnpool[txnID][1]) # mark all txns as unused
            allBalances = [0 for id in range(number_of_peers)] # set all balances to 0
            # Now we traverse the chain and modify txnpool and allBalances as we go on to verify the new block
            for anc_block in chain:
                for txn in anc_block.txns[:-1]: # For all txns except coinbase in block
                    tmp = txn.split()
                    txnID, sender, receiver, amount = int(tmp[0][:-1]), int(tmp[1]), int(tmp[3]), int(tmp[4])
                    txnpool[txnID] = (1, txn) # mark txn as used
                    allBalances[sender] -= amount # update sender balance
                    allBalances[receiver] += amount # update receiver balance
                    
                # Handle coinbase seperately, no need to add coinbase in txnpool
                tmp = anc_block.txns[-1].split()
                txnID, receiver = int(tmp[0][:-1]), int(tmp[1])
                allBalances[receiver] += 50
            

        # No need to verify coinbase as it only increments balance of a peer
        for txn in block.txns[:-1]:
            tmp = txn.split()
            txnID, sender, receiver, amount = int(tmp[0][:-1]), int(tmp[1]), int(tmp[3]), int(tmp[4])
            if sender < 0 or sender >= number_of_peers or receiver < 0 or receiver >= number_of_peers or txnID < 0 or amount < 0:
                return False
            # if txn is already present in current chain, discard the block
            elif txnID in txnpool and txnpool[txnID][0] == 1:
                return False
            # if sender is trying to pay more than balance, discard the block
            elif allBalances[sender] < amount:
                return False
            else:
                txnpool[txnID] = (1, txn) # mark txn as used in txnpool
                allBalances[sender] -= amount # deduct amount from sender's balance
                allBalances[receiver] += amount # add amount in receiver's balance
            
        # Handle coinbase seperately
        tmp = block.txns[-1].split()
        txnID, receiver = int(tmp[0][:-1]), int(tmp[1])
        allBalances[receiver] += 50

        self.blocktree[block.id] = (block, arrivalTime) # Add block in blocktree
        self.allBalances = allBalances # update peer.allBalances
        self.txnpool = txnpool
        self.longestChainLeaf = block.id # Update longest chain leaf
        return True

    def giveVote(self):
        return np.random.choice(number_of_peers, p=global_trust_values/np.sum(global_trust_values))