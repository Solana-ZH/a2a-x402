# Solana Payments for A2A x402

Complete guide to running Solana SPL token payments in the A2A x402 protocol demo.

## Overview

This implementation adds Solana support to the x402 payment protocol, enabling agents to pay for services using SPL tokens (like USDC) on Solana.

### Key Features

- ✅ **SPL Token Payments**: Pay with USDC or any SPL token
- ✅ **Client Pays Fees**: In this implementation, the client pays both the token transfer and transaction fees
- ✅ **Fully-Signed Transactions**: Client signs the complete transaction (no partial signing needed)
- ✅ **Mock Mode**: Test without blockchain for development
- ✅ **Devnet Ready**: Real transactions on Solana devnet

## Quick Start (Mock Mode)

Test the flow without needing any blockchain setup:

### 1. Install Dependencies

```bash
cd /Users/jonasmac2/Documents/GitHub/a2a-x402/python/examples/adk-demo
uv sync
```

### 2. Set Mock Mode

```bash
export GOOGLE_API_KEY="your-api-key-here"
export USE_MOCK_FACILITATOR=true
```

### 3. Run the Demo

Terminal 1 (Server):

```bash
uv run server
```

Terminal 2 (Client Web UI):

```bash
uv --directory=python/examples/adk-demo run adk web --port=8000
```

### 4. Test It

1. Open `http://localhost:8000`
2. Say: "I want to buy a banana"
3. Approve the payment when prompted
4. See the mock transaction complete!

---

## Real Devnet Transactions

To send actual transactions on Solana devnet:

### 1. Generate Keys

```bash
cd /Users/jonasmac2/Documents/GitHub/a2a-x402/python/examples/adk-demo
uv run python setup_solana_keys.py
```

This generates:

- **Client keypair** (makes payments, pays transaction fees)
- **Merchant pubkey** (receives USDC)
- **Facilitator keypair** (Sends the transaction to the RPC)

The script outputs `.env` content - copy it for the next step.

### 2. Create `.env` File

Create a `.env` file in `python/examples/adk-demo/`:

```bash
# Google API Key (required for Gemini)
GOOGLE_API_KEY=your-api-key-here

# Solana Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
USE_MOCK_FACILITATOR=false

# Keys from setup_solana_keys.py
CLIENT_SOLANA_PRIVATE_KEY=[85,48,206,71,...]
MERCHANT_SOLANA_PUBKEY=BzTes76rrZTfZnVVn7kPaqsAB8uaw3My4LB4UZmMFMiB
FACILITATOR_SOLANA_PRIVATE_KEY=[174,47,154,16,...]
```

> 💡 **Tip**: Use a paid RPC endpoint (like QuickNode or Helius) to avoid rate limits.

### 3. Fund the Wallets

Client needs SOL for transaction fees:

```bash
# Get the public keys from the setup script output
# Fund client (needs SOL for transaction fees + rent)
solana airdrop 2 <CLIENT_PUBKEY> --url devnet
```

Or use the web faucet: https://faucet.solana.com

### 4. Create USDC Token Accounts

Both client and merchant need Associated Token Accounts (ATAs) for USDC:

```bash
# USDC devnet mint address
USDC_MINT=4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU

# Create merchant's USDC account
spl-token create-account $USDC_MINT --owner <MERCHANT_PUBKEY> --url devnet

# Create client's USDC account
spl-token create-account $USDC_MINT --owner <CLIENT_PUBKEY> --url devnet
```

### 5. Fund Client with USDC

The client needs USDC to make payments:

```bash
# Use Circle's devnet USDC faucet
# Visit: https://faucet.circle.com/

# Or transfer from another funded wallet
spl-token transfer $USDC_MINT 10 <CLIENT_USDC_TOKEN_ACCOUNT> --url devnet --fund-recipient
```

### 6. Start the Demo

Terminal 1 (Server):

```bash
uv run server
```

Terminal 2 (Client):

```bash
uv --directory=python/examples/adk-demo run adk web --port=8000
```

### 7. Make a Payment

1. Open `http://localhost:8000`
2. Say: "I want to buy a banana"
3. Approve the payment (costs 0.005 USDC)
4. See the success message with transaction link! 🎉

Example output:

```
Great! Your order for a banana has been successfully placed and is now being prepared.

🎉 Paid with Solana USDC! 🍌
🔗 Transaction: 5NqW8...mock
🌐 View on Explorer: https://explorer.solana.com/tx/5NqW8...?cluster=devnet
```

---

## How It Works

### Payment Flow

```
Client                  Merchant                Facilitator         Solana Network
  |                        |                         |                    |
  |--Request Service------>|                         |                    |
  |                        |                         |                    |
  |<-Payment Required------|                         |                    |
  |  (Solana requirements) |                         |                    |
  |                        |                         |                    |
  | Create & Sign TX       |                         |                    |
  |                        |                         |                    |
  |--Payment Submitted---->|                         |                    |
  |                        |                         |                    |
  |                        |---Verify Payment------->|                    |
  |                        |<--Valid/Invalid---------|                    |
  |                        |                         |                    |
  |                        |---Settle Payment------->|                    |
  |                        |                         |--Submit TX-------->|
  |                        |                         |<--Signature--------|
  |                        |<--Settlement Result-----|                    |
  |                        |                         |                    |
  |<-Service Delivered-----|                         |                    |
```

### Key Concepts

**Fully-Signed Transactions**:

- Client signs the complete transaction including the SPL token transfer
- Client is both the transfer authority and fee payer
- Simple, straightforward model with no partial signing complexity

**Associated Token Accounts (ATAs)**:

- SPL tokens are held in ATAs derived from `owner + mint`
- Both client and merchant need ATAs for the token being transferred
- Must be created before first transaction

**Fee Payment**:

- Client pays SOL transaction fees (~0.00025 SOL per transaction)
- Client needs both SPL tokens (e.g., USDC) for payment and SOL for fees
- Simple implementation without facilitator fee payment complexity

---

## Configuration

### Environment Variables

| Variable                         | Required | Description                                    |
| -------------------------------- | -------- | ---------------------------------------------- |
| `GOOGLE_API_KEY`                 | Yes      | Google Gemini API key for the agent            |
| `USE_MOCK_FACILITATOR`           | No       | `true` for mock, `false` for real transactions |
| `SOLANA_RPC_URL`                 | No\*     | Solana RPC endpoint (default: devnet)          |
| `CLIENT_SOLANA_PRIVATE_KEY`      | No\*     | Client's private key as JSON array             |
| `MERCHANT_SOLANA_PUBKEY`         | No\*     | Merchant's public key (default provided)       |
| `FACILITATOR_SOLANA_PRIVATE_KEY` | No\*     | Facilitator's private key as JSON array        |

\* Required when `USE_MOCK_FACILITATOR=false`

### Key Formats

Private keys support two formats:

**JSON Array (Recommended)**:

```bash
CLIENT_SOLANA_PRIVATE_KEY=[253,57,238,31,24,117,...]
```

**Base58**:

```bash
CLIENT_SOLANA_PRIVATE_KEY=3Zu8vD7q2xqFJ8Y...
```

---

## Architecture

### Files Created

#### Core Types (`python/x402_a2a/types/`)

- **`solana.py`**: Solana-specific payment types
  - `SolanaSupportedNetworks`: Network definitions
  - `SolanaPaymentPayload`: Contains partially-signed transaction
  - `SolanaPaymentRequirementsExtra`: Fee payer configuration

#### Core Logic (`python/x402_a2a/core/`)

- **`solana_wallet.py`**: Client-side payment signing
  - Creates SPL token transfer instructions
  - Signs transactions with client's private key
- **`solana_facilitator.py`**: Server-side verification and settlement

  - Validates transaction structure
  - Broadcasts fully-signed transactions to network

- **`solana_merchant.py`**: Payment requirements helpers
  - Creates Solana-compatible payment requirements
  - Handles camelCase/snake_case conversion

#### Demo Integration (`python/examples/adk-demo/`)

- **`client_agent/solana_wallet.py`**: Demo wallet implementation
- **`client_agent/multi_chain_wallet.py`**: Supports both EVM and Solana
- **`server/agents/solana_facilitator.py`**: Real + mock facilitators
- **`server/agents/multi_chain_executor.py`**: Routes to correct facilitator
- **`server/agents/adk_merchant_agent.py`**: Updated to support Solana payments

### Dependencies Added

```toml
solana>=0.36.0   # Solana RPC and blockchain interactions
solders>=0.21.0  # Solana types (Keypair, Transaction, etc.)
base58>=2.1.1    # Key format support
```

---

## Troubleshooting

### "insufficient funds"

- **Client**: Needs USDC to make payments AND SOL for transaction fees
  - Solution for USDC: Fund via Circle's faucet or transfer USDC
  - Solution for SOL: `solana airdrop 2 <CLIENT_PUBKEY> --url devnet`

### "Account does not exist" / "InvalidAccountData"

- Token accounts (ATAs) don't exist yet
- Solution: Create ATAs for both client and merchant:
  ```bash
  spl-token create-account 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU --owner <PUBKEY> --url devnet
  ```

### "Blockhash not found"

- Transaction blockhash expired (max ~60 seconds on Solana)
- Usually happens with public RPC rate limits
- Solution: Use a paid RPC endpoint (QuickNode, Helius, etc.)

### No transaction link in output

- Make sure you restarted the client after code changes
- Check that `.env` file is loaded correctly

---

## Testing

### Mock Mode vs Real Mode

| Mode | USE_MOCK_FACILITATOR | Behavior                              |
| ---- | -------------------- | ------------------------------------- |
| Mock | `true`               | Simulates transactions, no blockchain |
| Real | `false`              | Sends actual transactions to devnet   |

Mock mode is perfect for:

- ✅ Development and testing
- ✅ No blockchain setup needed
- ✅ Instant responses
- ✅ No transaction costs

Real mode for:

- ✅ End-to-end testing
- ✅ Transaction verification
- ✅ Integration testing
- ✅ Production readiness

---

## Example: Adding Solana to Your Merchant

```python
from x402_a2a import x402PaymentRequiredException
import os

def get_product_details(product_name: str) -> dict:
    """Merchant tool that requires Solana payment."""

    price = "5000"  # 0.005 USDC (6 decimals)
    merchant_address = os.getenv("MERCHANT_SOLANA_PUBKEY", "default-pubkey")

    # Raise payment exception with Solana requirements
    # Note: Client will pay their own transaction fees (needs SOL)
    raise x402PaymentRequiredException.for_solana_service(
        price=price,
        pay_to_address=merchant_address,
        asset_address="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # USDC devnet
        resource=f"/product/{product_name}",
        fee_payer_address=merchant_address,  # Not used in client-pays-fees model
        network="solana-devnet",
        description=f"Payment for: {product_name}",
        decimals=6,
    )
```

---

## Resources

- [Solana Documentation](https://docs.solana.com)
- [SPL Token Program](https://spl.solana.com/token)
- [solana-py Library](https://michaelhly.com/solana-py/)
- [x402 Specification](https://github.com/coinbase/x402)
- [A2A Protocol](https://www.a2a-protocol.org/)
- [Solana Devnet Faucet](https://faucet.solana.com)
- [Circle USDC Faucet](https://faucet.circle.com/)

---

## Next Steps

- [ ] Test in mock mode first
- [ ] Generate and fund real devnet keys
- [ ] Make your first devnet transaction
- [ ] Experiment with different token amounts
- [ ] Try multi-product purchases
- [ ] Contribute improvements upstream to `coinbase/x402`

---

## License

Apache-2.0 (same as parent repository)
