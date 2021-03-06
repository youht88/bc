
CONFIG_FILE='./config.yaml'
PEERS_FILE='peers'

ROOT_DIR='/bc'
CHAINDATA_DIR = 'chaindata/'
PRIVATE_DIR = 'private/'
BROADCASTED_BLOCK_DIR = CHAINDATA_DIR + 'blocks/'
BROADCASTED_TRANSACTION_DIR=CHAINDATA_DIR+'transactions/'
UTXO_DIR = CHAINDATA_DIR+'utxo/'


NUM_ZEROS = 2
TRANSACTION_TO_BLOCK=3
NUM_FORK=6
REWARD=2.0

BLOCK_VAR_CONVERSIONS = {'index': int, 'nonce': int, 'hash': str, 'prev_hash': str, 'timestamp': int,
    'diffcult': int}

TRANSACTION_VAR_CONVERSIONS = {'hash': str}

DEBUG_MODE = False
