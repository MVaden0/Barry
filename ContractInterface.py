from operator import contains
import os

import web3
import solcx


solcx.install_solc(version='0.6.6')


class ContractInterface:
    def __init__(self, project_id, private_key, path, network) -> None:
        self.private_key = private_key
        self.path = path

        self.url = f"https://{network}.infura.io/v3/{project_id}"

        self.w3 = web3.Web3(web3.Web3.HTTPProvider(self.url))

        # contract source code
        with open(self.path, "r") as f:
            self.source_contract = f.read()
            f.close()

        # compile contract
        self.compiled_contract = solcx.compile_source(
            self.source_contract,
            output_values=["abi", "bin"]
        )
        self.contract_id, self.contract_interface = self.compiled_contract.popitem()

        self.bytecode = self.contract_interface['bin']
        self.abi = self.contract_interface['abi']

        # contract object
        self.contract, self.contract_address = self.compile()

    def compile(self):
        # raw contract
        contract = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)

        account = self.w3.eth.account.privateKeyToAccount(self.private_key)

        # raw transaction
        raw_txn = contract.constructor().buildTransaction({
            'from': account.address,
            'nonce': self.w3.eth.getTransactionCount(account.address),
            'gas': contract.constructor().estimateGas(),
            'gasPrice': self.w3.toWei('21', 'gwei')})

        # signed transaction
        signed_txn = account.signTransaction(raw_txn)

        txn_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

        # built contract
        contract_address = txn_receipt.contractAddress
        contract = self.w3.eth.contract(address=contract_address, abi=self.abi)

        return contract, contract_address


c = ContractInterface(
        os.environ.get("PROJECT_ID"), 
        os.environ.get("PRIVATE_KEY"), 
        "contracts/v2/FlashloanV2.sol", 
        "kovan"
    )


print(c.contract.functions.greet().call())
print(c.contract_address)