import os
import time
import random
import argparse
import traceback
import bittensor as bt
import subprocess
import json
import torch
import base64

from protocol import Bundle

class Validator:
    def __init__(self):
        self.config = self.get_config()
        self.setup_logging()
        self.setup_bittensor_objects()
        self.my_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        self.scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)
        self.js_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "js/bundler.js")


    def get_config(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        config = bt.config(parser)
        config.full_path = os.path.expanduser(
            "{}/{}/{}/netuid{}/validator".format(
                config.logging.logging_dir,
                config.wallet.name,
                config.wallet.hotkey.ss58_address,
                config.netuid,
            )
        )
        os.makedirs(config.full_path, exist_ok=True)
        return config

    def setup_logging(self):
        bt.logging(config=self.config, logging_dir=self.config.full_path)
        bt.logging.info(f"Running validator for subnet: {self.config.netuid} on network: {self.config.subtensor.network}")
        bt.logging.info(self.config)

    def setup_bittensor_objects(self):
        bt.logging.info("Setting up Bittensor objects.")
        self.wallet = bt.wallet(config=self.config)
        bt.logging.info(f"Wallet: {self.wallet}")
        self.subtensor = bt.subtensor(config=self.config)
        bt.logging.info(f"Subtensor: {self.subtensor}")
        self.dendrite = bt.dendrite(wallet=self.wallet)
        bt.logging.info(f"Dendrite: {self.dendrite}")
        self.metagraph = self.subtensor.metagraph(self.config.netuid)
        bt.logging.info(f"Metagraph: {self.metagraph}")

        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
            bt.logging.error(f"Your validator: {self.wallet} is not registered to chain connection: {self.subtensor}")
            exit()
            
        self.my_subnet_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running validator on uid: {self.my_subnet_uid}")
        
        bt.logging.info("Building validation weights.")
        self.scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Weights: {self.scores}")

    def call_bundler_script(self, command, payload):
        """Calls the bundler.js script to verify a bundle."""
        try:
            input_data = json.dumps({"command": command, **payload})
            process = subprocess.run(
                ['node', self.js_path],
                input=input_data,
                capture_output=True,
                text=True,
                check=True
            )
            response = json.loads(process.stdout)
            return response
        except Exception as e:
            bt.logging.error(f"Error verifying with bundler.js: {e}")
            return None

    def verify_bundle_and_score(self, axon, synapse_to_verify: Bundle):
        """Verifies the miner's response and returns a score."""
        miner_hotkey = axon.hotkey
        
        # 1. Check for a valid response
        if not synapse_to_verify.bundle_data or not synapse_to_verify.merkle_root or not synapse_to_verify.signature:
            bt.logging.warning(f"Miner {miner_hotkey} returned an incomplete response.")
            return 0.0

        # 2. Verify the miner's hotkey signature on the Merkle root
        keypair = bt.Keypair(ss58_address=miner_hotkey)
        is_signature_valid = keypair.verify(synapse_to_verify.merkle_root.encode('utf-8'), bytes.fromhex(synapse_to_verify.signature))
        if not is_signature_valid:
            bt.logging.warning(f"Signature verification failed for miner {miner_hotkey}.")
            return 0.0
        bt.logging.trace(f"Signature from {miner_hotkey} is valid.")

        # 3. Verify the Merkle root itself by re-bundling locally
        # We call the same script the miner used, but to create a bundle locally for verification
        local_verification = self.call_bundler_script("bundle", {"data_items": synapse_to_verify.data_items})
        
        if not local_verification or not local_verification.get("success"):
            bt.logging.error("Local bundle creation for verification failed.")
            return 0.0

        local_merkle_root = local_verification.get("merkle_root")
        if local_merkle_root != synapse_to_verify.merkle_root:
            bt.logging.warning(f"Merkle root mismatch for miner {miner_hotkey}. Expected {local_merkle_root[:30]}..., got {synapse_to_verify.merkle_root[:30]}...")
            return 0.0

        bt.logging.info(f"Successfully verified bundle from miner {miner_hotkey}.")
        # Here, you could post the bundle to Arweave and check the response
        # For this template, we'll assume successful verification means reward.
        return 1.0

    def run(self):
        bt.logging.info("Starting validator loop.")
        step = 0
        while True:
            try:
                # Get a random set of active miners
                miner_uids = self.metagraph.get_active_uids().tolist()
                if not miner_uids:
                    bt.logging.info("No active miners to query.")
                    time.sleep(20)
                    continue

                # Create a sample query
                data_to_bundle = [
                    f"item_{random.randint(1000, 9999)}",
                    f"item_{random.randint(1000, 9999)}",
                    f"timestamp_{time.time()}"
                ]
                synapse = Bundle(data_items=data_to_bundle)

                # Broadcast the query
                axons_to_query = [self.metagraph.axons[uid] for uid in miner_uids]
                responses = self.dendrite.query(
                    axons=axons_to_query,
                    synapse=synapse,
                    timeout=15  # 15 seconds timeout
                )

                # Score the responses
                for i, resp in enumerate(responses):
                    uid = miner_uids[i]
                    score = self.verify_bundle_and_score(axons_to_query[i], resp)
                    self.scores[uid] = score
                
                bt.logging.info(f"Scores for step {step}: {self.scores}")

                # Set weights every 20 steps
                if step % 20 == 0:
                    if torch.sum(self.scores) > 0:
                        weights = self.scores / torch.sum(self.scores)
                        bt.logging.info(f"Setting weights: {weights}")
                        
                        self.subtensor.set_weights(
                            netuid=self.config.netuid,
                            wallet=self.wallet,
                            uids=self.metagraph.uids,
                            weights=weights,
                            wait_for_inclusion=False
                        )
                    else:
                        bt.logging.info("No valid scores to set weights.")
                
                # Sync metagraph and sleep
                self.metagraph.sync(subtensor=self.subtensor)
                step += 1
                time.sleep(30) # Wait for 30 seconds before next query round

            except RuntimeError as e:
                bt.logging.error(e)
                traceback.print_exc()

            except KeyboardInterrupt:
                bt.logging.success("Keyboard interrupt detected. Exiting validator.")
                exit()

if __name__ == "__main__":
    validator = Validator()
    validator.run()
