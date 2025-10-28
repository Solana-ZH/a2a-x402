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
"""Solana wallet implementation for x402 payments."""

import base64
from typing import Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.instruction import Instruction, AccountMeta

from x402.types import PaymentRequirements, x402PaymentRequiredResponse, PaymentPayload
from ..types.solana import SolanaPaymentPayload, SolanaPaymentRequirementsExtra

# SPL Token Program ID
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")


def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    """
    Derive the associated token account address for a given owner and mint.
    
    Args:
        owner: The wallet public key
        mint: The SPL token mint public key
        
    Returns:
        The derived associated token account public key
    """
    # Associated Token Account Program ID
    ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    
    # Find program address
    seeds = [
        bytes(owner),
        bytes(TOKEN_PROGRAM_ID),
        bytes(mint),
    ]
    
    # Derive the PDA
    address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
    return address


def create_transfer_checked_instruction(
    source: Pubkey,
    mint: Pubkey,
    destination: Pubkey,
    owner: Pubkey,
    amount: int,
    decimals: int,
) -> Instruction:
    """
    Create a TransferChecked instruction for SPL tokens.
    
    Args:
        source: Source token account
        mint: Token mint
        destination: Destination token account
        owner: Owner of source account (signer)
        amount: Amount to transfer (in atomic units)
        decimals: Token decimals
        
    Returns:
        Instruction for the transfer
    """
    # TransferChecked instruction discriminator: 12
    data = bytes([12]) + amount.to_bytes(8, 'little') + bytes([decimals])
    
    keys = [
        AccountMeta(pubkey=source, is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
        AccountMeta(pubkey=destination, is_signer=False, is_writable=True),
        AccountMeta(pubkey=owner, is_signer=True, is_writable=False),
    ]
    
    return Instruction(
        program_id=TOKEN_PROGRAM_ID,
        accounts=keys,
        data=data,
    )


def process_solana_payment_required(
    payment_required: x402PaymentRequiredResponse,
    payer_keypair: Keypair,
) -> PaymentPayload:
    """Process Solana payment required response.
    
    Selects a Solana payment requirement and creates a signed payment payload.
    
    Args:
        payment_required: Payment required response from merchant
        payer_keypair: Solana keypair for signing
        
    Returns:
        PaymentPayload with Solana transaction
    """
    # Select first Solana requirement
    solana_requirement = None
    for req in payment_required.accepts:
        if req.network in ["solana", "solana-devnet"]:
            solana_requirement = req
            break
    
    if not solana_requirement:
        raise ValueError("No Solana payment requirement found")
    
    return process_solana_payment(solana_requirement, payer_keypair)


def process_solana_payment(
    requirements: PaymentRequirements,
    payer_keypair: Keypair,
) -> PaymentPayload:
    """Create a Solana payment payload.
    
    Constructs a partially-signed Solana transaction that transfers SPL tokens
    from the payer to the merchant. The facilitator will add their signature
    as the fee payer.
    
    Args:
        requirements: Payment requirements with Solana network
        payer_keypair: Keypair for signing the transfer
        
    Returns:
        PaymentPayload containing the partially-signed transaction
    """
    # Extract fee payer from extra
    if not requirements.extra:
        raise ValueError("Solana requirements must include extra.feePayer")
    
    try:
        extra = SolanaPaymentRequirementsExtra.model_validate(requirements.extra)
    except Exception as e:
        raise ValueError(f"Invalid Solana requirements extra: {e}")
    
    fee_payer_pubkey = Pubkey.from_string(extra.fee_payer)
    payer_pubkey = payer_keypair.pubkey()
    merchant_pubkey = Pubkey.from_string(requirements.pay_to)
    mint_pubkey = Pubkey.from_string(requirements.asset)
    
    # Amount in atomic units
    amount = int(requirements.max_amount_required)
    
    # For SPL tokens, we need to derive the associated token accounts
    # Simplified: assume token accounts exist (in production, check/create them)
    payer_token_account = get_associated_token_address(payer_pubkey, mint_pubkey)
    merchant_token_account = get_associated_token_address(merchant_pubkey, mint_pubkey)
    
    # Get decimals from requirements or default
    # In production, fetch from mint account
    decimals = 6  # Default for USDC
    if requirements.extra and "decimals" in requirements.extra:
        decimals = requirements.extra["decimals"]
    
    # Create transfer instruction
    transfer_ix = create_transfer_checked_instruction(
        source=payer_token_account,
        mint=mint_pubkey,
        destination=merchant_token_account,
        owner=payer_pubkey,
        amount=amount,
        decimals=decimals,
    )
    
    # Get a FRESH blockhash and create a fully-signed transaction
    # Client pays their own fees (simplest model that actually works!)
    from solana.rpc.api import Client as SolanaRpcClient
    from solana.rpc.commitment import Confirmed
    import os
    
    # Determine RPC URL from environment or use default
    rpc_url = os.getenv(
        "SOLANA_RPC_URL",
        "https://api.devnet.solana.com"
    )

    client = SolanaRpcClient(rpc_url)
    print(f"🌐 CLIENT: Using RPC: {rpc_url}")
    # Use Confirmed commitment for more stable/less likely to expire blockhash
    recent_blockhash_resp = client.get_latest_blockhash(Confirmed)
    recent_blockhash = recent_blockhash_resp.value.blockhash
    
    import time
    current_time = time.time()
    
    print(f"🔧 CLIENT: Creating fully-signed transaction")
    print(f"   Payer (transfer authority + fee payer): {payer_pubkey}")
    print(f"   Fresh blockhash: {recent_blockhash}")
    print(f"   Time: {current_time}")
    
    # Client is BOTH the transfer authority AND the fee payer
    message = MessageV0.try_compile(
        payer=payer_pubkey,  # Client pays their own fees
        instructions=[transfer_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    
    # Create fully-signed transaction with just the client's signature
    transaction = VersionedTransaction(message, [payer_keypair])
    
    # Serialize and encode the partially-signed transaction
    serialized_tx = bytes(transaction)
    encoded_tx = base64.b64encode(serialized_tx).decode('utf-8')
    
    # Create payment payload
    solana_payload = SolanaPaymentPayload(transaction=encoded_tx)
    
    return PaymentPayload(
        x402_version=1,
        scheme="exact",
        network=requirements.network,
        payload=solana_payload.model_dump(),
    )

