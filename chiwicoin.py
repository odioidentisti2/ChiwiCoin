from hashlib import sha256
import json
from urllib.parse import urlparse
from time import ctime

import requests  # to get responses via http
from flask import Flask, request, render_template


PORT = 5000


class BlockChain:

    genesis_block = {'Per aspera': 'ad astra',
                     'proof': 0
                     }

    def __init__(self):
        self.nodes = set()
        self.chain = []
        self.pending_txs = []

    def __repr__(self):
        output = "BLOCKCHAIN:\n\n"
        for block in self.chain:
            output += str(block) + '\n'
        return output

    def last_block(self):
        try:
            return self.chain[-1]
        except IndexError:
            return self.genesis_block

    def new_tx(self, sender, recipient, amount):
        tx = {'from': sender,
              'to': recipient,
              'amount': amount
              }
        self.pending_txs.append(tx)
        # self.new_block()  # for now: 1 tx, 1 block!
        return tx

    def new_block(self):
        print(f"VALIDATING BLOCK\n> Transactions: {self.pending_txs}")
        last_block = self.last_block()
        last_hash = _hash(last_block)
        proof = proof_of_work(last_block['proof'], last_hash, verbose=True)
        block = {'index': len(self.chain),
                 'time': ctime(),
                 'transactions': self.pending_txs,
                 'prev_hash': last_hash,
                 'proof': proof
                 }
        self.chain.append(block)
        self.pending_txs = []
        return block

    def validate(self):
        prev_hash = _hash(self.genesis_block)
        prev_proof = self.genesis_block['proof']
        for block in self.chain:
            # pow = valid_pow(prev_proof, block['proof'], prev_hash)
            if block['prev_hash'] != prev_hash or\
                    not valid_pow(prev_proof, block['proof'], prev_hash):
                return False
            prev_hash = _hash(block)
            prev_proof = block['proof']
        return True

    def add_node(self, address):
        self.nodes.add(address)
        # if url := urlparse(address).path:
        #     self.nodes.add(url)
        #     return True\

    def update(self):
        longest = self.chain
        for node in bc.nodes:
            resp = requests.get(f'http://{node}/')
            if resp.status_code == 200:
                chain = resp.json()['chain']
                if len(chain) > len(longest):
                    longest = chain
        if longest != self.chain:
            self.chain = longest
            return True


def _hash(block):
    block_string = json.dumps(block, sort_keys=True).encode()  # encode unicode
    return sha256(block_string).hexdigest()  # hashing


def proof_of_work(last_proof, last_hash, verbose=False):  # why last hash?
    if verbose: print("\tMining...")
    proof = 0
    while not valid_pow(last_proof, proof, last_hash, verbose=verbose):
        proof += 1
    return proof


def valid_pow(prev_proof, proof, prev_hash, verbose=False):
    zeroes = 4
    guess_hash = sha256(f"{prev_proof}{proof}{prev_hash}".encode()).hexdigest()
    # print(f"\t{guess_hash}")
    if guess_hash[:zeroes] == "0" * zeroes:
        if verbose:
            # print(f"\n\tprev_proof = {prev_proof} _ prev_hash = {prev_hash}")
            print(f"\t*** MINED: {guess_hash} ( proof = {proof} )\n")
        return guess_hash


app = Flask(__name__)

bc = BlockChain()
# bc.new_tx('Foo', 'Bar', 10)
# bc.new_block()
# bc.new_tx('Bar', 'Foo', 10)
# bc.new_block()
# print(bc)
# print("\nVALIDATION: {}\n".format(bc.validate()))

# bc.chain[0]['transactions'][0]['amount'] = 100  # CHEATING
# print(bc)
# print("\nVALIDATION: {}\n\n".format(bc.validate()))
## now = time.time()
## time.ctime(now)

# bc.nodes.add('127.0.0.1:5000')
# bc2 = BlockChain()
# bc2.new_block()
# bc.new_node('127.0.0.1')


# FLASK:  return dict  =>  jsonified automatically (+ pretty-print if debug=True)

@app.route('/')
def chain():
    return {'_README': 'Blockchain',
            'chain': bc.chain,
            'pending_tx': bc.pending_txs
            }


@app.route('/transaction')
def input_tx():
    return render_template('/transaction_form.html')


@app.route('/pending_transactions', methods=['POST'])
def add_tx():
    new_tx = bc.new_tx(request.form['from'],
                       request.form['to'],
                       request.form['amount'])
    return {'_README': 'New transaction added to the que',
            'tx': new_tx,
            'pending_transactions': len(bc.pending_txs)}


@app.route('/mine')
def mine():
    new_block = bc.new_block()
    return {'README': "Mined new block",
            'block': new_block,
            }


@app.route('/register')
def add_node():
    address = f'{request.remote_addr}:{PORT}'
    bc.add_node(address)
    return {'_README': 'Your node (IP) has been added to the network',
            'node': address,
            'total_nodes': len(bc.nodes) + 1
            }


@app.route('/sync')
def sync():
    is_updated = bc.update()
    if is_updated:
        return {'msg': 'Blockchain UPDATED!',
                'length': len(bc.chain)
                }
    else:
        return {'msg': 'This node is up to date',
                'length': len(bc.chain)
                }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)  # host='127.0.0.1')  # 0.0.0.0 to be visible from externally as well
