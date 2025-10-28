#!/usr/bin/env python3
"""
Quick setup script to generate Solana keypairs for the demo.
This is for testing only - in production, use proper key management.
"""

from solders.keypair import Keypair
import json

def main():
    print("="*60)
    print("Solana Devnet Demo - Key Generation")
    print("="*60)
    print()
    
    # Generate client keypair
    client = Keypair()
    print("👤 CLIENT (makes payments)")
    print(f"   Public Key:  {client.pubkey()}")
    print(f"   Private Key: {list(bytes(client))}")
    print()
    
    # Generate merchant keypair
    merchant = Keypair()
    print("🏪 MERCHANT (receives payments)")
    print(f"   Public Key:  {merchant.pubkey()}")
    print(f"   Private Key: {list(bytes(merchant))}")
    print()
    
    # Generate facilitator keypair  
    facilitator = Keypair()
    print("⚡ FACILITATOR (pays transaction fees)")
    print(f"   Public Key:  {facilitator.pubkey()}")
    print(f"   Private Key: {list(bytes(facilitator))}")
    print()
    
    # Generate .env content
    print("="*60)
    print("Add these to your .env file:")
    print("="*60)
    print()
    print("# Solana Configuration")
    print("SOLANA_RPC_URL=https://api.devnet.solana.com")
    print("USE_MOCK_FACILITATOR=false")
    print()
    print("# Client (makes payments)")
    print(f"CLIENT_SOLANA_PRIVATE_KEY={json.dumps(list(bytes(client)))}")
    print()
    print("# Merchant (receives USDC)")
    print(f"MERCHANT_SOLANA_PUBKEY={merchant.pubkey()}")
    print()
    print("# Facilitator (pays fees)")
    print(f"FACILITATOR_SOLANA_PRIVATE_KEY={json.dumps(list(bytes(facilitator)))}")
    print()
    print("="*60)
    print("NEXT STEPS:")
    print("="*60)
    print()
    print("1. Copy the above to your .env file")
    print()
    print("2. Fund the FACILITATOR with SOL for transaction fees:")
    print(f"   solana airdrop 2 {facilitator.pubkey()} --url devnet")
    print("   Or visit: https://faucet.solana.com")
    print()
    print("3. Fund the CLIENT with SOL (for token account creation):")
    print(f"   solana airdrop 1 {client.pubkey()} --url devnet")
    print()
    print("4. Create USDC token accounts:")
    print(f"   # For merchant")
    print(f"   spl-token create-account 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU --owner {merchant.pubkey()}")
    print()
    print(f"   # For client")
    print(f"   spl-token create-account 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU --owner {client.pubkey()}")
    print()
    print("5. Fund the CLIENT with devnet USDC (You can get that from here: https://faucet.circle.com/)")
    print(f"   Client's USDC account will need tokens to make payments")
    print()
    print("🔗 Devnet USDC Mint: 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
    print()
    print("   Keep these keys safe .")
    print()

if __name__ == "__main__":
    main()

