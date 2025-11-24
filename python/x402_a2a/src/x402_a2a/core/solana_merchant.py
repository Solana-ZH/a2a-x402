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
"""Solana merchant helpers for creating payment requirements."""

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class SolanaPaymentRequirements(BaseModel):
    """Solana-specific payment requirements.
    
    This bypasses upstream x402 validation to support Solana networks locally.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    scheme: str = "exact"
    network: str  # "solana" or "solana-devnet"
    max_amount_required: str = Field(alias="maxAmountRequired")
    resource: str
    description: str
    mime_type: str = Field(default="application/json", alias="mimeType")
    max_timeout_seconds: int = Field(default=600, alias="maxTimeoutSeconds")
    pay_to: str = Field(alias="payTo")
    asset: str
    extra: Optional[dict] = None
    output_schema: Optional[Any] = Field(default=None, alias="outputSchema")
    
    def model_dump(self, **kwargs):
        """Override to always use aliases when serializing."""
        kwargs.setdefault('by_alias', True)
        return super().model_dump(**kwargs)


def create_solana_payment_requirements(
    price: str,  # Amount in atomic units as string
    pay_to_address: str,
    asset_address: str,  # SPL token mint
    resource: str,
    fee_payer_address: str,  # Facilitator's public key
    network: str = "solana-devnet",
    description: str = "",
    decimals: int = 6,
    mime_type: str = "application/json",
    max_timeout_seconds: int = 600,
    output_schema: Optional[Any] = None,
) -> SolanaPaymentRequirements:
    """Create Solana payment requirements without upstream validation.
    
    Args:
        price: Payment amount in atomic units (e.g., "1000000" for 1 USDC with 6 decimals)
        pay_to_address: Merchant's Solana public key (base58)
        asset_address: SPL token mint address
        resource: Resource identifier
        fee_payer_address: Facilitator's public key (will pay transaction fees)
        network: "solana" or "solana-devnet"
        description: Human-readable description
        decimals: Token decimals (6 for USDC)
        mime_type: Expected response content type
        max_timeout_seconds: Payment validity timeout
        output_schema: Response schema
        
    Returns:
        SolanaPaymentRequirements ready for x402PaymentRequiredResponse
    """
    return SolanaPaymentRequirements(
        scheme="exact",
        network=network,
        asset=asset_address,
        pay_to=pay_to_address,
        max_amount_required=price,
        resource=resource,
        description=description,
        mime_type=mime_type,
        max_timeout_seconds=max_timeout_seconds,
        output_schema=output_schema,
        extra={
            "feePayer": fee_payer_address,
            "decimals": decimals,
        },
    )

