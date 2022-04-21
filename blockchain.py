from block import Block
from globalVariables import *
from events import *

class Blockchain:
    def __init__(self, id, genesisBlock):
        self.id = id # unique id of BlockChain

        self.allBalances = [10 for id in range(number_of_peers)]

        # Dictionary of the form txnID: (usedFlag, txn), where usedFlag is 1 if txn is used in the longest 
        # chain of the block and 0 if it's not
        self.txnpool = {}

        # blocktree stores all accepted blocks received or mined by this peer. blkID: (Block)
        self.blocktree = {0: genesisBlock}

        self.longestChainLeaf = 0 # the blkID of the leaf in the longest chain of this peer
                        
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
    def VerifyAddBlock(self, block):
        assert(self.blocktree[block.parent].accepted)

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
            

        invalid_txns = []
        # No need to verify coinbase as it only increments balance of a peer
        for txn in block.txns[:-1]:
            tmp = txn.split()
            txnID, sender, receiver, amount = int(tmp[0][:-1]), int(tmp[1]), int(tmp[3]), int(tmp[4])
            if sender < 0 or sender >= number_of_peers or receiver < 0 or receiver >= number_of_peers or txnID < 0 or amount < 0:
                # return False
                invalid_txns.append(txnID)
            # if txn is already present in current chain, discard the block
            elif txnID in txnpool and txnpool[txnID][0] == 1:
                invalid_txns.append(txnID)
                # return False
            # if sender is trying to pay more than balance, discard the block
            elif allBalances[sender] < amount:
                invalid_txns.append(txnID)
                # return False
            else:
                txnpool[txnID] = (1, txn) # mark txn as used in txnpool
                allBalances[sender] -= amount # deduct amount from sender's balance
                allBalances[receiver] += amount # add amount in receiver's balance
        
        if len(invalid_txns) > 0:
            return invalid_txns

        # Handle coinbase seperately
        tmp = block.txns[-1].split()
        txnID, receiver = int(tmp[0][:-1]), int(tmp[1])
        allBalances[receiver] += 50

        self.blocktree[block.id] = block # Add block in blocktree
        self.allBalances = allBalances # update peer.allBalances
        self.txnpool = txnpool
        self.longestChainLeaf = block.id # Update longest chain leaf
        return invalid_txns