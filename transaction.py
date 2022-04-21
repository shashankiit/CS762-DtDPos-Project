class Transaction:
    '''
    Attributes:
        txn_id: Transaction ID
        sender_id: Sender node ID
        receiver_id: Receiver node ID
        coins: Bitcoins in transaction
    '''
    txn_count = 0
    
    def __init__(self, sender_id, receiver_id, coins):
        self.txn_id = Transaction.txn_count
        Transaction.txn_count += 1
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.coins = coins

    def is_coinbase_txn(self):
        return (self.sender_id is None)