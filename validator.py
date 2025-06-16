import os
import time
import random
import argparse
import traceback
import bittensor as bt
import subprocess
import json
import torch

from protocol import Bundle

class Validator:
    def __init__(self):
        self.config = self.get_config()
        self.setup_logging()
        self.setup_bittensor_objects()
        # Ensure my_uid is determined after metagraph sync
        if self.wallet.hotkey.ss58_address in self.metagraph.hotkeys:
            self.my_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        else:
            bt.logging.error("Validator hotkey not found in metagraph. Exiting.")
            exit()
            
        self.scores = torch.zeros_like(self.metagraph.S, dtype=torch.float32) # S is already a tensor
        self.js_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "js/bundler.js")


    def get_config(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")
        
        parser.add_argument("--wallet.path", type=str, default=os.path.expanduser("~/.bittensor/wallets/"), help="Path to bittensor wallets")
        parser.add_argument("--wallet.name", type=str, default="default", help="Name of the wallet")
        parser.add_argument("--wallet.hotkey", type=str, default="default", help="Name of the hotkey")

        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        

        config = bt.config(parser)
        config.full_path = os.path.expanduser(
            "{}/{}/{}/netuid{}/validator".format(
                config.logging.logging_dir,
                config.wallet.name,
                config.wallet.hotkey, # Using hotkey name string as per logs
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
            bt.logging.error(f"Your validator: {self.wallet} is not registered to chain connection: {self.subtensor}. Please register your hotkey using 'btcli s register --netuid {self.config.netuid}'.")
            exit()
            
        # self.my_subnet_uid is set in __init__ after metagraph is available.
        bt.logging.info(f"Running validator on uid: {self.my_uid}")
        
        bt.logging.info("Building validation weights.")
        # self.scores initialized in __init__
        bt.logging.info(f"Initial Weights: {self.scores}")

    def call_bundler_script(self, command, payload):
        """Calls the bundler.js script to create/verify a bundle."""
        try:
            input_data = json.dumps({"command": command, **payload})
            process = subprocess.run(
                ['node', self.js_path],
                input=input_data,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), "js") # Ensure node runs in the js dir
            )
            response = json.loads(process.stdout)
            return response
        except subprocess.CalledProcessError as e:
            bt.logging.error(f"Error executing bundler.js (CalledProcessError): {e.stderr}")
            bt.logging.error(f"stdout: {e.stdout}") # Log stdout too for more context
            return None
        except json.JSONDecodeError as e:
            # It's useful to see the output that failed to parse
            raw_output = "N/A"
            if 'process' in locals() and hasattr(process, 'stdout'):
                raw_output = process.stdout
            bt.logging.error(f"Failed to parse JSON response from bundler.js. Raw output: '{raw_output}'. Error: {e}")
            return None
        except Exception as e:
            bt.logging.error(f"An unexpected error occurred while calling bundler.js: {e}")
            return None


    def verify_bundle_and_score(self, axon_info: bt.AxonInfo, response_synapse: Bundle, original_data_items: list):
        """Verifies the miner's response and returns a score."""
        miner_hotkey = axon_info.hotkey
        
        # Step 0: Check if we got a valid synapse response object
        if not response_synapse:
            bt.logging.warning(f"No response synapse from miner {miner_hotkey} (UID corresponding to axon_info).")
            return 0.0

        # Step 1: Check for a complete response from the miner
        if not response_synapse.bundle_data or \
           not response_synapse.merkle_root or \
           not response_synapse.signature:
            bt.logging.warning(f"Miner {miner_hotkey} returned an incomplete response: "
                               f"bundle_data: {'present' if response_synapse.bundle_data else 'missing'}, "
                               f"merkle_root: {'present' if response_synapse.merkle_root else 'missing'}, "
                               f"signature: {'present' if response_synapse.signature else 'missing'}")
            return 0.0

        # Step 2: Verify the miner's hotkey signature on the Merkle root
        # The signature is on the merkle_root string itself.
        try:
            keypair = bt.Keypair(ss58_address=miner_hotkey) # Create keypair from miner's hotkey
            is_signature_valid = keypair.verify(
                response_synapse.merkle_root.encode('utf-8'), 
                bytes.fromhex(response_synapse.signature)
            )
            if not is_signature_valid:
                bt.logging.warning(f"Signature verification failed for miner {miner_hotkey}.")
                return 0.0
            bt.logging.trace(f"Signature from miner {miner_hotkey} is valid for Merkle root {response_synapse.merkle_root[:30]}...")
        except Exception as e:
            bt.logging.error(f"Error during signature verification for miner {miner_hotkey}: {e}")
            return 0.0

        # Step 3: Locally recompute the Merkle root from the *original* data_items
        # The validator uses the data_items it initially sent to the miner.
        bt.logging.trace(f"Recomputing Merkle root locally for data_items: {original_data_items}")
        local_computation_result = self.call_bundler_script("bundle", {"data_items": original_data_items})
        
        if not local_computation_result or not local_computation_result.get("success"):
            bt.logging.error(f"Local Merkle root computation failed for data from miner {miner_hotkey}. JS script error: {local_computation_result.get('error') if local_computation_result else 'Unknown JS error'}")
            return 0.0

        local_merkle_root = local_computation_result.get("merkle_root")
        if not local_merkle_root:
            bt.logging.error(f"Local Merkle root computation did not return a merkle_root for data from miner {miner_hotkey}.")
            return 0.0
        
        # Step 4: Compare the received Merkle root with the recomputed one
        if local_merkle_root != response_synapse.merkle_root:
            bt.logging.warning(f"Merkle root mismatch for miner {miner_hotkey}. "
                               f"Expected (local): {local_merkle_root[:30]}..., "
                               f"Got (miner): {response_synapse.merkle_root[:30]}...")
            return 0.0

        bt.logging.info(f"Successfully verified bundle and signature from miner {miner_hotkey}.")
        # If all checks pass, the bundle is accepted.
        # For this  successful verification means a score of 1.0.
        # In a real scenario, you might post to Arweave here and verify the transaction ID.
        return 1.0

    def run(self):
        bt.logging.info("Starting validator loop.")
        step = 0
        while True:
            try:
                # Sync metagraph before fetching UIDs
                self.metagraph.sync(subtensor=self.subtensor)
                
                
                miner_uids = [uid.item() for uid in self.metagraph.uids if uid.item() != self.my_uid and self.metagraph.active[uid.item()]]

                if not miner_uids:
                    bt.logging.info("No active miners (excluding self) to query. Waiting...")
                    time.sleep(20) 
                    continue

                
                query_uids = miner_uids 
                
                if not query_uids:
                    bt.logging.info("No UIDs selected for querying. Waiting...")
                    time.sleep(20)
                    continue

               
                current_time = time.time()
                data_to_bundle = [
                    f"data_item_1_validator_{self.my_uid}_time_{current_time}",
                    f"another_piece_of_data_from_validator_uid_{self.my_uid}",
                    f"random_content_{random.randint(10000, 99999)}"
                ]
                
                query_synapse = Bundle(data_items=data_to_bundle)

               
                axons_to_query = [self.metagraph.axons[uid] for uid in query_uids]
                bt.logging.info(f"Querying {len(axons_to_query)} miners with {len(data_to_bundle)} data items.")
                
                responses = self.dendrite.query(
                    axons=axons_to_query,
                    synapse=query_synapse, 
                    timeout=20  
                )

                
                for i, response_synapse in enumerate(responses):
                    uid = query_uids[i] 
                    

                    if response_synapse is None:
                        bt.logging.warning(f"No response received from UID {uid}.")
                        self.scores[uid] = 0.0 # Penalize for no response
                        continue

                    # Verify the bundle and signature from the responding miner
                    # Pass the original data_items for local re-computation
                    score = self.verify_bundle_and_score(axons_to_query[i], response_synapse, data_to_bundle)
                    self.scores[uid] = score # Update score for this UID
                
                bt.logging.info(f"Scores for step {step}: {self.scores.tolist()}")

                # Set weights every 20 steps (adjust as needed)
                if step > 0 and step % 1 == 0: 
                    if torch.sum(self.scores) > 0:
                        # Normalize scores to get weights
                        weights = self.scores / torch.sum(self.scores)
                        bt.logging.info(f"Setting weights: {weights.tolist()}")
                        
                        # API call to set weights
                        self.subtensor.set_weights(
                            netuid=self.config.netuid,
                            wallet=self.wallet,
                            uids=self.metagraph.uids, 
                            weights=weights,         
                            wait_for_inclusion=False,
                            wait_for_finalization=False 
                        )
                    else:
                        bt.logging.info("No valid scores to set weights (all scores are zero).")
                
                # Sync metagraph regularly
                if step % 5 == 0: 
                    self.metagraph.sync(subtensor=self.subtensor)
                    bt.logging.info("Synced metagraph.")

                step += 1
                time.sleep(random.uniform(25, 35)) 

            except RuntimeError as e:
                bt.logging.error(f"RuntimeError in validator loop: {e}")
                traceback.print_exc()
                time.sleep(30)

            except Exception as e:
                bt.logging.error(f"General Exception in validator loop: {e}")
                traceback.print_exc()
                time.sleep(30)

            except KeyboardInterrupt:
                bt.logging.success("Keyboard interrupt detected. Exiting validator.")
                exit()

if __name__ == "__main__":
    validator = Validator()
    validator.run()