class Block:
    BlkID = -1 # This is incremented every time we attempt to create a block
    def __init__(self, parent, txns, broadcastTime):
        
        Block.BlkID += 1
        self.id = Block.BlkID
        self.parent = parent # ID of parent of this block
        self.txns = txns # List of Txns (with coinbase as last entry)
        self.broadcastTime = broadcastTime # Time at which block was mined and broadcasted
        self.accepted = False  # Voting is succesful
        self.votes = 0 # Number of votes received in voting