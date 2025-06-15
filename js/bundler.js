const { createData, ArweaveSigner } = require("arbundles");
const Arweave = require("arweave");

/** @type {*} */
const arweave = Arweave.init({
  host: "127.0.0.1", // "arweave.net" for production, 127.0.0.1 for local dev
  port: 1984, // 443 for production, 1984 for local dev
  protocol: "http", // "https" for production, "http" for local dev
  logging: false, // set to true for debugging
});

// This function reads all data from stdin.
async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf-8"); // ensure input is string, not Buffer

    process.stdin.on("data", (chunk) => {
      data += chunk;
    });

    process.stdin.on("end", () => {
      try {
        const parsed = JSON.parse(data);
        resolve(parsed);
      } catch (error) {
        reject(new Error("Invalid JSON input"));
      }
    });

    process.stdin.on("error", (err) => {
      reject(err);
    });
  });
}

// Function to create a bundle from a list of data items.
async function createBundle(dataItems) {
  if (!Array.isArray(dataItems)) {
    throw new Error("data_items must be an array of strings.");
  }

  const jwk = await arweave.wallets.generate(); // auto generates the wallet if needed replace with your actual JWK

  const signer = new ArweaveSigner(jwk);
  const createdDataItems = createData(dataItems, signer, {});
  await createdDataItems.sign(signer);

  const endpoint = "https://turbo.ardrive.io/tx";
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: createdDataItems.getRaw(),
  });
  if (!res.ok) {
    throw new Error(`Failed to upload bundle: ${res.statusText}`);
  }
  const tx = await arweave.createTransaction({ data: createdDataItems.id });
  await arweave.transactions.sign(tx, jwk);

  return {
    bundle_data_b64: createdDataItems.getRaw().toString("base64"),
    bundle_id: createdDataItems.id, // Just an example ID
    merkle_root: tx.data_root,
  };
}

// Main function to process commands.
async function main() {
  try {
    const input = await readStdin();
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
