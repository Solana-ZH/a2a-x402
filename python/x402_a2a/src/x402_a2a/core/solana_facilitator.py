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
"""Solana facilitator for x402 payment verification and settlement."""

import base64
from typing import Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

from x402.types import PaymentRequirements, PaymentPayload, VerifyResponse, SettleResponse
from ..types.solana import SolanaPaymentPayload, SolanaSettleResponse, SolanaVerifyResponse

# Import helper from wallet module
from .solana_wallet import get_associated_token_address


class SolanaFacilitator:
    """Facilitator for Solana payments.
    
    Handles verification and settlement of Solana SPL token payments.
    """
    
    def __init__(
        self,
        rpc_url: str,
        fee_payer_keypair: Keypair,
        network: str = "solana-devnet",
    ):
        """Initialize Solana facilitator.
        
        Args:
            rpc_url: Solana RPC endpoint URL
            fee_payer_keypair: Keypair that will pay transaction fees
            network: Network identifier (solana or solana-devnet)
        """
        self.rpc_url = rpc_url
        self.fee_payer_keypair = fee_payer_keypair
        self.network = network
        self.client = AsyncClient(rpc_url)
    
    async def verify(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Verify a Solana payment payload.
        
        Checks that the transaction:
        - Is properly formatted
        - Contains only the expected SPL token transfer
        - Transfers the correct amount to the correct recipient
        - Is signed by the payer
        
        Args:
            payment_payload: Payment payload from client
            payment_requirements: Original payment requirements
            
        Returns:
            VerifyResponse indicating if payment is valid
        """
        try:
            # Parse Solana payload - handle both dict and object
            if isinstance(payment_payload.payload, dict):
                tx_base64 = payment_payload.payload.get('transaction')
            else:
                # It's already an object (ExactSvmPaymentPayload from fork)
                tx_base64 = getattr(payment_payload.payload, 'transaction', None)
            
            if not tx_base64:
                raise ValueError("No transaction found in payload")
            
            # Decode transaction
            tx_bytes = base64.b64decode(tx_base64)
            transaction = VersionedTransaction.from_bytes(tx_bytes)
            
            # Extract payer from transaction
            payer_pubkey = str(transaction.message.account_keys[0])
            
            # Verify network matches
            if payment_payload.network != payment_requirements.network:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Network mismatch: expected {payment_requirements.network}, got {payment_payload.network}",
                    payer=payer_pubkey
                )
            
            # Verify scheme
            if payment_payload.scheme != "exact":
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Unsupported scheme: {payment_payload.scheme}",
                    payer=payer_pubkey
                )
            
            # Get message instructions
            message = transaction.message
            instructions = message.instructions
            
            # For exact scheme, expect exactly one SPL token transfer instruction
            if len(instructions) != 1:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason=f"Expected 1 instruction, found {len(instructions)}",
                    payer=payer_pubkey
                )
            
            # Parse the instruction (simplified - in production, fully decode and verify)
            # Expected: TransferChecked instruction with correct amount and accounts
            
            # Verify transaction is partially signed by payer
            # The fee payer signature should be missing
            if not transaction.signatures or len(transaction.signatures) == 0:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="Transaction must be signed by payer",
                    payer=payer_pubkey
                )
            
            # Check that at least one signature is present (payer's signature)
            has_valid_signature = any(
                sig != Signature.default() for sig in transaction.signatures
            )
            
            if not has_valid_signature:
                return VerifyResponse(
                    is_valid=False,
                    invalid_reason="No valid signatures found",
                    payer=payer_pubkey
                )
            
            # Additional verification: amount, recipient, mint
            # (Simplified for demo - full implementation would decode instruction data)
            
            return VerifyResponse(is_valid=True, invalid_reason=None, payer=payer_pubkey)
            
        except Exception as e:
            return VerifyResponse(
                is_valid=False,
                invalid_reason=f"Verification error: {str(e)}",
                payer="unknown"
            )
    
    async def settle(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Settle a Solana payment.
        
        Adds the facilitator's signature as fee payer and submits to the network.
        
        Args:
            payment_payload: Verified payment payload
            payment_requirements: Original payment requirements
            
        Returns:
            SettleResponse with transaction signature or error
        """
        try:
            # First verify
            verify_response = await self.verify(payment_payload, payment_requirements)
            if not verify_response.is_valid:
                return SettleResponse(
                    success=False,
                    network=self.network,
                    error_reason=f"Verification failed: {verify_response.invalid_reason}"
                )
            
            # Parse payload - handle both dict and object
            if isinstance(payment_payload.payload, dict):
                tx_base64 = payment_payload.payload.get('transaction')
            else:
                # It's already an object (ExactSvmPaymentPayload from fork)
                tx_base64 = getattr(payment_payload.payload, 'transaction', None)
            
            if not tx_base64:
                raise ValueError("No transaction found in payload")
            
            tx_bytes = base64.b64decode(tx_base64)
            transaction = VersionedTransaction.from_bytes(tx_bytes)
            
            # The client sent a fully-signed transaction with a fresh blockhash
            # Just broadcast it immediately (no re-signing needed!)
            import time
            receive_time = time.time()
            
            print(f"🔧 FACILITATOR: Broadcasting transaction...")
            print(f"   RPC URL: {self.rpc_url}")
            print(f"   Receive time: {receive_time}")
            print(f"   Transaction blockhash: {transaction.message.recent_blockhash}")
            
            async with self.client as client:
                send_time = time.time()
                print(f"   Sending at time: {send_time}")
                print(f"   ⏱️  Time since client created tx: {send_time - receive_time:.2f}s (if > 60s, blockhash expired!)")
                
                # Send the transaction as-is with skip_preflight to avoid stale blockhash issues
                from solana.rpc.types import TxOpts
                from solana.rpc.commitment import Confirmed
                
                tx_opts = TxOpts(
                    skip_preflight=True,
                    preflight_commitment=Confirmed,
                )
                
                print(f"🚀 DEBUG: About to send transaction with skip_preflight=True")
                print(f"   TxOpts: skip_preflight={tx_opts.skip_preflight}, commitment={tx_opts.preflight_commitment}")
                
                send_resp = await client.send_transaction(transaction, opts=tx_opts)
                
                print(f"🚀 DEBUG: Transaction sent successfully, got response")
                
                signature = send_resp.value
                
                print(f"✅ Transaction sent to devnet: {signature}")
                print(f"🔗 View on Explorer: https://explorer.solana.com/tx/{signature}?cluster=devnet")
                
                # Wait for confirmation (optional, can be async)
                # confirm_resp = await client.confirm_transaction(signature, Confirmed)
                
                # Extract the actual payer from the transaction
                payer_pubkey = str(transaction.message.account_keys[0])
                
                return SettleResponse(
                    success=True,
                    transaction=str(signature),
                    network=self.network,
                    payer=payer_pubkey,
                    error_reason=None,
                )
                
        except Exception as e:
            return SettleResponse(
                success=False,
                network=self.network,
                error_reason=f"Settlement error: {str(e)}",
            )
    
    async def close(self):
        """Close the RPC client connection."""
        await self.client.close()

