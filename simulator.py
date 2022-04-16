from globalVariables import *
from peer import Peer
from Events import GenerateTransaction, GenerateBlock
from visulaize import drawGraph, plotPeerGraph, graphFromBlockTree, getNodeLabels
import os, shutil

if __name__ == '__main__':

    # Everyone starts mining on empty block
    for peer in nodeList:
        pq.put((0, next(unique), GenerateBlock(0, peer.id)))
    
    # Everyone starts generating transactions
    for peer in nodeList:
        # Randomly choose another peer to pay (cannot be itself)
        pids = list(range(len(nodeList)))
        pids.remove(peer.id)
        peer2ID = nodeList[rng.choice(pids)].id
        
        # amount (int) can be from 0 (inclusive) to the balance of that peer (inclusive) in the longest chain stored in the peer
        amount = rng.integers(0,peer.allBalances[peer.id]+1) if peer.allBalances[peer.id]>0 else 0
        pq.put((0, next(unique), GenerateTransaction(0, peer.id, peer2ID, amount)))
    
    # the main loop, fetch events from queue and process them
    while True:
        # If all peers have atleast 100 blocks in their blocktree, end the simulation
        if all([len(peer.blocktree)>=100 for peer in nodeList]):
            break
        e = pq.get()[2]
        e.process()
    
    # Remove previous outputs if they exist
    if os.path.exists('output'):
        shutil.rmtree('output')
    
    os.mkdir('output')
    
    peerRatios = [] # Stores the ratio of blocks generated by this peer in the longest chain to the 
                    # total number of blocks generated by this peer
    peerBranchLength = [] # Stores average length of branch originating from longest chain of a peer
    # Write the arrival time of blocks for each peer into .txt files and save visualizations of the
    # blocktrees for each peer as .png files
    for peer in nodeList:
        graph, mapping = graphFromBlockTree(peer.blocktree)
        labels = getNodeLabels(peer.blocktree)

        output = []
        def generateOutput(node, blockNum):
            block, arrivalTime = peer.blocktree[labels[node]]
            output.append((block.id, blockNum, arrivalTime, block.parent))
            for child in graph[node]:
                generateOutput(child, blockNum + 1)
        generateOutput(0, 0)

        with open(f'output/{peer.id}.txt','w') as f:
            for entry in sorted(output, key=lambda x: (x[1], x[2])):
                f.write(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}\n")
        
        drawGraph(peer.blocktree, peer.longestChainLeaf, f"output/blocktree_{peer.id}.png")
        
        genBlocksInLongestChain, totalGenBlocks = 0, 0

        for blockID, val in peer.blocktree.items():
            block = val[0]
            if block.id != 0:
                coinbaseTxn = block.txns[-1]
                # ID of peer in coinbase Txn is the one who mined the block
                if peer.id == int(coinbaseTxn.split()[1]):
                    totalGenBlocks += 1
        
        longestChain = [] # Stores longest chain
        currBlockID = peer.longestChainLeaf
        
        while currBlockID is not None:
            longestChain.insert(0, mapping[currBlockID])
            currBlock = peer.blocktree[currBlockID][0]
            if currBlock.id != 0:
                coinbaseTxn = currBlock.txns[-1]
                if peer.id == int(coinbaseTxn.split()[1]):
                    genBlocksInLongestChain += 1
                
            currBlockID = currBlock.parent
        
        ratio = genBlocksInLongestChain/totalGenBlocks if totalGenBlocks > 0 else 0
        peerRatios.append(ratio)

        branchLengths = [] # Stores lengths of all branches for a particular peer
        for i in range(len(longestChain)):
            node = longestChain[i]
            
            def branchDFS(root, length):
                # If we are at the leaf node or at the child of node which is present in longest chain
                if i < len(longestChain)-1 and root == longestChain[i+1]:
                    return
                elif len(graph[root]) == 0: # If we are at leaf of a branch, append its length
                    branchLengths.append(length)
                else:
                    for child in graph[root]:
                        branchDFS(child, length + 1)
            # If node has 0 children, then it means we are at the leaf of longest chain
            # If node has 1 child, there are no branches from this node as its only child is a part of longest chain
            # If node has more than 1 child, then we are sure that this node has atleast 1 branch, so we run branchDFS
            if len(graph[node]) > 1:
                branchDFS(node, 0)
            
        meanBL = np.mean(branchLengths) if len(branchLengths) > 0 else 0 # average branch length for a peer
        peerBranchLength.append(meanBL)

        print(f"Peer {peer.id} | {peer.label} | meanT_k = {meanT_k[peer.id]} | Ratio = {ratio} | Avg. branch length = {meanBL}")

    print("Average Ratio for all Peers = ", np.mean(peerRatios))
    print("Average Branch Length for all Peers = ", np.mean(peerBranchLength))
    # plotPeerGraph(G)
    fout.close()
    

