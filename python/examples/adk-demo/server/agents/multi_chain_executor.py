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
"""Multi-chain executor that handles both EVM and Solana payments."""

import os
from typing import Optional

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from x402_a2a.executors import x402ServerExecutor
from x402_a2a import (
    FacilitatorClient,
    FacilitatorConfig,
    x402ExtensionConfig,
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
)

from .mock_facilitator import MockFacilitator
from .solana_facilitator import MockSolanaFacilitator, DemoSolanaFacilitator


class MultiChainFacilitator:
    """
    Facilitator that routes to the appropriate chain-specific facilitator.
    """

    def __init__(self):
        """Initialize facilitators for all supported chains."""
        # EVM facilitator - always use mock for this demo
        # (The demo focuses on Solana; for EVM configure FacilitatorConfig separately)
        self.evm_facilitator = MockFacilitator()
        
        # Solana facilitator - controlled by USE_MOCK_FACILITATOR
        use_mock = os.getenv("USE_MOCK_FACILITATOR", "true").lower() == "true"
        if use_mock:
            self.solana_facilitator = MockSolanaFacilitator()
            print("🟣 Using Mock Solana Facilitator")
        else:
            self.solana_facilitator = DemoSolanaFacilitator()
            print(f"🟣 Using Real Solana Facilitator: {self.solana_facilitator.fee_payer_pubkey}")

    def _is_solana_network(self, network: str) -> bool:
        """Check if the network is Solana."""
        return network in ["solana", "solana-devnet"]

    async def verify(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> VerifyResponse:
        """Route verification to the appropriate facilitator."""
        if self._is_solana_network(payment_requirements.network):
            print(f"🟣 Verifying Solana payment on {payment_requirements.network}")
            return await self.solana_facilitator.verify(payment_payload, payment_requirements)
        else:
            print(f"🔵 Verifying EVM payment on {payment_requirements.network}")
            return await self.evm_facilitator.verify(payment_payload, payment_requirements)

    async def settle(
        self,
        payment_payload: PaymentPayload,
        payment_requirements: PaymentRequirements,
    ) -> SettleResponse:
        """Route settlement to the appropriate facilitator."""
        if self._is_solana_network(payment_requirements.network):
            print(f"🟣 Settling Solana payment on {payment_requirements.network}")
            return await self.solana_facilitator.settle(payment_payload, payment_requirements)
        else:
            print(f"🔵 Settling EVM payment on {payment_requirements.network}")
            return await self.evm_facilitator.settle(payment_payload, payment_requirements)

    async def close(self):
        """Close all facilitator connections."""
        if hasattr(self.evm_facilitator, 'close'):
            await self.evm_facilitator.close()
        if hasattr(self.solana_facilitator, 'close'):
            await self.solana_facilitator.close()


class MultiChainMerchantExecutor(x402ServerExecutor):
    """
    Merchant executor that supports both EVM and Solana payments.
    
    Automatically routes verification and settlement to the appropriate
    chain-specific facilitator based on the payment network.
    """

    def __init__(self, delegate: AgentExecutor):
        """
        Initialize with multi-chain facilitator support.
        
        Args:
            delegate: The underlying agent executor
        """
        # Initialize the base x402ServerExecutor
        config = x402ExtensionConfig()
        super().__init__(delegate, config)
        
        # Use multi-chain facilitator instead of single-chain
        self._facilitator = MultiChainFacilitator()

    async def verify_payment(
        self, payload: PaymentPayload, requirements: PaymentRequirements
    ) -> VerifyResponse:
        """Verify payment using the appropriate facilitator."""
        return await self._facilitator.verify(payload, requirements)

    async def settle_payment(
        self, payload: PaymentPayload, requirements: PaymentRequirements
    ) -> SettleResponse:
        """Settle payment using the appropriate facilitator."""
        result = await self._facilitator.settle(payload, requirements)
        
        # Log the result for debugging
        if result.success:
            print(f"✅ Payment settled successfully!")
            print(f"   Transaction: {result.transaction}")
            print(f"   Network: {result.network}")
            if hasattr(result, 'payer'):
                print(f"   Payer: {result.payer}")
        else:
            print(f"❌ Payment settlement failed: {result.error_reason}")
        
        return result

