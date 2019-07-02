import datetime
import hashlib
import json
import pickle

"""
Each block has a hash key which acts as a unique id
This id can be published publicly to verify block anywhere

The hash_block and is_block are the main interface for users
create_block creates valid block

"""
AUTHOR = "author"
DATA = "payload"
DATA_HASH = "payload_hash"
METADATA = "metadata"
DATE = "date"
HASH = "hash"
KEYS = [
        AUTHOR,
        DATA,
        DATA_HASH,
        METADATA,
        DATE,
        HASH
]


# Unused
DATA_TYPES = [str, int, float, bytes]


def hash_data(data):
    return repr(hashlib.sha1(str(data).encode("utf-8")).hexdigest())


def is_block(block, full=True):
    for key in KEYS:
        if full or key != HASH:
            if key not in block:
                return False
    return True


def is_valid(block):
    if not is_block(block):
        raise TypeError("Not a block")
    if hash_data(block[DATA]) != block[DATA_HASH]:
        return False
    if hash_block(block) != block[HASH]:
        return False
    return True


# TODO: !!! sign hash with this AMI's asymetric key
#       this prevents anyone else from changing the block
def hash_block(block):
    if not is_block(block, full=False):
        raise TypeError("Not a block")

    hashes = [hash_data(block[key]) for key in KEYS if key not in [DATA, HASH]]

    return hash_data(' '.join(hashes))


def serialize(block):
    if is_block(block) and is_valid(block):
        return pickle.dumps(block, 2)
    else:
        raise ValueError("not a  block or invalid block")


def deserialize(raw):
    block = pickle.loads(raw)
    if not is_block(block):
        raise TypeError("invalid block structure")
    if not is_valid(block):
        raise ValueError("block is corrupted")
    return block


def create(author, payload, metadata=None):
    if author is None or type(author) != str:
        raise TypeError("Author must be a string")
    if payload is not None and type(payload) not in (str, dict, list, int,
                                                     float, bytes):
        raise TypeError("Payload must be a list,dict,str")
    if metadata is not None and type(metadata) != dict:
        raise TypeError("Metadata must be None or a dict")

    block = {
        AUTHOR: author,
        DATA: payload,
        DATA_HASH: hash_data(payload),
        METADATA: metadata,
        DATE: str(datetime.datetime.now()),
        HASH: u''
    }

    block[HASH] = hash_block(block)
    return block
