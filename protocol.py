import typing
import bittensor as bt

class Bundle(bt.Synapse):
    """
    A custom protocol for handling Arweave bundle creation requests.
    This Synapse is designed to be sent from a validator to a miner.

    Attributes:
    - data_items: A list of strings, where each string is a piece of data to be included in the bundle.
    - bundle_data: A base64 encoded string representing the bundled data, returned by the miner.
    - bundle_id: A string representing the bundle's identifier, returned by the miner.
    - merkle_root: A string representing the Merkle root of the bundle, used as proof.
    - signature: A string representing the miner's digital signature of the Merkle root.
    """

    # Required request input, filled by the dendrite caller.
    data_items: typing.List[str]

    # Optional response output, filled by the axon responder.
    bundle_data: typing.Optional[str] = None
    bundle_id: typing.Optional[str] = None
    merkle_root: typing.Optional[str] = None
    signature: typing.Optional[str] = None

    def deserialize(self) -> str:
        """
        Deserialize the dummy output. This method is used by the dendrite to extract the response
        from the axon.
        """
        # The dendrite client queries the miner axon and receives a response containing vital bundle information
        return self.bundle_data
