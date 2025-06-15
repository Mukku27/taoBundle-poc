const { createData, bundleAndSignData, ArweaveSigner } = require("@ar.io/arbundles");
const Arweave = require("arweave");

// A simple in-memory JWK for demonstration.
// In a real application, this should be managed securely.
const jwk = {
    "kty":"RSA",
    "n":"p_3w_5YgJz-tI_3Z9s6-1I_5g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q",
    "e":"AQAB",
    "d":"p_3w_5YgJz-tI_3Z9s6-1I_5g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q",
    "p":"p_3w_5YgJz-tI_3Z9s6-1I_5g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q-I_9g_7I-2P-g-Q"
};
const signer = new ArweaveSigner(jwk);

const arweave = Arweave.init({});

// This function reads all data from stdin.
async function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => {
      resolve(data);
    });
  });
}

// Function to create a bundle from a list of data items.
async function createBundle(dataItems) {
  if (!Array.isArray(dataItems)) {
    throw new Error("data_items must be an array of strings.");
  }
  const items = dataItems.map((item) => createData(item, signer, {}));
  const bundle = await bundleAndSignData(items, signer);
  const bundleBuffer = Buffer.from(bundle.getRaw());
  
  // To get the Merkle root, we need to create a transaction.
  const tx = await arweave.createTransaction({ data: bundleBuffer });
  tx.addTag("Bundle-Format", "binary");
  tx.addTag("Bundle-Version", "2.0.0");
  await arweave.transactions.sign(tx, jwk);

  return {
    bundle_data_b64: bundleBuffer.toString("base64"),
    bundle_id: bundle.getIds()[0], // Just an example ID
    merkle_root: tx.data_root,
  };
}

// Main function to process commands.
async function main() {
  try {
    const rawInput = await readStdin();
    const input = JSON.parse(rawInput);

    let result;
    switch (input.command) {
      case "bundle":
        result = await createBundle(input.data_items);
        break;
      default:
        throw new Error(`Unknown command: ${input.command}`);
    }

    // Output result as JSON to stdout
    process.stdout.write(JSON.stringify({ success: true, ...result }));
  } catch (e) {
    // Output error as JSON to stdout
    process.stdout.write(JSON.stringify({ success: false, error: e.message }));
  }
}

main();
