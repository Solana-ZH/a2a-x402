# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Solana wallet implementation for the demo client agent."""

import os
import json
from solders.keypair import Keypair

from x402_a2a.types import PaymentPayload, x402PaymentRequiredResponse
from x402_a2a.core.solana_wallet import process_solana_payment_required
from .wallet import Wallet


class SolanaWallet(Wallet):
    """
    Solana wallet that signs payment requirements using a Solana keypair.
    """

    def __init__(self, keypair: Keypair):
        """
        Initialize the Solana wallet.

        Args:
            keypair: Solana keypair for signing transactions
        """
        self.keypair = keypair

    def sign_payment(self, requirements: x402PaymentRequiredResponse) -> PaymentPayload:
        """
        Signs a Solana payment requirement and returns the signed payload.

        Args:
            requirements: Payment requirements from the merchant

        Returns:
            PaymentPayload with partially-signed Solana transaction
        """
        print(f"🔑 CLIENT: Signing new Solana payment transaction...")
        print(f"🔑 CLIENT: Payer public key: {self.keypair.pubkey()}")
        result = process_solana_payment_required(requirements, self.keypair)
        print(f"🔑 CLIENT: Transaction signed successfully!")
        return result

    @classmethod
    def from_private_key(cls, private_key: bytes) -> "SolanaWallet":
        """
        Create a wallet from a private key.

        Args:
            private_key: 32-byte Solana private key

        Returns:
            SolanaWallet instance
        """
        keypair = Keypair.from_bytes(private_key)
        return cls(keypair)

    @classmethod
    def from_seed_phrase(cls, seed_phrase: str) -> "SolanaWallet":
        """
        Create a wallet from a seed phrase.

        Args:
            seed_phrase: BIP39 seed phrase

        Returns:
            SolanaWallet instance
        """
        # For demo purposes, use a simple derivation
        # In production, use proper BIP39/BIP44 derivation
        from solders.keypair import Keypair
        import hashlib

        seed = hashlib.sha256(seed_phrase.encode()).digest()
        keypair = Keypair.from_seed(seed[:32])
        return cls(keypair)

    @classmethod
    def generate(cls) -> "SolanaWallet":
        """
        Generate a new random wallet or load from environment.
        
        Checks CLIENT_SOLANA_PRIVATE_KEY environment variable first.
        If not set, generates a new random keypair.

        Returns:
            SolanaWallet with keypair from env or newly generated
        """
        # Try to load from environment variable
        env_key = os.getenv("CLIENT_SOLANA_PRIVATE_KEY")
        if env_key:
            try:
                # Support both JSON array and base58 formats
                if env_key.startswith("["):
                    # JSON array format: [123, 45, 67, ...]
                    key_bytes = bytes(json.loads(env_key))
                else:
                    # Base58 format
                    import base58
                    key_bytes = base58.b58decode(env_key)
                
                keypair = Keypair.from_bytes(key_bytes)
                print(f"✅ Loaded client wallet from env: {keypair.pubkey()}")
                return cls(keypair)
            except Exception as e:
                print(f"❌ Failed to load client key from env: {e}")
                print("⚠️  Generating random keypair instead")
        
        # Generate a new random keypair
        keypair = Keypair()
        print(f"🔧 Generated random client wallet: {keypair.pubkey()}")
        print(f"⚠️  To reuse this wallet, set CLIENT_SOLANA_PRIVATE_KEY={list(bytes(keypair))}")
        print(f"⚠️  Fund this wallet with USDC to make payments")
        return cls(keypair)

    @property
    def public_key(self) -> str:
        """Get the base58-encoded public key."""
        return str(self.keypair.pubkey())

