# TaoBundle Subnet - Bittensor Proof of Concept (PoC)

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js Version](https://img.shields.io/badge/Node.js-22.18.0-green.svg)](https://nodejs.org/en/download/)
[![Bittensor Version](https://img.shields.io/badge/Bittensor-v9.4.0-black.svg)](https://bittensor.com/)
[![Arweave Version](https://img.shields.io/badge/Arweave-v2.9.1-black.svg)](https://www.arweave.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🔹 Overview

This repository implements a **TaoBundle Subnet** on the Bittensor network as a **Proof of Concept (PoC)**.  
It demonstrates a decentralized system where **miners** provide data bundling services for the Arweave network, and **validators** verify this work, scoring miners accordingly.

The primary innovation lies in the **hybrid architecture**, combining:

- **Python** — Bittensor neuron logic  
- **Node.js** — Specialized data bundling tasks via Arweave's `arbundles` library  

This PoC provides a strong foundation for experimenting with **decentralized AI** and **blockchain-based data workflows**.

---

## 📌 Table of Contents
1. [How It Works](#️-how-it-works)
2. [Workflow Diagram](#-workflow-diagram)
3. [Command Flow Chart](#-command-flow-chart)
4. [Repository Structure](#-repository-structure)
5. [Getting Started](#-getting-started)
6. [Running the PoC Locally](#-running-the-poc-locally)
7. [Key Concepts Demonstrated](#-key-concepts-demonstrated)
8. [Disclaimer](#-disclaimer)

---

## ⚙️ How It Works

The TaoBundle subnet implements a **request-response workflow** between validators and miners:

1. **Challenge (Query)**  
   Validator generates random data items and sends them to active miners via a custom **Bundle Synapse**.

2. **Work (Bundling)**  
   Miner receives the request and uses the Node.js `bundler.js` script with the `arbundles` library to create an **Arweave bundle**.

3. **Proof of Work**  
   - Bundler calculates the Arweave transaction **data root (merkle_root)**.  
   - Miner digitally signs the `merkle_root` with its hotkey as verifiable proof of work.

4. **Response**  
   Miner sends back:
   - `bundle_data`  
   - `bundle_id`  
   - `merkle_root`  
   - `signature`  

5. **Verification & Scoring**  
   Validator verifies:
   - ✅ Signature is valid for the Merkle root.  
   - ✅ Merkle root matches recomputed root.  
   - 📊 Miner scored **1.0** if all checks pass, else **0.0**.

6. **Setting Weights**  
   Validator periodically updates blockchain weights based on miners’ scores, incentivizing accurate and efficient work.

---

## 📊 Workflow Diagram

```mermaid
flowchart TD
    A[Validator Generates Challenge] --> B[Send to Miners via Bundle Synapse]
    B --> C[Miner Receives Request]
    C --> D[Node.js bundler.js Creates Arweave Bundle]
    D --> E[Calculate Merkle Root]
    E --> F[Sign Merkle Root with Hotkey]
    F --> G[Send Bundle Data + Proof to Validator]
    G --> H[Validator Verifies Signature & Merkle Root]
    H --> I[Score Miner]
    I --> J[Update Blockchain Weights]
````

---

## 🖥 Command Flow Chart

```mermaid
graph LR
    subgraph Setup
    S1[Install Python 3.8+] --> S2[Install Node.js 22.18.0]
    S2 --> S3[Install Bittensor]
    S3 --> S4[Clone TaoBundle Repo]
    end
    
    subgraph Run
    R1[Start Local Subtensor Chain] --> R2[Create Wallets]
    R2 --> R3[Register Subnet & Neurons]
    R3 --> R4[Start Local Arweave Gateway]
    R4 --> R5[Run Miner Neuron]
    R5 --> R6[Run Validator Neuron]
    end
```

---

## 📂 Repository Structure

```plaintext
mukku27-taobundle-poc/
├── README.md           # This file
├── validator.py        # Validator neuron logic
├── miner.py            # Miner neuron logic
├── protocol.py         # Custom `Bundle` Synapse definitions
├── validator_logs.txt  # Example validator logs
├── miner_logs.txt      # Example miner logs
└── js/
    ├── bundler.js      # Node.js script for Arweave bundling
    └── package.json    # Node.js dependencies
```

---

## 🚀 Getting Started

### **Prerequisites**

* Python 3.8+ and pip
* Node.js v22.18.0 and npm
* Bittensor (`btcli`) installed
* Git, cURL, and build tools (`make`, `clang`, etc.)
* Rust & Cargo

---

### **Initial Setup**

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/mukku27/taobundle-poc.git
cd taobundle-poc
```

#### 2️⃣ Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3️⃣ Install Node.js Dependencies

```bash
cd js
npm install
cd ..
```

---

## 🏃 Running the PoC Locally

### **Phase 1: Set Up the Local Bittensor Blockchain**

Install Substrate & Rust:

```bash
sudo apt update
sudo apt install -y make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

Clone and run `subtensor`:

```bash
git clone https://github.com/opentensor/subtensor.git
cd subtensor
./scripts/init.sh
cargo build -p node-subtensor --release --features pow-faucet
./scripts/localnet.sh
```

Local endpoint: `ws://127.0.0.1:9944` (keep running)

---

### **Phase 2: Configure Your Subnet**

Create wallets:

```bash
btcli wallet new_coldkey --wallet.name owner
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default
```

Fund wallets:

```bash
btcli wallet faucet --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9944
btcli wallet faucet --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9944
```

Create subnet & register neurons:

```bash
btcli subnet create --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9944
btcli subnet register --netuid 1 --wallet.name miner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9944
btcli subnet register --netuid 1 --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9944
```

---

### **Phase 3: Run the TaoBundle Neurons**

Start local Arweave gateway:

```bash
npx arlocal
```

Run Miner:

```bash
source venv/bin/activate
python miner.py \
    --netuid 1 \
    --wallet.name miner \
    --wallet.hotkey default \
    --subtensor.chain_endpoint ws://127.0.0.1:9944 \
    --axon.port 8901 \
    --logging.debug
```

Run Validator:

```bash
source venv/bin/activate
python validator.py \
    --netuid 1 \
    --wallet.name validator \
    --wallet.hotkey default \
    --subtensor.chain_endpoint ws://127.0.0.1:9944 \
    --logging.debug
```

---

## 🧠 Key Concepts Demonstrated

* **Hybrid Neuron Architecture**: Python + Node.js integration
* **Custom Synapse Protocol**: Tailored `bt.Synapse` subclass for bundling
* **Verifiable Proof of Work**: Cryptographic signature of a Merkle root
* **Trustless Verification**: Validator independently computes outcomes

---

## ⚠️ Disclaimer

This project is **educational and demonstrational only** — not production-ready.
Consider enhancements for:

* Robust error handling & security
* More sophisticated scoring & incentives
* Integration with live Arweave network
* Performance & scalability optimizations

---


