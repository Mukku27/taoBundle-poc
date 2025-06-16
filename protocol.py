import typing
import bittensor as bt

class Bundle(bt.Synapse):
    """
    A custom protocol for handling Arweave bundle creation requests.
    This Synapse is designed to be sent from a validator to a miner.

    Attributes:
    - data_items: A list of strings, where each string is a piece of data to be included in the bundle.
                  This is sent by the validator in the request.
    - bundle_data: A base64 encoded string representing the bundled data, returned by the miner.
                  
    - bundle_id: A string representing the bundle's identifier, returned by the miner.
                .
    - merkle_root: A string representing the Merkle root of an Arweave transaction whose data
                   is the bundle_id. This is used as proof by the miner.
    - signature: A string representing the miner's hotkey digital signature of the Merkle root.
    """


    data_items: typing.List[str]

   
    bundle_data: typing.Optional[str] = None
    bundle_id: typing.Optional[str] = None
    merkle_root: typing.Optional[str] = None
    signature: typing.Optional[str] = None # Miner's signature of the merkle_root

    def deserialize(self) -> typing.Optional[str]:
        """
        Deserialize the bundle_data. This method could be used by the dendrite
        if it expects only the bundle_data as the primary response.
        """
        return self.bundle_data