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
"""Solana-specific types for x402 payments.

These types extend the x402 protocol to support Solana payments.
Once upstream x402 adds Solana support, these should be replaced with official types.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


# Extend SupportedNetworks to include Solana
SolanaSupportedNetworks = Literal["solana", "solana-devnet"]


class SolanaPaymentPayload(BaseModel):
    """Payload for Solana exact scheme payments.
    
    Contains a partially-signed Solana transaction that transfers SPL tokens
    from the payer to the merchant. The facilitator will add their signature
    as the fee payer and submit to the network.
    """
    
    # Base64-encoded serialized Solana transaction (partially signed by client)
    transaction: str = Field(
        description="Base64-encoded serialized Solana VersionedTransaction, partially signed by payer"
    )


class SolanaPaymentRequirementsExtra(BaseModel):
    """Extra fields for Solana PaymentRequirements.
    
    Required for the exact scheme on Solana to specify the fee payer.
    Supports both snake_case (fee_payer) and camelCase (feePayer) for compatibility.
    """
    
    model_config = ConfigDict(populate_by_name=True)
    
    fee_payer: str = Field(
        alias="feePayer",
        description="Public key (base58) of the account that will pay transaction fees (typically facilitator)"
    )
    decimals: Optional[int] = Field(
        default=6,
        description="Number of decimals for the SPL token (e.g., 6 for USDC)"
    )


class SolanaSettleResponse(BaseModel):
    """Response from settling a Solana payment."""
    
    success: bool
    transaction: Optional[str] = Field(
        None, description="Base58-encoded transaction signature if successful"
    )
    network: str = Field(description="Solana network (solana or solana-devnet)")
    payer: Optional[str] = Field(
        None, description="Base58-encoded public key of the fee payer"
    )
    error_reason: Optional[str] = Field(None, description="Error message if failed")


class SolanaVerifyResponse(BaseModel):
    """Response from verifying a Solana payment."""
    
    is_valid: bool
    invalid_reason: Optional[str] = None

