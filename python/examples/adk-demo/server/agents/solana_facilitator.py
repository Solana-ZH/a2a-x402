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
"""Solana facilitator wrapper for the demo server."""

import os
import json
from typing import Optional
from solders.keypair import Keypair

from x402_a2a.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
    SolanaPaymentPayload,
)
from x402_a2a.core.solana_facilitator import SolanaFacilitator


class DemoSolanaFacilitator:
    """
    Wrapper for SolanaFacilitator that can be used as a drop-in replacement
    for the EVM facilitator in the demo.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        fee_payer_private_key: Optional[bytes] = None,
        network: str = "solana-devnet",
    ):
        """
        Initialize the demo Solana facilitator.

        Args:
            rpc_url: Solana RPC URL (defaults to devnet)
            fee_payer_private_key: Private key for fee payer (generates random if None)
            network: Network identifier
        """
        # Load RPC URL from environment or use default public devnet
        if rpc_url is None:
            rpc_url = os.getenv(
                "SOLANA_RPC_URL",
                "https://api.devnet.solana.com"
            )

        # Load fee payer keypair from environment or generate
        if fee_payer_private_key:
            fee_payer_keypair = Keypair.from_bytes(fee_payer_private_key)
            print(f"✅ Loaded facilitator from provided key: {fee_payer_keypair.pubkey()}")
        else:
            # Try to load from environment variable
            env_key = os.getenv("FACILITATOR_SOLANA_PRIVATE_KEY")
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
                    
                    fee_payer_keypair = Keypair.from_bytes(key_bytes)
                    print(f"✅ Loaded facilitator from env: {fee_payer_keypair.pubkey()}")
                except Exception as e:
                    print(f"❌ Failed to load facilitator key from env: {e}")
                    print("⚠️  Generating random keypair instead")
                    fee_payer_keypair = Keypair()
                    print(f"Generated facilitator fee payer: {fee_payer_keypair.pubkey()}")
            else:
                # Generate a new keypair for testing
                fee_payer_keypair = Keypair()
                print(f"🔧 Generated random facilitator fee payer: {fee_payer_keypair.pubkey()}")
                print("⚠️  For real transactions, set FACILITATOR_SOLANA_PRIVATE_KEY env var")
                print("⚠️  Fund this address with SOL: https://faucet.solana.com")

        self.facilitator = SolanaFacilitator(
            rpc_url=rpc_url,
            fee_payer_keypair=fee_payer_keypair,
            network=network,
        )
        self.fee_payer_pubkey = str(fee_payer_keypair.pubkey())

    async def verify(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify a Solana payment."""
        return await self.facilitator.verify(payment_payload, payment_requirements)

    async def settle(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle a Solana payment."""
        return await self.facilitator.settle(payment_payload, payment_requirements)

    async def close(self):
        """Close facilitator connections."""
        await self.facilitator.close()

    @property
    def fee_payer_address(self) -> str:
        """Get the fee payer's public address."""
        return self.fee_payer_pubkey


class MockSolanaFacilitator:
    """
    Mock Solana facilitator for testing without real blockchain interactions.
    """

    def __init__(self):
        """Initialize mock facilitator."""
        # Generate a mock fee payer for requirements
        mock_keypair = Keypair()
        self.fee_payer_pubkey = str(mock_keypair.pubkey())

    async def verify(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Mock verify - always returns valid."""
        return VerifyResponse(is_valid=True, invalid_reason=None, payer="MockPayer")

    async def settle(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Mock settle - always returns success with fake signature."""
        import base64
        from solders.transaction import VersionedTransaction
        
        # Decode the transaction to show details
        try:
            # Extract transaction from payload - handle both dict and object
            if isinstance(payment_payload.payload, dict):
                tx_base64 = payment_payload.payload.get('transaction')
            else:
                # It's already an object (ExactSvmPaymentPayload from fork)
                tx_base64 = getattr(payment_payload.payload, 'transaction', None)
            
            if tx_base64:
                tx_bytes = base64.b64decode(tx_base64)
                transaction = VersionedTransaction.from_bytes(tx_bytes)
                
                print("="*60)
                print("🎯 MOCK SOLANA PAYMENT SETTLED")
                print("="*60)
                print(f"Network: {payment_requirements.network}")
                print(f"Amount: {payment_requirements.max_amount_required} (atomic units)")
                print(f"To: {payment_requirements.pay_to}")
                print(f"Asset: {payment_requirements.asset}")
                print(f"\n📝 Transaction Details:")
                print(f"Signatures: {len(transaction.signatures)}")
                for i, sig in enumerate(transaction.signatures):
                    print(f"  Signature {i+1}: {sig}")
                print(f"\n🔗 In real mode, view on Solana Explorer:")
                print(f"https://explorer.solana.com/tx/<SIGNATURE>?cluster=devnet")
                print("="*60)
        except Exception as e:
            print(f"Error decoding transaction: {e}")
        
        # Return mock success
        mock_signature = "5" + "M" * 86 + "ock"  # Fake but properly formatted signature
        return SettleResponse(
            success=True,
            transaction=mock_signature,
            network=payment_requirements.network,
            payer=self.fee_payer_pubkey,
            error_reason=None,
        )

    async def close(self):
        """No-op for mock."""
        pass

    @property
    def fee_payer_address(self) -> str:
        """Get the mock fee payer's address."""
        return self.fee_payer_pubkey

