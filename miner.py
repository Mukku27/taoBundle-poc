import os
import time
import argparse
import traceback
import bittensor as bt
import subprocess
import json
import base64

from protocol import Bundle

class Miner:
    def __init__(self):
        self.config = self.get_config()
        self.setup_logging()
        self.setup_bittensor_objects()
        self.js_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "js/bundler.js")


    def get_config(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        bt.wallet.add_args(parser)
        bt.axon.add_args(parser)
        config = bt.config(parser)
        config.full_path = os.path.expanduser(
            "{}/{}/{}/netuid{}/{}".format(
                config.logging.logging_dir,
                config.wallet.name,
                config.wallet.hotkey.ss58_address,
                config.netuid,
                "miner",
            )
        )
        os.makedirs(config.full_path, exist_ok=True)
        return config

    def setup_logging(self):
        bt.logging(config=self.config, logging_dir=self.config.full_path)
        bt.logging.info(
            f"Running miner for subnet: {self.config.netuid} on network: {self.config.subtensor.network} with config:"
        )
        bt.logging.info(self.config)

    def setup_bittensor_objects(self):
        bt.logging.info("Setting up Bittensor objects.")
        self.wallet = bt.wallet(config=self.config)
        bt.logging.info(f"Wallet: {self.wallet}")
        self.subtensor = bt.subtensor(config=self.config)
        bt.logging.info(f"Subtensor: {self.subtensor}")
        self.metagraph = self.subtensor.metagraph(self.config.netuid)
        bt.logging.info(f"Metagraph: {self.metagraph}")

        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
            bt.logging.error(
                f"\nYour miner: {self.wallet} is not registered to chain connection: {self.subtensor} \nRun 'btcli s register --netuid {self.config.netuid}' and try again."
            )
            exit()
        
        self.my_subnet_uid = self.metagraph.hotkeys.index(self.wallet.hotkey.ss58_address)
        bt.logging.info(f"Running miner on uid: {self.my_subnet_uid}")

    def call_bundler_script(self, command, payload):
        """Calls the bundler.js script with the given command and payload."""
        try:
            # Prepare the JSON input for the Node.js script
            input_data = json.dumps({"command": command, **payload})
            
            # Execute the Node.js script as a subprocess
            process = subprocess.run(
                ['node', self.js_path],
                input=input_data,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON output from the script
            response = json.loads(process.stdout)
            if response.get("success"):
                return response
            else:
                bt.logging.error(f"Bundler script error: {response.get('error', 'Unknown error')}")
                return None
        except subprocess.CalledProcessError as e:
            bt.logging.error(f"Error executing bundler.js: {e.stderr}")
            return None
        except json.JSONDecodeError:
            bt.logging.error("Failed to parse JSON response from bundler.js")
            return None
        except Exception as e:
            bt.logging.error(f"An unexpected error occurred: {e}")
            return None

    def forward(self, synapse: Bundle) -> Bundle:
        bt.logging.info(f"Received bundling request for {len(synapse.data_items)} items.")

        # Call the JS script to create the bundle
        bundle_response = self.call_bundler_script("bundle", {"data_items": synapse.data_items})

        if bundle_response:
            synapse.bundle_data = bundle_response.get("bundle_data_b64")
            synapse.bundle_id = bundle_response.get("bundle_id")
            synapse.merkle_root = bundle_response.get("merkle_root")

            # Sign the Merkle root as proof of work
            if synapse.merkle_root:
                signature = self.wallet.hotkey.sign(synapse.merkle_root.encode('utf-8')).hex()
                synapse.signature = signature
                bt.logging.info(f"Successfully bundled {len(synapse.data_items)} items. Merkle root: {synapse.merkle_root[:30]}...")
            else:
                bt.logging.error("Bundler script did not return a merkle_root.")
        else:
            bt.logging.error("Failed to create bundle.")

        return synapse

    def blacklist_fn(self, synapse: Bundle) -> typing.Tuple[bool, str]:
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.trace(f"Blacklisting unrecognized hotkey {synapse.dendrite.hotkey}")
            return True, "Unrecognized hotkey"
        
        bt.logging.trace(f"Not blacklisting recognized hotkey {synapse.dendrite.hotkey}")
        return False, "Hotkey recognized"

    def setup_axon(self):
        self.axon = bt.axon(wallet=self.wallet, config=self.config)
        bt.logging.info("Attaching forward function to axon.")
        self.axon.attach(
            forward_fn=self.forward,
            blacklist_fn=self.blacklist_fn,
        )
        bt.logging.info(f"Serving axon on network: {self.config.subtensor.network} with netuid: {self.config.netuid}")
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)
        bt.logging.info(f"Axon: {self.axon}")
        bt.logging.info(f"Starting axon server on port: {self.config.axon.port}")
        self.axon.start()

    def run(self):
        self.setup_axon()
        bt.logging.info("Starting main loop")
        step = 0
        while True:
            try:
                if step % 5 == 0:
                    self.metagraph.sync(subtensor=self.subtensor)
                    bt.logging.info(f"Synced metagraph: {self.metagraph}")
                step += 1
                time.sleep(1)
            except KeyboardInterrupt:
                self.axon.stop()
                bt.logging.success("Miner killed by keyboard interrupt.")
                break
            except Exception as e:
                bt.logging.error(traceback.format_exc())
                continue

if __name__ == "__main__":
    miner = Miner()
    miner.run()
