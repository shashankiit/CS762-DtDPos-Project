from os import remove
import numpy as np
from block import Block
from globalVariables import *

TXNID = 0 # Incremented every time a txn is generated

def random_choice_except(low, high, excluding):
    choice = np.random.randint(low, high - 1)
    choice = choice + int(choice >= excluding)
    return choice

class Event:
    ''' All types of events are derived from this class
    '''

    num_events = 0
    def __str__(self):
        '''For printing into the log file
        '''
        return "Event: " + str(self.__class__.__name__)


# Event for generating a Txn
class GenerateTransaction(Event):
    # Txn for 'peer1ID' pays 'peer2ID' 'amount' coins
    def __init__(self, time, peer1ID, peer2ID, amount):
        self.time = time
        self.peer1ID = peer1ID
        self.peer2ID = peer2ID
        self.amount = amount
    
    def process(self):
        peer1 = nodeList[self.peer1ID]
        global TXNID
        txn = f"{TXNID}: {self.peer1ID} pays {self.peer2ID} {self.amount} coins" # Each txn (except coinbase) is a string of this format
        
        if loggingTxn:
            fout.write(f"Time = {self.time} | GenTxn: {txn}\n") # Write event to log file
        peer1.txnpool[TXNID] = [0, txn] # Add txn to txnpool of peer and mark it as unused
        TXNID += 1 # increment TXNID as new txn is generated
        
        peer1.broadcastTxnToNeighbors(self.time, txn)
        
        # Randomly choose next peer and amount
        peer2ID = random_choice_except(0, number_of_peers, self.peer1ID)
        # If we have a malicious peer, it will generate invalid txns and broadcast them
        if rng.random() < peer1.invalidTxnProb:
            amount = rng.integers(peer1.allBalances[self.peer1ID] + 10, peer1.allBalances[self.peer1ID] + 100)
        else:
            amount = rng.integers(0,peer1.allBalances[self.peer1ID]+1) if peer1.allBalances[self.peer1ID]>0 else 0
        sleepTime = rng.exponential(peerSleepBeta) # Next Txn will be generated by this peer after this much time
        recTime = self.time + sleepTime
        pq.put((recTime, next(unique), GenerateTransaction(recTime, self.peer1ID, peer2ID, amount)))
        
# Event for receiving a txn by a peer
class ReceiveTransaction(Event):
    def __init__(self, time, peerID, txn):
        self.time = time
        self.peerID = peerID # receiver
        self.txn = txn

    def process(self):
        peer = nodeList[self.peerID]

        txnID = int(self.txn.split(":")[0]) # Extract txnID from txn
        # If txn is already in txnpool of a peer then we have seen this txn before so we can ignore it
        # This ensures loop-less forwarding of txn throughout the network
        if txnID not in peer.txnpool:
            if loggingTxn:
                fout.write(f"Time = {self.time} | RecTxn on Peer {self.peerID} | {self.txn}\n") # Write event in log file
            
            peer.txnpool[txnID] = [0, self.txn] # Add txn to txnpool and mark it as unused
            peer.broadcastTxnToNeighbors(self.time, self.txn) # Broadcast Txn

# Event for starting mining by a peer
class GenerateBlock(Event):
    def __init__(self, time, peerID, blk_parent):
        self.time = time
        self.peerID = peerID
        self.blk_parent = blk_parent
    
    def process(self):
        peer = nodeList[self.peerID]
        verifiedTxns = [] # The selected txns to be included in the block are stored in this list in order
        
        for txnID, val in peer.txnpool.items():
            if val[0] == 0: # Add all transactions unused
                txn = val[1]
                verifiedTxns.append(txn)
            if len(verifiedTxns) >= 1023: # Do not include more than 1024 txns (max allowed size is 1MB)
                break
        
        broadcastTime = self.time # Instanteous block generation
        miningBlock = Block(self.blk_parent, verifiedTxns, broadcastTime)
        print(f'Generate Block {self.peerID} {miningBlock.id}')
        # As ths block will be mined at self.time, we pass peerID and senderID the same value of self.peerID
        # to identify this as mining completed event
        pq.put((broadcastTime, next(unique), ReceiveBlock(broadcastTime, self.peerID, miningBlock, self.peerID)))

# Event for Receiving a block on a peer
class ReceiveBlock(Event):
    # We also give the ID of the sender in this case to be able to identify mining case
    def __init__(self, time, peerID, block, senderID):
        self.time = time
        self.peerID = peerID
        self.block = block
        self.senderID = senderID
    
    def process(self):
        global TXNID
        peer = nodeList[self.peerID]
        if self.block.id in peer.blocktree: # If block already present in tree, discard it loopless forwarding
            return
        # if block already present in pending blocks, discard it
        elif self.block.parent in peer.pendingBlocks and self.block.id in [x[0] for x in peer.pendingBlocks[self.block.parent]]:
            return
        # If this condition is true, then self.peerID has possibly mined a block
        elif self.peerID == self.senderID:
            # if longest chain hasn't changed since starting the mining, meaning that the parent of the mined block is
            # the same as leaf of longest chain, then we have successfully mined a block. Otherwise we discard it
            # if self.block.parent == peer.longestChainLeaf:
            if loggingBlock:
                fout.write(f"Time = {self.time} | Block {self.block.id} Mined by Peer {self.peerID}\n") # Write event to log file
            
            coinbaseTxn = f"{TXNID}: {self.peerID} mines 50 coins" # generate coinbase txn for this block
            TXNID += 1 # increment TXNID as new txn is generated
            self.block.txns.append(coinbaseTxn) # add coinbase at the end of block txns
            
            # mark the txns present in this block as used
            for txn in self.block.txns[:-1]:
                peer.txnpool[int(txn.split(":")[0])] = (1, txn)
            
            peer.blocktree[self.block.id] = (self.block, self.time) # Add block to blocktree of peer
            peer.longestChainLeaf = self.block.id # update longest chain leaf
            # peer.longestChainLength += 1 # increment longest chain length
            peer.updateBalances(self.block.txns) # TODO: Recheck update balances of peers as new txns are included
            
            peer.broadcastBlockToNeighbors(self.time, self.block)
                    
        else: 
            # If self.senderID is different from self.peerID, this means we have received a block from someone else


            # Try to add block in blocktree. Returns 0 if block is discarded, 1 if it is added in tree and 
            # -1 if it is a pending block
            def addBlock(block, arrivalTime):
                if block.id in peer.blocktree: # discard if block already in tree
                    return 0
                # discard if block already in pending blocks
                elif block.parent in peer.pendingBlocks and block.id in [x[0] for x in peer.pendingBlocks[block.parent]]:
                    return 0

                # In this case the block can possibly be attached to some block other than leaf.
                # Note parent is always accepted; Since somebody mined on it
                # Covers both cases: block.parent == peer.longestChainLeaf and block.parent != peer.longestChainLeaf
                elif block.parent in peer.blocktree:
                    
                    # Can also be rejected
                    assert(peer.blocktree[block.parent][0].accepted)
                    if peer.VerifyAddBlock(block, arrivalTime):
                        if loggingBlock:
                            fout.write(f"Time = {self.time} | Block {block.id} added by Peer {self.peerID} in Block Tree\n")
                        peer.broadcastBlockToNeighbors(self.time, block) # broadcast block to neighbors
                        
                        # Voting by witnessNodes if block under vote
                        if peer.id in witnessNodes and block.id == Block.BlkID:
                            block_Votes += 1
                        return 1 # leaf has changed
                    else:
                        return 0 # verify block failed
                
                # If block.parent is not in blocktree, we add it to pending blocks
                else:
                    if loggingBlock:
                        fout.write(f"Time = {self.time} | Block {block.id} added by Peer {self.peerID} in pending Blocks\n")
                    # If block.parent is a key in peer.pendingBlocks, we append it to the value otherwise we create and new
                    # key value pair in the dictionary
                    if block.parent in peer.pendingBlocks:
                        peer.pendingBlocks[block.parent].append((block, arrivalTime))
                    else:
                        peer.pendingBlocks[block.parent] = [(block, arrivalTime)]
                    return -1
            
            def removePendingChildren(blockID):
                if blockID in peer.pendingBlocks:
                    for pendingBlock, pendingTime in peer.pendingBlocks[blockID]:
                        removePendingChildren(pendingBlock.id)
                    peer.pendingBlocks.pop(blockID)
                    
            # To add pending blocks to block tree, we need to traverse self.pendingBlocks in a DFS manner, because when we 
            # receive a new block we need to check if any pending blocks has it as parent, then we try to add those blocks,
            # and if successful we try to add their children in pending blocks

            def addRecursive(block, arrivalTime):
                retval = addBlock(block, arrivalTime) # Try to add block in blocktree
                # If block is discarded, remove children of this block in pendingBlocks in a DFS manner
                if retval == 0:
                    if loggingBlock:
                        fout.write(f"Time = {self.time} | Block {block.id} discarded by Peer {self.peerID}\n")
                    removePendingChildren(block.id)
                elif retval == 1: # Proceed only if block is added in tree
                    # if the added block is parent to some blocks in pending blocks, we start DFS on those blocks
                    if block.id in peer.pendingBlocks: 
                        for pendingBlock, pendingTime in peer.pendingBlocks[block.id]:
                            addRecursive(pendingBlock, pendingTime)
                        # As these blocks have their parent in the tree, remove them from pending blocks
                        peer.pendingBlocks.pop(block.id)
            
            addRecursive(self.block, self.time) # add recursively from received block