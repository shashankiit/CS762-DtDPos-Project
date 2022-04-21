from cProfile import label
from globalVariables import *
from peer import Peer
from block import Block
from Events import GenerateTransaction, GenerateBlock, random_choice_except
from visulaize import drawGraph, plotPeerGraph, graphFromBlockTree, getNodeLabels
import os, shutil
from blockchain import Blockchain
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # plotPeerGraph(G)
    # Genesis Block is included in the blocktree of every peer during initialization
    # It is the first block being created, so it's ID is 0
    genesisBlock = Block(None, [], 0)
    genesisBlock.accepted = True
    
    invalidTxnProbList = [0 if (x+1)%5==0 else 0 for x in range(number_of_peers)]
    # Add peers to nodeList
    for p in range(number_of_peers):
        peer = Peer(p, G[p], genesisBlock, 0)
        nodeList.append(peer)
        global_trust_values.append(1/number_of_peers)

    timestamp = 0
    parNextBlock = 0
    BlockTree = Blockchain(0, genesisBlock) # Blockchain to keep track of nodes

    # Transaction generation by all nodes
    for sender in nodeList:
        # Randomly choose another peer to pay (cannot be itself)
        receiverID = random_choice_except(0, number_of_peers, sender.id)

        # amount (int) can be from 0 (inclusive) to the balance of that peer (inclusive) in the longest chain stored in the peer
        amount = rng.integers(0, sender.getBalance()+1) if sender.getBalance() > 0 else 0
        pq.put((0, next(unique), GenerateTransaction(timestamp, sender.id, receiverID, amount, False)))
    
    # plotPeerList = [3, 7, 9, 14, 19] # Peers to plot trust values
    plotPeerList = list(range(number_of_peers))
    peerGlobalTrustValues = np.zeros((numElectionCycles + 1, len(plotPeerList)))
    peerGlobalTrustValues[0, :] = np.array([global_trust_values[x] for x in plotPeerList])
    
    # Conduct numElectionCycles for simulation
    for electionIdx in range(numElectionCycles):
        print(f'\n*******************\nElection Cycle #: {electionIdx + 1}')
        # Voting in current Election Cycle
        votes = np.zeros((number_of_peers,))
        for peer in nodeList:
            votes[peer.giveVote()] += peer.getBalance() # Vote is proportional to stake
        witnessNodesList = list(np.argsort(votes)[-numWitnessNodes:]) # Choose witnessNodes
        changeWitnessNodes(witnessNodesList)
        print(f'Selected Witness Nodes: {witnessNodes}\n')
        # Witness nodes start generating blocks
        curr_cycle_blocks = []
        
        for i in range(roundNumBlocks):
            witnessID = witnessNodes[i%numWitnessNodes] # ID of the witness node generating blocks
            print(f'\nPeer {witnessID} attempting to generate block')
            pq.put((timestamp, next(unique), GenerateBlock(timestamp, witnessID, parNextBlock)))
            
            endtime = timestamp + timeforVote # Time for voting
            # Fetch events from queue and process them
            while not pq.empty():
                time, dummy, e = pq.get()
                if time > endtime:
                    pq.put((time, next(unique), e))
                    break
                timestamp = time
                e.process()
            
            curr_block = nodeList[witnessID].blocktree[Block.BlkID][0] # Extract the block under voting
            curr_cycle_blocks.append(curr_block)
            
            if curr_block.votes >= numWitnessNodes*0.5:
                print(f'Block {Block.BlkID} received {curr_block.votes} votes, hence accepted!')
                curr_block.accepted = True
                parNextBlock = Block.BlkID
            else:
                print(f'Block {Block.BlkID} received {curr_block.votes} votes, hence rejected!')

        print('\nUpdating trust values ...')
        # Calculate local trust values
        sat = np.zeros((number_of_peers, number_of_peers))
        unsat = np.zeros((number_of_peers, number_of_peers))
        for block in curr_cycle_blocks:
            invalid_txns = BlockTree.VerifyAddBlock(block) # returns list of invalid txns

            for txn in block.txns[:-1]:
                txnID, sender, receiver, amount = txn.txn_id, txn.sender_id, txn.receiver_id, txn.coins
                if receiver in nodeList[sender].neighbors:
                    if txnID in invalid_txns:
                        unsat[sender,receiver] += 1
                    else:
                        sat[sender,receiver] += 1
        
        s = np.maximum(sat - unsat, 0)
        c = s/np.sum(s, axis=1, keepdims=True)
        m = c
        while True:
            m1 = np.matmul(m, m)
            new_entries = (m==0)
            np.fill_diagonal(new_entries, False)
            m[new_entries] = m1[new_entries]
            m = m/np.sum(m, axis=1, keepdims=True)
            if new_entries.any() == False:
                break
            if (m1[new_entries] == 0).all():
                break
        global_trust_values = m.T@global_trust_values
        print(np.sum(global_trust_values))
        # norm_trust_values = np.array(global_trust_values)/max(np.sum(np.array(global_trust_values)),1e-3)
        peerGlobalTrustValues[electionIdx + 1, :] = np.array([global_trust_values[x] for x in plotPeerList])

    plt.figure()
    for p_idx in range(len(plotPeerList)):
        plt.plot(np.arange(numElectionCycles + 1), peerGlobalTrustValues[:, p_idx], label = f'Peer {plotPeerList[p_idx]}', marker=".", markersize=10)
    plt.xticks(np.arange(numElectionCycles + 1), np.arange(numElectionCycles + 1, dtype=int))
    plt.legend()
    plt.show()
    
    
    # ---------------------
    # TODO: Update Output
    # Remove previous outputs if they exist
    # if os.path.exists('output'):
    #     shutil.rmtree('output')
    
    # os.mkdir('output')
    
    # peerRatios = [] # Stores the ratio of blocks generated by this peer in the longest chain to the 
    #                 # total number of blocks generated by this peer
    # peerBranchLength = [] # Stores average length of branch originating from longest chain of a peer
    # # Write the arrival time of blocks for each peer into .txt files and save visualizations of the
    # # blocktrees for each peer as .png files
    # for peer in nodeList:
    #     graph, mapping = graphFromBlockTree(peer.blocktree)
    #     labels = getNodeLabels(peer.blocktree)

    #     output = []
    #     def generateOutput(node, blockNum):
    #         block, arrivalTime = peer.blocktree[labels[node]]
    #         output.append((block.id, blockNum, arrivalTime, block.parent))
    #         for child in graph[node]:
    #             generateOutput(child, blockNum + 1)
    #     generateOutput(0, 0)

    #     with open(f'output/{peer.id}.txt','w') as f:
    #         for entry in sorted(output, key=lambda x: (x[1], x[2])):
    #             f.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")
        
    #     drawGraph(peer.blocktree, peer.longestChainLeaf, f"output/blocktree_{peer.id}.png")
        
    #     genBlocksInLongestChain, totalGenBlocks = 0, 0

    #     for blockID, val in peer.blocktree.items():
    #         block = val[0]
    #         if block.id != 0:
    #             coinbaseTxn = block.txns[-1]
    #             # ID of peer in coinbase Txn is the one who mined the block
    #             if peer.id == int(coinbaseTxn.split()[1]):
    #                 totalGenBlocks += 1
        
    #     longestChain = [] # Stores longest chain
    #     currBlockID = peer.longestChainLeaf
        
    #     while currBlockID is not None:
    #         longestChain.insert(0, mapping[currBlockID])
    #         currBlock = peer.blocktree[currBlockID][0]
    #         if currBlock.id != 0:
    #             coinbaseTxn = currBlock.txns[-1]
    #             if peer.id == int(coinbaseTxn.split()[1]):
    #                 genBlocksInLongestChain += 1
                
    #         currBlockID = currBlock.parent
        
    #     ratio = genBlocksInLongestChain/totalGenBlocks if totalGenBlocks > 0 else 0
    #     peerRatios.append(ratio)

    #     branchLengths = [] # Stores lengths of all branches for a particular peer
    #     for i in range(len(longestChain)):
    #         node = longestChain[i]
            
    #         def branchDFS(root, length):
    #             # If we are at the leaf node or at the child of node which is present in longest chain
    #             if i < len(longestChain)-1 and root == longestChain[i+1]:
    #                 return
    #             elif len(graph[root]) == 0: # If we are at leaf of a branch, append its length
    #                 branchLengths.append(length)
    #             else:
    #                 for child in graph[root]:
    #                     branchDFS(child, length + 1)
    #         # If node has 0 children, then it means we are at the leaf of longest chain
    #         # If node has 1 child, there are no branches from this node as its only child is a part of longest chain
    #         # If node has more than 1 child, then we are sure that this node has atleast 1 branch, so we run branchDFS
    #         if len(graph[node]) > 1:
    #             branchDFS(node, 0)
            
    #     meanBL = np.mean(branchLengths) if len(branchLengths) > 0 else 0 # average branch length for a peer
    #     peerBranchLength.append(meanBL)

    #     # print(f"Peer {peer.id} | {peer.label} | meanT_k = {meanT_k[peer.id]} | Ratio = {ratio} | Avg. branch length = {meanBL}")

    # print("Average Ratio for all Peers = ", np.mean(peerRatios))
    # print("Average Branch Length for all Peers = ", np.mean(peerBranchLength))
    # # plotPeerGraph(G)
    # fout.close()
    


