BlkID = 0 # This is incremented every time we attempt to create a block
class Block:
    def __init__(self, parent, txns, broadcastTime):
        global BlkID
        
        self.id = BlkID
        BlkID += 1
        self.parent = parent # ID of parent of this block
        self.txns = txns # List of Txns (with coinbase as last entry)
        self.broadcastTime = broadcastTime # Time at which block was mined and broadcasted
        self.accepted=False